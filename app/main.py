import sys
import argparse
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uuid
from app.core.config import settings
from app.core.logging import logger
from app.agent.queue_manager import task_queue_manager
from app.voice.speech_to_text import stt_engine
from app.voice.text_to_speech import tts_engine
from app.voice.wake_word import wake_detector
from app.memory.database import init_db

def print_banner():
    print("=" * 65)
    print("      🤖 KIRA - Autonomous Agentic OS Co-Pilot for Windows      ")
    print(f"      Tier 1: {settings.OLLAMA_MODEL} | Tier 2: {settings.GEMINI_MODEL} (Fallback)  ")
    print("      Features: 'Hey KIRA' Wake-Word | Task Queue | Multi-Browser ")
    print("=" * 65)

def handle_voice_interaction(session_id: str):
    """Called when 'Hey KIRA' wake word is detected or voice mode is triggered."""
    print("\n✨ Wake word detected! [Hey KIRA]")
    tts_engine.speak("I'm listening!", block=True)

    print("🎙️ Listening to your command...")
    user_speech = stt_engine.record_until_silence(max_duration=15.0)

    if not user_speech or not user_speech.strip():
        print("⚠️ No command detected.")
        return

    print(f"\n🗣️ You said: \"{user_speech}\"")
    process_user_command(user_speech, session_id)

def process_user_command(command: str, session_id: str):
    """Processes single or multi-task instructions using the Task Queue Manager."""
    print(f"\n🧠 KIRA is processing: '{command}'...")

    def on_task_start(idx, total, goal):
        msg = f"Starting task {idx} of {total}: {goal}"
        print(f"  ▶️ {msg}")
        tts_engine.speak(msg, block=False)

    result = task_queue_manager.process_command(
        user_command=command,
        session_id=session_id,
        on_task_start=on_task_start if " and then " in command.lower() or " also " in command.lower() else None
    )

    final_resp = result["final_response"]
    print(f"\n🤖 KIRA: {final_resp}\n")
    if final_resp:
        tts_engine.speak(final_resp, block=True)

def run_always_on_daemon():
    """Runs KIRA as an always-on background OS service listening for 'Hey KIRA'."""
    init_db()
    print_banner()
    session_id = f"daemon_{str(uuid.uuid4())[:6]}"
    print("🚀 KIRA Always-On Co-Pilot is running in the background.")
    print("Say 'Hey KIRA' at any time to give a command.\n")
    tts_engine.speak("KIRA Co-Pilot is online and ready.", block=False)

    try:
        wake_detector.listen_loop(on_wake=lambda: handle_voice_interaction(session_id))
    except KeyboardInterrupt:
        print("\nStopping KIRA background service...")
        wake_detector.stop()

def run_interactive_cli():
    """Interactive terminal loop supporting text, voice, and wake-word modes."""
    init_db()
    print_banner()
    session_id = str(uuid.uuid4())[:8]
    print(f"Session: {session_id}")
    print("\nCommands:")
    print("  Type your task and press Enter")
    print("  Type 'v' to record a voice command directly")
    print("  Type 'wake' or 'listen' to start continuous 'Hey KIRA' wake-word mode")
    print("  Type 'exit' or 'q' to quit\n")

    tts_engine.speak("Hello! I am KIRA. How can I help you today?", block=False)

    while True:
        try:
            user_input = input("\n👤 You > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                tts_engine.speak("Goodbye!", block=True)
                break

            if user_input.lower() in ("wake", "listen"):
                print("👂 Entering continuous 'Hey KIRA' wake-word mode. Press Ctrl+C to return to CLI.")
                try:
                    wake_detector.listen_loop(on_wake=lambda: handle_voice_interaction(session_id))
                except KeyboardInterrupt:
                    print("\nReturning to CLI mode...")
                    wake_detector.stop()
                    continue

            if user_input.lower() in ("voice", "v"):
                handle_voice_interaction(session_id)
                continue

            process_user_command(user_input, session_id)

        except KeyboardInterrupt:
            print("\nExiting KIRA...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="KIRA Agentic Voice Assistant")
    parser.add_argument("--always-on", "--daemon", action="store_true", help="Run in continuous background wake-word mode")
    args = parser.parse_args()

    if args.always_on:
        run_always_on_daemon()
    else:
        run_interactive_cli()

if __name__ == "__main__":
    main()
