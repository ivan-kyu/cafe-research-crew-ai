import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    google_places_api_key: str
    llm_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GOOGLE_PLACES_API_KEY is not configured.")

        if not os.getenv("OPENAI_API_KEY", "").strip():
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        return cls(
            google_places_api_key=api_key,
            llm_model=os.getenv("LLM_MODEL", "openai/gpt-4.1-mini").strip(),
        )

