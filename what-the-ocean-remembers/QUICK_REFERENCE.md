# Quick Reference - New Backend Structure

## Running the System

### Start the Backend
```bash
cd backend
python main_refactored.py
```

### Run Tests
```bash
cd backend
.\venv\Scripts\python.exe -m pytest test_refactored.py -v
```

### Send Test Messages (Still Works!)
```bash
python test_sender.py
```

---

## Core Modules

### events.py
**Purpose:** Event schema and protocol

**Key Classes:**
```python
Event              # Base event
MovementEvent      # Visitor position/movement
SpeechEvent        # Transcribed text
PresenceEvent      # Visitor entered/left
AudioLevelEvent    # Microphone level
```

**Usage:**
```python
# Create event
event = SpeechEvent.create(
    source=SourceEnvironment.ENVIRONMENT_A,
    text="Hello"
)

# Serialize
data = event.to_dict()

# Deserialize
event = parse_event(data)
```

---

### config_loader.py
**Purpose:** Load room configuration from JSON

**Key Class:**
```python
RoomConfig      # Loads config/{room_id}.json
```

**Usage:**
```python
config = RoomConfig("A")
port = config.get("osc_output_port", 7001)
```

**Config Files:**
- `config/room_a.json` - Environment A settings
- `config/room_b.json` - Environment B settings

---

### room.py
**Purpose:** Encapsulate per-environment state

**Key Class:**
```python
Room            # Represents Environment A or B
```

**Usage:**
```python
# Initialize
config = RoomConfig("A")
room = Room(config, event_router=router_callback)

# Receive remote event (from opposite room)
room.receive_remote_event(event)

# Emit local event (to opposite room)
room.emit_local_event(event)

# Get diagnostics
status = room.get_connection_status()
history = room.get_event_history(10)
```

**What it does:**
- Receives events from router, sends to TouchDesigner via OSC
- Receives local events, routes to opposite environment
- De-duplicates events by event_id
- Maintains event history for diagnostics

---

### communication_refactored.py
**Purpose:** Route events between rooms

**Key Classes:**
```python
EventRouter         # Routes A↔B, never echoes back
CommunicationServer # OSC server listening for input
```

**Usage:**
```python
# Create system
router, server = create_communication_server(backend_port=8000)

# Start listening (blocks)
server.start()
```

**What it does:**
- Listens for incoming OSC messages on port 8000
- Converts OSC messages to Event objects
- Routes to opposite room (never back to source)
- Handles all message types: text, movement, presence, object, audio

---

## OSC Message Reference

### Input Messages (Coming Into Backend)

```python
/input/text A "message text"
/input/movement A x y intensity
/input/presence A 0_or_1
/input/object A "object_name"
/input/audio A level
```

### Output Messages (Going to TouchDesigner)

```python
/ocean/text "message text"
/ocean/movement [x, y, intensity]
/ocean/presence 0_or_1
/ocean/audio_level level
```

---

## File Organization

```
backend/
├── events.py                    ← Event schema
├── config_loader.py            ← Configuration loading
├── room.py                      ← Room abstraction
├── communication_refactored.py  ← Router and server
├── main_refactored.py           ← Entry point (USE THIS)
├── test_refactored.py           ← 24 automated tests
│
├── config/
│   ├── room_a.json              ← Environment A config
│   └── room_b.json              ← Environment B config
│
├── [old files - still work]
│   ├── communication.py
│   ├── speech.py
│   ├── environment_a_test.py
│   ├── environment_b_test.py
│   └── ...
│
└── venv/                        ← Python environment
```

---

## Configuration Reference

### room_a.json
```json
{
  "room_id": "A",
  "environment": "grass",
  "mode": "simulation",
  "osc_output_host": "127.0.0.1",
  "osc_output_port": 7001,
  "microphone_device": -1,
  "whisper_model": "base",
  "whisper_device": "cpu",
  "whisper_compute_type": "int8",
  "audio_sample_rate": 44100,
  "whisper_sample_rate": 16000,
  "audio_process_seconds": 4,
  "enable_vad": false
}
```

**Key Settings:**
- `room_id` - Room identifier (A or B)
- `environment` - Type (grass or dirt)
- `mode` - simulation or production
- `osc_output_port` - Port to send to TouchDesigner
- `microphone_device` - -1 for auto-detect
- `whisper_model` - tiny/base/small/medium/large

---

## Event Structure Reference

```json
{
  "event_id": "uuid-string",
  "type": "speech|movement|presence|audio_level",
  "source": "A|B",
  "timestamp": 1234567890.123,
  "data": {
    // Event-specific fields
  }
}
```

