# Phase 2 Quick Reference

## 🎯 What's New

Three new files implementing speech-to-event integration:

1. **speech_refactored.py** — Whisper processor with event callbacks
2. **speech_integration.py** — Room integration wrapper
3. **test_speech_integration.py** — 17 comprehensive tests

## 🚀 Quick Start

### Standalone (Testing)
```bash
cd backend
python speech_refactored.py
```
Listens to microphone, logs transcriptions to console and `between_signals.log`.

### Room-Integrated (Production)
```python
from config_loader import RoomConfig
from room import Room
from speech_integration import RoomSpeechProcessor

config = RoomConfig(room_id="A")
room = Room(config)
processor = RoomSpeechProcessor.create(room)
processor.start_listening()  # Blocks until Ctrl+C
```

Microphone → Whisper → SpeechEvent → EventRouter → TouchDesigner

## 📊 Test Results

```
Phase 1 (Backend): 24/24 ✅
Phase 2 (Speech):  17/17 ✅
Total:            41/41 ✅
```

Run tests:
```bash
# Phase 2 only
pytest test_speech_integration.py -v

# All (Phase 1 + 2)
pytest test_refactored.py test_speech_integration.py -v
```

## 🔧 Configuration

Edit `config/room_a.json` or `config/room_b.json`:
```json
{
  "audio_device": 1,
  "whisper_model": "base",
  "audio_process_seconds": 4,
  "whisper_device": "cpu",
  "whisper_compute_type": "int8"
}
```

## 📝 Key Changes to Phase 1

**events.py:** `create()` methods now accept string room IDs
```python
# Old: SpeechEvent.create(source=SourceEnvironment.ENVIRONMENT_A, ...)
# New: SpeechEvent.create(source="A", ...)  # Both work
```

## 🔄 Data Flow

```
Microphone (device:1)
    ↓
AudioStream (44100 Hz, 4 seconds per buffer)
    ↓
SpeechProcessor.transcribe_buffer()  [Whisper]
    ↓
SpeechEvent.create(source="A", text="...")
    ↓
room.emit_local_event(event)
    ↓
EventRouter.route_event(event)  [No echo-back]
    ↓
opposite_room.receive_remote_event(event)
    ↓
TouchDesigner OSC message: /speech "{source: A, text: '...'}"
```

## 🛠️ Common Tasks

**Check available microphone devices:**
```python
import sounddevice as sd
print(sd.query_devices())
```

**Use different Whisper model (for speed vs accuracy):**
```python
# Fast: tiny → base (default) → small → medium → large (slowest)
processor = RoomSpeechProcessor.create(room, whisper_model="tiny")
```

**Enable logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Use GPU for Whisper (if available):**
Edit config JSON:
```json
{
  "whisper_device": "cuda",
  "whisper_compute_type": "float16"
}
```

## 📦 Dependencies

Installed in Phase 2:
- numpy, scipy, sounddevice, faster-whisper
- Plus transitive: ctranslate2, onnxruntime, pyyaml, etc.

Install if missing:
```bash
pip install numpy scipy sounddevice faster-whisper
```

## ✅ Verification

After Phase 2:
- ✅ Microphone audio captured at 44100 Hz
- ✅ 4-second buffers transcribed by Whisper
- ✅ Transcriptions emit SpeechEvent objects
- ✅ Events routed through rooms without echo-back
- ✅ OSC messages sent to TouchDesigner (port 7001/7002)
- ✅ All tests passing (41/41)
- ✅ Logging to file (between_signals.log)
- ✅ Error resilience (callback failures don't crash)

## 🚫 Known Limitations (Phase 2)

- Single speaker per room (no multi-speaker support yet)
- Blocking audio stream (use asyncio in Phase 3)
- Language hard-coded to English
- No speaker identification
- No real-time streaming (waits for 4-second buffer)

## 🔮 Next: Phase 3

**Simulation Mode** (no hardware needed):
- Movement simulator
- Speech simulator
- Full end-to-end testing on one computer

---

**Status:** Production ready ✅  
**Tests:** 41/41 passing ✅  
**Last Updated:** Phase 2 complete
