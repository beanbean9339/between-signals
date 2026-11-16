"""
Test suite for simulation.py

Tests for MovementSimulator, SpeechSimulator, and SimulationRunner.
"""

import pytest
import time
import threading
from events import MovementEvent, SpeechEvent
from simulation import (
    MovementSimulator, SpeechSimulator, SimulationRunner,
    MovementPattern, SpeechPattern
)


class TestMovementPattern:
    """Test MovementPattern dataclass."""
    
    def test_create_movement_pattern(self):
        """Test creating a movement pattern."""
        pattern = MovementPattern(
            delay_seconds=1.0,
            x=0.5,
            y=0.3,
            z=0.0,
            velocity=0.5,
            description="Test movement"
        )
        
        assert pattern.delay_seconds == 1.0
        assert pattern.x == 0.5
        assert pattern.y == 0.3
        assert pattern.z == 0.0
        assert pattern.velocity == 0.5
        assert pattern.description == "Test movement"
    
    def test_movement_pattern_defaults(self):
        """Test MovementPattern with minimal fields."""
        pattern = MovementPattern(
            delay_seconds=0.5,
            x=0.1,
            y=0.2,
            z=0.0,
            velocity=0.3
        )
        
        assert pattern.description == ""


class TestSpeechPattern:
    """Test SpeechPattern dataclass."""
    
    def test_create_speech_pattern(self):
        """Test creating a speech pattern."""
        pattern = SpeechPattern(
            delay_seconds=2.0,
            text="Hello world",
            confidence=0.95,
            language="en",
            description="Greeting"
        )
        
        assert pattern.delay_seconds == 2.0
        assert pattern.text == "Hello world"
        assert pattern.confidence == 0.95
        assert pattern.language == "en"
        assert pattern.description == "Greeting"
    
    def test_speech_pattern_defaults(self):
        """Test SpeechPattern with defaults."""
        pattern = SpeechPattern(
            delay_seconds=1.0,
            text="Hello"
        )
        
        assert pattern.confidence == 1.0
        assert pattern.language == "en"
        assert pattern.description == ""


