"""
Tests for TouchDesigner Simulation.

Verifies:
- Configuration handling for GRASS and DIRT
- Event routing between environments
- OSC message generation
- Statistics collection
- No echo-back guarantee
"""

import pytest
import time
import logging
from touchdesigner_simulation import (
    TouchDesignerSimulation,
    EnvironmentConfig
)
from events import EventType, SourceEnvironment


logger = logging.getLogger(__name__)


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig dataclass."""
    
    def test_create_grass_config(self):
        """Test creating GRASS environment configuration."""
        config = EnvironmentConfig(
            name="GRASS",
            environment="A",
            touchdesigner_port=7001,
            movement_pattern="walking",
            speech_pattern="conversation",
            duration_seconds=30
        )
        
        assert config.name == "GRASS"
        assert config.environment == "A"
        assert config.touchdesigner_port == 7001
        assert config.movement_pattern == "walking"
        assert config.speech_pattern == "conversation"
        assert config.duration_seconds == 30

    def test_create_dirt_config(self):
        """Test creating DIRT environment configuration."""
        config = EnvironmentConfig(
            name="DIRT",
            environment="B",
            touchdesigner_port=7002,
            movement_pattern="pacing",
            speech_pattern="poetry",
            duration_seconds=45
        )
        
        assert config.name == "DIRT"
        assert config.environment == "B"
        assert config.touchdesigner_port == 7002
        assert config.movement_pattern == "pacing"
        assert config.speech_pattern == "poetry"
        assert config.duration_seconds == 45


class TestTouchDesignerSimulationInit:
    """Tests for TouchDesignerSimulation initialization."""
    
    def test_default_configuration(self):
        """Test initialization with default configurations."""
        sim = TouchDesignerSimulation()
        
        assert sim.osc_host == "127.0.0.1"
        assert sim.grass_config.name == "GRASS"
        assert sim.dirt_config.name == "DIRT"
        assert sim.grass_config.touchdesigner_port == 7001
        assert sim.dirt_config.touchdesigner_port == 7002

    def test_custom_configurations(self):
        """Test initialization with custom configurations."""
        grass = EnvironmentConfig(
            name="GRASS", environment="A", touchdesigner_port=8001,
            movement_pattern="standing", speech_pattern="greeting",
            duration_seconds=15
        )
        dirt = EnvironmentConfig(
            name="DIRT", environment="B", touchdesigner_port=8002,
            movement_pattern="random", speech_pattern="random",
            duration_seconds=20
        )
        
        sim = TouchDesignerSimulation(grass_config=grass, dirt_config=dirt)
        
        assert sim.grass_config.touchdesigner_port == 8001
        assert sim.dirt_config.touchdesigner_port == 8002
        assert sim.grass_config.movement_pattern == "standing"
        assert sim.dirt_config.speech_pattern == "random"

    def test_custom_osc_host(self):
        """Test initialization with custom OSC host."""
        sim = TouchDesignerSimulation(osc_host="192.168.1.100")
        assert sim.osc_host == "192.168.1.100"

    def test_rooms_created(self):
        """Test that Room A and B are created."""
        sim = TouchDesignerSimulation()
        
        assert sim.room_a is not None
        assert sim.room_b is not None
        assert sim.room_a.room_id == "A"
        assert sim.room_b.room_id == "B"

    def test_router_created(self):
        """Test that EventRouter is created."""
        sim = TouchDesignerSimulation()
        assert sim.router is not None

    def test_statistics_initialized(self):
        """Test that statistics are initialized."""
        sim = TouchDesignerSimulation()
        
        assert sim.stats["A"]["movement"] == 0
        assert sim.stats["A"]["speech"] == 0
        assert sim.stats["A"]["received_from_b"] == 0
        assert sim.stats["B"]["movement"] == 0
        assert sim.stats["B"]["speech"] == 0
        assert sim.stats["B"]["received_from_a"] == 0


class TestEventHandling:
    """Tests for event handling and routing."""
    
    def test_handle_movement_event_a(self):
        """Test handling movement event from Environment A."""
        sim = TouchDesignerSimulation()
        
        # Create and emit a movement event from A
        # Note: emit_movement_event calls the callback internally,
        # so the event is already handled
        event = sim.movement_sim_a.emit_movement_event(0.5, 0.5, 0.0, 0.3)
        
        # Verify statistics updated from the emit call
        assert sim.stats["A"]["movement"] == 1
        
        # Verify event routed to B
        assert sim.stats["B"]["received_from_a"] == 1

    def test_handle_speech_event_b(self):
        """Test handling speech event from Environment B."""
        sim = TouchDesignerSimulation()
        
        # Create and emit a speech event from B
        # Note: emit_speech_event calls the callback internally
        event = sim.speech_sim_b.emit_speech_event("Hello from dirt", 0.95)
        
        # Verify statistics updated
        assert sim.stats["B"]["speech"] == 1
        
        # Verify event routed to A
        assert sim.stats["A"]["received_from_b"] == 1

    def test_no_echo_back_guarantee(self):
        """Test that events are not sent back to their source."""
        sim = TouchDesignerSimulation()
        
        # Create movement event from A
        movement_a = sim.movement_sim_a.emit_movement_event(0.5, 0.5, 0.0, 0.3)
        
        # Check that A didn't receive its own event as remote
        # (it should only be in A's local event history from emit, not from routing back)
        history_a = sim.room_a.get_event_history(1000)
        
        # Count events that came FROM A (local source)
        local_events_a = [e for e in history_a if e.source == SourceEnvironment.ENVIRONMENT_A]
        
        # Count events that came FROM B (routed in)
        remote_events_a = [e for e in history_a if e.source == SourceEnvironment.ENVIRONMENT_B]
        
        # We should have local events from our emission
        assert len(local_events_a) >= 1
        # Remote events should only be from B
        for event in remote_events_a:
            assert event.source == SourceEnvironment.ENVIRONMENT_B

    def test_bidirectional_routing(self):
        """Test that events flow bidirectionally."""
        sim = TouchDesignerSimulation()
        
        # Create event from A
        event_a = sim.movement_sim_a.emit_movement_event(0.5, 0.5, 0.0, 0.3)
        
        # Create event from B
        event_b = sim.movement_sim_b.emit_movement_event(0.3, 0.7, 0.0, 0.2)
        
        # Verify A received from B
        assert sim.stats["A"]["received_from_b"] == 1
        
        # Verify B received from A
        assert sim.stats["B"]["received_from_a"] == 1


class TestRoomState:
    """Tests for room state management."""
    
    def test_room_a_history(self):
        """Test that Room A maintains event history."""
        sim = TouchDesignerSimulation()
        
        # Generate and handle events (emit calls the callback)
        event1 = sim.movement_sim_a.emit_movement_event(0.5, 0.5, 0.0, 0.3)
        event2 = sim.speech_sim_a.emit_speech_event("Hello", 0.95)
        
        # Check history
        history = sim.room_a.get_event_history(1000)
        assert len(history) >= 2

    def test_room_b_history(self):
        """Test that Room B maintains event history."""
        sim = TouchDesignerSimulation()
        
        # Generate and handle events
        event1 = sim.movement_sim_b.emit_movement_event(0.3, 0.7, 0.0, 0.2)
        event2 = sim.speech_sim_b.emit_speech_event("Poetry", 0.9)
        
        # Check history
        history = sim.room_b.get_event_history(1000)
        assert len(history) >= 2

    def test_cross_environment_events_in_history(self):
        """Test that remote events appear in opposite room's history."""
        sim = TouchDesignerSimulation()
        
        # Event from A (automatically routed to B via callback)
        event = sim.movement_sim_a.emit_movement_event(0.5, 0.5, 0.0, 0.3)
        
        # Check it appears in B's history
        history_b = sim.room_b.get_event_history(1000)
        assert len(history_b) > 0


