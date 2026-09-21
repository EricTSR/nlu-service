"""Zentrale, typisierte Konfiguration des NLU-Service."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    mistral_api_key: SecretStr | None = None
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    mistral_model: str = "ministral-8b-2512"
    mistral_extract_temperature: float = 0.0
    mistral_question_temperature: float = 0.3

    def require_mistral_api_key(self) -> str:
        if self.mistral_api_key is None:
            raise RuntimeError("MISTRAL_API_KEY nicht gesetzt. Bitte in .env eintragen")
        return self.mistral_api_key.get_secret_value()

@lru_cache
def get_settings() -> Settings:
    return Settings()
