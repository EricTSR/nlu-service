import logging
import time
from fastapi import APIRouter

from src.posts.models import SemanticRankResponseDto, SemanticRankRequestDto
from src.services.semantic_ranker import rank_semantically

logger = logging.getLogger(__name__)

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
    """
    Rangiert Kandidaten basierend auf semantischer Ähnlichkeit zu Suchpräferenzen.
    """
    start_time = time.time()
    
    logger.info(f"📥 Ranking request: {len(request.candidates)} candidates")
    
    result = rank_semantically(request)
    
    elapsed_time = time.time() - start_time
    logger.info(f"📤 Ranking response: {len(result.results)} results in {elapsed_time:.3f}s")
    
    return result
