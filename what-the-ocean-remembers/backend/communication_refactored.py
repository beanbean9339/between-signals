"""
Central communication router for Between Signals.

Manages bidirectional routing of events between Environment A and Environment B.
Ensures events are routed to opposite environment with no echo-back.
"""

import logging
from typing import Dict, Optional, Callable
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

from events import Event, EventType, SourceEnvironment
from room import Room
from config_loader import RoomConfig

logger = logging.getLogger(__name__)


class EventRouter:
    """
    Routes events between two rooms, ensuring proper cross-environment delivery.
    
    Receives incoming OSC messages, converts them to Events, and routes to
    the opposite room (A→B or B→A, never echo-back).
    """

    def __init__(self, room_a: Room, room_b: Room):
        """
        Initialize the router with two rooms.
        
        Args:
            room_a: Room instance for Environment A
            room_b: Room instance for Environment B
        """
        self.rooms = {
            SourceEnvironment.ENVIRONMENT_A: room_a,
            SourceEnvironment.ENVIRONMENT_B: room_b,
        }
        
        logger.info("EventRouter initialized")

    def route_event(self, event: Event) -> None:
        """
        Route an event to the opposite room.
        
        Args:
            event: Event to route
            
        Raises:
            ValueError: If source environment is unknown
        """
        # Get the room that sent this event
        source_room = self.rooms.get(event.source)
        if source_room is None:
            raise ValueError(f"Unknown source: {event.source}")

        # Determine target room (opposite of source)
        target_env = (
            SourceEnvironment.ENVIRONMENT_B 
            if event.source == SourceEnvironment.ENVIRONMENT_A
            else SourceEnvironment.ENVIRONMENT_A
        )
        target_room = self.rooms[target_env]

        logger.debug(f"Routing {event.type.value} from {event.source.value} to {target_env.value}")

        # Send to target room
        target_room.receive_remote_event(event)

    def get_target_room(self, source: SourceEnvironment) -> Room:
        """
        Get the room that should receive an event from the given source.
        
        Args:
            source: Source environment
            
        Returns:
            Target Room instance
        """
        if source == SourceEnvironment.ENVIRONMENT_A:
            return self.rooms[SourceEnvironment.ENVIRONMENT_B]
        elif source == SourceEnvironment.ENVIRONMENT_B:
            return self.rooms[SourceEnvironment.ENVIRONMENT_A]
        else:
            raise ValueError(f"Unknown source: {source}")


