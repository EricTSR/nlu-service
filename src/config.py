"""
Zentrale Konfiguration für den NLU-Service.
"""

# Sentence-Transformer Modell
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# MISTRAL Modell
MISTRAL_MODEL = "mistral-small-latest"
MISTRAL_EXTRACT_TEMP = 0.0
MISTRAL_QUESTION_TEMP = 0.3
MISTRAL_MAX_RETRIES = 3