class TestMovementSimulator:
    """Test MovementSimulator class."""
    
    def test_movement_simulator_creation(self):
        """Test creating a movement simulator."""
        sim = MovementSimulator(room_id="A")
        
        assert sim.room_id == "A"
        assert sim.event_callback is None
        assert sim.is_running is False
        assert sim.thread is None
    
    def test_movement_simulator_with_callback(self):
        """Test movement simulator with event callback."""
        events = []
        def capture(event):
            events.append(event)
        
        sim = MovementSimulator(room_id="B", event_callback=capture)
        assert sim.event_callback is capture
    
    def test_emit_movement_event(self):
        """Test emitting a movement event."""
        events = []
        def capture(event):
            events.append(event)
        
        sim = MovementSimulator(room_id="A", event_callback=capture)
        event = sim.emit_movement_event(x=0.5, y=0.3, z=0.0, velocity=0.4)
        
        assert isinstance(event, MovementEvent)
        assert event.data["position"]["x"] == 0.5
        assert event.data["position"]["y"] == 0.3
        assert event.data["velocity"] == 0.4
        assert len(events) == 1
        assert events[0] == event
    
    def test_emit_movement_without_callback(self):
        """Test emitting event without callback doesn't crash."""
        sim = MovementSimulator(room_id="A")
        event = sim.emit_movement_event(x=0.1, y=0.2, z=0.0, velocity=0.3)
        
        assert isinstance(event, MovementEvent)
    
    def test_generate_walking_pattern(self):
        """Test generating walking pattern."""
        sim = MovementSimulator(room_id="A")
        pattern = sim.generate_pattern("walking")
        
        assert len(pattern) == 6
        assert all(isinstance(p, MovementPattern) for p in pattern)
        assert pattern[0].delay_seconds == 0.0
        assert pattern[-1].delay_seconds == 2.5
    
    def test_generate_pacing_pattern(self):
        """Test generating pacing pattern."""
        sim = MovementSimulator(room_id="A")
        pattern = sim.generate_pattern("pacing")
        
        assert len(pattern) == 7
        assert all(isinstance(p, MovementPattern) for p in pattern)
    
    def test_generate_standing_pattern(self):
        """Test generating standing pattern."""
        sim = MovementSimulator(room_id="A")
        pattern = sim.generate_pattern("standing")
        
        assert len(pattern) == 3
        # All positions should be same (stationary)
        for p in pattern:
            assert p.x == 0.5
            assert p.y == 0.5
            assert p.velocity == 0.0
    
    def test_generate_slow_walk_pattern(self):
        """Test generating slow walk pattern."""
        sim = MovementSimulator(room_id="A")
        pattern = sim.generate_pattern("slow_walk")
        
        assert len(pattern) == 5
        # Velocities should be small
        for p in pattern:
            assert p.velocity <= 0.1
    
    def test_generate_random_pattern(self):
        """Test generating random pattern."""
        sim = MovementSimulator(room_id="A")
        pattern = sim.generate_pattern("random")
        
        assert len(pattern) > 0
        assert all(isinstance(p, MovementPattern) for p in pattern)
        # Random pattern should have varying positions
        positions = [(p.x, p.y) for p in pattern]
        assert len(set(positions)) > 1  # Not all same
    
    def test_run_pattern_completes(self):
        """Test running a pattern completes."""
        events = []
        sim = MovementSimulator(room_id="A", event_callback=lambda e: events.append(e))
        
        pattern = [
            MovementPattern(0.0, 0.1, 0.1, 0.0, 0.1),
            MovementPattern(0.1, 0.2, 0.2, 0.0, 0.2),
        ]
        
        start = time.time()
        sim.run_pattern(pattern, loop=False)
        elapsed = time.time() - start
        
        # Should take at least 0.1 seconds (delay between events)
        assert elapsed >= 0.08
        assert len(events) == 2
        assert sim.is_running is False
    
    def test_run_pattern_async(self):
        """Test running pattern asynchronously."""
        events = []
        sim = MovementSimulator(room_id="A", event_callback=lambda e: events.append(e))
        
        pattern = [
            MovementPattern(0.0, 0.1, 0.1, 0.0, 0.1),
            MovementPattern(0.05, 0.2, 0.2, 0.0, 0.2),
        ]
        
        sim.run_pattern_async(pattern, loop=False)
        time.sleep(0.3)  # Let it run
        sim.stop()
        
        assert len(events) >= 2
    
    def test_stop_simulator(self):
        """Test stopping a simulator."""
        sim = MovementSimulator(room_id="A")
        
        pattern = [
            MovementPattern(0.0, 0.1, 0.1, 0.0, 0.1),
            MovementPattern(1.0, 0.2, 0.2, 0.0, 0.2),  # 1 second later
        ]
        
        sim.run_pattern_async(pattern, loop=True)
        time.sleep(0.2)
        sim.stop()
        
        # Should stop before the second event
        time.sleep(1.0)
        assert sim.is_running is False


