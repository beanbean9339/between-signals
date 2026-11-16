# Phase 3: Simulation Mode — Quick Reference

## TL;DR

Phase 3 adds **simulation mode** to test the entire system without real hardware. Run Room A with simulated visitors in 10 seconds:

```bash
python simulation_integration.py --room A --duration 10
```

**Result:** 40+ events (movement + speech) successfully processed by Room A ✅

---

## Quick Start

### 1. Run a 15-second simulation of Room A
```bash
python simulation_integration.py --room A --duration 15
```

### 2. Test with specific patterns
```bash
python simulation_integration.py \
  --room A \
  --duration 20 \
  --movement walking \
  --speech conversation
```

### 3. Run all tests
```bash
pytest test_refactored.py test_speech_integration.py test_simulation.py -v
# 81 tests total (Phase 1: 24 + Phase 2: 17 + Phase 3: 40)
```

---

## Pattern Types

### Movement Patterns
- `walking` — Crosses space (default)
- `pacing` — Walks back and forth
- `standing` — Stands still
- `slow_walk` — Very slow movement
- `random` — Randomly generated

### Speech Patterns
- `greeting` — Simple greeting (default for conversations)
- `conversation` — Multi-turn dialogue
- `questions` — Series of questions
- `poetry` — Poetic/thematic text
- `random` — Random utterances

---

## Example Commands

```bash
# Room A, 30 seconds, all defaults
python simulation_integration.py --room A --duration 30

# Room B, 60 seconds, pacing + questions
python simulation_integration.py --room B --duration 60 \
  --movement pacing --speech questions

# Minimal logging
python simulation_integration.py --room A --log-level WARNING

# No OSC server (faster)
python simulation_integration.py --room A --no-osc --duration 10
```

---

## Python API (Programmatic Use)

### Generate movement events
```python
from simulation import MovementSimulator

sim = MovementSimulator(room_id="A")
pattern = sim.generate_pattern("walking")
sim.run_pattern(pattern, loop=False)
```

### Generate speech events
```python
from simulation import SpeechSimulator

sim = SpeechSimulator(room_id="A")
pattern = sim.generate_pattern("conversation")
sim.run_pattern(pattern, loop=False)
```

### Full orchestration
```python
from simulation import SimulationRunner

runner = SimulationRunner(room_id="A")
runner.run_simulation(
    duration_seconds=30,
    movement_pattern="walking",
    speech_pattern="conversation"
)
```

### Integrate with room
```python
from config_loader import RoomConfig
from room import Room
from simulation_integration import SimulationIntegrationRunner

runner = SimulationIntegrationRunner(room_id="A", include_osc=True)
runner.run_simulation(
    duration_seconds=30,
    movement_pattern="walking",
    speech_pattern="conversation"
)
```

---

## Expected Output

### Success Output
```
=================================================================
PHASE 3 INTEGRATION TEST - Room A
=================================================================
Duration: 15.0s
Movement pattern: walking
Speech pattern: conversation
Room config: A (grass)
OSC output port: 7001

... [simulation running for 15 seconds] ...

SIMULATION RESULTS
==================
Total events: 44
  Movement events: 36
  Speech events: 8

Events in room history: 44

Recent events:
  - MOVEMENT: 47d965af-50e9-4f63-9a3b-d4be77aa3cfe
  - MOVEMENT: bdc905d7-5d7f-46c6-967d-0ff5e0aa3bd6
  - SPEECH: a7e77cc5-5dee-41d4-a066-a4cb39710c2f

VERIFICATION CHECKLIST
======================
✅ PASS: Events received
✅ PASS: Movement events
✅ PASS: Speech events
✅ PASS: Events in history
✅ PASS: Room operational

Result: 5/5 checks passed
🎉 ALL CHECKS PASSED - Room is operational!
```

---

## Test Results

```
Phase 1 (Backend infrastructure):     24 tests ✅
Phase 2 (Speech integration):          17 tests ✅
Phase 3 (Simulation mode):             40 tests ✅
─────────────────────────────────────────────────
Total:                                 81 tests ✅

Execution time: ~85 seconds
```

---

## Component Overview

| Component | Purpose | Key Classes |
|-----------|---------|------------|
| `simulation.py` | Core simulators | MovementSimulator, SpeechSimulator, SimulationRunner |
| `simulation_integration.py` | Room integration | SimulationIntegrationRunner |
| `test_simulation.py` | Tests | 40 comprehensive test cases |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No module named simulation" | `cd what-the-ocean-remembers/backend` before running |
| Simulation hangs | Press Ctrl+C, or use --duration flag |
| No events shown | Check callback is defined and room config loads |
| All tests fail | Run `pytest test_simulation.py -v` to see errors |
| OSC errors | Use `--no-osc` flag to disable OSC server |

---

## What's Next?

**Phase 4: Cross-Room Testing**
- Test Room A ↔ Room B routing
- Verify no-echo-back guarantee
- Full end-to-end flow validation
- Performance profiling

**For now:** Use Phase 3 to validate single environments and test movement/speech patterns!

---

## File Locations

```
what-the-ocean-remembers/backend/
├── simulation.py                 # Core simulators
├── simulation_integration.py      # Room integration
├── test_simulation.py             # 40 tests
├── config/
│   ├── room_a.json
│   └── room_b.json
├── venv/                          # Python environment
└── phase3_simulation.log          # Generated log file
```

---

## Key Metrics

- **Events per second:** 2-3 events/sec (during pattern)
- **Room capacity:** 1000 event history max
- **Dedup buffer:** 100 recent event IDs
- **Simulation accuracy:** ±0.5 seconds
- **Memory usage:** ~50 MB per simulation
- **CPU usage:** Minimal (Python threads, not intensive)

---

For detailed documentation, see **PHASE_3_COMPLETION.md**.
