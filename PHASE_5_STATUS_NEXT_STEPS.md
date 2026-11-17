# Phase 5: Next Steps - From Simulation to Real Hardware

## Status Update

✅ **What's Ready:**
- Orbbec camera driver class (`orbbec_camera.py`) - Tested in mock mode
- Depth processor class (`depth_processor.py`) - Tested in mock mode  
- Multi-camera system support - Working
- Real-time depth frame capture - Working
- Visitor position extraction - Working
- 30 FPS streaming capability - Ready

⏳ **What We Need Next:**
1. Install Orbbec SDK on your system
2. Connect real cameras and test hardware detection
3. Configure TouchDesigner OSC receive
4. Create real-time orchestrator for both cameras + rooms
5. Full end-to-end testing

---

## Setup Checklist

### Step 1: Install Orbbec SDK ✅ (You do this)

```bash
# Download from: https://www.orbbec.com/en/try
# Select: Femto Bolt
# Select: Windows SDK

# After download:
# 1. Run the installer
# 2. Install to default location: C:\Program Files\OrbbecSDK

# Verify installation:
dir "C:\Program Files\OrbbecSDK"
# Should show: bin, lib, include, samples folders
```

### Step 2: Verify Camera Connection ✅ (You do this)

```bash
# Test with Orbbec's viewer first (from SDK):
# C:\Program Files\OrbbecSDK\samples\Viewer.exe

# Should show:
# - Device 0: Orbbec Femto Bolt
# - Device 1: Orbbec Femto Bolt
```

### Step 3: Install Python SDK Bindings (I'll help)

Once SDK is installed:
```bash
cd backend
pip install pyorbec
# or if that doesn't work:
# Copy Python bindings from SDK to backend folder
```

### Step 4: Test Camera Connection

```bash
cd backend
python orbbec_camera.py

# Should show real camera data instead of mock data
```

---

## Architecture: Real Mode

```
System with Real Hardware
═════════════════════════════════════════════════════════════════

Room A (GRASS)                          Room B (DIRT)
│                                       │
├─ Orbbec Femto Bolt                    ├─ Orbbec Femto Bolt
│  USB:0                                │  USB:1
│  │                                    │  │
│  └─→ OrbbecDepthCamera               └─→ OrbbecDepthCamera
│      (Real depth @ 30 FPS)               (Real depth @ 30 FPS)
│      │                                   │
│      └─→ DepthProcessor              └─→ DepthProcessor
│          (Visitor detection)            (Visitor detection)
│          │                              │
│          └─→ MovementEvent           └─→ MovementEvent
│              (Real visitor position)     (Real visitor position)
│              │                           │
└──────────────┼───────────────────────────┼───────────────┘
               │                           │
               └───→ EventRouter ←─────────┘
                   (No echo-back)
                   │
                   └─→ OSC Output
                       ├─ GRASS.toe (port 7001)
                       │  Receives depth + visitor position
                       └─ DIRT.toe (port 7002)
                          Receives depth + visitor position
```

---

## Files Created (Ready to Use)

### 1. `orbbec_camera.py` (12.7 KB)
- **OrbbecDepthCamera class**: Real camera connection
- **MultiCameraSystem class**: Manage 2 cameras
- **Mock mode support**: Test without real hardware
- **30 FPS streaming**: Background thread

```python
# Usage
from orbbec_camera import MultiCameraSystem

system = MultiCameraSystem(num_cameras=2)
system.start_all()

# Get visitor positions
positions = system.get_all_positions()
# {0: {"x": 0.1, "y": -0.2, "z": 0.8, "confidence": 0.7}, ...}

system.stop_all()
```

### 2. `depth_processor.py` (8.1 KB)
- **DepthProcessor class**: Convert depth frames to events
- **RealtimeDepthMonitor class**: Continuous monitoring
- **Movement detection**: Smart thresholding
- **Position smoothing**: Reduce jitter