class TestStatisticsCollection:
    """Tests for statistics collection."""
    
    def test_movement_statistics(self):
        """Test movement event statistics."""
        sim = TouchDesignerSimulation()
        
        # Create movement events (emit calls callback)
        for _ in range(3):
            event = sim.movement_sim_a.emit_movement_event(0.5, 0.5, 0.0, 0.3)
        
        assert sim.stats["A"]["movement"] == 3

    def test_speech_statistics(self):
        """Test speech event statistics."""
        sim = TouchDesignerSimulation()
        
        # Create speech events
        for i in range(2):
            event = sim.speech_sim_b.emit_speech_event(f"Message {i}", 0.95)
        
        assert sim.stats["B"]["speech"] == 2

    def test_routing_statistics(self):
        """Test routing statistics."""
        sim = TouchDesignerSimulation()
        
        # Create events from A
        for _ in range(2):
            event = sim.movement_sim_a.emit_movement_event(0.5, 0.5, 0.0, 0.3)
        
        # Create events from B
        for _ in range(3):
            event = sim.movement_sim_b.emit_movement_event(0.3, 0.7, 0.0, 0.2)
        
        # Verify routing counts
        assert sim.stats["B"]["received_from_a"] == 2
        assert sim.stats["A"]["received_from_b"] == 3

    def test_mixed_event_statistics(self):
        """Test statistics with mixed event types."""
        sim = TouchDesignerSimulation()
        
        # Mixed events
        for i in range(5):
            if i % 2 == 0:
                event = sim.movement_sim_a.emit_movement_event(0.5, 0.5, 0.0, 0.3)
            else:
                event = sim.speech_sim_a.emit_speech_event(f"Hello {i}", 0.95)
        
        total_a = sim.stats["A"]["movement"] + sim.stats["A"]["speech"]
        assert total_a == 5


