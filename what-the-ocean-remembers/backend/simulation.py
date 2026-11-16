"""
Phase 3: Simulation mode for Between Signals

Provides event simulators for testing without real hardware:
- MovementSimulator: Generates random movement patterns
- SpeechSimulator: Emits pre-recorded speech transcripts
- SimulationRunner: Orchestrates both for end-to-end testing

Usage:
    from simulation import SimulationRunner
    runner = SimulationRunner(room_id="A")
    runner.run_simulation(duration_seconds=60)
"""

import logging
import threading
import time
import random
from dataclasses import dataclass
from typing import Callable, Optional, List
from datetime import datetime

from events import MovementEvent, SpeechEvent, PresenceEvent, SourceEnvironment


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@dataclass
class MovementPattern:
    """Single movement event in a simulation."""
    delay_seconds: float
    x: float
    y: float
    z: float
    velocity: float
    description: str = ""


@dataclass
class SpeechPattern:
    """Single speech event in a simulation."""
    delay_seconds: float
    text: str
    confidence: float = 1.0
    language: str = "en"
    description: str = ""


class MovementSimulator:
    """
    Generates realistic movement patterns.
    
    Simulates a visitor walking through the space with varying speeds
    and directions. Emits MovementEvent objects via callback.
    """
    
    def __init__(self, room_id: str, event_callback: Optional[Callable] = None):
        """
        Initialize movement simulator.
        
        Args:
            room_id: "A" or "B"
            event_callback: Function to call when movement occurs
                           Signature: callback(event: MovementEvent)
        """
        self.room_id = room_id
        self.event_callback = event_callback
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        logger.info(f"MovementSimulator initialized for room {room_id}")
    
    def emit_movement_event(self, x: float, y: float, z: float, velocity: float) -> MovementEvent:
        """Create and emit a movement event."""
        event = MovementEvent.create(
            source=self.room_id,
            present=True,
            position_x=x,
            position_y=y,
            velocity=velocity,
            direction="forward",
            intensity=velocity
        )
        
        if self.event_callback:
            try:
                self.event_callback(event)
                logger.debug(f"Emitted movement event: {event.event_id} at ({x}, {y}, {z})")
            except Exception as e:
                logger.error(f"Error in movement event callback: {e}")
        
        return event
    
    def generate_pattern(self, pattern_name: str = "walking") -> List[MovementPattern]:
        """
        Generate a predefined movement pattern.
        
        Args:
            pattern_name: "walking", "pacing", "standing", "slow_walk"
        
        Returns:
            List of MovementPattern objects with timing and coordinates
        """
        if pattern_name == "walking":
            # Visitor walks across space
            return [
                MovementPattern(0.0, 0.0, 0.0, 0.0, 0.0, "Start: stationary"),
                MovementPattern(0.5, 0.2, 0.1, 0.0, 0.5, "Walking right"),
                MovementPattern(1.0, 0.4, 0.2, 0.0, 0.6, "Continuing"),
                MovementPattern(1.5, 0.6, 0.3, 0.0, 0.5, "Moving"),
                MovementPattern(2.0, 0.8, 0.4, 0.0, 0.4, "Slowing down"),
                MovementPattern(2.5, 0.9, 0.5, 0.0, 0.0, "Stop: stationary"),
            ]
        
        elif pattern_name == "pacing":
            # Visitor paces back and forth
            return [
                MovementPattern(0.0, 0.5, 0.5, 0.0, 0.0, "Start: stationary"),
                MovementPattern(0.4, 0.6, 0.5, 0.0, 0.3, "Walking"),
                MovementPattern(0.8, 0.7, 0.5, 0.0, 0.3, "Continuing"),
                MovementPattern(1.2, 0.6, 0.5, 0.0, 0.3, "Turning back"),
                MovementPattern(1.6, 0.5, 0.5, 0.0, 0.3, "Pacing"),
                MovementPattern(2.0, 0.4, 0.5, 0.0, 0.3, "Reversing"),
                MovementPattern(2.4, 0.5, 0.5, 0.0, 0.0, "Stop"),
            ]
        
        elif pattern_name == "standing":
            # Visitor stands still with minor adjustments
            return [
                MovementPattern(0.0, 0.5, 0.5, 0.0, 0.0, "Standing"),
                MovementPattern(1.0, 0.5, 0.5, 0.0, 0.0, "Stationary"),
                MovementPattern(2.0, 0.5, 0.5, 0.0, 0.0, "Still standing"),
            ]
        
        elif pattern_name == "slow_walk":
            # Visitor walks slowly through space
            return [
                MovementPattern(0.0, 0.0, 0.0, 0.0, 0.0, "Start"),
                MovementPattern(1.0, 0.1, 0.05, 0.0, 0.1, "Slow walk"),
                MovementPattern(2.0, 0.2, 0.1, 0.0, 0.1, "Continuing slowly"),
                MovementPattern(3.0, 0.3, 0.15, 0.0, 0.1, "Still moving"),
                MovementPattern(4.0, 0.4, 0.2, 0.0, 0.0, "Stop"),
            ]
        
        else:
            # Random pattern
            return self._generate_random_pattern()
    
    def _generate_random_pattern(self, num_events: int = 5) -> List[MovementPattern]:
        """Generate a random movement pattern."""
        patterns = []
        current_x, current_y = 0.5, 0.5
        
        for i in range(num_events):
            delay = i * 0.5
            # Random walk (small step)
            current_x += random.uniform(-0.15, 0.15)
            current_y += random.uniform(-0.15, 0.15)
            # Clamp to [0, 1]
            current_x = max(0.0, min(1.0, current_x))
            current_y = max(0.0, min(1.0, current_y))
            velocity = random.uniform(0.1, 0.5)
            
            patterns.append(MovementPattern(
                delay_seconds=delay,
                x=current_x,
                y=current_y,
                z=0.0,
                velocity=velocity,
                description=f"Random step {i+1}"
            ))
        
        return patterns
    
    def run_pattern(self, pattern: List[MovementPattern], loop: bool = False):
        """
        Execute a movement pattern sequentially.
        
        Args:
            pattern: List of MovementPattern objects
            loop: Repeat pattern indefinitely
        """
        self.is_running = True
        
        try:
            iteration = 0
            while self.is_running:
                iteration += 1
                logger.info(f"MovementSimulator: Starting pattern iteration {iteration}")
                
                start_time = time.time()
                for event_pattern in pattern:
                    if not self.is_running:
                        break
                    
                    # Wait until it's time for this event
                    elapsed = time.time() - start_time
                    wait_time = event_pattern.delay_seconds - elapsed
                    if wait_time > 0:
                        time.sleep(wait_time)
                    
                    # Emit the event
                    self.emit_movement_event(
                        x=event_pattern.x,
                        y=event_pattern.y,
                        z=event_pattern.z,
                        velocity=event_pattern.velocity
                    )
                    
                    logger.info(f"Movement: {event_pattern.description}")
                
                if not loop:
                    break
                
                logger.info("Pattern loop completed, restarting...")
        
        except Exception as e:
            logger.error(f"Error in movement pattern execution: {e}", exc_info=True)
        finally:
            self.is_running = False
            logger.info("MovementSimulator stopped")
    
    def run_pattern_async(self, pattern: List[MovementPattern], loop: bool = False):
        """
        Execute pattern in background thread.
        
        Args:
            pattern: List of MovementPattern objects
            loop: Repeat pattern indefinitely
        """
        if self.thread and self.thread.is_alive():
            logger.warning("Pattern already running")
            return
        
        self.thread = threading.Thread(
            target=self.run_pattern,
            args=(pattern, loop),
            daemon=False
        )
        self.thread.start()
        logger.info("Movement pattern started in background thread")
    
    def stop(self):
        """Stop the simulator."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            logger.info("MovementSimulator stopped")


class SpeechSimulator:
    """
    Generates predefined speech patterns.
    
    Emits SpeechEvent objects with realistic transcripts at specified times.
    Useful for testing without a microphone.
    """
    
    def __init__(self, room_id: str, event_callback: Optional[Callable] = None):
        """
        Initialize speech simulator.
        
        Args:
            room_id: "A" or "B"
            event_callback: Function to call when speech occurs
                           Signature: callback(event: SpeechEvent)
        """
        self.room_id = room_id
        self.event_callback = event_callback
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        logger.info(f"SpeechSimulator initialized for room {room_id}")
    
    def emit_speech_event(self, text: str, confidence: float = 1.0,
                         language: str = "en") -> SpeechEvent:
        """Create and emit a speech event."""
        event = SpeechEvent.create(
            source=self.room_id,
            text=text,
            confidence=confidence,
            language=language
        )
        
        if self.event_callback:
            try:
                self.event_callback(event)
                logger.debug(f"Emitted speech event: {event.event_id}")
            except Exception as e:
                logger.error(f"Error in speech event callback: {e}")
        
        return event
    
    def generate_pattern(self, pattern_name: str = "greeting") -> List[SpeechPattern]:
        """
        Generate a predefined speech pattern.
        
        Args:
            pattern_name: "greeting", "conversation", "questions", "poetry"
        
        Returns:
            List of SpeechPattern objects with timing and text
        """
        if pattern_name == "greeting":
            # Simple greeting exchange
            return [
                SpeechPattern(0.0, "Hello", 0.95, "en", "Greeting"),
                SpeechPattern(2.0, "How are you?", 0.92, "en", "Question"),
                SpeechPattern(4.0, "I am well", 0.88, "en", "Response"),
            ]
        
        elif pattern_name == "conversation":
            # Longer conversation
            return [
                SpeechPattern(0.0, "Welcome to this space", 0.95, "en", "Welcome"),
                SpeechPattern(3.0, "Take your time to explore", 0.90, "en", "Guidance"),
                SpeechPattern(6.0, "Notice the sounds around you", 0.92, "en", "Instruction"),
                SpeechPattern(9.0, "What do you hear from the other room?", 0.88, "en", "Question"),
            ]
        
        elif pattern_name == "questions":
            # Series of questions
            return [
                SpeechPattern(1.0, "Can you hear me?", 0.90, "en", "Question 1"),
                SpeechPattern(3.5, "What do you see?", 0.92, "en", "Question 2"),
                SpeechPattern(6.0, "Do you feel connected?", 0.88, "en", "Question 3"),
                SpeechPattern(8.5, "What would you like to say?", 0.85, "en", "Question 4"),
            ]
        
        elif pattern_name == "poetry":
            # Poetic text (installation concept)
            return [
                SpeechPattern(1.0, "Between signals we drift", 0.92, "en", "Line 1"),
                SpeechPattern(4.0, "Two spaces connected by voice", 0.90, "en", "Line 2"),
                SpeechPattern(7.0, "Echoes return transformed", 0.88, "en", "Line 3"),
                SpeechPattern(10.0, "What reaches across the ocean", 0.85, "en", "Line 4"),
            ]
        
        else:
            # Random speech pattern
            return self._generate_random_pattern()
    
    def _generate_random_pattern(self, num_events: int = 3) -> List[SpeechPattern]:
        """Generate random speech events."""
        samples = [
            "Hello from this environment",
            "I am here with you",
            "Can you hear me across the distance?",
            "The space is vast",
            "Listen carefully",
            "What do you feel?",
            "Time flows differently here",
            "We are connected",
        ]
        
        patterns = []
        for i in range(num_events):
            delay = i * 2.5  # 2.5 seconds between utterances
            text = random.choice(samples)
            confidence = random.uniform(0.80, 0.95)
            
            patterns.append(SpeechPattern(
                delay_seconds=delay,
                text=text,
                confidence=confidence,
                language="en",
                description=f"Speech event {i+1}"
            ))
        
        return patterns
    
    def run_pattern(self, pattern: List[SpeechPattern], loop: bool = False):
        """
        Execute a speech pattern sequentially.
        
        Args:
            pattern: List of SpeechPattern objects
            loop: Repeat pattern indefinitely
        """
        self.is_running = True
        
        try:
            iteration = 0
            while self.is_running:
                iteration += 1
                logger.info(f"SpeechSimulator: Starting pattern iteration {iteration}")
                
                start_time = time.time()
                for event_pattern in pattern:
                    if not self.is_running:
                        break
                    
                    # Wait until it's time for this event
                    elapsed = time.time() - start_time
                    wait_time = event_pattern.delay_seconds - elapsed
                    if wait_time > 0:
                        time.sleep(wait_time)
                    
                    # Emit the event
                    self.emit_speech_event(
                        text=event_pattern.text,
                        confidence=event_pattern.confidence,
                        language=event_pattern.language
                    )
                    
                    logger.info(f"Speech: {event_pattern.description} - \"{event_pattern.text}\"")
                
                if not loop:
                    break
                
                logger.info("Speech pattern loop completed, restarting...")
        
        except Exception as e:
            logger.error(f"Error in speech pattern execution: {e}", exc_info=True)
        finally:
            self.is_running = False
            logger.info("SpeechSimulator stopped")
    
    def run_pattern_async(self, pattern: List[SpeechPattern], loop: bool = False):
        """
        Execute pattern in background thread.
        
        Args:
            pattern: List of SpeechPattern objects
            loop: Repeat pattern indefinitely
        """
        if self.thread and self.thread.is_alive():
            logger.warning("Pattern already running")
            return
        
        self.thread = threading.Thread(
            target=self.run_pattern,
            args=(pattern, loop),
            daemon=False
        )
        self.thread.start()
        logger.info("Speech pattern started in background thread")
    
    def stop(self):
        """Stop the simulator."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            logger.info("SpeechSimulator stopped")


