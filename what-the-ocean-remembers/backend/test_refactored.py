"""
Integration test for refactored Between Signals backend.

Tests that the refactored communication system maintains all functionality
of the original code while providing better structure and error handling.
"""

import pytest
import logging
from unittest.mock import MagicMock, patch

from events import (
    Event, EventType, SourceEnvironment,
    MovementEvent, SpeechEvent, PresenceEvent, AudioLevelEvent,
    parse_event
)
from config_loader import RoomConfig
from room import Room
from communication_refactored import EventRouter, CommunicationServer


# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


class TestEventCreation:
    """Test event creation and validation."""

    def test_create_movement_event(self):
        """Test creating a movement event."""
        event = MovementEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            present=True,
            position_x=0.5,
            position_y=0.3,
            velocity=0.7,
            direction="right",
            intensity=0.9
        )
        
        assert event.source == SourceEnvironment.ENVIRONMENT_A
        assert event.type == EventType.MOVEMENT
        assert event.event_id is not None
        assert event.timestamp > 0
        assert event.data["position"]["x"] == 0.5
        assert event.data["intensity"] == 0.9

    def test_create_speech_event(self):
        """Test creating a speech event."""
        event = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_B,
            text="Hello from the other ocean",
            language="en"
        )
        
        assert event.source == SourceEnvironment.ENVIRONMENT_B
        assert event.type == EventType.SPEECH
        assert event.data["text"] == "Hello from the other ocean"
        assert event.data["language"] == "en"

    def test_create_presence_event(self):
        """Test creating a presence event."""
        event = PresenceEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            present=True
        )
        
        assert event.source == SourceEnvironment.ENVIRONMENT_A
        assert event.type == EventType.PRESENCE
        assert event.data["present"] is True

    def test_create_audio_level_event(self):
        """Test creating an audio level event."""
        event = AudioLevelEvent.create(
            source=SourceEnvironment.ENVIRONMENT_B,
            level=0.75
        )
        
        assert event.source == SourceEnvironment.ENVIRONMENT_B
        assert event.type == EventType.AUDIO_LEVEL
        assert event.data["level"] == 0.75

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            text="Test message"
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["type"] == "speech"
        assert event_dict["source"] == "A"
        assert event_dict["data"]["text"] == "Test message"
        assert "event_id" in event_dict
        assert "timestamp" in event_dict

    def test_parse_event(self):
        """Test parsing event from dictionary."""
        original_event = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_B,
            text="Parsed message"
        )
        
        event_dict = original_event.to_dict()
        parsed_event = parse_event(event_dict)
        
        assert parsed_event.type == EventType.SPEECH
        assert parsed_event.source == SourceEnvironment.ENVIRONMENT_B
        assert parsed_event.data["text"] == "Parsed message"


class TestRoomConfiguration:
    """Test room configuration loading."""

    def test_load_config_file(self):
        """Test loading configuration from file."""
        config = RoomConfig("A")
        
        assert config.room_id == "A"
        assert config.get("environment") == "grass"
        assert config.get("osc_output_port") == 7001
        assert config.get("mode") == "simulation"

    def test_config_missing_file_uses_defaults(self):
        """Test that missing config file uses defaults."""
        with patch('config_loader.Path.exists', return_value=False):
            config = RoomConfig("C")  # Non-existent room
            
            assert config.get("room_id") == "C"
            assert config.get("mode") == "simulation"
            assert config.get("backend_port") == 8000

    def test_config_dict_access(self):
        """Test dict-like access to configuration."""
        config = RoomConfig("A")
        
        assert config["environment"] == "grass"
        assert "environment" in config
        assert config.to_dict() is not None


