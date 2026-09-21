from fastapi import APIRouter

from src.api.endpoints.health import router as health_router
from src.api.endpoints.nlu import router as nlu_router
from src.api.endpoints.semantic import router as semantic_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(nlu_router)
api_router.include_router(semantic_router)

