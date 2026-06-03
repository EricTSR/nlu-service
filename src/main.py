from fastapi import FastAPI, status

from src.api.routes_nlu import router as nlu_router
from src.api.routes_semantic import router as semantic_router
from src.schemas.health import HealthCheck
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s:%(name)s:%(message)s"
)

app = FastAPI(
    title="NLU Service",
    version="1.0.0",
    description="NLU microservice for intent matching and preference extraction."
)


# YAGNI?!
@app.get("/health",
         tags=["Health"],
         summary="Perform a Health Check",
         response_description="Return HTTP Status Code 200 (OK)",
         response_model=HealthCheck,
         status_code=status.HTTP_200_OK,
         )
def get_health() -> HealthCheck:
    return HealthCheck()


app.include_router(nlu_router)
app.include_router(semantic_router)