### Movement Event Data
```json
{
  "present": true,
  "position": {"x": 0.0-1.0, "y": 0.0-1.0},
  "velocity": 0.0-1.0,
  "direction": "left|right|up|down|none",
  "intensity": 0.0-1.0
}
```

### Speech Event Data
```json
{
  "text": "transcribed text",
  "language": "en",
  "confidence": 0.0-1.0
}
```

### Presence Event Data
```json
{
  "present": true|false,
  "visitor_id": "optional-id"
}
```

### Audio Level Event Data
```json
{
  "level": 0.0-1.0
}
```

---

## Logging

### View Logs
```bash
# Console output (when running)
python main_refactored.py

# Log file
type between_signals.log
```

### Log Levels
- **DEBUG** - Detailed tracing
- **INFO** - Startup, routing info
- **ERROR** - Problems that occurred

### Example Log Output
```
2026-11-16 16:50:00,123 - communication_refactored - INFO - Routing movement from A to B
2026-11-16 16:50:00,124 - room - DEBUG - Room A received: Event(speech from B, id=550e8400...)
2026-11-16 16:50:00,125 - room - DEBUG - Sent speech OSC message: Hello...
```

---

## Testing

### Run All Tests
```bash
cd backend
.\venv\Scripts\python.exe -m pytest test_refactored.py -v
```

### Run Specific Test
```bash
.\venv\Scripts\python.exe -m pytest test_refactored.py::TestEventRouter::test_router_no_echo_back -v
```

### Expected Output
```
======================== 24 passed in 0.48s ==========================
```

### Test Structure
- `TestEventCreation` - Event objects work correctly
- `TestRoomConfiguration` - Config files load properly
- `TestRoomClass` - Room abstraction works
- `TestEventRouter` - Routing is correct (A→B, B→A, no echo-back)
- `TestOSCOutputFormats` - Messages formatted correctly
- `TestBidirectionalCommunication` - Full end-to-end flow

---

## Troubleshooting

### "No module named events"
```bash
# Make sure you're in the backend directory
cd backend
# Run with correct Python path
.\venv\Scripts\python.exe main_refactored.py
```

### "Port 8000 already in use"
```bash
# Change backend_port in main_refactored.py
server = create_communication_server(backend_port=9000)
```

### "Config file not found"
```bash
# Config loader falls back to defaults automatically
# To use specific config:
config = RoomConfig("A", config_path="path/to/room_a.json")
```

### Events not reaching TouchDesigner
```bash
# 1. Verify OSC output port is correct
#    Check config/room_a.json osc_output_port

# 2. Check TouchDesigner is listening
#    Run environment_a_test.py to verify

# 3. Check logs
#    python main_refactored.py  # Look for errors
```

---

## Common Operations

### Create and Send a Movement Event
```python
from events import MovementEvent, SourceEnvironment

event = MovementEvent.create(
    source=SourceEnvironment.ENVIRONMENT_A,
    present=True,
    position_x=0.5,
    position_y=0.3,
    velocity=0.7,
    direction="right",
    intensity=0.9
)

# Event now has:
# - event_id (auto-generated UUID)
# - timestamp (auto-generated)
# - type (MOVEMENT)
# - source (A)
# - data (all the motion info)
```

### Create and Send a Speech Event
```python
from events import SpeechEvent, SourceEnvironment

event = SpeechEvent.create(
    source=SourceEnvironment.ENVIRONMENT_B,
    text="Hello from the dirt environment"
)

# Event is ready to route
```

### Access Configuration
```python
from config_loader import RoomConfig

config = RoomConfig("A")

# Get values
room_id = config.get("room_id")
osc_port = config["osc_output_port"]  # Dict-style access

# Check if exists
if "whisper_model" in config:
    model = config.get("whisper_model")
```

---

## Next Steps

After Phase 1 is complete:

**Phase 2: Integrate Speech Processor**
- Modify `speech.py` to emit SpeechEvent objects
- Connect to room.emit_local_event()
- Test microphone → Whisper → Event → Router → TouchDesigner

**Phase 3: Add Simulation Mode**
- Create event simulators
- Test without real hardware

**Phase 4: Cloud Communication**
- Implement WebSocket relay
- Support two separate computers

**Phase 5: Sensor Integration**
- Add depth sensor support
- Detect visitor movement

---

## Important Notes

- ✅ All old code still works (backward compatible)
- ✅ No breaking changes
- ✅ Configuration is external (easy to change)
- ✅ Events are structured (ready for future features)
- ✅ System is logged (easy to debug)
- ✅ No echo-back is guaranteed and tested
- ✅ Ready for speech, movement, and cloud relay integration

---

**For detailed documentation, see PHASE_1_COMPLETION.md**
