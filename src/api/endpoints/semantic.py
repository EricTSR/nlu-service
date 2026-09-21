from fastapi import APIRouter

from src.api.dependencies import EmbeddingModelProviderDep
from src.schemas.semantic import SemanticRankRequestDto, SemanticRankResponseDto
from src.semantic.ranking import rank_semantically

router = APIRouter(prefix="/api/v1/semantic", tags=["Semantic Ranking"])


@router.post(
    "/rank",
    response_model=SemanticRankResponseDto,
    summary="Rank items semantically based on user preferences",
)
def rank_items(
    request: SemanticRankRequestDto,
    model_provider: EmbeddingModelProviderDep,
) -> SemanticRankResponseDto:
    """
    Rangiert Kandidaten basierend auf semantischer Ähnlichkeit zu Suchpräferenzen.
    """
    return rank_semantically(request, model_provider)
