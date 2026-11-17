# Phase 5: Real Hardware Integration - Orbbec Femto Bolt

## Current Status: Transitioning from Simulation to Real Hardware

You're moving from simulated events to **real 3D camera data**.

---

## What We Need to Build

```
Orbbec Femto Bolt Camera (USB)
  │
  ├─→ Depth Frame Processing
  │
  ├─→ Movement Detection (position from depth)
  │
  ├─→ Event Generation (visitor locations)
  │
  ├─→ EventRouter (bidirectional routing)
  │
  ├─→ OSC Output (Depth Map Data)
  │
  └─→ TouchDesigner
       ├─ GRASS.toe (displays depth from camera A)
       └─ DIRT.toe (displays depth from camera B)
```

---

## Implementation Plan

### Phase 5.1: Orbbec Integration (This Week)

#### Step 1: Install Orbbec SDK
```bash
# Download from: https://www.orbbec.com/products/super-high-resolution-depth-camera/femto-bolt/

# Windows installation
# 1. Download SDK from Orbbec website
# 2. Install USB drivers
# 3. Test with Orbbec's viewer first

# Then install Python wrapper
pip install obersdk
# or
pip install pyorbec
```

#### Step 2: Create Real Camera Driver Class
```python
# File: backend/orbbec_camera.py

class OrbbecDepthCamera:
    """Real Orbbec Femto Bolt 3D camera integration"""
    
    def __init__(self, camera_id: int = 0):
        """Initialize connection to Orbbec camera"""
        self.camera_id = camera_id
        self.depth_frame = None
        self.rgb_frame = None
        
    def get_depth_frame(self) -> np.ndarray:
        """Get current depth map (512x512 or similar resolution)"""
        # Return raw depth data from camera
        
    def get_visitor_position(self) -> dict:
        """Extract visitor X,Y position from depth map"""
        # Find foreground (closest object) = visitor
        # Calculate center of mass = visitor position
        # Return {"x": float, "y": float, "z": float}
        
    def start_streaming(self):
        """Start continuous depth frame capture"""
        
    def stop_streaming(self):
        """Stop streaming and close camera"""
```

#### Step 3: Create Depth-to-Event Converter
```python
# File: backend/depth_processor.py

class DepthToEventConverter:
    """Convert depth frames to movement events"""
    
    def process_depth_frame(self, depth_data: np.ndarray) -> MovementEvent:
        """
        Takes raw depth frame from camera
        Returns MovementEvent with visitor position
        """
        
    def track_visitor(self, depth_data: np.ndarray) -> dict:
        """
        Detect and track visitor position from depth
        Returns: {"x": float, "y": float, "confidence": float}
        """
```

---

## Setup Instructions

### 1️⃣ Install Orbbec SDK

**Windows:**
```bash
# Download from Orbbec website
# https://www.orbbec.com/en/try

# Install to: C:\Program Files\Orbbec\SDK
# (default location)

# Add to PATH if needed
set PATH=%PATH%;C:\Program Files\Orbbec\SDK\bin
```

**Verify Installation:**
```bash
# Test camera connection
python -c "import pyorbec; print(pyorbec.__version__)"
```

### 2️⃣ Install Python Dependencies

```bash
cd backend
pip install numpy scipy opencv-python
# Wait for Orbbec to release Python bindings
# For now, may need to use C++ wrapper or alternative
```

### 3️⃣ Test Camera Connection

```bash
python test_camera_connection.py
```

Expected output:
```
Orbbec Femto Bolt Camera 0: Connected ✓
  Resolution: 512x512
  FPS: 30
  Depth Range: 0.1m - 3.0m
  
Starting depth capture...
Frame 1: Min depth=0.5m, Max depth=2.1m
Frame 2: Min depth=0.5m, Max depth=2.0m
```

---

## Camera Specifications (Orbbec Femto Bolt)

| Spec | Value |
|------|-------|
| **Resolution** | 640x576 (depth) / 1280x960 (RGB) |
| **FPS** | 30 FPS @ full resolution |
| **Depth Range** | 0.2m - 10m |
| **Field of View** | ~87° diagonal |
| **USB** | USB 3.0 (or 3.1) |
| **Power** | 5V USB powered (also needs 5V external for optimal) |

---

## OSC Message Format (Depth Map)

We'll send depth data to TouchDesigner as:

```
/ocean/depth_map
  - width: int (512)
  - height: int (512)
  - depth_data: bytes (flattened array)
  - min_depth: float (meters)
  - max_depth: float (meters)
  - visitor_x: float (-1 to 1, normalized)
  - visitor_y: float (-1 to 1, normalized)
  - visitor_z: float (meters, raw depth)
```

