from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

class ToolResult(BaseModel):
    """Structured result returned by any agent tool."""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    recoverable: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_observation_text(self) -> str:
        """Formats the result as a concise text observation for the LLM."""
        if self.success:
            return f"Tool [{self.tool_name}] succeeded:\n{self.output}"
        else:
            rec_status = "recoverable" if self.recoverable else "unrecoverable"
            return f"Tool [{self.tool_name}] FAILED ({rec_status}):\nError: {self.error}"

class ToolDefinition(BaseModel):
    """Metadata and schema for an agent tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable

TOOL_REGISTRY: Dict[str, ToolDefinition] = {}

def register_tool(name: str, description: str, parameters: Dict[str, Any]):
    """Decorator to register a function into the global tool registry."""
    def decorator(func: Callable):
        TOOL_REGISTRY[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            func=func,
        )
        return func
    return decorator

def get_all_tool_schemas() -> List[Dict[str, Any]]:
    """Returns tool definitions formatted for LLM function/tool binding."""
    schemas = []
    for tool in TOOL_REGISTRY.values():
        schemas.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
        })
    return schemas

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
    """Executes a tool by name with provided arguments and returns ToolResult."""
    if tool_name not in TOOL_REGISTRY:
        return ToolResult(
            tool_name=tool_name,
            success=False,
            output=None,
            error=f"Tool '{tool_name}' is not registered. Available tools: {list(TOOL_REGISTRY.keys())}",
            recoverable=False,
        )
    try:
        tool_def = TOOL_REGISTRY[tool_name]
        result = tool_def.func(**arguments)
        if isinstance(result, ToolResult):
            return result
        return ToolResult(tool_name=tool_name, success=True, output=result)
    except Exception as e:
        return ToolResult(
            tool_name=tool_name,
            success=False,
            output=None,
            error=str(e),
            recoverable=True,
        )