class TestRoomClass:
    """Test Room class functionality."""

    def test_room_initialization(self):
        """Test room initialization."""
        config = RoomConfig("A")
        room = Room(config)
        
        assert room.room_id == "A"
        assert room.environment_type == "grass"
        assert room.osc_client is not None

    def test_room_receives_remote_event(self):
        """Test room receiving an event from opposite room."""
        config = RoomConfig("A")
        room = Room(config)
        
        event = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_B,
            text="Message from B"
        )
        
        # Mock OSC client to avoid actual network calls
        room.osc_client.send_message = MagicMock()
        
        room.receive_remote_event(event)
        
        # Verify OSC message was sent
        room.osc_client.send_message.assert_called()
        assert event.event_id in room._recent_event_ids

    def test_room_duplicate_detection(self):
        """Test that duplicate events are ignored."""
        config = RoomConfig("A")
        room = Room(config)
        
        event = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_B,
            text="Duplicate test"
        )
        
        room.osc_client.send_message = MagicMock()
        
        # First time should process
        room.receive_remote_event(event)
        assert room.osc_client.send_message.call_count == 1
        
        # Second time (duplicate) should be ignored
        room.receive_remote_event(event)
        assert room.osc_client.send_message.call_count == 1  # No change

    def test_room_emits_local_event(self):
        """Test room emitting a local event."""
        config = RoomConfig("A")
        room = Room(config)
        
        # Mock the router
        router_mock = MagicMock()
        room.event_router = router_mock
        
        event = MovementEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            present=True,
            position_x=0.5,
            position_y=0.5
        )
        
        room.emit_local_event(event)
        
        # Verify router was called
        router_mock.assert_called()

    def test_room_event_history(self):
        """Test room maintains event history."""
        config = RoomConfig("A")
        room = Room(config)
        
        room.osc_client.send_message = MagicMock()
        
        for i in range(5):
            event = SpeechEvent.create(
                source=SourceEnvironment.ENVIRONMENT_B,
                text=f"Message {i}"
            )
            room.receive_remote_event(event)
        
        history = room.get_event_history(10)
        assert len(history) == 5


class TestEventRouter:
    """Test EventRouter functionality."""

    def test_router_routes_a_to_b(self):
        """Test that events from A are routed to B."""
        config_a = RoomConfig("A")
        config_b = RoomConfig("B")
        
        room_a = Room(config_a)
        room_b = Room(config_b)
        
        router = EventRouter(room_a, room_b)
        
        # Mock OSC clients
        room_a.osc_client.send_message = MagicMock()
        room_b.osc_client.send_message = MagicMock()
        
        event = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            text="Message from A"
        )
        
        router.route_event(event)
        
        # Event should reach B
        room_b.osc_client.send_message.assert_called()

    def test_router_routes_b_to_a(self):
        """Test that events from B are routed to A."""
        config_a = RoomConfig("A")
        config_b = RoomConfig("B")
        
        room_a = Room(config_a)
        room_b = Room(config_b)
        
        router = EventRouter(room_a, room_b)
        
        # Mock OSC clients
        room_a.osc_client.send_message = MagicMock()
        room_b.osc_client.send_message = MagicMock()
        
        event = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_B,
            text="Message from B"
        )
        
        router.route_event(event)
        
        # Event should reach A
        room_a.osc_client.send_message.assert_called()

    def test_router_no_echo_back(self):
        """Test that router never echoes events back to source."""
        config_a = RoomConfig("A")
        config_b = RoomConfig("B")
        
        room_a = Room(config_a)
        room_b = Room(config_b)
        
        router = EventRouter(room_a, room_b)
        
        # Mock OSC clients
        room_a.osc_client.send_message = MagicMock()
        room_b.osc_client.send_message = MagicMock()
        
        event = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            text="Test message"
        )
        
        router.route_event(event)
        
        # A should NOT receive the message it sent
        room_a.osc_client.send_message.assert_not_called()
        # B should receive it
        room_b.osc_client.send_message.assert_called()


