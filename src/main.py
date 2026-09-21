import logging

from fastapi import FastAPI

from src.api.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)


def create_application() -> FastAPI:
    application = FastAPI(
        title="NLU Service",
        version="1.0.0",
        description="NLU microservice for intent matching and preference extraction.",
    )
    application.include_router(api_router)
    return application


app = create_application()