class SimulationRunner:
    """
    Orchestrates movement and speech simulators for end-to-end testing.
    
    Runs both simulators in background, optionally generating both movement
    and speech events, with configurable patterns and timing.
    """
    
    def __init__(self, room_id: str, event_callback: Optional[Callable] = None):
        """
        Initialize simulation runner.
        
        Args:
            room_id: "A" or "B"
            event_callback: Function to call when any event occurs
                           Signature: callback(event: Event)
        """
        self.room_id = room_id
        self.event_callback = event_callback
        self.movement_simulator = MovementSimulator(room_id, event_callback)
        self.speech_simulator = SpeechSimulator(room_id, event_callback)
        self.is_running = False
        self.start_time: Optional[float] = None
        logger.info(f"SimulationRunner initialized for room {room_id}")
    
    def run_simulation(self,
                      duration_seconds: float = 30.0,
                      movement_pattern: str = "walking",
                      speech_pattern: str = "conversation",
                      include_movement: bool = True,
                      include_speech: bool = True):
        """
        Run a complete simulation for specified duration.
        
        Args:
            duration_seconds: How long to run simulation
            movement_pattern: Name of movement pattern to use
            speech_pattern: Name of speech pattern to use
            include_movement: Enable movement events
            include_speech: Enable speech events
        """
        self.is_running = True
        self.start_time = time.time()
        
        try:
            logger.info(f"Starting {duration_seconds}s simulation for room {self.room_id}")
            logger.info(f"Movement: {include_movement} ({movement_pattern})")
            logger.info(f"Speech: {include_speech} ({speech_pattern})")
            
            # Start simulators in background
            if include_movement:
                movement_patt = self.movement_simulator.generate_pattern(movement_pattern)
                self.movement_simulator.run_pattern_async(movement_patt, loop=True)
            
            if include_speech:
                speech_patt = self.speech_simulator.generate_pattern(speech_pattern)
                self.speech_simulator.run_pattern_async(speech_patt, loop=True)
            
            # Wait for duration
            elapsed = 0
            while self.is_running and elapsed < duration_seconds:
                remaining = duration_seconds - elapsed
                sleep_time = min(1.0, remaining)
                time.sleep(sleep_time)
                elapsed = time.time() - self.start_time
                
                # Log progress every 5 seconds
                if int(elapsed) % 5 == 0 and elapsed >= 0:
                    logger.info(f"Simulation progress: {elapsed:.1f}s / {duration_seconds}s")
            
            logger.info(f"Simulation completed after {elapsed:.1f}s")
        
        except Exception as e:
            logger.error(f"Error during simulation: {e}", exc_info=True)
        finally:
            self.is_running = False
            self.stop_all()
    
    def stop_all(self):
        """Stop all simulators."""
        logger.info("Stopping all simulators")
        self.movement_simulator.stop()
        self.speech_simulator.stop()
        self.is_running = False
    
    def get_statistics(self) -> dict:
        """
        Get simulation statistics.
        
        Returns:
            Dict with event counts, durations, etc.
        """
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            "room_id": self.room_id,
            "is_running": self.is_running,
            "elapsed_seconds": elapsed,
            "movement_running": self.movement_simulator.is_running,
            "speech_running": self.speech_simulator.is_running,
        }


