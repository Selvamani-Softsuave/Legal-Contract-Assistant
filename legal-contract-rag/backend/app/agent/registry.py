"""
Agent Tool Registry - Enterprise Pluggable Tool Architecture.
Allows dynamic registration, discovery, parameter validation, and execution of agent tools.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel


class BaseTool(ABC):
    """Abstract base class for any tool usable by ReAct / Squad agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed documentation explaining the tool's purpose and usage."""
        pass

    @property
    def input_schema(self) -> Optional[Type[BaseModel]]:
        """Optional Pydantic schema for parameter validation."""
        return None

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Executes the tool with the given keyword arguments."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serializes tool metadata for OpenAI / ReAct prompt formatting."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema() if self.input_schema else {}
        }


class ToolRegistry:
    """Central registry for managing pluggable agent tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def list_tool_definitions(self) -> List[Dict[str, Any]]:
        return [tool.to_dict() for tool in self._tools.values()]

    def execute(self, tool_name: str, **kwargs) -> Any:
        tool = self.get_tool(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found. Available tools: {list(self._tools.keys())}"
        return tool.execute(**kwargs)


# Global default registry instance
tool_registry = ToolRegistry()
