import os
import tempfile
import numpy as np
from typing import Optional
from app.core.config import settings
from app.core.logging import logger

class LocalSpeechToText:
    """Local Speech-to-Text transcriber using faster-whisper with sounddevice recording."""

    def __init__(self):
        self.model = None
        self.sample_rate = 16000

    def _ensure_model_loaded(self):
        if self.model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Loading faster-whisper model ({settings.WHISPER_MODEL_SIZE}) on {settings.WHISPER_DEVICE}...")
                self.model = WhisperModel(
                    settings.WHISPER_MODEL_SIZE,
                    device=settings.WHISPER_DEVICE,
                    compute_type="int8"
                )
                logger.info("faster-whisper model loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load faster-whisper: {e}. Voice input may be limited to text.")
                self.model = False

    def transcribe_audio_file(self, audio_path: str) -> str:
        """Transcribes a saved audio file to text."""
        self._ensure_model_loaded()
        if not self.model:
            raise RuntimeError("faster-whisper is not loaded.")

        segments, info = self.model.transcribe(audio_path, beam_size=5)
        text = " ".join([segment.text for segment in segments]).strip()
        logger.info(f"STT Transcript: '{text}' (lang={info.language})")
        return text

    def record_and_transcribe(self, duration_seconds: int = 5) -> Optional[str]:
        """Records from microphone for a fixed duration and transcribes."""
        try:
            import sounddevice as sd
            import soundfile as sf

            self._ensure_model_loaded()
            if not self.model:
                return None

            logger.info(f"🎙️ Listening for {duration_seconds} seconds... Speak now!")
            recording = sd.rec(
                int(duration_seconds * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16"
            )
            sd.wait()
            logger.info("Processing speech audio...")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            sf.write(tmp_path, recording, self.sample_rate)

            try:
                text = self.transcribe_audio_file(tmp_path)
                return text
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            logger.error(f"Microphone recording failed: {e}")
            return None

stt_engine = LocalSpeechToText()
