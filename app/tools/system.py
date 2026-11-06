import os
import platform
import psutil
import datetime
from pathlib import Path
import pyautogui
from app.tools.base import register_tool, ToolResult
from app.core.safety import sanitize_path

@register_tool(
    name="get_system_info",
    description="Returns current hardware and OS metrics: CPU usage, RAM utilization, disk space, and OS version.",
    parameters={
        "type": "object",
        "properties": {}
    }
)
def get_system_info() -> ToolResult:
    try:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        info = {
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "ram_total_gb": round(mem.total / (1024 ** 3), 2),
            "ram_available_gb": round(mem.available / (1024 ** 3), 2),
            "ram_used_percent": mem.percent,
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            "disk_used_percent": disk.percent
        }
        return ToolResult(tool_name="get_system_info", success=True, output=info)
    except Exception as e:
        return ToolResult(tool_name="get_system_info", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="take_screenshot",
    description="Takes a screenshot of the desktop and saves it to a specified path or Desktop.",
    parameters={
        "type": "object",
        "properties": {
            "save_path": {"type": "string", "description": "Destination file path (e.g. 'Desktop/screenshot.png')"}
        }
    }
)
def take_screenshot(save_path: str = "Desktop/screenshot.png") -> ToolResult:
    try:
        target = sanitize_path(save_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        screenshot = pyautogui.screenshot()
        screenshot.save(str(target))

        return ToolResult(
            tool_name="take_screenshot",
            success=True,
            output=f"Screenshot saved successfully at '{target}'.",
            metadata={"path": str(target)}
        )
    except Exception as e:
        return ToolResult(tool_name="take_screenshot", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="get_datetime",
    description="Returns current date, local time, day of the week, and timezone.",
    parameters={
        "type": "object",
        "properties": {}
    }
)
def get_datetime() -> ToolResult:
    try:
        now = datetime.datetime.now()
        data = {
            "current_time": now.strftime("%I:%M %p"),
            "current_date": now.strftime("%Y-%m-%d"),
            "day_of_week": now.strftime("%A"),
            "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p")
        }
        return ToolResult(tool_name="get_datetime", success=True, output=data)
    except Exception as e:
        return ToolResult(tool_name="get_datetime", success=False, output=None, error=str(e), recoverable=True)
