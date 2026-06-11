"""
Semantic Ranking Service für Items basierend auf Benutzer-Keywords.
Rangiert Kandidaten durch semantische Ähnlichkeit zwischen Nutzertext und Beschreibung.
"""

import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.schemas.semantic import (
    SemanticRankRequestDto, SemanticRankResponseDto, 
    NluRankItemDto
)
from src.services.model_loader import get_model

logger = logging.getLogger(__name__)

MAIN_SIM_WEIGHT = 0.4
CHUNK_SIM_WEIGHT = 0.6
TOP_K_CHUNKS = 3


def build_ranking_query(request: SemanticRankRequestDto) -> str:
    """
    Konstruiert eine Query ausschließlich aus Benutzertext.

    """
    user_messages = []
    fallback_messages = []

    for dialog_message in request.dialogContext:
        print(dialog_message)
        message_text = normalize_text(getattr(dialog_message, "message", None))
        if len(message_text) <= 1:
            continue

        fallback_messages.append(message_text)

        sender = getattr(dialog_message, "sender", None)
        if isinstance(sender, str) and sender.upper() == "USER":
            user_messages.append(message_text)

    source_messages = user_messages or fallback_messages
    query = normalize_text(" ".join(dict.fromkeys(source_messages)))

    logger.debug(f"🔍 Optimized Query: '{query}'")
    return query


def calculate_chunk_similarity(
    query_embedding: np.ndarray,
    text: str,
    model
) -> float:
    """
    Teile langen Text in Sätze auf und berechne beste Similarity.
    
    Nutzung: Wenn Beschreibung lang ist (> 200 Zeichen),
    könnte ein einzelner Satz perfekt zur Query passen.
    """
    # Teile in Sätze
    sentences = [
        s.strip() 
        for s in text.replace("!", ".").split(".") 
        if s.strip() and len(s.strip()) > 10
    ]
    
    if not sentences or len(sentences) == 1:
        # Zu wenig oder nur 1 Satz: fallback auf normal
        return float(cosine_similarity(
            query_embedding.reshape(1, -1),
            model.encode([text]).reshape(1, -1)
        )[0][0])
    
    # Bei zu vielen Sätzen: sample Top-10 (zu viele = langsam)
    if len(sentences) > 10:
        sentences = sorted(sentences, key=len, reverse=True)[:10]
    
    # Embedde alle Sätze
    chunk_embeddings = model.encode(sentences)
    
    # Berechne Similarity zu jedem Chunk
    similarities = cosine_similarity(
        query_embedding.reshape(1, -1),
        chunk_embeddings
    )[0]
    
    # Fokus auf die besten Treffer statt den Durchschnitt über alle Sätze.
    top_k = min(TOP_K_CHUNKS, len(similarities))
    top_k_similarities = np.sort(similarities)[-top_k:]
    return float(np.mean(top_k_similarities))


def rank_semantically(
        request: SemanticRankRequestDto
) -> SemanticRankResponseDto:
    """
    Rangiert Kandidaten basierend auf semantischer Ähnlichkeit.
    
    Strategie:
    - 40% Haupttext-Ähnlichkeit
    - 60% Top-Chunk-Ähnlichkeit (bei langen Texten)
    """
    if not request.candidates:
        return SemanticRankResponseDto(results=[])

    print("req", request)
    query_text = build_ranking_query(request)
    if not query_text:
        logger.info("Keine Benutzer-Keywords im Dialogkontext gefunden - alle Kandidaten erhalten Score 0.0")
        return SemanticRankResponseDto(
            results=[
                NluRankItemDto(id=candidate.id, semanticScore=0.0)
                for candidate in request.candidates
            ]
        )

    model = get_model()

    candidate_texts = [
        normalize_text(candidate.description)
        for candidate in request.candidates
    ]
    query_embedding = model.encode([query_text])[0]
    candidate_embeddings = model.encode(candidate_texts)

    results = []
    
    for candidate, cand_embedding, cand_text in zip(
        request.candidates, candidate_embeddings, candidate_texts
    ):
        scores = {}
        
        # Score 1: Haupt-Text Similarity (40%)
        main_sim = float(cosine_similarity(
            query_embedding.reshape(1, -1),
            cand_embedding.reshape(1, -1)
        )[0][0])
        scores['main'] = main_sim * MAIN_SIM_WEIGHT
        
        # Score 2: Chunked Similarity für längere Texte (60%)
        if len(cand_text) > 200:
            chunk_sim = calculate_chunk_similarity(
                query_embedding, cand_text, model
            )
            scores['chunks'] = chunk_sim * CHUNK_SIM_WEIGHT
        else:
            scores['chunks'] = main_sim * CHUNK_SIM_WEIGHT
        
        final_score = sum(scores.values())
        
        results.append(NluRankItemDto(
            id=candidate.id,
            semanticScore=normalize_similarity(final_score)
        ))
        
        logger.debug(f"📊 Candidate {candidate.id}: main={scores['main']:.3f}, "
                     f"chunks={scores['chunks']:.3f} → total={final_score:.3f}")

    # Sortiere nach Score (descending)
    results.sort(key=lambda item: item.semanticScore, reverse=True)

    return SemanticRankResponseDto(results=results)


def normalize_text(value: str | None) -> str:
    """
    Normalisierung: Whitespace entfernen und vereinheitlichen.
    """
    if not value:
        return ""
    return " ".join(value.strip().split())


def normalize_similarity(value: float) -> float:
    """
    Normalisiert Ähnlichkeitsscore auf 0-1 Bereich.
    
    Cosine Similarity liegt theoretisch zwischen -1 und 1.
    Für Ranking wird sie auf 0 bis 1 begrenzt.
    
    Args:
        value: Ähnlichkeitswert
    
    Returns:
        Normalisierter Wert im Range [0, 1]
    """
    return max(0.0, min(1.0, value))

