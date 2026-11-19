"""Extensible Tool Registry with parameter schema generation and error trapping."""

import inspect
import math
import platform
import re
from typing import Any, Callable, Dict, List, Optional
import httpx


class Tool:
    """Encapsulates a callable tool, its name, description, and parameter signature."""

    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func
        self.signature = inspect.signature(func)

    def get_schema(self) -> Dict[str, Any]:
        """Generates OpenAI/Gemini compatible tool definition schema."""
        properties = {}
        required = []

        for param_name, param in self.signature.parameters.items():
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == list:
                param_type = "array"
            elif param.annotation == dict:
                param_type = "object"

            properties[param_name] = {"type": param_type}
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def execute(self, **kwargs) -> Any:
        """Executes the tool with passed keyword arguments."""
        return self.func(**kwargs)


class ToolRegistry:
    """Registry maintaining available tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, name: str, description: str):
        """Decorator to register a function as an agent tool."""
        def decorator(func: Callable):
            tool = Tool(name=name, description=description, func=func)
            self._tools[name] = tool
            return func
        return decorator

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [tool.get_schema() for tool in self._tools.values()]

    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        tool = self.get(name)
        if not tool:
            return {"status": "error", "error": f"Tool '{name}' not found in registry."}
        try:
            result = tool.execute(**kwargs)
            return {"status": "success", "output": result}
        except Exception as exc:
            return {"status": "error", "error": f"Execution error in '{name}': {str(exc)}"}


default_registry = ToolRegistry()


@default_registry.register(name="calculator", description="Evaluates mathematical expressions safely.")
def calculate(expression: str) -> str:
    clean_expr = expression.replace(" ", "").replace("x", "*").replace("^", "**")
    if not re.match(r"^[\d\+\-\*\/\.\(\)\%]+$", clean_expr):
        raise ValueError(f"Unsafe expression: {expression}")
    allowed_names = {"__builtins__": None, "math": math}
    return str(eval(clean_expr, allowed_names, {}))


@default_registry.register(name="http_get", description="Performs an HTTP GET request to retrieve web content or JSON.")
def http_get(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(url)
        return {
            "status_code": resp.status_code,
            "url": str(resp.url),
            "content_snippet": resp.text[:300],
        }


@default_registry.register(name="text_summarize", description="Extracts the first N words of a text as a summary.")
def text_summarize(text: str, max_words: int = 50) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


@default_registry.register(name="system_info", description="Returns basic operating system information.")
def system_info() -> Dict[str, str]:
    return {
        "os": platform.system(),
        "release": platform.release(),
        "python_version": platform.python_version(),
    }