```python
# Usage
from depth_processor import RealtimeDepthMonitor

monitor = RealtimeDepthMonitor(camera_id=0, room_id="room_a")
monitor.initialize()

event = monitor.get_next_event()
# Returns MovementEvent with real visitor position

monitor.shutdown()
```

---

## Next: Real-Time Orchestrator

We need to create a **real-time version** that replaces simulation with real hardware:

### File: `real_hardware_simulation.py` (to create)

```python
"""
Real-time Between Signals with Orbbec cameras
Replaces touchdesigner_simulation.py for real hardware mode
"""

from orbbec_camera import MultiCameraSystem
from depth_processor import RealtimeDepthMonitor
from room import Room
from communication_refactored import EventRouter
from config_loader import load_room_config
import threading
import time

class RealHardwareBetweenSignals:
    """Main orchestrator for real hardware mode"""
    
    def __init__(self):
        self.cameras = MultiCameraSystem(num_cameras=2)
        self.monitors = {
            "room_a": RealtimeDepthMonitor(camera_id=0, room_id="room_a"),
            "room_b": RealtimeDepthMonitor(camera_id=1, room_id="room_b")
        }
        self.rooms = {}
        self.event_router = EventRouter()
    
    def initialize(self):
        """Setup real hardware system"""
        # Load room configs
        self.rooms["room_a"] = Room(room_id="room_a", config=load_room_config("room_a"))
        self.rooms["room_b"] = Room(room_id="room_b", config=load_room_config("room_b"))
        
        # Initialize monitors
        for monitor in self.monitors.values():
            monitor.initialize()
    
    def run(self, duration: float = 60.0):
        """
        Run real-time event capture and routing
        
        Args:
            duration: How long to run (seconds)
        """
        start_time = time.time()
        events_generated = 0
        events_routed = 0
        
        while time.time() - start_time < duration:
            # Capture events from both rooms
            for room_id, monitor in self.monitors.items():
                event = monitor.get_next_event()
                if event:
                    events_generated += 1
                    
                    # Route event to opposite room
                    target_room_id = "room_b" if room_id == "room_a" else "room_a"
                    
                    # Use EventRouter to ensure no echo-back
                    routed_events = self.event_router.route_event(
                        event=event,
                        source_room_id=room_id,
                        target_room_id=target_room_id
                    )
                    
                    if routed_events:
                        events_routed += 1
                        # Send to TouchDesigner via OSC
                        for routed_event in routed_events:
                            self.rooms[target_room_id].receive_remote_event(routed_event)
            
            time.sleep(0.01)  # 100 Hz polling
        
        return {
            "duration": time.time() - start_time,
            "events_generated": events_generated,
            "events_routed": events_routed
        }
    
    def shutdown(self):
        """Cleanup"""
        for monitor in self.monitors.values():
            monitor.shutdown()


if __name__ == "__main__":
    system = RealHardwareBetweenSignals()
    system.initialize()
    
    print("Real hardware Between Signals running for 60 seconds...")
    stats = system.run(duration=60)
    
    system.shutdown()
    
    print(f"Results: {stats['events_generated']} events, {stats['events_routed']} routed")
```

---

## TouchDesigner Configuration

### In GRASS.toe (listening on port 7001):

```
OSC In node:
  - Port: 7001
  - Pattern: /ocean/*
  
Null CHOP (for depth data):
  - Channel from OSC: depth_map
  - Convert to TOP for visualization
  
Geometry CHOP (for visitor position):
  - Channel from OSC: visitor_x, visitor_y, visitor_z
  - Use for position indicator/marker
```

### In DIRT.toe (listening on port 7002):

Same configuration as GRASS.toe but port 7002.

---

## OSC Message Format

We'll send this structure for real hardware:

