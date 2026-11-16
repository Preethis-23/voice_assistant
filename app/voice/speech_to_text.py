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

    def record_until_silence(
        self,
        max_duration: float = 15.0,
        silence_timeout: float = 1.2,
        energy_threshold: int = 400
    ) -> Optional[str]:
        """Dynamically records from microphone and automatically stops after silence is detected."""
        try:
            import sounddevice as sd
            import soundfile as sf
            import time

            self._ensure_model_loaded()
            if not self.model:
                return None

            logger.info("🎙️ Listening... (speak your command, auto-detects when you finish)")
            chunk_duration = 0.2
            chunk_samples = int(chunk_duration * self.sample_rate)

            frames = []
            has_started_speaking = False
            silence_start_time = None
            start_time = time.time()

            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="int16") as stream:
                while time.time() - start_time < max_duration:
                    chunk, _ = stream.read(chunk_samples)
                    frames.append(chunk)

                    # Compute RMS energy of this audio chunk
                    rms = np.sqrt(np.mean(chunk.astype(np.float32)**2))

                    if rms > energy_threshold:
                        has_started_speaking = True
                        silence_start_time = None
                    elif has_started_speaking:
                        if silence_start_time is None:
                            silence_start_time = time.time()
                        elif time.time() - silence_start_time >= silence_timeout:
                            # User stopped speaking for silence_timeout seconds
                            logger.info("Silence detected. Processing speech...")
                            break

            if not frames:
                return None

            audio_data = np.concatenate(frames, axis=0)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            sf.write(tmp_path, audio_data, self.sample_rate)
            try:
                return self.transcribe_audio_file(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            logger.error(f"Dynamic microphone recording failed: {e}")
            return None

    def record_and_transcribe(self, duration_seconds: int = 5) -> Optional[str]:
        """Records from microphone dynamically (fallback to duration if needed)."""
        res = self.record_until_silence(max_duration=float(duration_seconds))
        return res

stt_engine = LocalSpeechToText()
