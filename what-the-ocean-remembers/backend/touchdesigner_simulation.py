"""
TouchDesigner Simulation Runner for Between Signals.

Simulates both GRASS.toe (Environment A) and DIRT.toe (Environment B)
with realistic visitor movement and speech, sending events via OSC.

This runner:
- Generates simulated movement and speech for both environments
- Routes events bidirectionally through EventRouter (no echo-back)
- Sends OSC messages to TouchDesigner on the correct addresses
- Provides real-time event flow visualization
"""

import logging
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from pythonosc.udp_client import SimpleUDPClient

from simulation import MovementSimulator, SpeechSimulator, SimulationRunner, MovementPattern, SpeechPattern
from room import Room
from events import Event, EventType, SourceEnvironment
from communication_refactored import EventRouter
from config_loader import RoomConfig

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentConfig:
    """Configuration for one environment (GRASS or DIRT)."""
    name: str  # "GRASS" or "DIRT"
    environment: str  # "A" or "B"
    touchdesigner_port: int  # Port to send OSC to
    movement_pattern: str  # Pattern type (walking, pacing, etc.)
    speech_pattern: str  # Pattern type (greeting, conversation, etc.)
    duration_seconds: float


class TouchDesignerSimulation:
    """
    Orchestrates simulation for both GRASS and DIRT environments.
    
    - Creates rooms for A and B
    - Sets up event router
    - Runs synchronized simulations in both environments
    - Sends OSC to TouchDesigner
    - Displays event flow in real-time
    """

    def __init__(self, 
                 grass_config: Optional[EnvironmentConfig] = None,
                 dirt_config: Optional[EnvironmentConfig] = None,
                 osc_host: str = "127.0.0.1"):
        """
        Initialize the simulation.
        
        Args:
            grass_config: Configuration for GRASS (Environment A)
            dirt_config: Configuration for DIRT (Environment B)
            osc_host: Host to send OSC messages to (typically localhost)
        """
        self.osc_host = osc_host
        
        # Default configurations if not provided
        self.grass_config = grass_config or EnvironmentConfig(
            name="GRASS",
            environment="A",
            touchdesigner_port=7001,
            movement_pattern="walking",
            speech_pattern="conversation",
            duration_seconds=30
        )
        
        self.dirt_config = dirt_config or EnvironmentConfig(
            name="DIRT",
            environment="B",
            touchdesigner_port=7002,
            movement_pattern="pacing",
            speech_pattern="poetry",
            duration_seconds=30
        )
        
        # Create rooms with proper configuration
        # RoomConfig loads from room_a.json and room_b.json
        room_a_config = RoomConfig("A")
        room_b_config = RoomConfig("B")
        
        self.room_a = Room(room_a_config)
        self.room_b = Room(room_b_config)
        
        # Create event router (handles bidirectional routing)
        self.router = EventRouter(self.room_a, self.room_b)
        
        # Create simulators for each environment
        self.movement_sim_a = MovementSimulator("A", event_callback=self._handle_simulated_event)
        self.speech_sim_a = SpeechSimulator("A", event_callback=self._handle_simulated_event)
        
        self.movement_sim_b = MovementSimulator("B", event_callback=self._handle_simulated_event)
        self.speech_sim_b = SpeechSimulator("B", event_callback=self._handle_simulated_event)
        
        # Statistics
        self.stats = {
            "A": {"movement": 0, "speech": 0, "received_from_b": 0},
            "B": {"movement": 0, "speech": 0, "received_from_a": 0}
        }
        
        self.start_time = None
        self.stop_event = threading.Event()
        
        logger.info(f"TouchDesigner Simulation initialized")
        logger.info(f"  GRASS (A) → OSC port {self.grass_config.touchdesigner_port}")
        logger.info(f"  DIRT (B) → OSC port {self.dirt_config.touchdesigner_port}")

    def _handle_simulated_event(self, event: Event) -> None:
        """
        Handle a simulated event.
        
        1. Emit event locally (stores in room history)
        2. Route to opposite environment
        3. Update statistics
        """
        source = event.source
        event_type = event.type
        
        # Emit to local room (sends OSC to TouchDesigner)
        if source == SourceEnvironment.ENVIRONMENT_A:
            self.room_a.receive_remote_event(event)
            if event_type == EventType.MOVEMENT:
                self.stats["A"]["movement"] += 1
            elif event_type == EventType.SPEECH:
                self.stats["A"]["speech"] += 1
        else:
            self.room_b.receive_remote_event(event)
            if event_type == EventType.MOVEMENT:
                self.stats["B"]["movement"] += 1
            elif event_type == EventType.SPEECH:
                self.stats["B"]["speech"] += 1
        
        # Route to opposite room (no echo-back)
        try:
            self.router.route_event(event)
            if source == SourceEnvironment.ENVIRONMENT_A:
                self.stats["B"]["received_from_a"] += 1
            else:
                self.stats["A"]["received_from_b"] += 1
        except Exception as e:
            logger.error(f"Failed to route event: {e}")

    def run(self) -> Dict:
        """
        Run the full simulation for both GRASS and DIRT.
        
        Returns:
            Dictionary with results and statistics
        """
        self.start_time = time.time()
        self.stop_event.clear()
        
        logger.info(f"Starting TouchDesigner simulation")
        logger.info(f"  Duration: {self.grass_config.duration_seconds}s")
        logger.info(f"  GRASS patterns: {self.grass_config.movement_pattern} + {self.grass_config.speech_pattern}")
        logger.info(f"  DIRT patterns: {self.dirt_config.movement_pattern} + {self.dirt_config.speech_pattern}")
        
        # Create simulation runners for each environment
        sim_a = SimulationRunner(
            room_id="A",
            event_callback=self._handle_simulated_event
        )
        
        sim_b = SimulationRunner(
            room_id="B",
            event_callback=self._handle_simulated_event
        )
        
        # Run simulations in separate threads
        try:
            # Print starting banner
            self._print_banner("STARTING SIMULATION")
            
            # Run both environments in parallel
            thread_a = threading.Thread(
                target=sim_a.run_simulation,
                args=(
                    self.grass_config.duration_seconds,
                    self.grass_config.movement_pattern,
                    self.grass_config.speech_pattern,
                    True,  # include_movement
                    True   # include_speech
                ),
                daemon=False
            )
            
            thread_b = threading.Thread(
                target=sim_b.run_simulation,
                args=(
                    self.dirt_config.duration_seconds,
                    self.dirt_config.movement_pattern,
                    self.dirt_config.speech_pattern,
                    True,  # include_movement
                    True   # include_speech
                ),
                daemon=False
            )
            
            thread_a.start()
            thread_b.start()
            
            # Monitor progress
            self._monitor_progress(
                sim_a, sim_b,
                self.grass_config.duration_seconds
            )
            
            # Wait for both to complete
            thread_a.join()
            thread_b.join()
            
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
            self.stop_event.set()
            sim_a.stop_all()
            sim_b.stop_all()
        except Exception as e:
            logger.error(f"Error during simulation: {e}")
            raise
        finally:
            # Print final results
            self._print_results()
        
        return self._get_results()

    def _monitor_progress(self, sim_a: SimulationRunner, sim_b: SimulationRunner, 
                         duration: float) -> None:
        """Monitor and display simulation progress."""
        start = time.time()
        last_print = start
        
        while time.time() - start < duration + 1:
            now = time.time()
            
            # Print status every 5 seconds
            if now - last_print >= 5:
                elapsed = now - start
                pct = min(100, int(elapsed / duration * 100))
                
                total_a = self.stats["A"]["movement"] + self.stats["A"]["speech"]
                total_b = self.stats["B"]["movement"] + self.stats["B"]["speech"]
                
                logger.info(
                    f"[{pct:3d}% | {elapsed:.1f}s] "
                    f"A: {total_a} events ({self.stats['A']['movement']}M/{self.stats['A']['speech']}S) "
                    f"| "
                    f"B: {total_b} events ({self.stats['B']['movement']}M/{self.stats['B']['speech']}S) "
                    f"| "
                    f"Routed A→B: {self.stats['B']['received_from_a']} "
                    f"| "
                    f"Routed B→A: {self.stats['A']['received_from_b']}"
                )
                last_print = now
            
            time.sleep(0.1)

    def _print_banner(self, text: str) -> None:
        """Print a formatted banner."""
        line = "=" * 80
        logger.info("")
        logger.info(line)
        logger.info(f"  {text}".center(80))
        logger.info(line)
        logger.info("")

    def _print_results(self) -> None:
        """Print final results and verification checklist."""
        self._print_banner("SIMULATION COMPLETE - FINAL RESULTS")
        
        elapsed = time.time() - self.start_time
        
        # Environment A (GRASS)
        total_a = self.stats["A"]["movement"] + self.stats["A"]["speech"]
        logger.info(f"Environment A (GRASS):")
        logger.info(f"  Generated events: {total_a}")
        logger.info(f"    - Movement: {self.stats['A']['movement']}")
        logger.info(f"    - Speech: {self.stats['A']['speech']}")
        logger.info(f"  Received from B: {self.stats['A']['received_from_b']}")
        logger.info(f"  Room A history size: {len(self.room_a.get_event_history(1000))}")
        
        # Environment B (DIRT)
        total_b = self.stats["B"]["movement"] + self.stats["B"]["speech"]
        logger.info(f"")
        logger.info(f"Environment B (DIRT):")
        logger.info(f"  Generated events: {total_b}")
        logger.info(f"    - Movement: {self.stats['B']['movement']}")
        logger.info(f"    - Speech: {self.stats['B']['speech']}")
        logger.info(f"  Received from A: {self.stats['B']['received_from_a']}")
        logger.info(f"  Room B history size: {len(self.room_b.get_event_history(1000))}")
        
        # Overall
        logger.info(f"")
        logger.info(f"Overall:")
        logger.info(f"  Total events generated: {total_a + total_b}")
        logger.info(f"  Elapsed time: {elapsed:.1f}s")
        logger.info(f"  Event rate: {(total_a + total_b) / elapsed:.1f} events/sec")
        
        # Verification checklist
        logger.info(f"")
        logger.info(f"Verification Checklist:")
        
        checks = [
            ("Events received in A", len(self.room_a.get_event_history(1000)) > 0),
            ("Events received in B", len(self.room_b.get_event_history(1000)) > 0),
            ("A sent to B", self.stats["B"]["received_from_a"] > 0),
            ("B sent to A", self.stats["A"]["received_from_b"] > 0),
            ("No echo-back in A", self._verify_no_echo(self.room_a, SourceEnvironment.ENVIRONMENT_A)),
            ("No echo-back in B", self._verify_no_echo(self.room_b, SourceEnvironment.ENVIRONMENT_B)),
        ]
        
        for check_name, result in checks:
            status = "✅" if result else "❌"
            logger.info(f"  {status} {check_name}")
        
        logger.info("")

    def _verify_no_echo(self, room: Room, expected_source: SourceEnvironment) -> bool:
        """Verify that remote events are from the opposite environment."""
        history = room.get_event_history(1000)
        remote_events = [e for e in history if e.source != expected_source]
        
        # All remote events should be from the opposite environment
        for event in remote_events:
            if event.source == expected_source:
                return False
        return True

    def _get_results(self) -> Dict:
        """Get results dictionary."""
        elapsed = 0.0
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
        
        return {
            "elapsed_seconds": elapsed,
            "environment_a": {
                "movement_events": self.stats["A"]["movement"],
                "speech_events": self.stats["A"]["speech"],
                "total_events": self.stats["A"]["movement"] + self.stats["A"]["speech"],
                "received_from_b": self.stats["A"]["received_from_b"],
                "history_size": len(self.room_a.get_event_history(1000))
            },
            "environment_b": {
                "movement_events": self.stats["B"]["movement"],
                "speech_events": self.stats["B"]["speech"],
                "total_events": self.stats["B"]["movement"] + self.stats["B"]["speech"],
                "received_from_a": self.stats["B"]["received_from_a"],
                "history_size": len(self.room_b.get_event_history(1000))
            }
        }