class TestOSCOutputFormats:
    """Test OSC output message formats."""

    def test_movement_osc_format(self):
        """Test movement event OSC format."""
        config = RoomConfig("A")
        room = Room(config)
        
        room.osc_client.send_message = MagicMock()
        
        event = MovementEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            present=True,
            position_x=0.5,
            position_y=0.3,
            intensity=0.9
        )
        
        room._send_movement_osc(event)
        
        # Verify correct OSC address and data format
        room.osc_client.send_message.assert_called_with(
            "/ocean/movement",
            [0.5, 0.3, 0.9]
        )

    def test_speech_osc_format(self):
        """Test speech event OSC format."""
        config = RoomConfig("A")
        room = Room(config)
        
        room.osc_client.send_message = MagicMock()
        
        event = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            text="Hello world"
        )
        
        room._send_speech_osc(event)
        
        room.osc_client.send_message.assert_called_with(
            "/ocean/text",
            "Hello world"
        )

    def test_presence_osc_format(self):
        """Test presence event OSC format."""
        config = RoomConfig("A")
        room = Room(config)
        
        room.osc_client.send_message = MagicMock()
        
        event = PresenceEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            present=True
        )
        
        room._send_presence_osc(event)
        
        room.osc_client.send_message.assert_called_with(
            "/ocean/presence",
            1
        )

    def test_audio_level_osc_format(self):
        """Test audio level event OSC format."""
        config = RoomConfig("A")
        room = Room(config)
        
        room.osc_client.send_message = MagicMock()
        
        event = AudioLevelEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            level=0.75
        )
        
        room._send_audio_level_osc(event)
        
        room.osc_client.send_message.assert_called_with(
            "/ocean/audio_level",
            0.75
        )


class TestBidirectionalCommunication:
    """Integration tests for bidirectional communication."""

    def test_full_communication_cycle_a_to_b(self):
        """Test complete message flow from A to B."""
        config_a = RoomConfig("A")
        config_b = RoomConfig("B")
        
        room_a = Room(config_a)
        room_b = Room(config_b)
        
        router = EventRouter(room_a, room_b)
        
        room_a.event_router = router.route_event
        room_b.event_router = router.route_event
        
        # Mock OSC clients
        room_a.osc_client.send_message = MagicMock()
        room_b.osc_client.send_message = MagicMock()
        
        # Create event from A
        event = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            text="Hello from grass"
        )
        
        # Emit from A
        room_a.emit_local_event(event)
        
        # Verify B received it and A did not
        room_b.osc_client.send_message.assert_called()
        room_a.osc_client.send_message.assert_not_called()

    def test_full_communication_cycle_b_to_a(self):
        """Test complete message flow from B to A."""
        config_a = RoomConfig("A")
        config_b = RoomConfig("B")
        
        room_a = Room(config_a)
        room_b = Room(config_b)
        
        router = EventRouter(room_a, room_b)
        
        room_a.event_router = router.route_event
        room_b.event_router = router.route_event
        
        # Mock OSC clients
        room_a.osc_client.send_message = MagicMock()
        room_b.osc_client.send_message = MagicMock()
        
        # Create event from B
        event = MovementEvent.create(
            source=SourceEnvironment.ENVIRONMENT_B,
            present=True,
            position_x=0.4,
            position_y=0.6,
            intensity=0.8
        )
        
        # Emit from B
        room_b.emit_local_event(event)
        
        # Verify A received it and B did not
        room_a.osc_client.send_message.assert_called()
        room_b.osc_client.send_message.assert_not_called()

    def test_simultaneous_bidirectional_messages(self):
        """Test that simultaneous messages from both rooms work correctly."""
        config_a = RoomConfig("A")
        config_b = RoomConfig("B")
        
        room_a = Room(config_a)
        room_b = Room(config_b)
        
        router = EventRouter(room_a, room_b)
        
        room_a.event_router = router.route_event
        room_b.event_router = router.route_event
        
        # Mock OSC clients
        room_a.osc_client.send_message = MagicMock()
        room_b.osc_client.send_message = MagicMock()
        
        # Simultaneous messages from both
        event_a = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_A,
            text="Hello from A"
        )
        event_b = SpeechEvent.create(
            source=SourceEnvironment.ENVIRONMENT_B,
            text="Hello from B"
        )
        
        room_a.emit_local_event(event_a)
        room_b.emit_local_event(event_b)
        
        # Both should have received exactly one message each
        assert room_a.osc_client.send_message.call_count == 1
        assert room_b.osc_client.send_message.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
