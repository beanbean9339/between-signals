"""
Convert Orbbec depth camera frames to movement events

Processes real depth data and generates events that can be routed via EventRouter
"""

import logging
from typing import Optional
from dataclasses import dataclass
from orbbec_camera import DepthFrame, OrbbecDepthCamera
from events import MovementEvent

logger = logging.getLogger(__name__)


@dataclass
class VisitorTrack:
    """Track a single visitor over time"""
    visitor_id: int
    last_x: float
    last_y: float
    last_z: float
    frames_seen: int
    confidence_history: list


class DepthProcessor:
    """
    Processes depth frames to extract visitor information
    and generate movement events
    """
    
    def __init__(self, room_id: str, threshold: float = 0.05):
        """
        Initialize depth processor
        
        Args:
            room_id: ID of the room this processor belongs to ("room_a" or "room_b")
            threshold: Minimum normalized movement distance to trigger event
        """
        self.room_id = room_id
        self.position_threshold = threshold
        self.last_position = None
        self.position_history = []
        self.max_history = 30  # Keep last 30 positions
        
        logger.info(f"[DepthProcessor {room_id}] Initialized with threshold={threshold}")
    
    def process_frame(
        self, 
        frame: DepthFrame, 
        camera: OrbbecDepthCamera
    ) -> Optional[MovementEvent]:
        """
        Process a single depth frame and generate movement event if visitor moved
        
        Args:
            frame: Depth frame from camera
            camera: Camera object for position extraction
            
        Returns:
            MovementEvent if significant movement detected, None otherwise
        """
        # Get visitor position from camera
        position = camera.get_visitor_position()
        
        if position is None:
            return None
        
        # Check if significant movement occurred
        if self.last_position is not None:
            # Calculate movement distance
            dx = position['x'] - self.last_position['x']
            dy = position['y'] - self.last_position['y']
            movement = (dx ** 2 + dy ** 2) ** 0.5
            
            if movement < self.position_threshold:
                # Minimal movement, ignore
                return None
        
        # Movement detected! Update position history
        self.last_position = position
        self.position_history.append(position)
        
        # Keep only recent history
        if len(self.position_history) > self.max_history:
            self.position_history.pop(0)
        
        # Create movement event
        event = MovementEvent(
            source_room_id=self.room_id,
            timestamp=frame.timestamp,
            data={
                "position": {
                    "x": position['x'],
                    "y": position['y'],
                    "z": position['z']
                },
                "confidence": position['confidence'],
                "frame_id": frame.frame_id,
                "sensor": "orbbec_femto_bolt",
                "depth_resolution": {
                    "width": frame.width,
                    "height": frame.height
                }
            }
        )
        
        logger.debug(
            f"[DepthProcessor {self.room_id}] "
            f"Movement detected: x={position['x']:.3f}, y={position['y']:.3f}, z={position['z']:.2f}m"
        )
        
        return event
    
    def get_smoothed_position(self) -> Optional[dict]:
        """
        Get visitor position smoothed over recent history
        Reduces jitter from individual frames
        
        Returns:
            Smoothed position or None if no position history
        """
        if not self.position_history:
            return None
        
        # Average recent positions
        avg_x = sum(p['x'] for p in self.position_history) / len(self.position_history)
        avg_y = sum(p['y'] for p in self.position_history) / len(self.position_history)
        avg_z = sum(p['z'] for p in self.position_history) / len(self.position_history)
        avg_conf = sum(p['confidence'] for p in self.position_history) / len(self.position_history)
        
        return {
            "x": avg_x,
            "y": avg_y,
            "z": avg_z,
            "confidence": avg_conf,
            "smoothed": True
        }
    
    def reset(self):
        """Reset position tracking (e.g., when no visitor detected for long time)"""
        self.last_position = None
        self.position_history.clear()
        logger.info(f"[DepthProcessor {self.room_id}] Position tracking reset")


class RealtimeDepthMonitor:
    """
    Real-time monitor for depth camera that continuously:
    1. Captures frames
    2. Processes them for visitor detection
    3. Generates movement events
    4. Can be hooked into EventRouter for bidirectional communication
    """
    
    def __init__(self, camera_id: int, room_id: str):
        """
        Initialize real-time depth monitor
        
        Args:
            camera_id: Orbbec camera index (0 or 1)
            room_id: Room identifier ("room_a" or "room_b")
        """
        self.camera = OrbbecDepthCamera(device_id=camera_id)
        self.processor = DepthProcessor(room_id=room_id)
        self.room_id = room_id
        self.camera_id = camera_id
        
        # Statistics
        self.total_frames = 0
        self.total_events = 0
        
        logger.info(f"[RealtimeDepthMonitor] Camera {camera_id} → {room_id}")
    
    def initialize(self) -> bool:
        """
        Connect to camera and start streaming
        
        Returns:
            True if successful, False otherwise
        """
        if not self.camera.connect():
            logger.error(f"[RealtimeDepthMonitor] Failed to connect to camera {self.camera_id}")
            return False
        
        self.camera.start_streaming()
        return True
    
    def get_next_event(self) -> Optional[MovementEvent]:
        """
        Poll for next movement event
        
        Returns:
            MovementEvent if movement detected, None otherwise
        """
        frame = self.camera.get_latest_frame()
        if frame is None:
            return None
        
        self.total_frames += 1
        
        # Process frame and generate event
        event = self.processor.process_frame(frame, self.camera)
        if event:
            self.total_events += 1
        
        return event
    
    def shutdown(self):
        """Stop streaming and cleanup"""
        self.camera.stop_streaming()
        self.camera.disconnect()
        logger.info(
            f"[RealtimeDepthMonitor {self.room_id}] "
            f"Shutdown - Processed {self.total_frames} frames, "
            f"Generated {self.total_events} events"
        )


if __name__ == "__main__":
    # Test the depth processor
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("Testing Depth Processor")
    print("=" * 70)
    
    # Initialize monitor for Room A
    monitor = RealtimeDepthMonitor(camera_id=0, room_id="room_a")
    
    if not monitor.initialize():
        print("Failed to initialize camera!")
        exit(1)
    
    print("\nPolling for movement events (10 seconds)...\n")
    
    import time
    start_time = time.time()
    event_count = 0
    
    while time.time() - start_time < 10:
        event = monitor.get_next_event()
        if event:
            print(f"Event: {event.data['position']}")
            event_count += 1
        time.sleep(0.1)
    
    monitor.shutdown()
    
    print(f"\nTest complete! Detected {event_count} movement events")
    print("=" * 70)