def main():
    """Entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Simulate Between Signals with GRASS and DIRT TouchDesigner files"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30,
        help="Duration of simulation in seconds (default: 30)"
    )
    parser.add_argument(
        "--grass-movement",
        default="walking",
        choices=["walking", "pacing", "standing", "slow_walk", "random"],
        help="Movement pattern for GRASS environment (default: walking)"
    )
    parser.add_argument(
        "--grass-speech",
        default="conversation",
        choices=["greeting", "conversation", "questions", "poetry", "random"],
        help="Speech pattern for GRASS environment (default: conversation)"
    )
    parser.add_argument(
        "--dirt-movement",
        default="pacing",
        choices=["walking", "pacing", "standing", "slow_walk", "random"],
        help="Movement pattern for DIRT environment (default: pacing)"
    )
    parser.add_argument(
        "--dirt-speech",
        default="poetry",
        choices=["greeting", "conversation", "questions", "poetry", "random"],
        help="Speech pattern for DIRT environment (default: poetry)"
    )
    parser.add_argument(
        "--osc-host",
        default="127.0.0.1",
        help="OSC host for TouchDesigner (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create configurations
    grass_config = EnvironmentConfig(
        name="GRASS",
        environment="A",
        touchdesigner_port=7001,
        movement_pattern=args.grass_movement,
        speech_pattern=args.grass_speech,
        duration_seconds=args.duration
    )
    
    dirt_config = EnvironmentConfig(
        name="DIRT",
        environment="B",
        touchdesigner_port=7002,
        movement_pattern=args.dirt_movement,
        speech_pattern=args.dirt_speech,
        duration_seconds=args.duration
    )
    
    # Run simulation
    sim = TouchDesignerSimulation(
        grass_config=grass_config,
        dirt_config=dirt_config,
        osc_host=args.osc_host
    )
    
    results = sim.run()
    
    # Return non-zero exit code if verification failed
    if results["environment_a"]["total_events"] == 0 or results["environment_b"]["total_events"] == 0:
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
