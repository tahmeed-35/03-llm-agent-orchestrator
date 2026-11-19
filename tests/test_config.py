"""Tests for YAML config loading and validation."""

from pathlib import Path
from src.config import load_config, OrchestratorConfig


def test_load_agent_config():
    config_file = Path(__file__).resolve().parent.parent / "configs" / "agent_config.yaml"
    config = load_config(str(config_file))

    assert isinstance(config, OrchestratorConfig)
    assert config.agent.name == "modular-agent-orchestrator"
    assert config.execution.max_iterations > 0
    assert config.execution.timeout_seconds > 0
    assert len(config.tools) >= 2


def test_default_config():
    config = OrchestratorConfig()
    assert config.model.name == "gemini-1.5-flash"
    assert config.execution.max_retries == 3
