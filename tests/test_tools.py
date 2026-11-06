import os
import pytest
from pathlib import Path
from app.tools.base import TOOL_REGISTRY, execute_tool
from app.tools.filesystem import search_files, read_file, write_file, create_directory
from app.tools.system import get_system_info, get_datetime
from app.tools.utilities import calculate, read_clipboard, write_clipboard
from app.core.safety import is_safe_path, sanitize_path

def test_tool_registry_populated():
    assert "search_files" in TOOL_REGISTRY
    assert "write_file" in TOOL_REGISTRY
    assert "launch_application" in TOOL_REGISTRY
    assert "search_web" in TOOL_REGISTRY
    assert "calculate" in TOOL_REGISTRY

def test_safe_math_calculator():
    res = calculate("25 * 4 + 10")
    assert res.success is True
    assert res.output == 110

    res_complex = calculate("(100 / 4) ** 2")
    assert res_complex.success is True
    assert res_complex.output == 625.0

def test_system_info():
    res = get_system_info()
    assert res.success is True
    assert "cpu_count_logical" in res.output
    assert "ram_total_gb" in res.output

def test_datetime_tool():
    res = get_datetime()
    assert res.success is True
    assert "current_date" in res.output
    assert "current_time" in res.output

def test_filesystem_write_and_read(tmp_path):
    test_file = tmp_path / "test_artifact.txt"
    write_res = write_file(str(test_file), "Hello from KIRA Agent!")
    assert write_res.success is True

    read_res = read_file(str(test_file))
    assert read_res.success is True
    assert read_res.output["content"] == "Hello from KIRA Agent!"

def test_safety_guardrails():
    windows_dir = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    safe, msg = is_safe_path(windows_dir / "System32" / "calc.exe")
    assert safe is False
    assert "denied" in msg.lower()
