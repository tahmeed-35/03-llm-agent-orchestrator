"""Tests for Tool Registry, schema generation, and tool execution."""

from src.tools import ToolRegistry, default_registry


def test_built_in_tools_registered():
    assert default_registry.get("calculator") is not None
    assert default_registry.get("system_info") is not None
    assert default_registry.get("text_summarize") is not None


def test_tool_schema_generation():
    calc_tool = default_registry.get("calculator")
    schema = calc_tool.get_schema()

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "calculator"
    assert "expression" in schema["function"]["parameters"]["properties"]


def test_tool_execution():
    calc_res = default_registry.execute_tool("calculator", expression="15 * 4")
    assert calc_res["status"] == "success"
    assert calc_res["output"] == "60"

    sys_res = default_registry.execute_tool("system_info")
    assert sys_res["status"] == "success"
    assert "os" in sys_res["output"]


def test_custom_tool_registration():
    custom_reg = ToolRegistry()

    @custom_reg.register(name="reverse_str", description="Reverses a string")
    def reverse_str(text: str) -> str:
        return text[::-1]

    assert custom_reg.get("reverse_str") is not None
    res = custom_reg.execute_tool("reverse_str", text="hello")
    assert res["status"] == "success"
    assert res["output"] == "olleh"
