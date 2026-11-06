import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uuid
from app.core.config import settings
from app.core.logging import logger
from app.agent.graph import run_agent_goal
from app.voice.speech_to_text import stt_engine
from app.voice.text_to_speech import tts_engine
from app.memory.database import init_db

def print_banner():
    print("=" * 60)
    print("      🤖 KIRA - Agentic AI Voice Assistant for Windows      ")
    print(f"      Model: {settings.OLLAMA_MODEL} | Local SQLite Memory  ")
    print("=" * 60)

def run_interactive_cli():
    """Main interactive terminal loop supporting text and voice input."""
    init_db()
    print_banner()

    session_id = str(uuid.uuid4())[:8]
    print(f"Session initialized: {session_id}")
    print("\nCommands:")
    print("  Type your task and press Enter")
    print("  Type 'voice' or 'v' to record from your microphone")
    print("  Type 'exit' or 'q' to quit\n")

    # Speak greeting
    tts_engine.speak("Hello! I am KIRA, your agentic desktop assistant. How can I help you today?", block=False)

    while True:
        try:
            user_input = input("\n👤 You > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                tts_engine.speak("Goodbye!", block=True)
                break

            # Handle Voice Command trigger
            if user_input.lower() in ("voice", "v"):
                print("🎤 Listening for 5 seconds...")
                voice_text = stt_engine.record_and_transcribe(duration_seconds=5)
                if not voice_text:
                    print("⚠️ No speech recognized. Try typing your command.")
                    continue
                user_input = voice_text
                print(f"🗣️ Heard: \"{user_input}\"")

            print(f"\n🧠 KIRA is understanding your goal: '{user_input}'...")
            final_state = run_agent_goal(user_goal=user_input, session_id=session_id)

            print("\n📋 Execution Plan & Results:")
            for s in final_state.plan:
                icon = "✅" if s.status == "completed" else "❌" if s.status == "failed" else "⏳"
                tool_info = f" [{s.tool_name}]" if s.tool_name else ""
                print(f"  {icon} Step {s.step_number}: {s.description}{tool_info}")
                if s.result:
                    preview = s.result.replace("\n", " ")[:90]
                    print(f"     ↳ {preview}...")

            print(f"\n🤖 KIRA: {final_state.final_response}\n")

            # Speak final answer
            if final_state.final_response:
                tts_engine.speak(final_state.final_response, block=False)

        except KeyboardInterrupt:
            print("\nExiting KIRA...")
            break
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)

if __name__ == "__main__":
    run_interactive_cli()
