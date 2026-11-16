"""
Event protocol module for Between Signals.

Defines the structured event format used for communication between environments.
All events follow this schema to ensure consistency and validate ability.
"""

import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Literal
from enum import Enum


class EventType(str, Enum):
    """Supported event types."""
    MOVEMENT = "movement"
    PRESENCE = "presence"
    SPEECH = "speech"
    OBJECT_DETECTION = "object_detection"
    AUDIO_LEVEL = "audio_level"


class SourceEnvironment(str, Enum):
    """Environment source identifiers."""
    ENVIRONMENT_A = "A"
    ENVIRONMENT_B = "B"


@dataclass
class Event:
    """
    Base event structure for all inter-environment communication.
    
    Attributes:
        event_id: Unique identifier for this event
        type: Event type (movement, speech, etc.)
        source: Source environment (A or B)
        timestamp: Unix timestamp when event was created
        data: Event-specific data payload
    """
    event_id: str
    type: EventType
    source: SourceEnvironment
    timestamp: float
    data: Dict[str, Any]

    @staticmethod
    def create(
        event_type: EventType,
        source: SourceEnvironment,
        data: Dict[str, Any]
    ) -> "Event":
        """
        Factory method to create a new event with auto-generated ID and timestamp.
        
        Args:
            event_type: Type of event
            source: Source environment (A or B)
            data: Event-specific data payload
            
        Returns:
            New Event instance
        """
        return Event(
            event_id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            timestamp=time.time(),
            data=data
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "source": self.source.value,
            "timestamp": self.timestamp,
            "data": self.data
        }

    def __str__(self) -> str:
        """String representation for logging."""
        return f"Event({self.type.value} from {self.source.value}, id={self.event_id[:8]}...)"


@dataclass
class MovementEvent(Event):
    """
    Movement event data structure.
    
    Contains normalized visitor position and motion information.
    """
    
    def __init__(
        self,
        source: SourceEnvironment,
        present: bool,
        position_x: float,
        position_y: float,
        velocity: float,
        direction: str,
        intensity: float,
        event_id: str = None,
        timestamp: float = None
    ):
        if event_id is None:
            event_id = str(uuid.uuid4())
        if timestamp is None:
            timestamp = time.time()
            
        data = {
            "present": present,
            "position": {
                "x": float(position_x),
                "y": float(position_y)
            },
            "velocity": float(velocity),
            "direction": str(direction),
            "intensity": float(intensity)
        }
        
        super().__init__(
            event_id=event_id,
            type=EventType.MOVEMENT,
            source=source,
            timestamp=timestamp,
            data=data
        )

    @staticmethod
    def create(
        source,  # Can be string "A"/"B" or SourceEnvironment enum
        present: bool,
        position_x: float,
        position_y: float,
        velocity: float = 0.0,
        direction: str = "none",
        intensity: float = 0.0
    ) -> "MovementEvent":
        """Create a new movement event."""
        # Convert string to enum if needed
        if isinstance(source, str):
            source = SourceEnvironment.ENVIRONMENT_A if source == "A" else SourceEnvironment.ENVIRONMENT_B
        
        return MovementEvent(
            source=source,
            present=present,
            position_x=position_x,
            position_y=position_y,
            velocity=velocity,
            direction=direction,
            intensity=intensity
        )


@dataclass
class SpeechEvent(Event):
    """
    Speech event data structure.
    
    Contains transcribed text from speech-to-text processing.
    """
    
    def __init__(
        self,
        source: SourceEnvironment,
        text: str,
        language: str = "en",
        confidence: float = 1.0,
        event_id: str = None,
        timestamp: float = None
    ):
        if event_id is None:
            event_id = str(uuid.uuid4())
        if timestamp is None:
            timestamp = time.time()
            
        data = {
            "text": str(text),
            "language": str(language),
            "confidence": float(confidence)
        }
        
        super().__init__(
            event_id=event_id,
            type=EventType.SPEECH,
            source=source,
            timestamp=timestamp,
            data=data
        )

    @staticmethod
    def create(
        source,  # Can be string "A"/"B" or SourceEnvironment enum
        text: str,
        language: str = "en",
        confidence: float = 1.0
    ) -> "SpeechEvent":
        """Create a new speech event."""
        # Convert string to enum if needed
        if isinstance(source, str):
            source = SourceEnvironment.ENVIRONMENT_A if source == "A" else SourceEnvironment.ENVIRONMENT_B
        
        return SpeechEvent(
            source=source,
            text=text,
            language=language,
            confidence=confidence
        )


