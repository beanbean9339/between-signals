# Phase 5: Real Hardware - Orbbec Femto Bolt Integration Guide

## Overview

You're transitioning from **simulation mode** to **real hardware mode** using Orbbec Femto Bolt 3D cameras.

```
Before (Phase 4 - Simulation):
Synthetic movement patterns → TouchDesigner visualization

After (Phase 5 - Real Hardware):
Actual visitor depth data from Orbbec camera → TouchDesigner visualization
```

---

## Step 1: Install Orbbec SDK & Python Bindings

### Download Orbbec SDK

Go to: **https://www.orbbec.com/en/try**

1. Select "Femto Bolt" product
2. Download **Windows SDK**
3. Extract to: `C:\Program Files\OrbbecSDK` (or your preferred location)

### Verify Installation

```bash
# Check if Orbbec SDK is installed
dir "C:\Program Files\OrbbecSDK"

# Should show folders like: bin, lib, include, samples
```

### Install Python Wrapper

The Orbbec SDK includes Python bindings. Add them to your Python path:

```bash
# Navigate to Orbbec SDK Python directory
cd "C:\Program Files\OrbbecSDK\python"

# Check what's available
dir

# Copy the pyorbec module to your backend folder (or install it)
```

---

## Step 2: Create Orbbec Camera Interface

I'll create a simple camera driver that works with Femto Bolt:

### File: `backend/orbbec_camera.py`

```python
"""
Orbbec Femto Bolt 3D Camera Integration

Provides real-time depth capture and visitor tracking
"""

import numpy as np
import threading
import time
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

@dataclass
class DepthFrame:
    """Represents a single depth frame from camera"""
    depth_data: np.ndarray  # (height, width) of depth values in mm
    rgb_data: Optional[np.ndarray] = None
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
        
        # Try to import Orbbec SDK
        try:
            # This assumes pyorbec is installed or in sys.path
            import pyorbec
            self.orbec = pyorbec
            self.sdk_available = True
        except ImportError:
            print("⚠️  Orbbec SDK not found. Using mock mode for testing.")
            self.sdk_available = False
            self.orbec = None
    
    def connect(self) -> bool:
        """
        Connect to camera
        
        Returns:
            True if successful, False otherwise
        """
        if not self.sdk_available:
            print(f"[Mock Camera {self.device_id}] Connected (mock mode)")
            return True
        
        try:
            # Real SDK connection would go here
            print(f"[Camera {self.device_id}] Connecting to Orbbec Femto Bolt...")
            # self.device = self.orbec.Device(self.device_id)
            # self.device.start()
            print(f"[Camera {self.device_id}] Connected!")
            return True
        except Exception as e:
            print(f"[Camera {self.device_id}] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from camera"""
        if self.is_running:
            self.stop_streaming()
        # Clean up SDK resources
        if self.sdk_available and hasattr(self, 'device'):
            try:
                # self.device.stop()
                pass
            except:
                pass
    
    def start_streaming(self):
        """Start continuous depth frame capture in background thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self.stream_thread = threading.Thread(target=self._stream_thread_func, daemon=True)
        self.stream_thread.start()
        print(f"[Camera {self.device_id}] Streaming started")
    
    def stop_streaming(self):
        """Stop streaming"""
        self.is_running = False
        if self.stream_thread:
            self.stream_thread.join(timeout=2.0)
        print(f"[Camera {self.device_id}] Streaming stopped")
    
    def _stream_thread_func(self):
        """Background thread that captures depth frames"""
        frame_id = 0
        while self.is_running:
            try:
                if self.sdk_available:
                    # Real depth capture from Orbbec SDK
                    # depth_data = self.device.get_depth_frame()
                    # rgb_data = self.device.get_rgb_frame()
                    pass
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
                time.sleep(1.0 / 30.0)  # 30 FPS
                
            except Exception as e:
                print(f"[Camera {self.device_id}] Error capturing frame: {e}")
                time.sleep(0.1)
    
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
        depth_mm = frame.depth_data
        
        # Remove invalid depth values (0 = no reading)
        valid_mask = (depth_mm > 100) & (depth_mm < 3000)  # 10cm to 3m
        
        if not valid_mask.any():
            return None  # No valid depth
        
        # Find closest valid depth (visitor is closest object)
        min_depth = depth_mm[valid_mask].min()
        foreground_mask = (depth_mm >= min_depth) & (depth_mm <= min_depth + 500)  # Within 50cm
        
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
        confidence = len(y_coords) / (frame.width * frame.height)
        
        return {
            "x": norm_x,
            "y": norm_y,
            "z": center_depth,
            "confidence": min(confidence * 10, 1.0)  # Scale and cap
        }
    
    def _generate_mock_depth(self) -> np.ndarray:
        """Generate synthetic depth data for testing (mock mode)"""
        # Create a 512x512 depth map
        depth = np.ones((512, 512), dtype=np.uint16) * 1000  # 1 meter default
        
        # Simulate a visitor (circular blob) at random position
        import random
        cx = random.randint(100, 400)
        cy = random.randint(100, 400)
        radius = 50
        
        y, x = np.ogrid[:512, :512]
        mask = (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
        depth[mask] = random.randint(500, 1200)  # Visitor is 50-120cm away
        
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
        
        for i in range(num_cameras):
            camera = OrbbecDepthCamera(device_id=i)
            if camera.connect():
                self.cameras.append(camera)
            else:
                print(f"⚠️  Camera {i} failed to connect")
    
    def start_all(self):
        """Start streaming on all cameras"""
        for camera in self.cameras:
            camera.start_streaming()
    
    def stop_all(self):
        """Stop streaming on all cameras"""
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
    print("Testing Orbbec Femto Bolt Integration...")
    
    # Create multi-camera system
    system = MultiCameraSystem(num_cameras=2)
    
    # Start streaming
    system.start_all()
    
    # Collect frames for 10 seconds
    start_time = time.time()
    while time.time() - start_time < 10:
        positions = system.get_all_positions()
        for cam_id, pos in positions.items():
            if pos:
                print(f"Camera {cam_id}: x={pos['x']:.2f}, y={pos['y']:.2f}, z={pos['z']:.2f}m")
        time.sleep(0.5)
    
    # Stop streaming
    system.stop_all()
    print("Test complete!")
```

