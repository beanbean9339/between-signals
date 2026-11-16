"""
Room-aware speech processor integration.
Connects the speech processor to a room so transcribed speech
automatically emits as SpeechEvent objects to the communication router.
"""

import logging
from typing import Optional
from speech_refactored import SpeechProcessor, create_speech_processor, AudioConfig
from room import Room
from events import SpeechEvent

logger = logging.getLogger(__name__)


class RoomSpeechProcessor:
    """
    Wraps SpeechProcessor and Room, enabling automatic event routing
    when speech is transcribed.
    
    Usage:
        processor = RoomSpeechProcessor.create(room_a, room_id="A")
        processor.start_listening()  # Blocks until KeyboardInterrupt
    """
    
    def __init__(
        self,
        speech_processor: SpeechProcessor,
        room: Room
    ):
        """
        Initialize room-aware speech processor.
        
        Args:
            speech_processor: Configured SpeechProcessor instance
            room: Room instance to emit events to
        """
        self.speech_processor = speech_processor
        self.room = room
        
        # Attach room's emit_local_event as the callback
        self.speech_processor.event_callback = self._on_speech_event
        
        logger.info(
            f"RoomSpeechProcessor initialized for room {room.room_id}"
        )
    
    def _on_speech_event(self, event: SpeechEvent):
        """
        Handle transcribed speech by emitting to the room.
        
        Args:
            event: SpeechEvent from the speech processor
        """
        logger.info(f"Routing SpeechEvent to room {self.room.room_id}")
        self.room.emit_local_event(event)
    
    def start_listening(self):
        """
        Start continuous listening and processing.
        Blocks until KeyboardInterrupt.
        """
        logger.info(f"Starting speech listener for {self.room.room_id}")
        self.speech_processor.start_listening()
    
    def stop(self):
        """Stop listening"""
        self.speech_processor.is_running = False
        logger.info("Speech processor stopped")
    
    @staticmethod
    def create(
        room: Room,
        room_id: str = None,
        audio_device: int = None,
        whisper_model: str = "base"
    ) -> "RoomSpeechProcessor":
        """
        Factory method to create a speech processor for a room.
        
        Args:
            room: Room instance to route events to
            room_id: Room identifier (uses room.room_id if None)
            audio_device: Microphone device ID (uses config default if None)
            whisper_model: Whisper model size
        
        Returns:
            Configured RoomSpeechProcessor
        """
        room_id = room_id or room.room_id
        audio_device = audio_device or room.config.get("microphone_device", 1)
        
        speech_processor = create_speech_processor(
            room_id=room_id,
            audio_device=audio_device,
            whisper_model=whisper_model
        )
        
        return RoomSpeechProcessor(speech_processor, room)


if __name__ == "__main__":
    import logging.config
    from config_loader import load_config
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler("between_signals.log"),
            logging.StreamHandler()
        ]
    )
    
    # Example: Run speech processor for Room A
    config_a = load_config("config/room_a.json")
    room_a = Room.create(config_a)
    
    processor = RoomSpeechProcessor.create(room_a, audio_device=1)
    processor.start_listening()
