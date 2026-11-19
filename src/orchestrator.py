"""Main config-driven Agent Orchestrator with tool-calling loop and structured logging."""

import asyncio
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.config import OrchestratorConfig, load_config
from src.tools import ToolRegistry, default_registry
from src.client import AsyncLLMClient
from src.logger import StructuredLogger


class TurnTrace(BaseModel):
    iteration: int
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)


class OrchestrationResult(BaseModel):
    success: bool
    iterations_used: int
    final_response: str
    traces: List[TurnTrace] = Field(default_factory=list)
    error: Optional[str] = None


class AgentOrchestrator:
    """Config-driven orchestration engine managing the agent reasoning and tool execution loop."""

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        config_path: Optional[str] = None,
        registry: Optional[ToolRegistry] = None,
    ):
        if config:
            self.config = config
        elif config_path:
            self.config = load_config(config_path)
        else:
            self.config = OrchestratorConfig()

        self.logger = StructuredLogger(
            log_file=self.config.logging.log_file if self.config.logging.structured_json else None,
            console=True,
        )
        self.registry = registry or default_registry
        self.client = AsyncLLMClient(
            model_config=self.config.model,
            exec_config=self.config.execution,
            logger=self.logger,
        )

    async def run(self, user_prompt: str) -> OrchestrationResult:
        """Runs the agent orchestration loop until completion or max_iterations reached."""
        self.logger.log("AGENT_START", f"Starting orchestration for: '{user_prompt}'")
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": user_prompt}
        ]
        tools_schema = self.registry.list_tools()

        traces: List[TurnTrace] = []
        iteration = 0
        final_answer = ""

        try:
            while iteration < self.config.execution.max_iterations:
                iteration += 1
                self.logger.log("ITERATION_START", f"Starting iteration {iteration}/{self.config.execution.max_iterations}")

                # Call LLM client
                llm_response = await self.client.generate_response(messages, tools_schema)
                choice = llm_response.get("choices", [{}])[0]
                message = choice.get("message", {})
                tool_calls = message.get("tool_calls") or []

                trace = TurnTrace(iteration=iteration)

                # Check if agent requested tool calls
                if tool_calls:
                    self.logger.log(
                        "TOOL_CALLS_REQUESTED",
                        f"Agent requested {len(tool_calls)} tool call(s).",
                        payload={"tool_calls": tool_calls},
                    )

                    # Append assistant message with tool calls
                    messages.append(message)

                    for tc in tool_calls:
                        func_info = tc.get("function", {})
                        tool_name = func_info.get("name")
                        raw_args = func_info.get("arguments", "{}")

                        try:
                            parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        except json.JSONDecodeError:
                            parsed_args = {}

                        trace.tool_calls.append({"name": tool_name, "args": parsed_args})
                        self.logger.log("TOOL_EXECUTE_START", f"Executing tool: {tool_name}", payload=parsed_args)

                        # Execute tool
                        exec_result = self.registry.execute_tool(tool_name, **parsed_args)
                        trace.tool_results.append({"name": tool_name, "result": exec_result})

                        self.logger.log("TOOL_EXECUTE_FINISH", f"Tool {tool_name} returned status: {exec_result.get('status')}")

                        # Append tool response
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.get("id", "call_id"),
                            "name": tool_name,
                            "content": json.dumps(exec_result),
                        })

                    traces.append(trace)

                else:
                    # Final answer received
                    final_answer = message.get("content", "")
                    self.logger.log("AGENT_FINISH", "Agent produced final text response.", payload={"answer": final_answer})
                    traces.append(trace)
                    return OrchestrationResult(
                        success=True,
                        iterations_used=iteration,
                        final_response=final_answer,
                        traces=traces,
                    )

            # Max iterations reached without final text answer
            self.logger.log("MAX_ITERATIONS_REACHED", "Agent reached maximum iteration limit.", level="WARNING")
            return OrchestrationResult(
                success=False,
                iterations_used=iteration,
                final_response="Max iterations reached before completing task.",
                traces=traces,
                error="Max iterations limit reached",
            )

        except Exception as exc:
            self.logger.log("AGENT_ERROR", f"Orchestrator error: {str(exc)}", level="ERROR")
            return OrchestrationResult(
                success=False,
                iterations_used=iteration,
                final_response="",
                traces=traces,
                error=str(exc),
            )
