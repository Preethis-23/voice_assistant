import threading
from typing import Optional
from app.core.config import settings
from app.core.logging import logger

class LocalTextToSpeech:
    """Local offline Text-to-Speech synthesizer using pyttsx3 with thread-safe Windows COM initialization."""

    def __init__(self):
        self._lock = threading.Lock()

    def speak(self, text: str, block: bool = True):
        """Speaks the provided text aloud using local TTS."""
        if not text or not text.strip():
            return

        clean_text = text.replace("*", "").replace("#", "").strip()
        logger.info(f"[TTS Speaking] {clean_text}")

        def _speak_worker():
            with self._lock:
                try:
                    # Windows COM thread initialization
                    try:
                        import pythoncom
                        pythoncom.CoInitialize()
                    except Exception:
                        pass

                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty("rate", settings.TTS_RATE)
                    engine.setProperty("volume", settings.TTS_VOLUME)
                    engine.say(clean_text)
                    engine.runAndWait()
                except Exception as e:
                    logger.debug(f"TTS speak error: {e}")

        if block:
            _speak_worker()
        else:
            t = threading.Thread(target=_speak_worker, daemon=True)
            t.start()

tts_engine = LocalTextToSpeech()
