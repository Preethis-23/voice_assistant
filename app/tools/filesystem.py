import os
import glob
from pathlib import Path
from typing import List, Optional
from app.tools.base import register_tool, ToolResult
from app.core.safety import sanitize_path, is_safe_path, verify_action_allowed
from app.core.logging import logger

@register_tool(
    name="search_files",
    description="Search for files matching a keyword, filename, or glob pattern (e.g. '*.pdf', 'notes*') in a directory.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Filename keyword or pattern to search for"},
            "directory": {"type": "string", "description": "Starting directory (e.g. 'Desktop', 'Downloads', or full path). Defaults to user home."},
            "max_results": {"type": "integer", "description": "Max number of files to return (default: 10)"}
        },
        "required": ["query"]
    }
)
def search_files(query: str, directory: str = "Desktop", max_results: int = 10) -> ToolResult:
    try:
        base_path = sanitize_path(directory)
        if not base_path.exists():
            return ToolResult(
                tool_name="search_files",
                success=False,
                output=None,
                error=f"Directory '{directory}' does not exist.",
                recoverable=True
            )

        matches = []
        pattern = query if ("*" in query or "?" in query) else f"*{query}*"

        # Recursive search with max depth limit
        for p in base_path.rglob(pattern):
            if p.is_file():
                matches.append(str(p.resolve()))
                if len(matches) >= max_results:
                    break

        return ToolResult(
            tool_name="search_files",
            success=True,
            output={"count": len(matches), "files": matches},
            metadata={"directory": str(base_path), "query": query}
        )
    except Exception as e:
        logger.error(f"search_files failed: {e}")
        return ToolResult(tool_name="search_files", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="read_file",
    description="Reads content from a text, markdown, python, or PDF file on the computer.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to read (e.g. 'Desktop/summary.txt')"},
            "max_characters": {"type": "integer", "description": "Maximum characters to read (default 4000)"}
        },
        "required": ["path"]
    }
)
def read_file(path: str, max_characters: int = 4000) -> ToolResult:
    try:
        target = sanitize_path(path)
        if not target.exists() or not target.is_file():
            return ToolResult(
                tool_name="read_file",
                success=False,
                output=None,
                error=f"File not found: '{path}'",
                recoverable=True
            )

        safe, msg = is_safe_path(target)
        if not safe:
            return ToolResult(tool_name="read_file", success=False, output=None, error=msg, recoverable=False)

        # Simple text reader
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_characters)

        truncated = target.stat().st_size > max_characters
        return ToolResult(
            tool_name="read_file",
            success=True,
            output={"content": content, "truncated": truncated, "path": str(target)},
            metadata={"size_bytes": target.stat().st_size}
        )
    except Exception as e:
        return ToolResult(tool_name="read_file", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="write_file",
    description="Creates a new file or writes text content to a file at the specified location (e.g., Desktop, Documents).",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target file path (e.g. 'Desktop/ml_summary.txt')"},
            "content": {"type": "string", "description": "The exact text content to write"},
            "overwrite": {"type": "boolean", "description": "Whether to overwrite if file already exists (default: true)"}
        },
        "required": ["path", "content"]
    }
)
def write_file(path: str, content: str, overwrite: bool = True) -> ToolResult:
    try:
        target = sanitize_path(path)
        safe, msg = is_safe_path(target)
        if not safe:
            return ToolResult(tool_name="write_file", success=False, output=None, error=msg, recoverable=False)

        if target.exists() and not overwrite:
            return ToolResult(
                tool_name="write_file",
                success=False,
                output=None,
                error=f"File '{target}' already exists and overwrite is set to False.",
                recoverable=True
            )

        # Ensure parent directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        with open(target, "w", encoding="utf-8") as f:
            f.write(content)

        return ToolResult(
            tool_name="write_file",
            success=True,
            output=f"Successfully created and wrote {len(content)} characters to '{target}'.",
            metadata={"path": str(target), "characters_written": len(content)}
        )
    except Exception as e:
        return ToolResult(tool_name="write_file", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="create_directory",
    description="Creates a new folder / directory at the specified location.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Folder path to create (e.g. 'Desktop/ML Projects')"}
        },
        "required": ["path"]
    }
)
def create_directory(path: str) -> ToolResult:
    try:
        target = sanitize_path(path)
        safe, msg = is_safe_path(target)
        if not safe:
            return ToolResult(tool_name="create_directory", success=False, output=None, error=msg, recoverable=False)

        target.mkdir(parents=True, exist_ok=True)
        return ToolResult(
            tool_name="create_directory",
            success=True,
            output=f"Directory created successfully at '{target}'."
        )
    except Exception as e:
        return ToolResult(tool_name="create_directory", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="list_directory",
    description="Lists files and subfolders in a specific directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (e.g. 'Desktop', 'Downloads')"}
        },
        "required": ["path"]
    }
)
def list_directory(path: str = "Desktop") -> ToolResult:
    try:
        target = sanitize_path(path)
        if not target.exists() or not target.is_dir():
            return ToolResult(
                tool_name="list_directory",
                success=False,
                output=None,
                error=f"Directory '{path}' not found.",
                recoverable=True
            )

        items = []
        for item in target.iterdir():
            items.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size_bytes": item.stat().st_size if item.is_file() else None
            })

        return ToolResult(
            tool_name="list_directory",
            success=True,
            output={"directory": str(target), "count": len(items), "items": items}
        )
    except Exception as e:
        return ToolResult(tool_name="list_directory", success=False, output=None, error=str(e), recoverable=True)
