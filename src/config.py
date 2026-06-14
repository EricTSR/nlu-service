"""
Zentrale Konfiguration für den NLU-Service.
"""

# Sentence-Transformer Modell
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# MISTRAL Model und Parameter
MISTRAL_MODEL = "mistralai/Ministral-3-8B-Reasoning-2512"
MISTRAL_EXTRACT_TEMP = 0.0
MISTRAL_QUESTION_TEMP = 0.3
MISTRAL_MAX_RETRIES = 3