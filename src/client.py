"""Async LLM API client wrapper with exponential backoff retries and timeout controls."""

import asyncio
import json
import os
import random
from typing import Any, Dict, List, Optional
import httpx
from src.config import ExecutionConfig, ModelConfig
from src.logger import StructuredLogger


class AsyncLLMClient:
    """Async API client managing LLM inference requests with retry backoff."""

    def __init__(
        self,
        model_config: Optional[ModelConfig] = None,
        exec_config: Optional[ExecutionConfig] = None,
        logger: Optional[StructuredLogger] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model_config = model_config or ModelConfig()
        self.exec_config = exec_config or ExecutionConfig()
        self.logger = logger or StructuredLogger(console=False)
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Calls the LLM API with exponential backoff retries and timeout safeguards."""
        attempt = 0
        backoff = 1.0

        # If no API key is provided, use deterministic mock model engine
        if not self.api_key or self.api_key == "mock":
            return await self._mock_llm_response(messages, tools_schema)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_config.name,
            "messages": messages,
            "temperature": self.model_config.temperature,
            "max_tokens": self.model_config.max_tokens,
        }
        if tools_schema:
            payload["tools"] = tools_schema

        while attempt <= self.exec_config.max_retries:
            attempt += 1
            try:
                self.logger.log(
                    "API_REQUEST_START",
                    f"Sending inference request to {self.model_config.name} (Attempt {attempt})",
                )
                async with httpx.AsyncClient(timeout=self.exec_config.timeout_seconds) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )

                if resp.status_code in self.exec_config.retry_on_status_codes:
                    raise httpx.HTTPStatusError(
                        f"Retryable HTTP error {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
                resp.raise_for_status()
                return resp.json()

            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                self.logger.log(
                    "API_RETRY",
                    f"Request failed: {str(exc)}. Retrying in {backoff:.2f}s (Attempt {attempt}/{self.exec_config.max_retries})",
                    level="WARNING",
                )
                if attempt > self.exec_config.max_retries:
                    self.logger.log("API_MAX_RETRIES", "Exceeded max retries.", level="ERROR")
                    raise RuntimeError(f"LLM API call failed after {self.exec_config.max_retries} retries: {str(exc)}")

                await asyncio.sleep(backoff + random.uniform(0.1, 0.5))
                backoff *= self.exec_config.backoff_factor

        raise RuntimeError("Unexpected failure in LLM retry loop.")

    async def _mock_llm_response(
        self,
        messages: List[Dict[str, str]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Provides simulated LLM response for testing and offline development."""
        await asyncio.sleep(0.05)
        last_message = messages[-1]["content"] if messages else ""

        # Check if the query asks for math
        if any(c in last_message for c in ["+", "-", "*", "/", "^"]) and "calculate" in last_message.lower():
            expr = last_message.split("calculate")[-1].strip().strip("?").strip()
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_mock_calc_001",
                            "type": "function",
                            "function": {
                                "name": "calculator",
                                "arguments": json.dumps({"expression": expr}),
                            },
                        }],
                    }
                }]
            }

        # Check for system info
        if "system info" in last_message.lower() or "os info" in last_message.lower():
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_mock_sys_001",
                            "type": "function",
                            "function": {
                                "name": "system_info",
                                "arguments": "{}",
                            },
                        }],
                    }
                }]
            }

        # Otherwise answer directly
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"Completed reasoning on task: {last_message}",
                    "tool_calls": None,
                }
            }]
        }
