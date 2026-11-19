"""Tests for Orchestrator execution loop, retries, and traces."""

import pytest
from src.orchestrator import AgentOrchestrator
from src.config import OrchestratorConfig


@pytest.mark.asyncio
async def test_orchestrator_mock_direct_answer():
    orchestrator = AgentOrchestrator()
    result = await orchestrator.run("Summarize quantum computing principles")

    assert result.success is True
    assert result.iterations_used >= 1
    assert "quantum computing" in result.final_response.lower()


@pytest.mark.asyncio
async def test_orchestrator_mock_tool_loop():
    orchestrator = AgentOrchestrator()
    result = await orchestrator.run("Please calculate 10 + 20")

    assert result.success is True
    assert len(result.traces) > 0
    # Verify tool execution occurred in traces
    tool_calls = [tc for t in result.traces for tc in t.tool_calls]
    assert any(tc["name"] == "calculator" for tc in tool_calls)