if __name__ == "__main__":
    # Test the simulators
    print("Testing simulation module...")
    
    # Test movement simulator
    print("\n--- Movement Simulator Test ---")
    movement_events = []
    def capture_movement(event):
        movement_events.append(event)
    
    mover = MovementSimulator("A", capture_movement)
    pattern = mover.generate_pattern("walking")
    print(f"Generated {len(pattern)} movement events")
    for p in pattern:
        print(f"  {p.delay_seconds:.1f}s: ({p.x:.2f}, {p.y:.2f}) - {p.description}")
    
    # Test speech simulator
    print("\n--- Speech Simulator Test ---")
    speech_events = []
    def capture_speech(event):
        speech_events.append(event)
    
    speaker = SpeechSimulator("B", capture_speech)
    pattern = speaker.generate_pattern("greeting")
    print(f"Generated {len(pattern)} speech events")
    for p in pattern:
        print(f"  {p.delay_seconds:.1f}s: \"{p.text}\"")
    
    # Test simulation runner
    print("\n--- Simulation Runner Test (5 seconds) ---")
    runner = SimulationRunner("A")
    runner.run_simulation(
        duration_seconds=5.0,
        movement_pattern="slow_walk",
        speech_pattern="questions",
        include_movement=True,
        include_speech=True
    )
    
    stats = runner.get_statistics()
    print(f"\nSimulation complete: {stats}")
    print("All tests completed successfully!")