class CommunicationServer:
    """
    OSC server that receives messages from local sensors/input and routes them.
    
    Listens on a local port for OSC messages from Python sensor processes
    or other local applications, converts them to Events, and routes them
    through the EventRouter.
    """

    def __init__(self, event_router: EventRouter, backend_port: int = 8000):
        """
        Initialize the communication server.
        
        Args:
            event_router: EventRouter instance
            backend_port: Port to listen on for incoming OSC messages
        """
        self.event_router = event_router
        self.backend_port = backend_port
        self.server = None

        logger.info(f"CommunicationServer initialized on port {backend_port}")

    def start(self) -> None:
        """Start the OSC server."""
        dispatcher = Dispatcher()

        # Register handlers for different message types
        dispatcher.map("/input/text", self._handle_text_input)
        dispatcher.map("/input/movement", self._handle_movement_input)
        dispatcher.map("/input/presence", self._handle_presence_input)
        dispatcher.map("/input/object", self._handle_object_input)
        dispatcher.map("/input/audio", self._handle_audio_input)

        # Create and start server
        self.server = ThreadingOSCUDPServer(
            ("127.0.0.1", self.backend_port),
            dispatcher
        )

        logger.info(f"CommunicationServer listening on port {self.backend_port}")
        self.server.serve_forever()

    def stop(self) -> None:
        """Stop the OSC server."""
        if self.server:
            self.server.shutdown()
            logger.info("CommunicationServer stopped")

    def _handle_text_input(self, address: str, source: str, message: str) -> None:
        """
        Handle incoming text message (/input/text).
        
        Args:
            address: OSC address
            source: Source environment (A or B)
            message: Text message content
        """
        try:
            source_env = SourceEnvironment(source)
            event = Event.create(
                EventType.SPEECH,
                source_env,
                {"text": str(message), "language": "en", "confidence": 1.0}
            )
            self.event_router.route_event(event)
            logger.info(f"[TEXT] {source}: {message[:50]}...")
        except Exception as e:
            logger.error(f"Error handling text input: {e}")

    def _handle_movement_input(
        self, address: str, source: str, x: float, y: float, intensity: float
    ) -> None:
        """
        Handle incoming movement data (/input/movement).
        
        Args:
            address: OSC address
            source: Source environment (A or B)
            x: Normalized X position (0.0-1.0)
            y: Normalized Y position (0.0-1.0)
            intensity: Movement intensity (0.0-1.0)
        """
        try:
            source_env = SourceEnvironment(source)
            event = Event.create(
                EventType.MOVEMENT,
                source_env,
                {
                    "present": True,
                    "position": {"x": float(x), "y": float(y)},
                    "velocity": 0.0,  # Could be extended later
                    "direction": "none",  # Could be computed later
                    "intensity": float(intensity),
                }
            )
            self.event_router.route_event(event)
            logger.debug(f"[MOVEMENT] {source}: x={x:.2f}, y={y:.2f}, intensity={intensity:.2f}")
        except Exception as e:
            logger.error(f"Error handling movement input: {e}")

    def _handle_presence_input(
        self, address: str, source: str, present: int
    ) -> None:
        """
        Handle incoming presence data (/input/presence).
        
        Args:
            address: OSC address
            source: Source environment (A or B)
            present: 1 if visitor present, 0 if not
        """
        try:
            source_env = SourceEnvironment(source)
            event = Event.create(
                EventType.PRESENCE,
                source_env,
                {"present": bool(present), "visitor_id": None}
            )
            self.event_router.route_event(event)
            logger.info(f"[PRESENCE] {source}: {bool(present)}")
        except Exception as e:
            logger.error(f"Error handling presence input: {e}")

    def _handle_object_input(self, address: str, source: str, object_name: str) -> None:
        """
        Handle incoming object detection (/input/object).
        
        Args:
            address: OSC address
            source: Source environment (A or B)
            object_name: Name of detected object
        """
        try:
            source_env = SourceEnvironment(source)
            event = Event.create(
                EventType.OBJECT_DETECTION,
                source_env,
                {"object": str(object_name)}
            )
            self.event_router.route_event(event)
            logger.info(f"[OBJECT] {source}: {object_name}")
        except Exception as e:
            logger.error(f"Error handling object input: {e}")

    def _handle_audio_input(self, address: str, source: str, level: float) -> None:
        """
        Handle incoming audio level (/input/audio).
        
        Args:
            address: OSC address
            source: Source environment (A or B)
            level: Audio level (0.0-1.0)
        """
        try:
            source_env = SourceEnvironment(source)
            event = Event.create(
                EventType.AUDIO_LEVEL,
                source_env,
                {"level": float(level)}
            )
            self.event_router.route_event(event)
            logger.debug(f"[AUDIO] {source}: {level:.3f}")
        except Exception as e:
            logger.error(f"Error handling audio input: {e}")


def create_communication_server(
    backend_port: int = 8000
) -> tuple[EventRouter, CommunicationServer]:
    """
    Factory function to create and configure the communication system.
    
    Creates two Room instances, an EventRouter, and a CommunicationServer,
    all properly connected and configured.
    
    Args:
        backend_port: Port for the OSC backend server
        
    Returns:
        Tuple of (EventRouter, CommunicationServer)
    """
    # Load room configurations
    config_a = RoomConfig("A")
    config_b = RoomConfig("B")

    # Create rooms with router callback
    # Note: We'll set the router after creating both rooms
    room_a = Room(config_a)
    room_b = Room(config_b)

    # Create router
    router = EventRouter(room_a, room_b)

    # Set router callbacks on rooms (for local event emission)
    room_a.event_router = router.route_event
    room_b.event_router = router.route_event

    # Create communication server
    server = CommunicationServer(router, backend_port)

    logger.info("Communication system created and configured")
    return router, server


def start_server() -> None:
    """Start the communication server (entry point)."""
    router, server = create_communication_server()
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.stop()
