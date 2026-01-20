import asyncio
from aiohttp import web
from cellpack.autopack.DBRecipeHandler import DBUploader
from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS
from cellpack.autopack.loaders.recipe_loader import RecipeLoader
from cellpack.bin.pack import pack

SERVER_PORT = 80

class CellpackServer:
    def __init__(self):
        self.packing_tasks = set()

    def _get_firebase_handler(self, database_name="firebase"):
        handler = DATABASE_IDS.handlers().get(database_name)
        initialized_db = handler(default_db="staging")
        if initialized_db._initialized:
            return initialized_db
        return None

    def get_cached_result(self, job_id):
        """
        Check if a completed result already exists for this job_id (dedup_hash).
        Returns the cached result data if found with status DONE, otherwise None.
        """
        db = self._get_firebase_handler()
        if not db:
            return None

        job_status, _ = db.get_doc_by_id("job_status", job_id)
        if job_status and job_status.get("status") == "DONE":
        # TODO: if the same recipe is submitted again quickly, the status may not be updated in time ("RUNNING"), discuss if we need to handle this case
            return job_status
        return None

    async def run_packing(self, recipe, config, job_id, body=None):
        self.update_job_status(job_id, "RUNNING")
        try:
            pack(recipe=recipe, config_path=config, docker=True, json_recipe=body, job_id=job_id)
        except Exception as e:
            self.update_job_status(job_id, "FAILED", error_message=str(e))

    def update_job_status(self, job_id, status, result_path=None, error_message=None):
        db = self._get_firebase_handler()
        if db:
            db_uploader = DBUploader(db)
            db_uploader.upload_job_status(job_id, status, result_path, error_message)

    async def hello_world(self, request: web.Request) -> web.Response:
        return web.Response(text="Hello from the cellPACK server")

    async def health_check(self, request: web.Request) -> web.Response:
        # healthcheck endpoint needed for AWS load balancer
        return web.Response()

    async def pack_handler(self, request: web.Request) -> web.Response:
        recipe = request.rel_url.query.get("recipe") or ""
        if request.can_read_body:
            body = await request.json()
        else:
            body = None
        if not recipe and not body:
            raise web.HTTPBadRequest(
                "Pack requests must include recipe as a query param"
            )
        config = request.rel_url.query.get("config")

        # calculate dedup_hash from normalized recipe content
        # TODO: discuss when to hash firebase recipes(has references) vs raw json, this currently loads and processes the recipe twice (one here and once in pack())
        job_id = RecipeLoader.get_dedup_hash(recipe, json_recipe=body, use_docker=True)

        cached_result = self.get_cached_result(job_id)
        if cached_result:
            return web.json_response({
                "jobId": job_id,
                "status": "DONE",
                "cached": True,
                "outputs_directory": cached_result.get("outputs_directory"),
                "result_path": cached_result.get("result_path"),
            })

        # Initiate packing task to run in background
        packing_task = asyncio.create_task(self.run_packing(recipe, config, job_id, body))

        # Keep track of task references to prevent them from being garbage
        # collected, then discard after task completion
        self.packing_tasks.add(packing_task)
        packing_task.add_done_callback(self.packing_tasks.discard)

        # return job id immediately, rather than wait for task to complete,
        # to avoid timeout issues with API gateway
        return web.json_response({"jobId": job_id})


async def init_app() -> web.Application:
    app = web.Application()
    server = CellpackServer()
    app.add_routes(
        [
            web.get("/hello", server.hello_world),
            web.post("/start-packing", server.pack_handler),
            web.get("/", server.health_check)
        ]
    )
    return app

web.run_app(init_app(), host="0.0.0.0", port=SERVER_PORT)