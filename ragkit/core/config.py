from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseModel):
    provider: str = "openrouter"
    model: str = "openai/gpt-4o-mini"


class PipelineConfig(BaseModel):
    chunk_size: int = 500
    overlap: int = 50


class RetrievalConfig(BaseModel):
    top_k: int = 5
    method: str = "vector"


class CacheConfig(BaseModel):
    enabled: bool = True
    ttl: int = 3600
    directory: str = ".ragkit_cache"


class ProjectConfig(BaseModel):
    name: str = "ragkit-project"
    model: ModelConfig = Field(default_factory=ModelConfig)
    sources: list[str] = Field(default_factory=list)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"


def load_config(path: str | Path = "rag.yaml") -> ProjectConfig:
    config_path = Path(path)
    if not config_path.exists():
        return ProjectConfig()

    raw: dict[str, Any] = yaml.safe_load(config_path.read_text()) or {}

    project_name = raw.get("project", {}).get("name", "ragkit-project")
    model_raw = raw.get("model", {})
    pipeline_raw = raw.get("pipeline", {})
    retrieval_raw = raw.get("retrieval", {})
    cache_raw = raw.get("cache", {})

    return ProjectConfig(
        name=project_name,
        model=ModelConfig(**model_raw) if model_raw else ModelConfig(),
        sources=raw.get("sources", []),
        pipeline=PipelineConfig(**pipeline_raw) if pipeline_raw else PipelineConfig(),
        retrieval=RetrievalConfig(**retrieval_raw) if retrieval_raw else RetrievalConfig(),
        cache=CacheConfig(**cache_raw) if cache_raw else CacheConfig(),
    )


settings = Settings()
