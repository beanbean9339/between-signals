"""
Speech processing module for Between Signals.
Captures audio, transcribes with Whisper, and emits SpeechEvent objects.

Can run in two modes:
1. Module mode: Initialize SpeechProcessor and call process_audio() from room integration
2. Standalone mode: Run directly for testing or as a service with room emission
"""

import sounddevice as sd
import numpy as np
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
import queue
import logging
from typing import Callable, Optional
from dataclasses import dataclass
from events import SpeechEvent, Event

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Audio capture configuration"""
    device: int = 1
    sample_rate: int = 44100
    whisper_rate: int = 16000
    process_seconds: int = 4
    block_size: int = None  # Defaults to sample_rate
    
    def __post_init__(self):
        if self.block_size is None:
            self.block_size = self.sample_rate


class SpeechProcessor:
    """
    Captures audio, transcribes with Whisper, and emits SpeechEvent objects.
    
    Can be used in module mode (with event callback) or standalone mode.
    """
    
    def __init__(
        self,
        audio_config: AudioConfig = None,
        whisper_model: str = "base",
        whisper_device: str = "cpu",
        whisper_compute_type: str = "int8",
        event_callback: Optional[Callable[[SpeechEvent], None]] = None,
        room_id: str = "A"
    ):
        """
        Initialize speech processor.
        
        Args:
            audio_config: AudioConfig instance (uses defaults if None)
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            whisper_device: Device to run Whisper on (cpu, cuda, etc.)
            whisper_compute_type: Quantization (int8, int16, float16, float32)
            event_callback: Function called with SpeechEvent objects (optional)
            room_id: Room identifier (A or B) for event source
        """
        self.audio_config = audio_config or AudioConfig()
        self.event_callback = event_callback
        self.room_id = room_id
        self.audio_queue = queue.Queue()
        self.is_running = False
        
        logger.info(f"Loading Whisper model '{whisper_model}' on {whisper_device}...")
        try:
            self.model = WhisperModel(
                whisper_model,
                device=whisper_device,
                compute_type=whisper_compute_type
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            logger.warning(f"Audio stream status: {status}")
        
        self.audio_queue.put(indata.copy())
    
    def transcribe_buffer(self, audio_buffer: list) -> Optional[str]:
        """
        Transcribe a buffer of audio chunks.
        
        Args:
            audio_buffer: List of numpy arrays (audio chunks)
        
        Returns:
            Transcribed text or None if no speech detected
        """
        if not audio_buffer:
            return None
        
        # Concatenate all chunks
        audio = np.concatenate(audio_buffer)
        
        # Log audio level for diagnostics
        peak = np.max(np.abs(audio))
        logger.debug(f"Audio peak level: {peak:.4f}")
        
        # Resample from capture rate to Whisper rate
        audio = resample_poly(
            audio,
            self.audio_config.whisper_rate,
            int(self.audio_config.sample_rate * 160 / 441)
        ).astype(np.float32)
        
        try:
            segments, info = self.model.transcribe(
                audio,
                beam_size=1,
                vad_filter=False
            )
            
            text = " ".join(
                segment.text.strip() for segment in segments
            ).strip()
            
            if text:
                logger.info(f"Transcribed: {text}")
                return text
            else:
                logger.debug("No speech recognized in audio buffer")
                return None
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def emit_speech_event(self, text: str):
        """
        Create and emit a SpeechEvent.
        
        Args:
            text: Transcribed speech text
        """
        event = SpeechEvent.create(
            source=self.room_id,
            text=text,
            confidence=1.0,  # Whisper doesn't provide per-segment confidence
            language="en"
        )
        
        logger.info(f"Emitting SpeechEvent: {event.event_id}")
        
        if self.event_callback:
            try:
                self.event_callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    def start_listening(self):
        """
        Start continuous audio capture and processing.
        Blocks until KeyboardInterrupt.
        """
        logger.info(f"Starting speech processor (device={self.audio_config.device})")
        self.is_running = True
        
        try:
            audio_buffer = []
            
            with sd.InputStream(
                device=self.audio_config.device,
                samplerate=self.audio_config.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=self.audio_config.block_size,
                callback=self._audio_callback
            ):
                logger.info("Audio stream started. Listening for speech...")
                
                while self.is_running:
                    chunk = self.audio_queue.get()
                    audio_buffer.append(chunk.flatten())
                    
                    if len(audio_buffer) >= self.audio_config.process_seconds:
                        logger.debug(f"Buffer ready ({self.audio_config.process_seconds}s), processing...")
                        
                        text = self.transcribe_buffer(audio_buffer)
                        audio_buffer = []
                        
                        if text:
                            self.emit_speech_event(text)
        
        except KeyboardInterrupt:
            logger.info("Speech processor stopped by user")
        except Exception as e:
            logger.error(f"Speech processor error: {e}")
            raise
        finally:
            self.is_running = False


def create_speech_processor(
    room_id: str,
    audio_device: int = None,
    sample_rate: int = 44100,
    whisper_model: str = "base",
    event_callback: Optional[Callable[[SpeechEvent], None]] = None
) -> SpeechProcessor:
    """
    Factory function to create a speech processor with standard settings.
    
    Args:
        room_id: Room identifier (A or B)
        audio_device: Microphone device ID (uses default if None)
        sample_rate: Audio capture sample rate
        whisper_model: Whisper model size
        event_callback: Function called with SpeechEvent objects
    
    Returns:
        Configured SpeechProcessor instance
    """
    audio_config = AudioConfig(
        device=audio_device or 1,
        sample_rate=sample_rate
    )
    
    return SpeechProcessor(
        audio_config=audio_config,
        whisper_model=whisper_model,
        event_callback=event_callback,
        room_id=room_id
    )


# Standalone mode: for testing or service operation
if __name__ == "__main__":
    import logging.config
    
    # Basic logging setup for standalone mode
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    
    # Create a speech processor with no event callback (just logging)
    processor = create_speech_processor(
        room_id="A",
        audio_device=1,
        whisper_model="base"
    )
    
    # Start listening
    processor.start_listening()