TouchDesigner will convert this to visualization.

---

## Development Phases

### Phase 5.1: Camera Integration (1-2 days)
- [ ] Install Orbbec SDK
- [ ] Create OrbbecDepthCamera class
- [ ] Test real depth frame capture
- [ ] Create DepthToEventConverter

### Phase 5.2: TouchDesigner Visualization (1-2 days)
- [ ] Configure OSC receive in GRASS.toe
- [ ] Configure OSC receive in DIRT.toe
- [ ] Create GLSL shaders for depth visualization
- [ ] Test real-time depth display

### Phase 5.3: Movement Tracking (1-2 days)
- [ ] Implement visitor detection from depth
- [ ] Extract visitor position (X, Y, Z)
- [ ] Generate movement events (not simulated, real)
- [ ] Route events bidirectionally

### Phase 5.4: Testing & Optimization (1 day)
- [ ] Test with actual visitors walking
- [ ] Optimize frame rate and latency
- [ ] Tune depth processing thresholds
- [ ] Verify echo-back prevention still works

---

## Architecture: Real Hardware Mode

```
Room A                           Room B
(GRASS)                         (DIRT)
│                               │
├─ Orbbec Femto Bolt            ├─ Orbbec Femto Bolt
│  USB Camera 0                 │  USB Camera 1
│  └─ 30 FPS depth              │  └─ 30 FPS depth
│                               │
├─ DepthProcessor               ├─ DepthProcessor
│  └─ Extract visitor pos       │  └─ Extract visitor pos
│                               │
├─ Movement Event Gen           ├─ Movement Event Gen
│  └─ Real visitor position     │  └─ Real visitor position
│                               │
└─ Room (OSC output)            └─ Room (OSC output)
   │                               │
   ├─ EventRouter (no echo-back)
   │
   └─ OSC broadcast to TouchDesigner
      ├─ Port 7001 → GRASS.toe (depth + visitor pos)
      └─ Port 7002 → DIRT.toe (depth + visitor pos)
```

---

## Comparison: Simulation vs Real Hardware

| Feature | Simulation | Real Hardware |
|---------|-----------|---------------|
| **Data Source** | Random patterns | Orbbec depth camera |
| **Movement** | Synthetic walk/pace | Actual visitor position |
| **Speech** | Simulated text | Real microphone (later) |
| **Frame Rate** | Varies (5-10 fps) | 30 FPS steady |
| **Latency** | None (instant) | ~33ms per frame |
| **Accuracy** | Demo-level | Real-world tracking |
| **Scalability** | Unlimited events | Limited by camera FPS |

---

## Next Steps

### Immediate (Today):
1. ✅ Confirm camera hardware is ready
2. ⏳ Install Orbbec SDK
3. ⏳ Create camera connection test script

### This Week:
4. ⏳ Build OrbbecDepthCamera class
5. ⏳ Build DepthToEventConverter
6. ⏳ Test real depth capture
7. ⏳ Configure TouchDesigner for depth visualization
8. ⏳ Hook into Room/EventRouter/OSC pipeline

### This Month:
9. ⏳ Full integration testing
10. ⏳ Real visitor walk-through testing
11. ⏳ Performance tuning
12. ⏳ Production deployment

---

## Questions Before We Start

**For Orbbec SDK:**
1. Have you downloaded the SDK from Orbbec yet?
2. Are both cameras detected and working in Orbbec's viewer?
3. Do you have USB 3.0 cables? (Important for 30 FPS)

**For TouchDesigner:**
1. Do GRASS.toe and DIRT.toe already have OSC receive nodes?
2. What do you want depth to look like? (Heat map? Point cloud? Silhouette?)
3. Should we display visitor position as a dot/marker on the depth map?

**For Integration:**
1. Should we keep the EventRouter (no echo-back guarantee) with real camera?
2. Do you want real speech integration now or depth-only for Phase 5?
3. What FPS latency is acceptable? (30 FPS = 33ms per frame)

---

## Status

**Simulation Phase (Complete ✅):**
- ✅ EventRouter with no echo-back
- ✅ Pattern-based movement simulation
- ✅ Pattern-based speech simulation
- ✅ TouchDesigner OSC output
- ✅ 105 tests passing

**Hardware Phase (Ready to Build):**
- ⏳ Orbbec camera integration
- ⏳ Real depth processing
- ⏳ Visitor tracking from depth
- ⏳ TouchDesigner depth visualization
- ⏳ Full integration testing

---

**Ready to build Phase 5?** Let me know when the Orbbec SDK is installed, and we'll start integrating! 🎥
