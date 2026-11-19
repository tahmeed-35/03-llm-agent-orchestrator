"""YAML Configuration loader and Pydantic validator."""

from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field


class AgentMetaConfig(BaseModel):
    name: str = "modular-orchestrator"
    description: str = ""


class ModelConfig(BaseModel):
    name: str = "gemini-1.5-flash"
    temperature: float = 0.2
    max_tokens: int = 1024


class ExecutionConfig(BaseModel):
    max_iterations: int = Field(5, ge=1, le=20)
    timeout_seconds: float = Field(15.0, gt=0)
    max_retries: int = Field(3, ge=0)
    backoff_factor: float = Field(1.5, ge=1.0)
    retry_on_status_codes: List[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])


class LoggingConfig(BaseModel):
    log_file: str = "logs/orchestrator.jsonl"
    log_level: str = "INFO"
    structured_json: bool = True


class ToolItemConfig(BaseModel):
    name: str
    enabled: bool = True
    timeout: float = 5.0


class OrchestratorConfig(BaseModel):
    agent: AgentMetaConfig = Field(default_factory=AgentMetaConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    tools: List[ToolItemConfig] = Field(default_factory=list)


def load_config(config_path: str) -> OrchestratorConfig:
    """Loads and validates configuration from a YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return OrchestratorConfig(**data)