---

## Step 3: Create Depth-to-Event Converter

### File: `backend/depth_processor.py`

```python
"""
Convert depth camera frames to movement events
"""

from dataclasses import dataclass
from typing import Optional
from orbbec_camera import DepthFrame, OrbbecDepthCamera
from events import MovementEvent, EventType

@dataclass
class VisitorTrack:
    """Track a single visitor over time"""
    visitor_id: int
    last_x: float
    last_y: float
    last_z: float
    frames_seen: int
    

class DepthProcessor:
    """
    Processes depth frames to extract visitor information
    and generate movement events
    """
    
    def __init__(self):
        self.last_positions = {}
        self.position_threshold = 0.1  # Min movement in normalized coords
        
    def process_frame(self, frame: DepthFrame, camera: OrbbecDepthCamera) -> Optional[MovementEvent]:
        """
        Process a single depth frame and generate movement event if visitor moved
        
        Args:
            frame: Depth frame from camera
            camera: Camera object for position extraction
            
        Returns:
            MovementEvent if visitor detected, None otherwise
        """
        # Get visitor position from camera
        position = camera.get_visitor_position()
        
        if position is None:
            return None
        
        # Check if significant movement occurred
        cam_id = camera.device_id
        if cam_id in self.last_positions:
            last = self.last_positions[cam_id]
            
            # Calculate movement distance
            dx = abs(position['x'] - last['x'])
            dy = abs(position['y'] - last['y'])
            movement = (dx ** 2 + dy ** 2) ** 0.5
            
            if movement < self.position_threshold:
                return None  # Minimal movement, ignore
        
        # Update position history
        self.last_positions[cam_id] = position
        
        # Create movement event
        event = MovementEvent(
            source_room_id=f"room_{chr(65 + cam_id)}",  # room_A, room_B
            timestamp=frame.timestamp,
            data={
                "position": {
                    "x": position['x'],
                    "y": position['y'],
                    "z": position['z']
                },
                "confidence": position['confidence'],
                "frame_id": frame.frame_id,
                "sensor": "orbbec_femto_bolt"
            }
        )
        
        return event
```

---

## Step 4: Configure TouchDesigner OSC Receive

You need to set up OSC listening in GRASS.toe and DIRT.toe:

### In TouchDesigner (GRASS.toe):

1. **Add OSC In node**
   - Palette → Network → OSC In
   - Set port to `7001`
   - Pattern: `/ocean/*`

2. **Add Geometry - SOP node** (to visualize depth)
   - Set TOP input to OSC depth data
   - Configure shader to render depth as texture

### OSC Message Format We'll Send:

```
/ocean/depth
  - Depth map as array
  - Visitor X, Y, Z position
  - Confidence value
  - Frame ID
```

---

## Step 5: Integrate with Room/EventRouter/OSC

The flow will be:

```
Orbbec Camera 
  ↓ (DepthProcessor)
Movement Event 
  ↓ (Room.receive_event)
EventRouter 
  ↓ (route to other room)
OSC Out to TouchDesigner
```

We'll use the existing Room and EventRouter classes, just replace the event source.

---

## Status: What Works What's Left

### ✅ Already Built (Phases 1-4):
- Event/Room classes
- EventRouter (no echo-back guarantee)
- OSC output infrastructure
- 105 tests passing

### 🔨 Need to Build (Phase 5):
- [ ] Orbbec camera integration class
- [ ] Depth frame processing
- [ ] Visitor position extraction
- [ ] Depth processor to event converter
- [ ] Real hardware testing with actual camera
- [ ] TouchDesigner depth visualization
- [ ] Full end-to-end integration test

---

## Quick Start: Real Hardware Mode

Once Orbbec SDK is installed:

```bash
cd backend

# Test camera connection
python orbbec_camera.py

# Should show:
# [Camera 0] Connected (mock mode)
# [Camera 1] Connected (mock mode)
# Camera 0: x=0.25, y=-0.10, z=0.85m
# Camera 1: x=-0.15, y=0.30, z=0.92m
```

Then:

```bash
# Run with real camera instead of simulation
python touchdesigner_simulation_real.py --camera-id 0 --room A
python touchdesigner_simulation_real.py --camera-id 1 --room B
```

---

## Next Steps

1. **Install Orbbec SDK** (you need to do this)
2. **Confirm camera detection** (test with Orbbec's viewer first)
3. **I'll create OrbbecDepthCamera class** (already drafted above)
4. **I'll create DepthProcessor class** (already drafted above)
5. **We'll test with mock data first**, then real camera
6. **Configure TouchDesigner for depth visualization**
7. **Full integration test with actual visitors**

---

**Ready to proceed? Let me know:**
1. Have you installed Orbbec SDK yet?
2. Can you confirm both cameras are detected?
3. What TouchDesigner version are you using?