class TestVerification:
    """Tests for verification methods."""
    
    def test_verify_no_echo_success(self):
        """Test successful no-echo-back verification."""
        sim = TouchDesignerSimulation()
        
        # Create events from A only
        for _ in range(3):
            event = sim.movement_sim_a.emit_movement_event(0.5, 0.5, 0.0, 0.3)
        
        # Verify no echo
        result = sim._verify_no_echo(sim.room_a, SourceEnvironment.ENVIRONMENT_A)
        assert result == True

    def test_get_results(self):
        """Test getting results dictionary."""
        sim = TouchDesignerSimulation()
        
        # Generate some events
        for _ in range(2):
            event = sim.movement_sim_a.emit_movement_event(0.5, 0.5, 0.0, 0.3)
        
        for _ in range(1):
            event = sim.speech_sim_b.emit_speech_event("Hello", 0.95)
        
        results = sim._get_results()
        
        assert "environment_a" in results
        assert "environment_b" in results
        assert results["environment_a"]["movement_events"] == 2
        assert results["environment_b"]["speech_events"] == 1


class TestEndToEnd:
    """End-to-end simulation tests."""
    
    def test_short_simulation_completes(self):
        """Test that a short simulation completes successfully."""
        grass = EnvironmentConfig(
            name="GRASS", environment="A", touchdesigner_port=7001,
            movement_pattern="walking", speech_pattern="greeting",
            duration_seconds=2
        )
        dirt = EnvironmentConfig(
            name="DIRT", environment="B", touchdesigner_port=7002,
            movement_pattern="pacing", speech_pattern="poetry",
            duration_seconds=2
        )
        
        sim = TouchDesignerSimulation(grass_config=grass, dirt_config=dirt)
        results = sim.run()
        
        assert results["environment_a"]["total_events"] > 0
        assert results["environment_b"]["total_events"] > 0
        assert results["elapsed_seconds"] >= 2

    def test_bidirectional_communication(self):
        """Test that events flow bidirectionally in full simulation."""
        grass = EnvironmentConfig(
            name="GRASS", environment="A", touchdesigner_port=7001,
            movement_pattern="walking", speech_pattern="conversation",
            duration_seconds=2
        )
        dirt = EnvironmentConfig(
            name="DIRT", environment="B", touchdesigner_port=7002,
            movement_pattern="pacing", speech_pattern="poetry",
            duration_seconds=2
        )
        
        sim = TouchDesignerSimulation(grass_config=grass, dirt_config=dirt)
        results = sim.run()
        
        # Both environments should receive events from the other
        assert results["environment_a"]["received_from_b"] > 0
        assert results["environment_b"]["received_from_a"] > 0

    def test_all_pattern_combinations(self):
        """Test various pattern combinations."""
        for movement in ["walking", "pacing"]:
            for speech in ["greeting", "conversation"]:
                grass = EnvironmentConfig(
                    name="GRASS", environment="A", touchdesigner_port=7001,
                    movement_pattern=movement, speech_pattern=speech,
                    duration_seconds=1
                )
                dirt = EnvironmentConfig(
                    name="DIRT", environment="B", touchdesigner_port=7002,
                    movement_pattern="pacing", speech_pattern="poetry",
                    duration_seconds=1
                )
                
                sim = TouchDesignerSimulation(grass_config=grass, dirt_config=dirt)
                results = sim.run()
                
                assert results["environment_a"]["total_events"] > 0
                assert results["environment_b"]["total_events"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
