import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "pythonw.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

STARTUP_DIR = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))
VBS_TARGET = STARTUP_DIR / "KIRA_Assistant_AutoStart.vbs"

def install_startup():
    """Installs a silent background auto-start script in the Windows Startup directory."""
    print("=" * 60)
    print("  KIRA Windows Startup Auto-Boot Setup")
    print("=" * 60)

    STARTUP_DIR.mkdir(parents=True, exist_ok=True)

    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{PROJECT_ROOT}"
cmd = Chr(34) & "{PYTHON_EXE}" & Chr(34) & " app/main.py --always-on"
WshShell.Run cmd, 0, False
'''

    with open(VBS_TARGET, "w", encoding="utf-8") as f:
        f.write(vbs_content)

    print(f"\n✅ SUCCESS: KIRA has been configured to boot automatically with Windows!")
    print(f"Startup Script Location: {VBS_TARGET}")
    print("\nWhen you turn on your laptop, KIRA will run silently in the background")
    print("and instantly respond whenever you say 'Hey KIRA'!")

def remove_startup():
    """Removes KIRA from Windows Startup."""
    if VBS_TARGET.exists():
        VBS_TARGET.unlink()
        print(f"Removed KIRA startup script from: {VBS_TARGET}")
    else:
        print("No KIRA startup script found in Windows Startup.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        remove_startup()
    else:
        install_startup()
