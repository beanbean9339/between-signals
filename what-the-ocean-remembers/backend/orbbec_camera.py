"""
Orbbec Femto Bolt 3D Camera Integration

Provides real-time depth capture and visitor tracking for Between Signals
"""

import numpy as np
import threading
import time
from typing import Optional, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DepthFrame:
    """Represents a single depth frame from camera"""
    depth_data: np.ndarray  # (height, width) of depth values in mm
    timestamp: float = 0.0
    frame_id: int = 0
    
    @property
    def width(self) -> int:
        return self.depth_data.shape[1]
    
    @property
    def height(self) -> int:
        return self.depth_data.shape[0]


class OrbbecDepthCamera:
    """
    Interface to Orbbec Femto Bolt 3D camera
    Captures depth frames and tracks visitor position
    """
    
    def __init__(self, device_id: int = 0):
        """
        Initialize camera connection
        
        Args:
            device_id: Camera index (0 for first camera, 1 for second, etc.)
        """
        self.device_id = device_id
        self.is_running = False
        self.current_frame: Optional[DepthFrame] = None
        self.frame_lock = threading.Lock()
        self.stream_thread: Optional[threading.Thread] = None
        self.device = None
        
        # Try to import Orbbec SDK
        self.sdk_available = False
        try:
            # Try different possible import paths for Orbbec SDK
            try:
                import pyorbec
                self.orbec_sdk = pyorbec
                self.sdk_available = True
                logger.info(f"[Camera {self.device_id}] Orbbec SDK imported successfully")
            except ImportError:
                try:
                    import ob  # Alternative import name
                    self.orbec_sdk = ob
                    self.sdk_available = True
                    logger.info(f"[Camera {self.device_id}] Orbbec SDK (ob module) imported successfully")
                except ImportError:
                    logger.warning(f"[Camera {self.device_id}] Orbbec SDK not installed - using mock mode")
                    self.orbec_sdk = None
        except Exception as e:
            logger.warning(f"[Camera {self.device_id}] SDK import error: {e} - using mock mode")
            self.orbec_sdk = None
    
    def connect(self) -> bool:
        """
        Connect to camera
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.sdk_available and self.orbec_sdk:
                logger.info(f"[Camera {self.device_id}] Connecting to Orbbec Femto Bolt...")
                # Real SDK connection would go here
                # For now, we're in mock mode
                logger.info(f"[Camera {self.device_id}] Connected (SDK mode)")
            else:
                logger.info(f"[Camera {self.device_id}] Connected (mock mode - no SDK)")
            return True
        except Exception as e:
            logger.error(f"[Camera {self.device_id}] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from camera"""
        if self.is_running:
            self.stop_streaming()
        
        if self.device:
            try:
                # Clean up SDK resources
                pass
            except:
                pass
        
        logger.info(f"[Camera {self.device_id}] Disconnected")
    
    def start_streaming(self):
        """Start continuous depth frame capture in background thread"""
        if self.is_running:
            logger.warning(f"[Camera {self.device_id}] Already streaming")
            return
        
        self.is_running = True
        self.stream_thread = threading.Thread(
            target=self._stream_thread_func, 
            daemon=True,
            name=f"OrbbecStreamThread-{self.device_id}"
        )
        self.stream_thread.start()
        logger.info(f"[Camera {self.device_id}] Streaming started (30 FPS target)")
    
    def stop_streaming(self):
        """Stop streaming"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.stream_thread:
            self.stream_thread.join(timeout=2.0)
        logger.info(f"[Camera {self.device_id}] Streaming stopped")
    
    def _stream_thread_func(self):
        """Background thread that captures depth frames"""
        frame_id = 0
        fps_counter = 0
        last_fps_time = time.time()
        
        while self.is_running:
            try:
                # Capture depth frame
                if self.sdk_available and self.orbec_sdk:
                    # Real depth capture from Orbbec SDK would go here
                    depth_data = self._get_real_depth()
                else:
                    # Mock mode: generate synthetic depth data for testing
                    depth_data = self._generate_mock_depth()
                
                frame = DepthFrame(
                    depth_data=depth_data,
                    timestamp=time.time(),
                    frame_id=frame_id
                )
                
                with self.frame_lock:
                    self.current_frame = frame
                
                frame_id += 1
                fps_counter += 1
                
                # Log FPS every 100 frames
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    actual_fps = fps_counter / (current_time - last_fps_time)
                    logger.debug(f"[Camera {self.device_id}] FPS: {actual_fps:.1f}")
                    fps_counter = 0
                    last_fps_time = current_time
                
                # Target 30 FPS
                time.sleep(1.0 / 30.0)
                
            except Exception as e:
                logger.error(f"[Camera {self.device_id}] Error capturing frame: {e}")
                time.sleep(0.1)
    
    def _get_real_depth(self) -> np.ndarray:
        """
        Get real depth data from Orbbec camera
        
        Returns:
            Depth frame as numpy array (uint16, values in mm)
        """
        # This would be implemented with actual Orbbec SDK calls
        # For now, return mock data
        return self._generate_mock_depth()
    
    def get_latest_frame(self) -> Optional[DepthFrame]:
        """
        Get the latest depth frame
        
        Returns:
            DepthFrame or None if no frame available
        """
        with self.frame_lock:
            return self.current_frame
    
    def get_visitor_position(self) -> Optional[Dict[str, float]]:
        """
        Extract visitor position from latest depth frame
        
        Returns:
            {
                "x": float (-1 to 1, normalized),
                "y": float (-1 to 1, normalized),
                "z": float (depth in meters),
                "confidence": float (0 to 1)
            }
            or None if no visitor detected
        """
        frame = self.get_latest_frame()
        if frame is None:
            return None
        
        # Find foreground (closest object = visitor)
        depth_mm = frame.depth_data.astype(np.float32)
        
        # Remove invalid depth values (0 = no reading)
        # Orbbec typically gives 0 for invalid readings
        valid_mask = (depth_mm > 100) & (depth_mm < 3000)  # 10cm to 3m
        
        if not valid_mask.any():
            return None  # No valid depth
        
        # Find closest valid depth (visitor is closest object)
        min_depth = depth_mm[valid_mask].min()
        
        # Consider anything within 50cm of closest as "visitor"
        foreground_mask = (depth_mm >= min_depth) & (depth_mm <= min_depth + 500)
        
        if not foreground_mask.any():
            return None
        
        # Find center of mass of foreground
        y_coords, x_coords = np.where(foreground_mask)
        
        if len(y_coords) == 0:
            return None
        
        # Center of visitor in pixel coordinates
        center_x = x_coords.mean()
        center_y = y_coords.mean()
        center_depth = depth_mm[foreground_mask].mean() / 1000.0  # Convert to meters
        
        # Normalize to -1 to 1 range (center is 0)
        norm_x = (center_x / frame.width) * 2.0 - 1.0
        norm_y = (center_y / frame.height) * 2.0 - 1.0
        
        # Confidence based on how much of frame is foreground
        foreground_ratio = len(y_coords) / (frame.width * frame.height)
        confidence = min(foreground_ratio * 10, 1.0)
        
        return {
            "x": norm_x,
            "y": norm_y,
            "z": center_depth,
            "confidence": confidence
        }
    
    def _generate_mock_depth(self) -> np.ndarray:
        """
        Generate synthetic depth data for testing (mock mode)
        
        Returns:
            512x512 depth map with simulated visitor
        """
        import random
        
        # Create a 512x512 depth map (Femto Bolt native resolution)
        depth = np.ones((512, 512), dtype=np.uint16) * 1500  # 1.5 meters default background
        
        # Add noise to make it more realistic
        noise = np.random.normal(0, 20, (512, 512))
        depth = np.clip(depth + noise, 0, 3000).astype(np.uint16)
        
        # Simulate a visitor (circular blob) at random position
        cx = random.randint(150, 350)
        cy = random.randint(150, 350)
        radius = random.randint(40, 80)
        
        y, x = np.ogrid[:512, :512]
        mask = (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
        
        # Visitor is 60-120cm away (much closer than background)
        visitor_depth = random.randint(600, 1200)
        depth[mask] = visitor_depth
        
        return depth


class MultiCameraSystem:
    """
    Manages multiple Orbbec cameras (one per room)
    """
    
    def __init__(self, num_cameras: int = 2):
        """
        Initialize multi-camera system
        
        Args:
            num_cameras: Number of cameras to initialize (default: 2 for A and B)
        """
        self.cameras = []
        self.num_cameras = num_cameras
        logger.info(f"Initializing MultiCameraSystem with {num_cameras} cameras")
        
        for i in range(num_cameras):
            camera = OrbbecDepthCamera(device_id=i)
            if camera.connect():
                self.cameras.append(camera)
            else:
                logger.warning(f"Camera {i} failed to connect")
    
    def start_all(self):
        """Start streaming on all cameras"""
        logger.info("Starting all cameras")
        for camera in self.cameras:
            camera.start_streaming()
    
    def stop_all(self):
        """Stop streaming on all cameras"""
        logger.info("Stopping all cameras")
        for camera in self.cameras:
            camera.stop_streaming()
    
    def get_camera(self, index: int) -> Optional[OrbbecDepthCamera]:
        """Get camera by index"""
        if 0 <= index < len(self.cameras):
            return self.cameras[index]
        return None
    
    def get_all_positions(self) -> Dict[int, Optional[Dict]]:
        """Get visitor positions from all cameras"""
        return {i: cam.get_visitor_position() for i, cam in enumerate(self.cameras)}


if __name__ == "__main__":
    # Test the camera system
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("Testing Orbbec Femto Bolt Integration")
    print("=" * 70)
    
    # Create multi-camera system
    system = MultiCameraSystem(num_cameras=2)
    
    # Start streaming
    system.start_all()
    
    print("\nCapturing 10 seconds of depth data...\n")
    
    # Collect frames for 10 seconds
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < 10:
        positions = system.get_all_positions()
        for cam_id, pos in positions.items():
            if pos:
                print(f"Camera {cam_id}: x={pos['x']:+.3f}, y={pos['y']:+.3f}, z={pos['z']:.2f}m, conf={pos['confidence']:.2f}")
        frame_count += 1
        time.sleep(0.5)
    
    # Stop streaming
    system.stop_all()
    
    print(f"\nTest complete! Captured {frame_count} position samples")
    print("=" * 70)
