import asyncio
from aiohttp import web
import uuid
from cellpack.autopack.DBRecipeHandler import DBUploader
from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS
from cellpack.bin.pack import pack

SERVER_PORT = 80

class CellpackServer:
    def __init__(self):
        self.packing_tasks = set()

    async def run_packing(self, recipe, config, job_id, body=None):
        self.update_job_status(job_id, "RUNNING")
        try:
            pack(recipe=recipe, config_path=config, docker=True, json_recipe=body, job_id=job_id)
        except Exception as e:
            self.update_job_status(job_id, "FAILED", error_message=str(e))

    def update_job_status(self, job_id, status, result_path=None, error_message=None):
        handler = DATABASE_IDS.handlers().get("firebase")
        initialized_db = handler(
            default_db="staging"
        )
        if initialized_db._initialized:
            db_uploader = DBUploader(initialized_db)
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
        job_id = str(uuid.uuid4())

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