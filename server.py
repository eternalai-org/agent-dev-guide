from dotenv import load_dotenv
load_dotenv()

import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from app.configs import settings
from app.apis import api_router
import logging

print(f"Loaded port from settings: {settings.port}")

logging_fmt = "%(asctime)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=logging_fmt)
logger = logging.getLogger(__name__)

async def lifespan(app: fastapi.FastAPI):
    logger.info(f"Starting Launchpad Agent server at {settings.host}:{settings.port}")

    try:
        yield

    except Exception as e:
        logger.error(f"Error: {e}")
        raise e

    finally:
        logger.info("Shutting down server")

def main():

    server_app = fastapi.FastAPI(
        lifespan=lifespan
    )

    server_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    server_app.include_router(api_router)

    @server_app.get("/health")
    async def healthcheck():
        return {"status": "ok", "message": "Yo, I am still alive"}

    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    config = uvicorn.Config(
        server_app,
        loop=event_loop,
        host=settings.host,
        port=settings.port,
        log_level="warning",
        timeout_keep_alive=300,
        workers=32
    )

    server = uvicorn.Server(config)
    event_loop.run_until_complete(server.serve())

if __name__ == '__main__':
    main() 