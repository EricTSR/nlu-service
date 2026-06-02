from fastapi import APIRouter

from src.posts.models import SemanticRankResponseDto, SemanticRankRequestDto
from src.services.semantic_ranker import rank_semantically

router = APIRouter(
    prefix="/api/v1/semantic",
    tags=["Semantic Ranking"]
)

@router.post(
    "/rank",
    response_model=SemanticRankResponseDto,
    summary="Rank items semantically based on user preferences",
)
def rank_items(request: SemanticRankRequestDto) -> SemanticRankResponseDto:
    print(f"📥 Ranking request: {len(request.candidates)} candidates")
    result = rank_semantically(request)
    print(f"📤 Ranking response: {len(result.results)} results")
    return result
