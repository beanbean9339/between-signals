"""
Phase 3: Integration runner for single-environment simulation testing.

Demonstrates how to run Room A with both movement and speech simulators
in a fully integrated end-to-end test without real hardware.

Usage:
    python simulation_integration.py --room A --duration 30
"""

import argparse
import logging
import threading
import time
import sys
from typing import Optional

# Local imports
from config_loader import RoomConfig
from room import Room
from communication_refactored import EventRouter, create_communication_server
from simulation import SimulationRunner, MovementSimulator, SpeechSimulator
from events import Event, EventType


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase3_simulation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimulationIntegrationRunner:
    """
    Runs a single environment with simulators integrated into the room system.
    
    Demonstrates:
    1. Room initialization
    2. Event router setup
    3. OSC communication server startup
    4. Movement and speech simulators running
    5. Event flow through the system
    """
    
    def __init__(self, room_id: str = "A", include_osc: bool = True):
        """
        Initialize integration runner.
        
        Args:
            room_id: "A" or "B"
            include_osc: Whether to start OSC communication server
        """
        self.room_id = room_id
        self.include_osc = include_osc
        
        # Initialize room
        logger.info(f"Initializing Room {room_id}")
        self.config = RoomConfig(room_id)
        self.room = Room(self.config)
        
        # Initialize simulators
        self.simulation_runner = SimulationRunner(
            room_id=room_id,
            event_callback=self._handle_simulated_event
        )
        
        # Event statistics
        self.event_stats = {
            "movement": 0,
            "speech": 0,
            "other": 0,
            "total": 0
        }
        
        # OSC server (optional)
        self.osc_server = None
        self.osc_thread = None
        
        logger.info(f"SimulationIntegrationRunner initialized for room {room_id}")
    
    def _handle_simulated_event(self, event: Event):
        """
        Handle simulated events - integrate them into the room system.
        
        This is the callback from the simulators that connects them to the room.
        """
        try:
            # Count event types
            if event.type == EventType.MOVEMENT:
                self.event_stats["movement"] += 1
            elif event.type == EventType.SPEECH:
                self.event_stats["speech"] += 1
            else:
                self.event_stats["other"] += 1
            self.event_stats["total"] += 1
            
            # Emit to room (this is the key integration point)
            self.room.emit_local_event(event)
            
            logger.debug(f"Event {event.event_id} handled: {event.type}")
        
        except Exception as e:
            logger.error(f"Error handling simulated event: {e}", exc_info=True)
    
    def start_osc_server(self):
        """Start OSC communication server."""
        if not self.include_osc:
            logger.info("OSC server disabled")
            return
        
        try:
            logger.info("Starting OSC communication server")
            self.osc_server = create_communication_server(self.room, None)
            
            self.osc_thread = threading.Thread(
                target=self.osc_server.serve_forever,
                daemon=False
            )
            self.osc_thread.start()
            logger.info(f"OSC server running on port {self.config.osc_output_port}")
        
        except Exception as e:
            logger.error(f"Failed to start OSC server: {e}")
            self.osc_server = None
    
    def stop_osc_server(self):
        """Stop OSC communication server."""
        if self.osc_server:
            try:
                self.osc_server.shutdown()
                if self.osc_thread:
                    self.osc_thread.join(timeout=5.0)
                logger.info("OSC server stopped")
            except Exception as e:
                logger.error(f"Error stopping OSC server: {e}")
    
    def run_simulation(self,
                      duration_seconds: float = 30.0,
                      movement_pattern: str = "walking",
                      speech_pattern: str = "conversation"):
        """
        Run the integrated simulation.
        
        Args:
            duration_seconds: How long to run
            movement_pattern: Movement pattern type
            speech_pattern: Speech pattern type
        """
        logger.info("=" * 70)
        logger.info(f"PHASE 3 INTEGRATION TEST - Room {self.room_id}")
        logger.info("=" * 70)
        logger.info(f"Duration: {duration_seconds}s")
        logger.info(f"Movement pattern: {movement_pattern}")
        logger.info(f"Speech pattern: {speech_pattern}")
        logger.info(f"Room config: {self.config.room_id} ({self.config.get('environment')})")
        logger.info(f"OSC output port: {self.config.get('osc_output_port')}")
        
        # Start OSC server
        self.start_osc_server()
        
        try:
            # Run simulation
            self.simulation_runner.run_simulation(
                duration_seconds=duration_seconds,
                movement_pattern=movement_pattern,
                speech_pattern=speech_pattern,
                include_movement=True,
                include_speech=True
            )
            
            # Print results
            self.print_results()
        
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        
        except Exception as e:
            logger.error(f"Simulation error: {e}", exc_info=True)
        
        finally:
            self.cleanup()
    
    def print_results(self):
        """Print simulation results."""
        logger.info("=" * 70)
        logger.info("SIMULATION RESULTS")
        logger.info("=" * 70)
        
        # Event statistics
        logger.info(f"Total events: {self.event_stats['total']}")
        logger.info(f"  Movement events: {self.event_stats['movement']}")
        logger.info(f"  Speech events: {self.event_stats['speech']}")
        logger.info(f"  Other events: {self.event_stats['other']}")
        
        # Room statistics
        event_history = self.room.get_event_history(count=100)
        logger.info(f"\nEvents in room history: {len(event_history)}")
        
        # Print recent events
        logger.info("\nRecent events:")
        for event in event_history[-5:]:
            logger.info(f"  - {event.type.name}: {event.event_id}")
        
        # Verification
        logger.info("\n" + "=" * 70)
        logger.info("VERIFICATION CHECKLIST")
        logger.info("=" * 70)
        
        checks = [
            ("Events received", self.event_stats["total"] > 0),
            ("Movement events", self.event_stats["movement"] > 0),
            ("Speech events", self.event_stats["speech"] > 0),
            ("Events in history", len(event_history) > 0),
            ("Room operational", self.room is not None),
        ]
        
        passed = 0
        for check_name, result in checks:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}: {check_name}")
            if result:
                passed += 1
        
        logger.info(f"\nResult: {passed}/{len(checks)} checks passed")
        
        if passed == len(checks):
            logger.info("🎉 ALL CHECKS PASSED - Room is operational!")
        else:
            logger.warning("⚠️ Some checks failed - see log above")
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up...")
        self.stop_osc_server()
        self.simulation_runner.stop_all()
        logger.info("Cleanup complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 3: Single environment simulation test"
    )
    parser.add_argument(
        "--room",
        choices=["A", "B"],
        default="A",
        help="Which room to simulate"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Simulation duration in seconds"
    )
    parser.add_argument(
        "--movement",
        choices=["walking", "pacing", "standing", "slow_walk", "random"],
        default="walking",
        help="Movement pattern"
    )
    parser.add_argument(
        "--speech",
        choices=["greeting", "conversation", "questions", "poetry", "random"],
        default="conversation",
        help="Speech pattern"
    )
    parser.add_argument(
        "--no-osc",
        action="store_true",
        help="Disable OSC communication server"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and run
    runner = SimulationIntegrationRunner(
        room_id=args.room,
        include_osc=not args.no_osc
    )
    
    runner.run_simulation(
        duration_seconds=args.duration,
        movement_pattern=args.movement,
        speech_pattern=args.speech
    )


if __name__ == "__main__":
    main()