class TestSpeechSimulator:
    """Test SpeechSimulator class."""
    
    def test_speech_simulator_creation(self):
        """Test creating a speech simulator."""
        sim = SpeechSimulator(room_id="A")
        
        assert sim.room_id == "A"
        assert sim.event_callback is None
        assert sim.is_running is False
        assert sim.thread is None
    
    def test_emit_speech_event(self):
        """Test emitting a speech event."""
        events = []
        def capture(event):
            events.append(event)
        
        sim = SpeechSimulator(room_id="B", event_callback=capture)
        event = sim.emit_speech_event(text="Hello world", confidence=0.95)
        
        assert isinstance(event, SpeechEvent)
        assert event.data["text"] == "Hello world"
        assert event.data["confidence"] == 0.95
        assert len(events) == 1
    
    def test_emit_speech_without_callback(self):
        """Test emitting speech without callback."""
        sim = SpeechSimulator(room_id="A")
        event = sim.emit_speech_event(text="Test")
        
        assert isinstance(event, SpeechEvent)
    
    def test_generate_greeting_pattern(self):
        """Test generating greeting pattern."""
        sim = SpeechSimulator(room_id="A")
        pattern = sim.generate_pattern("greeting")
        
        assert len(pattern) == 3
        assert all(isinstance(p, SpeechPattern) for p in pattern)
        assert pattern[0].text == "Hello"
        assert pattern[1].text == "How are you?"
        assert pattern[2].text == "I am well"
    
    def test_generate_conversation_pattern(self):
        """Test generating conversation pattern."""
        sim = SpeechSimulator(room_id="A")
        pattern = sim.generate_pattern("conversation")
        
        assert len(pattern) == 4
        assert all(isinstance(p, SpeechPattern) for p in pattern)
        assert "Welcome" in pattern[0].text
    
    def test_generate_questions_pattern(self):
        """Test generating questions pattern."""
        sim = SpeechSimulator(room_id="A")
        pattern = sim.generate_pattern("questions")
        
        assert len(pattern) == 4
        # All should end with question mark
        for p in pattern:
            assert "?" in p.text
    
    def test_generate_poetry_pattern(self):
        """Test generating poetry pattern."""
        sim = SpeechSimulator(room_id="A")
        pattern = sim.generate_pattern("poetry")
        
        assert len(pattern) == 4
    
    def test_generate_random_speech(self):
        """Test generating random speech pattern."""
        sim = SpeechSimulator(room_id="A")
        pattern = sim.generate_pattern("random")
        
        assert len(pattern) > 0
        assert all(isinstance(p, SpeechPattern) for p in pattern)
    
    def test_run_speech_pattern(self):
        """Test running a speech pattern."""
        events = []
        sim = SpeechSimulator(room_id="A", event_callback=lambda e: events.append(e))
        
        pattern = [
            SpeechPattern(0.0, "Hello"),
            SpeechPattern(0.1, "World"),
        ]
        
        start = time.time()
        sim.run_pattern(pattern, loop=False)
        elapsed = time.time() - start
        
        assert elapsed >= 0.08
        assert len(events) == 2
        assert sim.is_running is False
    
    def test_run_speech_pattern_async(self):
        """Test running speech pattern asynchronously."""
        events = []
        sim = SpeechSimulator(room_id="A", event_callback=lambda e: events.append(e))
        
        pattern = [
            SpeechPattern(0.0, "First"),
            SpeechPattern(0.05, "Second"),
        ]
        
        sim.run_pattern_async(pattern, loop=False)
        time.sleep(0.2)
        sim.stop()
        
        assert len(events) >= 2
    
    def test_stop_speech_simulator(self):
        """Test stopping speech simulator."""
        sim = SpeechSimulator(room_id="A")
        
        pattern = [
            SpeechPattern(0.0, "Hello"),
            SpeechPattern(1.0, "Later"),
        ]
        
        sim.run_pattern_async(pattern, loop=True)
        time.sleep(0.2)
        sim.stop()
        
        time.sleep(1.0)
        assert sim.is_running is False


class TestSimulationRunner:
    """Test SimulationRunner orchestrator."""
    
    def test_simulation_runner_creation(self):
        """Test creating a simulation runner."""
        runner = SimulationRunner(room_id="A")
        
        assert runner.room_id == "A"
        assert runner.event_callback is None
        assert runner.is_running is False
        assert isinstance(runner.movement_simulator, MovementSimulator)
        assert isinstance(runner.speech_simulator, SpeechSimulator)
    
    def test_simulation_runner_with_callback(self):
        """Test runner with event callback."""
        events = []
        runner = SimulationRunner(room_id="B", event_callback=lambda e: events.append(e))
        
        # Manually emit events to test callback
        runner.movement_simulator.emit_movement_event(0.5, 0.5, 0.0, 0.3)
        runner.speech_simulator.emit_speech_event("Hello")
        
        assert len(events) == 2
    
    def test_run_simulation_basic(self):
        """Test running a basic simulation."""
        events = []
        runner = SimulationRunner(room_id="A", event_callback=lambda e: events.append(e))
        
        runner.run_simulation(
            duration_seconds=0.5,
            movement_pattern="standing",
            speech_pattern="greeting",
            include_movement=True,
            include_speech=True
        )
        
        assert runner.is_running is False
        assert len(events) > 0
    
    def test_run_simulation_movement_only(self):
        """Test simulation with movement only."""
        events = []
        runner = SimulationRunner(room_id="A", event_callback=lambda e: events.append(e))
        
        runner.run_simulation(
            duration_seconds=0.5,
            include_movement=True,
            include_speech=False
        )
        
        # Should have movement events only
        movement_events = [e for e in events if isinstance(e, MovementEvent)]
        speech_events = [e for e in events if isinstance(e, SpeechEvent)]
        
        assert len(movement_events) > 0
        assert len(speech_events) == 0
    
    def test_run_simulation_speech_only(self):
        """Test simulation with speech only."""
        events = []
        runner = SimulationRunner(room_id="A", event_callback=lambda e: events.append(e))
        
        runner.run_simulation(
            duration_seconds=0.5,
            include_movement=False,
            include_speech=True
        )
        
        # Should have speech events only
        movement_events = [e for e in events if isinstance(e, MovementEvent)]
        speech_events = [e for e in events if isinstance(e, SpeechEvent)]
        
        assert len(movement_events) == 0
        assert len(speech_events) > 0
    
    def test_run_simulation_neither(self):
        """Test simulation with neither movement nor speech."""
        events = []
        runner = SimulationRunner(room_id="A", event_callback=lambda e: events.append(e))
        
        runner.run_simulation(
            duration_seconds=0.2,
            include_movement=False,
            include_speech=False
        )
        
        # Should have no events
        assert len(events) == 0
    
    def test_simulation_statistics(self):
        """Test getting simulation statistics."""
        runner = SimulationRunner(room_id="B")
        
        stats = runner.get_statistics()
        
        assert stats["room_id"] == "B"
        assert stats["is_running"] is False
        assert "elapsed_seconds" in stats
        assert "movement_running" in stats
        assert "speech_running" in stats
    
    def test_stop_all_simulators(self):
        """Test stopping all simulators."""
        runner = SimulationRunner(room_id="A")
        
        # Manually start simulators
        pattern = runner.movement_simulator.generate_pattern("walking")
        runner.movement_simulator.run_pattern_async(pattern, loop=True)
        
        time.sleep(0.1)
        runner.stop_all()
        
        assert runner.movement_simulator.is_running is False
        assert runner.is_running is False
    
    def test_simulation_different_patterns(self):
        """Test simulation with different pattern combinations."""
        for movement in ["walking", "pacing", "standing", "slow_walk"]:
            for speech in ["greeting", "conversation", "questions", "poetry"]:
                runner = SimulationRunner(room_id="A")
                runner.run_simulation(
                    duration_seconds=0.3,
                    movement_pattern=movement,
                    speech_pattern=speech,
                    include_movement=True,
                    include_speech=True
                )
                # Just verify it doesn't crash
                assert runner.is_running is False


