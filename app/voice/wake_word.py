import time
import numpy as np
import tempfile
import os
from typing import Callable, Optional
from app.core.logging import logger
from app.voice.speech_to_text import stt_engine

# Supported activation phrases
WAKE_WORDS = ["hey kira", "kira", "keyra", "heykira", "hey keera", "keera"]

class WakeWordDetector:
    """Continuously monitors microphone in the background with minimal CPU footprint,
    triggering an activation callback when 'Hey KIRA' is spoken."""

    def __init__(
        self,
        wake_words: Optional[list] = None,
        sample_rate: int = 16000,
        energy_threshold: int = 500,
        chunk_duration: float = 1.5
    ):
        self.wake_words = [w.lower() for w in (wake_words or WAKE_WORDS)]
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.chunk_duration = chunk_duration
        self._is_running = False

    def is_wake_word(self, transcript: str) -> bool:
        """Determines if the transcribed text matches any wake word variant."""
        cleaned = transcript.lower().strip()
        # Remove punctuation
        for ch in [".", ",", "!", "?", "'", '"', "-"]:
            cleaned = cleaned.replace(ch, "")
        words = cleaned.split()

        for target in self.wake_words:
            if target in cleaned:
                return True
            target_words = target.split()
            if any(tw in words for tw in target_words):
                return True
        return False

    def listen_loop(self, on_wake: Callable[[], None], should_stop: Optional[Callable[[], bool]] = None):
        """Infinite passive listening loop with energy thresholding to keep CPU usage <1%."""
        try:
            import sounddevice as sd
            import soundfile as sf
        except ImportError as e:
            logger.error(f"Cannot initialize wake word listener: {e}")
            return

        stt_engine._ensure_model_loaded()
        self._is_running = True
        logger.info(f"👂 [WAKE WORD] Passive listener active. Say 'Hey KIRA' to wake up.")

        chunk_samples = int(self.chunk_duration * self.sample_rate)

        while self._is_running:
            if should_stop and should_stop():
                break

            try:
                # Record 1.5s audio slice
                recording = sd.rec(
                    chunk_samples,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="int16"
                )
                sd.wait()

                # Fast energy check: if below threshold, skip STT to conserve battery and CPU
                rms = np.sqrt(np.mean(recording.astype(np.float32)**2))
                if rms < self.energy_threshold:
                    continue

                # Speech detected: verify if wake word
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name

                sf.write(tmp_path, recording, self.sample_rate)
                try:
                    transcript = stt_engine.transcribe_audio_file(tmp_path)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

                if transcript and self.is_wake_word(transcript):
                    logger.info(f"✨ [WAKE WORD TRIGGERED] Heard: '{transcript}'")
                    on_wake()
                    # Short cool-down after handling
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error in wake word loop: {e}")
                time.sleep(1.0)

    def stop(self):
        self._is_running = False

wake_detector = WakeWordDetector()
