import pyperclip
import ast
import operator
from typing import Union
from app.tools.base import register_tool, ToolResult

# Safe mathematical operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}

def safe_eval_expr(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](safe_eval_expr(node.left), safe_eval_expr(node.right))
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](safe_eval_expr(node.operand))
    raise ValueError(f"Unsupported math operation: {ast.dump(node)}")

@register_tool(
    name="calculate",
    description="Safely evaluates basic to advanced mathematical expressions (e.g. '24 * 365', '(1000 / 12) * 1.08').",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Mathematical expression string to calculate"}
        },
        "required": ["expression"]
    }
)
def calculate(expression: str) -> ToolResult:
    try:
        clean_expr = expression.replace(",", "").replace("^", "**").strip()
        node = ast.parse(clean_expr, mode="eval").body
        result = safe_eval_expr(node)
        return ToolResult(tool_name="calculate", success=True, output=result)
    except Exception as e:
        return ToolResult(tool_name="calculate", success=False, output=None, error=f"Invalid calculation: {e}", recoverable=True)

@register_tool(
    name="read_clipboard",
    description="Reads current text content stored in the desktop clipboard.",
    parameters={"type": "object", "properties": {}}
)
def read_clipboard() -> ToolResult:
    try:
        text = pyperclip.paste()
        return ToolResult(tool_name="read_clipboard", success=True, output=text)
    except Exception as e:
        return ToolResult(tool_name="read_clipboard", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="write_clipboard",
    description="Copies text directly to the user's desktop clipboard.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to copy to clipboard"}
        },
        "required": ["text"]
    }
)
def write_clipboard(text: str) -> ToolResult:
    try:
        pyperclip.copy(text)
        return ToolResult(tool_name="write_clipboard", success=True, output=f"Copied {len(text)} characters to clipboard.")
    except Exception as e:
        return ToolResult(tool_name="write_clipboard", success=False, output=None, error=str(e), recoverable=True)