@dataclass
class PresenceEvent(Event):
    """
    Presence event data structure.
    
    Indicates visitor entering or leaving the interaction area.
    """
    
    def __init__(
        self,
        source: SourceEnvironment,
        present: bool,
        visitor_id: str = None,
        event_id: str = None,
        timestamp: float = None
    ):
        if event_id is None:
            event_id = str(uuid.uuid4())
        if timestamp is None:
            timestamp = time.time()
            
        data = {
            "present": bool(present),
            "visitor_id": visitor_id
        }
        
        super().__init__(
            event_id=event_id,
            type=EventType.PRESENCE,
            source=source,
            timestamp=timestamp,
            data=data
        )

    @staticmethod
    def create(
        source,  # Can be string "A"/"B" or SourceEnvironment enum
        present: bool,
        visitor_id: str = None
    ) -> "PresenceEvent":
        """Create a new presence event."""
        # Convert string to enum if needed
        if isinstance(source, str):
            source = SourceEnvironment.ENVIRONMENT_A if source == "A" else SourceEnvironment.ENVIRONMENT_B
        
        return PresenceEvent(
            source=source,
            present=present,
            visitor_id=visitor_id
        )


@dataclass
class AudioLevelEvent(Event):
    """
    Audio level event data structure.
    
    Contains microphone input level for visualization purposes.
    """
    
    def __init__(
        self,
        source: SourceEnvironment,
        level: float,
        event_id: str = None,
        timestamp: float = None
    ):
        if event_id is None:
            event_id = str(uuid.uuid4())
        if timestamp is None:
            timestamp = time.time()
            
        data = {
            "level": float(level)
        }
        
        super().__init__(
            event_id=event_id,
            type=EventType.AUDIO_LEVEL,
            source=source,
            timestamp=timestamp,
            data=data
        )

    @staticmethod
    def create(
        source,  # Can be string "A"/"B" or SourceEnvironment enum
        level: float
    ) -> "AudioLevelEvent":
        """Create a new audio level event."""
        # Convert string to enum if needed
        if isinstance(source, str):
            source = SourceEnvironment.ENVIRONMENT_A if source == "A" else SourceEnvironment.ENVIRONMENT_B
        
        return AudioLevelEvent(
            source=source,
            level=level
        )


def parse_event(event_dict: Dict[str, Any]) -> Event:
    """
    Parse a dictionary into an Event instance.
    
    Args:
        event_dict: Dictionary with event data
        
    Returns:
        Appropriate Event subclass instance
        
    Raises:
        ValueError: If event type is unknown or data is invalid
    """
    try:
        event_type = EventType(event_dict["type"])
        source = SourceEnvironment(event_dict["source"])
    except (KeyError, ValueError) as e:
        raise ValueError(f"Invalid event data: {e}")

    event_id = event_dict.get("event_id")
    timestamp = event_dict.get("timestamp")
    data = event_dict.get("data", {})

    # Route to appropriate event class based on type
    if event_type == EventType.MOVEMENT:
        return MovementEvent(
            source=source,
            present=data.get("present", False),
            position_x=data.get("position", {}).get("x", 0),
            position_y=data.get("position", {}).get("y", 0),
            velocity=data.get("velocity", 0),
            direction=data.get("direction", "none"),
            intensity=data.get("intensity", 0),
            event_id=event_id,
            timestamp=timestamp
        )
    elif event_type == EventType.SPEECH:
        return SpeechEvent(
            source=source,
            text=data.get("text", ""),
            language=data.get("language", "en"),
            confidence=data.get("confidence", 1.0),
            event_id=event_id,
            timestamp=timestamp
        )
    elif event_type == EventType.PRESENCE:
        return PresenceEvent(
            source=source,
            present=data.get("present", False),
            visitor_id=data.get("visitor_id"),
            event_id=event_id,
            timestamp=timestamp
        )
    elif event_type == EventType.AUDIO_LEVEL:
        return AudioLevelEvent(
            source=source,
            level=data.get("level", 0),
            event_id=event_id,
            timestamp=timestamp
        )
    else:
        # Return base Event for unknown types
        return Event(
            event_id=event_id or str(uuid.uuid4()),
            type=event_type,
            source=source,
            timestamp=timestamp or time.time(),
            data=data
        )
