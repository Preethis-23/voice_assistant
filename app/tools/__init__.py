# Auto-import all tools so they register into TOOL_REGISTRY
from app.tools.base import TOOL_REGISTRY, ToolResult, get_all_tool_schemas, execute_tool
import app.tools.filesystem
import app.tools.applications
import app.tools.web
import app.tools.system
import app.tools.utilities