class TestEndToEnd:
    """End-to-end simulation tests."""
    
    def test_full_simulation_room_a(self):
        """Test full simulation for Room A."""
        events = []
        runner = SimulationRunner(room_id="A", event_callback=lambda e: events.append(e))
        
        runner.run_simulation(
            duration_seconds=1.0,
            movement_pattern="walking",
            speech_pattern="conversation",
            include_movement=True,
            include_speech=True
        )
        
        # Should have both types of events
        movement_events = [e for e in events if isinstance(e, MovementEvent)]
        speech_events = [e for e in events if isinstance(e, SpeechEvent)]
        
        assert len(movement_events) > 0, "Should have movement events"
        assert len(speech_events) > 0, "Should have speech events"
        
        # All events should be from room A
        for event in events:
            assert event.source == "A", f"Event should be from room A, got {event.source}"
    
    def test_full_simulation_room_b(self):
        """Test full simulation for Room B."""
        events = []
        runner = SimulationRunner(room_id="B", event_callback=lambda e: events.append(e))
        
        runner.run_simulation(
            duration_seconds=1.0,
            movement_pattern="pacing",
            speech_pattern="poetry",
            include_movement=True,
            include_speech=True
        )
        
        # All events should be from room B
        for event in events:
            assert event.source == "B", f"Event should be from room B, got {event.source}"
    
    def test_simulation_event_timing(self):
        """Test that events have correct timing."""
        events = []
        runner = SimulationRunner(room_id="A", event_callback=lambda e: events.append(e))
        
        start = time.time()
        runner.run_simulation(
            duration_seconds=1.5,
            movement_pattern="standing",
            speech_pattern="greeting",
            include_movement=True,
            include_speech=True
        )
        elapsed = time.time() - start
        
        # Should run for approximately the requested duration (allow +/-0.5s margin)
        assert 1.0 <= elapsed <= 2.5, f"Expected ~1.5s, got {elapsed}s"
    
    def test_simulation_with_callback_errors(self):
        """Test that callback errors don't crash simulation."""
        def failing_callback(event):
            raise ValueError("Test error in callback")
        
        runner = SimulationRunner(room_id="A", event_callback=failing_callback)
        
        # Should not crash despite callback errors
        runner.run_simulation(
            duration_seconds=0.3,
            include_movement=True,
            include_speech=False
        )
        
        assert runner.is_running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
