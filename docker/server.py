from aiohttp import web
import os
import uuid
from cellpack.bin.pack import pack

SERVER_PORT = 80

async def hello_world(request: web.Request) -> web.Response:
    return web.Response(text="Hello from the cellPACK server")

async def health_check(request: web.Request) -> web.Response:
    # healthcheck endpoint needed for AWS load balancer
    return web.Response()

async def pack_handler(request: web.Request) -> web.Response:
    recipe = request.rel_url.query.get("recipe")
    if recipe is None:
        raise web.HTTPBadRequest(
            "Pack requests must include recipe as a query param"
        )
    config = request.rel_url.query.get("config")
    job_id = str(uuid.uuid4())
    os.environ["AWS_BATCH_JOB_ID"] = job_id
    try:
        pack(recipe=recipe, config_path=config, docker=True)
    except Exception as e:
        raise web.HTTPInternalServerError(e)
    return web.json_response({"jobId": job_id})

async def init_app() -> web.Application:
    app = web.Application()
    app.add_routes(
        [
            web.get("/hello", hello_world),
            web.get("/pack", pack_handler),
            web.get("/", health_check)
        ]
    )
    return app

web.run_app(init_app(), host="0.0.0.0", port=SERVER_PORT)