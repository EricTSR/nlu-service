"""
Semantic Ranking Service für Items basierend auf Suchpräferenzen.
Rangiert Kandidaten durch semantische Ähnlichkeit zwischen Query und Beschreibung.
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


# SDG-Labels für natürlichsprachige Query-Konstruktion
SDG_LABELS = {
    1: "Armut", 2: "Hunger", 3: "Gesundheit", 4: "Bildung",
    5: "Gleichstellung", 6: "Wasser", 7: "Saubere Energie",
    8: "Menschenwürdige Arbeit", 9: "Innovation", 10: "Ungleichheiten",
    11: "Nachhaltige Städte", 12: "Nachhaltiger Konsum", 13: "Klimaschutz",
    14: "Leben im Wasser", 15: "Leben an Land", 16: "Frieden", 17: "Partnerschaften"
}

# Thematic Focus Labels
THEMATIC_LABELS = {
    "CLIMATE_PROTECTION": "Klimaschutz",
    "EDUCATION": "Bildung",
    "CIRCULAR_ECONOMY": "Kreislaufwirtschaft",
    "BIODIVERSITY": "Biodiversität",
    "SUSTAINABLE_FINANCE": "Nachhaltige Finanzen",
    "HUMAN_RIGHTS": "Menschenrechte",
    "GENDER_EQUITY": "Gleichstellung",
    "PARTICIPATION": "Beteiligung",
    "SUSTAINABLE_BUILDING": "Nachhaltiges Bauen",
    "SUSTAINABLE_BUSINESS": "Nachhaltiges Wirtschaften",
    "SOCIAL_JUSTICE": "Soziale Gerechtigkeit",
    "AGRICULTURE": "Landwirtschaft",
    "MOBILITY": "Mobilität",
    "PEACE": "Frieden",
    "INTERNATIONAL_RESPONSIBILITY": "Internationale Verantwortung",
    "CULTURAL_SOCIAL_CHANGE": "Kultureller Wandel",
    "SPORT": "Sport",
    "URBAN_DEVELOPMENT": "Stadtentwicklung",
    "TOURISM": "Tourismus",
    "DIGITALIZATION": "Digitalisierung",
    "OTHER": "Sonstiges",
}


def build_ranking_query(request: SemanticRankRequestDto) -> str:
    """
    Konstruiert eine natürlichsprachige Query aus Dialog und Präferenzen.
    """
    parts = []
    
    # 1. Dialog-Nachrichten (aktueller User-Intent)
    messages = [
        message.message
        for message in request.dialogContext
        if getattr(message, "message", None) and len(message.message) > 5
    ]
    if messages:
        parts.append(messages[0])  # Nur wichtigste Message
    
    # 2. SDGs (als Label, nicht Zahlen)
    if request.preferences.sdgs:
        sdg_text = " ".join(
            SDG_LABELS.get(sdg, f"SDG{sdg}") for sdg in request.preferences.sdgs
        )
        parts.append(sdg_text)
    
    # 3. Thematic Focus
    if request.preferences.thematicFocus:
        theme = THEMATIC_LABELS.get(
            request.preferences.thematicFocus.value 
            if hasattr(request.preferences.thematicFocus, 'value')
            else str(request.preferences.thematicFocus),
            ""
        )
        if theme:
            parts.append(theme)
    
    # 4. Location
    if request.preferences.location:
        if request.preferences.location.city:
            parts.append(request.preferences.location.city)
        if request.preferences.location.country:
            parts.append(request.preferences.location.state)
        if request.preferences.location.country:
            parts.append(request.preferences.location.country)
    
    # 5. Online/Vor Ort
    if request.preferences.online is not None:
        format_word = "online" if request.preferences.online else "vor Ort"
        parts.append(format_word)
    
    # 6. Impact Area
    if request.preferences.impactArea:
        impact_map = {
            "LOCAL": "lokal",
            "REGIONAL": "regional",
            "STATE": "landesweit",
            "COUNTRY": "bundesweit",
            "CONTINENT": "europaweit",
            "WORLD": "global"
        }
        impact_key = request.preferences.impactArea.value \
            if hasattr(request.preferences.impactArea, 'value') \
            else str(request.preferences.impactArea)
        if impact_key in impact_map:
            parts.append(impact_map[impact_key])
    
    query = normalize_text(" ".join(parts))
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
    
    # Kombiniere: 70% Durchschnitt + 30% Bestes Match
    avg_sim = float(np.mean(similarities))
    top_sim = float(np.max(similarities))
    
    return (0.7 * avg_sim) + (0.3 * top_sim)


def rank_semantically(request: SemanticRankRequestDto) -> SemanticRankResponseDto:
    """
    Rangiert Kandidaten basierend auf semantischer Ähnlichkeit.
    
    Strategie:
    - 70% Haupttext-Ähnlichkeit
    - 30% Chunk-Ähnlichkeit (bei langen Texten)
    """
    if not request.candidates:
        return SemanticRankResponseDto(results=[])

    model = get_model()
    query_text = build_ranking_query(request)

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
        
        # Score 1: Haupt-Text Similarity (70%)
        main_sim = float(cosine_similarity(
            query_embedding.reshape(1, -1),
            cand_embedding.reshape(1, -1)
        )[0][0])
        scores['main'] = main_sim * 0.7
        
        # Score 2: Chunked Similarity für längere Texte (30%)
        if len(cand_text) > 200:
            chunk_sim = calculate_chunk_similarity(
                query_embedding, cand_text, model
            )
            scores['chunks'] = chunk_sim * 0.3
        else:
            scores['chunks'] = main_sim * 0.3
        
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

