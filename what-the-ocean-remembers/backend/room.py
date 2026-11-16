"""
Room class for Between Signals.

Encapsulates a single environment's state, event handling, and communication.
"""

import logging
from typing import Callable, Optional, Dict, Any, List
from collections import deque
from pythonosc.udp_client import SimpleUDPClient

from events import Event, EventType, SourceEnvironment
from config_loader import RoomConfig

logger = logging.getLogger(__name__)


class Room:
    """
    Represents a single environment (A or B) in the Between Signals installation.
    
    Each room:
    - Owns its local configuration
    - Manages OSC output to TouchDesigner
    - Receives events from the router
    - Maintains event history for de-duplication
    """

    def __init__(
        self,
        config: RoomConfig,
        event_router: Optional[Callable] = None
    ):
        """
        Initialize a room.
        
        Args:
            config: RoomConfig instance
            event_router: Callback function to route local events to opposite room
                         Signature: event_router(Event) -> None
        """
        self.config = config
        self.room_id = config.get("room_id")
        self.environment_type = config.get("environment")
        self.event_router = event_router
        
        # OSC output client (sends to TouchDesigner)
        osc_host = config.get("osc_output_host", "127.0.0.1")
        osc_port = config.get("osc_output_port", 7001)
        self.osc_client = SimpleUDPClient(osc_host, osc_port)
        
        # Event de-duplication (store recent event IDs)
        self._recent_event_ids: deque = deque(maxlen=100)
        
        # Event history for debugging/diagnostics
        self._event_history: deque = deque(maxlen=1000)
        
        logger.info(f"Room {self.room_id} initialized ({self.environment_type})")

    def receive_remote_event(self, event: Event) -> None:
        """
        Handle an event received from the opposite room.
        
        Args:
            event: Event from opposite environment
        """
        logger.debug(f"Room {self.room_id} received: {event}")
        
        # Check for duplicates
        if event.event_id in self._recent_event_ids:
            logger.debug(f"Ignoring duplicate event: {event.event_id}")
            return
        
        self._recent_event_ids.append(event.event_id)
        self._event_history.append(event)
        
        # Send event to TouchDesigner via OSC
        self._send_to_osc(event)

    def emit_local_event(self, event: Event) -> None:
        """
        Emit a local event (from sensors/microphone) to the opposite room.
        
        Args:
            event: Event from local sensors
        """
        logger.debug(f"Room {self.room_id} emitting: {event}")
        
        # Ensure event source is correct
        event.source = SourceEnvironment(self.room_id)
        
        self._event_history.append(event)
        
        # Route event to opposite room
        if self.event_router:
            try:
                self.event_router(event)
            except Exception as e:
                logger.error(f"Failed to route event: {e}")
        else:
            logger.warning("No event router configured")

    def _send_to_osc(self, event: Event) -> None:
        """
        Send event data to TouchDesigner via OSC.
        
        Args:
            event: Event to send
        """
        try:
            if event.type == EventType.MOVEMENT:
                self._send_movement_osc(event)
            elif event.type == EventType.SPEECH:
                self._send_speech_osc(event)
            elif event.type == EventType.PRESENCE:
                self._send_presence_osc(event)
            elif event.type == EventType.AUDIO_LEVEL:
                self._send_audio_level_osc(event)
            else:
                logger.warning(f"Unknown event type: {event.type}")
        except Exception as e:
            logger.error(f"Failed to send OSC message: {e}")

    def _send_movement_osc(self, event: Event) -> None:
        """Send movement event to TouchDesigner."""
        data = event.data
        position = data.get("position", {})
        
        self.osc_client.send_message(
            "/ocean/movement",
            [
                float(position.get("x", 0)),
                float(position.get("y", 0)),
                float(data.get("intensity", 0))
            ]
        )
        logger.debug("Sent movement OSC message")

    def _send_speech_osc(self, event: Event) -> None:
        """Send speech event to TouchDesigner."""
        data = event.data
        text = data.get("text", "")
        
        self.osc_client.send_message("/ocean/text", text)
        logger.debug(f"Sent speech OSC message: {text[:50]}...")

    def _send_presence_osc(self, event: Event) -> None:
        """Send presence event to TouchDesigner."""
        data = event.data
        present = data.get("present", False)
        
        self.osc_client.send_message("/ocean/presence", int(present))
        logger.debug(f"Sent presence OSC message: {present}")

    def _send_audio_level_osc(self, event: Event) -> None:
        """Send audio level event to TouchDesigner."""
        data = event.data
        level = data.get("level", 0)
        
        self.osc_client.send_message("/ocean/audio_level", float(level))
        logger.debug(f"Sent audio level OSC message: {level}")

    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status and diagnostics.
        
        Returns:
            Dictionary with status information
        """
        return {
            "room_id": self.room_id,
            "environment": self.environment_type,
            "osc_connected": self.osc_client is not None,
            "recent_events": len(self._recent_event_ids),
            "total_events_received": len(self._event_history),
        }

    def get_event_history(self, count: int = 10) -> List[Event]:
        """
        Get recent event history.
        
        Args:
            count: Number of recent events to return
            
        Returns:
            List of recent Event instances
        """
        return list(self._event_history)[-count:]

    def reset(self) -> None:
        """Reset room state (useful for testing)."""
        self._recent_event_ids.clear()
        self._event_history.clear()
        logger.info(f"Room {self.room_id} state reset")
