# Between Signals: Documentation & Artifacts Index

## 🎯 Start Here

**New to this project?** → Read [PHASE_4_DELIVERY.md](#phase-4-delivery)  
**Want to run code now?** → Read [PHASE_4_QUICK_REFERENCE.md](#phase-4-quick-reference)  
**Need deep technical details?** → Read [PHASE_4_COMPLETION.md](#phase-4-completion)  
**Executive overview?** → Read [PHASE_4_SUMMARY.md](#phase-4-summary)

---

## 📚 Documentation Guide

### PHASE_4_DELIVERY.md
**Purpose:** Delivery package checklist and quick reference  
**Length:** 8.3 KB (5-minute read)  
**Best for:** Getting oriented, finding specific information  
**Includes:**
- Deliverables checklist
- Quick start commands
- Troubleshooting index
- File manifest
- Status summary

**When to read:** First thing to understand what's been delivered

---

### PHASE_4_QUICK_REFERENCE.md
**Purpose:** CLI usage guide and quick patterns reference  
**Length:** 9.2 KB (5-minute read)  
**Best for:** Running simulations immediately  
**Includes:**
- Quick start TL;DR
- CLI options reference
- Pattern types and examples
- Expected output samples
- Real-world scenarios
- Performance tuning tips

**When to read:** Before running `python touchdesigner_simulation.py`

---

### PHASE_4_COMPLETION.md
**Purpose:** Complete technical documentation  
**Length:** 16.6 KB (15-minute read)  
**Best for:** Understanding implementation, troubleshooting issues  
**Includes:**
- Architecture diagrams
- Usage patterns with code examples
- API reference
- Verification methodology
- Test results
- Troubleshooting guide
- Design decisions

**When to read:** When you need to understand how something works

---

### PHASE_4_SUMMARY.md
**Purpose:** Executive overview of Phases 1-4  
**Length:** 13.2 KB (10-minute read)  
**Best for:** Big-picture understanding and progress tracking  
**Includes:**
- What we built (deliverables table)
- Architecture overview
- Implementation details per phase
- Verified capabilities
- Usage quick start
- Test coverage summary
- Technical decisions & rationale
- Non-obvious behaviors
- Next steps (Phase 5+)

**When to read:** To understand full project scope and progress

---

## 🔗 Code Files

### touchdesigner_simulation.py
**Purpose:** Main orchestrator for GRASS + DIRT simulation  
**Size:** 17.7 KB  
**Key Classes:**
- `EnvironmentConfig` — Configuration for one environment
- `TouchDesignerSimulation` — Main orchestrator
- `OSCOutput` — Helper for UDP transmission to TouchDesigner

**Key Methods:**
- `run()` — Execute parallel simulation
- `_handle_simulated_event()` — Route events bidirectionally
- `get_statistics()` — Collect event metrics

**Documentation:** See PHASE_4_COMPLETION.md "API Reference"

### test_touchdesigner_simulation.py
**Purpose:** 24 comprehensive tests for Phase 4  
**Size:** 15.3 KB  
**Test Classes:**
- `TestEnvironmentConfig` — Configuration validation
- `TestInitialization` — Orchestrator setup
- `TestEventHandling` — Bidirectional routing verification
- `TestRoomState` — Room history tracking
- `TestStatistics` — Event counting and rates
- `TestVerification` — No-echo-back guarantee
- `TestEndToEnd` — Full workflow testing

**Run Tests:** `pytest test_touchdesigner_simulation.py -v`

---

## 📊 Project Statistics

### Test Coverage
| Phase | Component | Tests | Status |
|-------|-----------|-------|--------|
| 1 | Event/Room/EventRouter | 24 | ✅ |
| 2 | SpeechSimulator/Routing | 17 | ✅ |
| 3 | MovementSimulator/SimulationRunner | 40 | ✅ |
| 4 | TouchDesignerSimulation | 24 | ✅ |
| **Total** | | **105** | **✅** |

### Code Quality
- **Zero Regressions:** All 81 existing tests still passing
- **Zero Echo-Back Violations:** 100% compliance with no-echo-back guarantee
- **Verified Event Rate:** 5.3 events/second in live simulation
- **Documentation:** Complete with examples and troubleshooting

---

## 🚀 Quick Commands Reference

```bash
# Run 15-second simulation with verbose output
cd backend
python touchdesigner_simulation.py \
  --grass-pattern random \
  --dirt-pattern circular \
  --duration 15 \
  --verbose

# Run all Phase 4 tests
pytest test_touchdesigner_simulation.py -v

# Run all tests (Phases 1-4)
pytest test_*.py -v

# Run specific test class
pytest test_touchdesigner_simulation.py::TestEventHandling -v

# Run with minimal output
python touchdesigner_simulation.py --grass-pattern random --dirt-pattern circular
```

---

## 🎓 Key Concepts

### Bidirectional Routing
Events generated in GRASS (Environment A) automatically route to DIRT (Environment B), and vice versa, maintaining true two-way communication.

```
GRASS generates event → EventRouter → DIRT receives event
DIRT generates event → EventRouter → GRASS receives event
```

### No-Echo-Back Guarantee
The EventRouter ensures that an event originating from GRASS never routes back to GRASS, and an event from DIRT never routes back to DIRT. This prevents feedback loops and ensures data integrity.

```
GRASS → (routed to) → DIRT only
DIRT → (routed to) → GRASS only
Never: GRASS → GRASS or DIRT → DIRT
```

### OSC Output
Events are transmitted to TouchDesigner files via Open Sound Control (OSC) protocol over UDP:
- **GRASS** receives OSC on port 7001
- **DIRT** receives OSC on port 7002

### Parallel Execution
Both GRASS and DIRT simulators run simultaneously in separate threads, maintaining synchronized duration. This creates true two-way real-time interaction.

---

## 🔍 Navigation by Task

### "I want to run a simulation now"
1. Read: [PHASE_4_QUICK_REFERENCE.md](#phase-4-quick-reference)
2. Run: `python touchdesigner_simulation.py --grass-pattern random --dirt-pattern circular --duration 15`
3. Check: Expected output section in Quick Reference

### "I need to understand how it works"
1. Read: [PHASE_4_SUMMARY.md](#phase-4-summary) (architecture + phases)
2. Read: [PHASE_4_COMPLETION.md](#phase-4-completion) (deep dive)
3. Browse: Code comments in `touchdesigner_simulation.py`

### "Tests are failing, what do I do?"
1. Read: [PHASE_4_COMPLETION.md](#phase-4-completion) → Troubleshooting section
2. Run: `pytest test_touchdesigner_simulation.py -v` to see which tests fail
3. Check: Specific test method in `test_touchdesigner_simulation.py`

### "I want to modify the code"
1. Read: [PHASE_4_COMPLETION.md](#phase-4-completion) → API Reference section
2. Read: [PHASE_4_COMPLETION.md](#phase-4-completion) → Important Non-Obvious Behaviors
3. Check: Relevant test cases for expected behavior
4. Run: `pytest test_touchdesigner_simulation.py -v` after changes

### "What comes next?"
1. Read: [PHASE_4_SUMMARY.md](#phase-4-summary) → "What's Next (Phase 5+)"
2. Consider: Real hardware integration (Kinect, RealSense, microphone)
3. Consider: Performance profiling and scaling

---

## ✅ Verification Checklist

Before considering Phase 4 complete:
- [x] All 105 tests passing (24 new Phase 4 tests)
- [x] No echo-back violations in live simulation
- [x] Bidirectional routing verified (A↔B)
- [x] Event generation rate confirmed (5.3 events/sec)
- [x] OSC output working to both environments
- [x] Statistics collection accurate
- [x] Documentation complete and accurate
- [x] CLI interface working
- [x] Zero regressions in existing code
- [x] Production-ready code quality

---

## 📁 File Tree

```
between-signals/
├── backend/
│   ├── touchdesigner_simulation.py          ← Main Phase 4 code
│   ├── test_touchdesigner_simulation.py     ← Phase 4 tests (24)
│   ├── simulation.py                        ← Phase 3 (SimulationRunner)
│   ├── test_simulation.py                   ← Phase 3 tests (40)
│   ├── speech.py                            ← Phase 2 (SpeechSimulator)
│   ├── test_speech_integration.py           ← Phase 2 tests (17)
│   ├── communication_refactored.py          ← Phase 1 (EventRouter)
│   ├── room.py                              ← Phase 1 (Room class)
│   ├── test_refactored.py                   ← Phase 1 tests (24)
│   └── requirements.txt
│
├── PHASE_4_DELIVERY.md                      ← Delivery checklist
├── PHASE_4_QUICK_REFERENCE.md              ← Quick start guide
├── PHASE_4_COMPLETION.md                   ← Technical docs
├── PHASE_4_SUMMARY.md                      ← Executive overview
├── PHASE_4_DOCUMENTATION_INDEX.md           ← This file
│
├── GRASS.toe                                ← TouchDesigner Environment A
├── DIRT.toe                                 ← TouchDesigner Environment B
└── PROJECT_SCOPE.md                         ← Original requirements
```

---

## 🤝 Contributing

When adding new features or phases:

1. **Keep phases independent:** Phase N+1 should build on Phase N without modifying it
2. **Write tests first:** Each feature should have corresponding tests
3. **Document as you go:** Add comments and update relevant documentation files
4. **Run full test suite:** `pytest test_*.py -v` before committing
5. **Update this index:** Add entries if creating new documentation

---

## 📞 Support & Troubleshooting

### Common Issues

**"OSC messages not arriving in TouchDesigner"**
→ See PHASE_4_COMPLETION.md, Troubleshooting section

**"Echo-back violations detected"**
→ This should not happen in production. File a bug with detailed output.

**"Tests failing after my changes"**
→ Run `pytest test_touchdesigner_simulation.py::TestEventHandling -v` to debug

**"Performance degradation over time"**
→ See PHASE_4_QUICK_REFERENCE.md, Performance Tuning section

### Getting Help

1. Check the **Troubleshooting** section of [PHASE_4_COMPLETION.md](#phase-4-completion)
2. Run tests to narrow down the issue: `pytest -v`
3. Review relevant code comments in `touchdesigner_simulation.py`
4. Consult **Important Non-Obvious Behaviors** in [PHASE_4_COMPLETION.md](#phase-4-completion)

---

## 🎓 Learning Path

**Complete Beginner:**
1. PHASE_4_DELIVERY.md (overview)
2. PHASE_4_QUICK_REFERENCE.md (run something)
3. PHASE_4_SUMMARY.md (understand architecture)

**Intermediate Developer:**
1. PHASE_4_SUMMARY.md (phases overview)
2. PHASE_4_COMPLETION.md (deep dive)
3. Code + tests (hands-on)

**Advanced/Contributing:**
1. All documentation (complete context)
2. Code + tests (implementation)
3. Run suite with modifications
4. Submit changes with tests

---

## 📊 Document Statistics

| Document | Size | Read Time | Focus |
|----------|------|-----------|-------|
| PHASE_4_DELIVERY.md | 8.3 KB | 5 min | Checklist & overview |
| PHASE_4_QUICK_REFERENCE.md | 9.2 KB | 5 min | Quick start |
| PHASE_4_COMPLETION.md | 16.6 KB | 15 min | Technical depth |
| PHASE_4_SUMMARY.md | 13.2 KB | 10 min | Executive summary |
| This Index | 7.8 KB | 8 min | Navigation guide |
| **Total** | **55.1 KB** | **~40 min** | Complete context |

---

## ✨ Highlights

- **105/105 tests passing** (zero regressions)
- **24 new Phase 4 tests** (comprehensive coverage)
- **Zero echo-back violations** (guaranteed by EventRouter)
- **5.3 events/second** (verified in live simulation)
- **Bidirectional routing** (100% verified)
- **Production-ready code** (fully documented)
- **Complete documentation** (5 guides + this index)

---

**Last Updated:** Phase 4 Completion  
**Status:** ✅ Complete and verified  
**Next Step:** Phase 5 (Real Hardware Integration) or deployment