```
/ocean/depth
  - depth_width: int (640)
  - depth_height: int (576)
  - visitor_x: float (-1 to 1)
  - visitor_y: float (-1 to 1)
  - visitor_z: float (0.1 to 3.0 meters)
  - visitor_confidence: float (0 to 1)
  - frame_id: int
  
/ocean/movement
  - x, y, z (alternative format, same data)
  - confidence
  
/ocean/depth_map
  - Raw 640x576 depth array (optional, for advanced visualization)
```

---

## Comparison: Mock Mode vs Real Mode

| Aspect | Mock Mode | Real Mode |
|--------|-----------|-----------|
| **Cameras** | Simulated | Orbbec Femto Bolt USB |
| **Depth Data** | Synthetic circular blob | Real depth sensor output |
| **Frame Rate** | 30 FPS (fixed) | 30 FPS (actual) |
| **Visitor Pos** | Random walk | Real visitor tracking |
| **Testing** | No hardware needed | Requires cameras + cables |
| **Accuracy** | Demo-level | Real-world tracking |

---

## Development Timeline

### Today ✅
- [x] Design Orbbec integration
- [x] Create OrbbecDepthCamera class
- [x] Create DepthProcessor class
- [x] Test in mock mode

### Tomorrow (1-2 hours)
- [ ] Install Orbbec SDK
- [ ] Verify camera hardware
- [ ] Test with real depth data
- [ ] Tune movement detection thresholds

### This Week (1-2 days)
- [ ] Create RealHardwareBetweenSignals orchestrator
- [ ] Configure TouchDesigner OSC
- [ ] Full integration test
- [ ] Test with actual visitors

### This Month
- [ ] Performance optimization
- [ ] Add speech integration (real microphone)
- [ ] Multi-visitor support
- [ ] Production deployment

---

## Troubleshooting Guide

### "Orbbec SDK not found"
Solution: Install from https://www.orbbec.com/en/try

### "No cameras detected"
Solution: Check USB cables, restart application, verify in Orbbec Viewer

### "OSC data not arriving in TouchDesigner"
Solution: Check port number (7001 for GRASS, 7002 for DIRT), verify OSC In node config

### "Visitor detection not working"
Solution: Adjust depth threshold in DepthProcessor, check camera angle/distance

### "Jittery movement in TouchDesigner"
Solution: Use smoothed_position from DepthProcessor, increase history length

---

## Status Summary

**Phase 4 (Simulation): ✅ COMPLETE**
- 105 tests passing
- 5.4 events/second
- Zero echo-back violations
- Ready for deployment

**Phase 5 (Real Hardware): 🔨 IN PROGRESS**
- Orbbec integration: ✅ Designed & tested (mock)
- Hardware setup: ⏳ Waiting for SDK installation
- TouchDesigner config: ⏳ Next step
- Full integration: ⏳ After hardware is ready
- Production ready: 🎯 Target 1 week

---

## Next Action Items

### For You:
1. Download Orbbec SDK from https://www.orbbec.com/en/try
2. Install to `C:\Program Files\OrbbecSDK`
3. Test with Orbbec Viewer to verify cameras work
4. Let me know when SDK is installed

### For Me:
1. Update OrbbecDepthCamera to use real SDK bindings (after SDK install)
2. Create RealHardwareBetweenSignals orchestrator
3. Create TouchDesigner OSC configuration guide
4. Full integration testing

---

## Questions?

Before proceeding, tell me:

1. **Is the Orbbec SDK downloaded?**
   - If yes, I can proceed with real integration immediately
   - If no, download from: https://www.orbbec.com/en/try

2. **Do both cameras show up in Orbbec Viewer?**
   - Shows USB device IDs match (should be 0 and 1)

3. **What TouchDesigner version are you using?**
   - Needed for OSC configuration compatibility

4. **Do GRASS.toe and DIRT.toe already exist?**
   - If yes, do they have OSC receive nodes?

---

**Ready to integrate real hardware? Let me know the status! 🎥**
