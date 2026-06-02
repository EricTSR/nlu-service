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
    """
    Rangiert Kandidaten basierend auf semantischer Ähnlichkeit zu Suchpräferenzen.
    
    - Query wird konstruiert aus Dialog + allen Präferenzen (natürlichsprachig)
    - Haupttext wird einmal embedded und gereiht (70% Gewicht)
    - Lange Texte werden zusätzlich in Sätze zerlegt und gematched (30% Gewicht)
    
    Request:
        - candidates: Liste mit {id, description}
        - preferences: SDGs, Location, Online, Thematic Focus, Impact Area, etc.
        - dialogContext: Bisheriger Chatverlauf (optional)
    
    Response:
        - results: Sortierte Liste mit {id, semanticScore}
    """
    print(f"📥 Ranking request: {len(request.candidates)} candidates")
    result = rank_semantically(request)
    print(f"📤 Ranking response: {len(result.results)} results")
    return result
