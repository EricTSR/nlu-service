import json
import os
from mistralai.client import Mistral
from dotenv import load_dotenv
from mistralai.client.models import ResponseFormat

from src.config import MISTRAL_MODEL

load_dotenv()

class MistralJsonClient:
    def __init__(self):
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError("MISTRAL_API_KEY nicht gesetzt – bitte in .env eintragen")

        self.client = Mistral(api_key=api_key)

    def complete_json(self, messages: list[dict[str, str]], temperature: float) -> dict:
        response = self.client.chat.complete(
            model=MISTRAL_MODEL,
            messages=messages,
            temperature=temperature,
            response_format=ResponseFormat(type="json_object"),
        )

        content = response.choices[0].message.content
        return json.loads(content)