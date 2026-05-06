"""Centralized config — load .env once, expose typed settings to the rest of the app."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_llm_model: str
    openai_embedding_model: str

    jira_base_url: str
    jira_email: str
    jira_api_token: str
    jira_project_key: str

    kb_dir: Path
    chroma_dir: Path

    @property
    def jira_enabled(self) -> bool:
        return bool(self.jira_base_url and self.jira_email and self.jira_api_token)


def load_settings() -> Settings:
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and fill it in."
        )

    return Settings(
        openai_api_key=openai_api_key,
        openai_llm_model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        jira_base_url=os.getenv("JIRA_BASE_URL", "").strip().rstrip("/"),
        jira_email=os.getenv("JIRA_EMAIL", "").strip(),
        jira_api_token=os.getenv("JIRA_API_TOKEN", "").strip(),
        jira_project_key=os.getenv("JIRA_PROJECT_KEY", "IT").strip(),
        kb_dir=PROJECT_ROOT / os.getenv("KB_DIR", "knowledge_base"),
        chroma_dir=PROJECT_ROOT / os.getenv("CHROMA_DIR", ".chroma"),
    )


SETTINGS = load_settings()
