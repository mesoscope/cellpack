import asyncio
from aiohttp import web
from cellpack.autopack.DBRecipeHandler import DataDoc, DBUploader
from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS
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

    def job_exists(self, dedup_hash):
        """
        Check if a job already exists for this dedup_hash.
        Returns True if a document exists, False otherwise.
        """
        db = self._get_firebase_handler()
        if not db:
            return False

        job_status, _ = db.get_doc_by_id("job_status", dedup_hash)
        return job_status is not None

    async def run_packing(self, dedup_hash, recipe=None, config=None, body=None):
        self.update_job_status(dedup_hash, "RUNNING")
        try:
            # Pack JSON recipe in body if provided, otherwise use recipe path
            pack(recipe=(body if body else recipe), config_path=config, docker=True, hash=dedup_hash)
        except Exception as e:
            self.update_job_status(dedup_hash, "FAILED", error_message=str(e))

    def update_job_status(self, dedup_hash, status, result_path=None, error_message=None):
        db = self._get_firebase_handler()
        if db:
            db_uploader = DBUploader(db)
            db_uploader.upload_job_status(dedup_hash, status, result_path, error_message)

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

        dedup_hash = DataDoc.generate_hash(body)

        if self.job_exists(dedup_hash):
            return web.json_response({"jobId": dedup_hash})

        # Initiate packing task to run in background
        packing_task = asyncio.create_task(self.run_packing(dedup_hash, recipe, config, body))

        # Keep track of task references to prevent them from being garbage
        # collected, then discard after task completion
        self.packing_tasks.add(packing_task)
        packing_task.add_done_callback(self.packing_tasks.discard)

        return web.json_response({"jobId": dedup_hash})


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