import pytest
from pydantic import BaseModel, Field
from backend.app.agent.registry import BaseTool, ToolRegistry


class SumInputSchema(BaseModel):
    a: int = Field(description="First number")
    b: int = Field(description="Second number")


class SumTool(BaseTool):
    @property
    def name(self) -> str:
        return "sum_numbers"

    @property
    def description(self) -> str:
        return "Adds two numbers together."

    @property
    def input_schema(self):
        return SumInputSchema

    def execute(self, a: int, b: int) -> int:
        return a + b


def test_tool_registry_registration_and_execution():
    registry = ToolRegistry()
    tool = SumTool()
    registry.register(tool)

    assert registry.get_tool("sum_numbers") == tool
    assert len(registry.list_tools()) == 1

    # Execute tool via registry
    result = registry.execute("sum_numbers", a=5, b=10)
    assert result == 15

    # Execute nonexistent tool
    err_result = registry.execute("unknown_tool")
    assert "not found" in err_result

    # Metadata dictionary check
    defs = registry.list_tool_definitions()
    assert len(defs) == 1
    assert defs[0]["name"] == "sum_numbers"
    assert "parameters" in defs[0]
