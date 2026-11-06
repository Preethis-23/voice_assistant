import subprocess
import os
import psutil
from typing import List, Dict, Optional
from app.tools.base import register_tool, ToolResult
from app.core.logging import logger

# Map of common application names to Windows executable commands
COMMON_APP_MAP = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "browser": "start msedge",
    "edge": "start msedge",
    "microsoft edge": "start msedge",
    "brave": "brave.exe",
    "firefox": "firefox.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "code": "code",
    "vs code": "code",
    "vscode": "code",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "cmd": "cmd.exe",
    "task manager": "taskmgr.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "youtube": "start msedge https://youtube.com",
    "spotify": "spotify.exe",
}

@register_tool(
    name="launch_application",
    description="Launches a desktop application on Windows (e.g. Chrome, Notepad, Calculator, VS Code, Edge).",
    parameters={
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "Name of the application (e.g., 'chrome', 'notepad', 'calculator', 'code')"}
        },
        "required": ["app_name"]
    }
)
def launch_application(app_name: str) -> ToolResult:
    try:
        clean_name = app_name.lower().strip()
        cmd = COMMON_APP_MAP.get(clean_name, clean_name)

        # Launch non-blocking background process
        if cmd.startswith("start "):
            subprocess.Popen(cmd, shell=True)
        else:
            try:
                subprocess.Popen([cmd], shell=True)
            except Exception:
                subprocess.Popen(f"start {cmd}", shell=True)

        return ToolResult(
            tool_name="launch_application",
            success=True,
            output=f"Application '{app_name}' launched successfully.",
            metadata={"command": cmd}
        )
    except Exception as e:
        logger.error(f"Failed to launch '{app_name}': {e}")
        return ToolResult(
            tool_name="launch_application",
            success=False,
            output=None,
            error=f"Could not launch application '{app_name}'. Error: {e}",
            recoverable=True
        )

@register_tool(
    name="close_application",
    description="Gracefully closes/terminates a running application by name (e.g., 'notepad', 'chrome').",
    parameters={
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "Name of the application process to terminate"}
        },
        "required": ["app_name"]
    }
)
def close_application(app_name: str) -> ToolResult:
    try:
        clean_name = app_name.lower().strip()
        target_name = clean_name.replace(".exe", "")
        terminated_count = 0

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pname = proc.info["name"].lower() if proc.info["name"] else ""
                if target_name in pname:
                    proc.terminate()
                    terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if terminated_count > 0:
            return ToolResult(
                tool_name="close_application",
                success=True,
                output=f"Closed {terminated_count} instance(s) of '{app_name}'."
            )
        else:
            return ToolResult(
                tool_name="close_application",
                success=False,
                output=None,
                error=f"No active processes found matching '{app_name}'.",
                recoverable=True
            )
    except Exception as e:
        return ToolResult(tool_name="close_application", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="list_running_applications",
    description="Lists currently running desktop applications and active processes.",
    parameters={
        "type": "object",
        "properties": {
            "max_count": {"type": "integer", "description": "Maximum processes to return (default: 20)"}
        }
    }
)
def list_running_applications(max_count: int = 20) -> ToolResult:
    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "memory_percent"]):
            try:
                if p.info["name"] and p.info["memory_percent"] and p.info["memory_percent"] > 0.1:
                    procs.append({
                        "name": p.info["name"],
                        "pid": p.info["pid"],
                        "memory_pct": round(p.info["memory_percent"], 2)
                    })
            except Exception:
                continue

        # Sort by memory usage
        procs.sort(key=lambda x: x["memory_pct"], reverse=True)
        return ToolResult(
            tool_name="list_running_applications",
            success=True,
            output={"count": min(len(procs), max_count), "processes": procs[:max_count]}
        )
    except Exception as e:
        return ToolResult(tool_name="list_running_applications", success=False, output=None, error=str(e), recoverable=True)
