# 🚀 QUICK START: Run Between Signals Simulation

## Prerequisites ✅
- Python 3.8+ (you have Python 3.14.7 ✅)
- Virtual environment activated
- All dependencies installed

## Step-by-Step Setup

### Step 1: Open Terminal
```bash
# Navigate to the backend folder
cd C:\Users\beanb\vscode_projects\between-signals\what-the-ocean-remembers\backend
```

### Step 2: Activate Virtual Environment
```bash
# Windows PowerShell
.\venv\Scripts\Activate

# You should see (venv) at the start of your terminal prompt
(venv) PS C:\Users\beanb\...backend>
```

### Step 3: Install Dependencies (if needed)
```bash
pip install -r requirements.txt
```

### Step 4: Run the Simulation

#### **Option A: Simple (Recommended for first time)**
```bash
python touchdesigner_simulation.py
```
✅ This will:
- Run for 10 seconds (default)
- Use random pattern for GRASS
- Use random pattern for DIRT
- Show statistics at the end

#### **Option B: With Custom Settings**
```bash
python touchdesigner_simulation.py \
  --grass-pattern random \
  --dirt-pattern circular \
  --duration 15 \
  --verbose
```

**What each option means:**
- `--grass-pattern random` → GRASS moves randomly
- `--dirt-pattern circular` → DIRT moves in circles
- `--duration 15` → Run for 15 seconds
- `--verbose` → Show detailed output while running

#### **Option C: Different Pattern Combinations**

```bash
# Random both environments
python touchdesigner_simulation.py --grass-pattern random --dirt-pattern random --duration 15 --verbose

# Circular both
python touchdesigner_simulation.py --grass-pattern circular --dirt-pattern circular --duration 15 --verbose

# Square grid
python touchdesigner_simulation.py --grass-pattern square --dirt-pattern square --duration 15 --verbose

# Linear traverse
python touchdesigner_simulation.py --grass-pattern linear --dirt-pattern linear --duration 15 --verbose

# Mix them
python touchdesigner_simulation.py --grass-pattern random --dirt-pattern square --duration 20 --verbose
```

---

## What You'll See

### Output Example (15 seconds, verbose mode)

```
=== Phase 4: TouchDesigner Simulation ===
Environment A (GRASS):  Random pattern, OSC port 7001
Environment B (DIRT):   Circular pattern, OSC port 7002
Duration: 15 seconds

[Simulation Running...]
Room A received movement from DIRT
Room B received movement from GRASS
Room A received speech from DIRT
...

[Statistics]
Total simulation time: 15.02 seconds

Events generated:
  GRASS (A): 42 movements, 8 speech
  DIRT (B):  39 movements, 7 speech

Routed events:
  A → B: 50 events
  B → A: 46 events
  Total: 96 events (100% routed)

Echo-back violations: 0 ✓

Event rate: 6.4 events/second

[Verification]
✓ No-echo-back guarantee maintained
✓ Event routing integrity confirmed
✓ Statistics accuracy verified
```

---

## Expected Behavior

✅ **What should happen:**
1. Terminal shows simulation starting
2. GRASS and DIRT run simultaneously (in background threads)
3. Events are generated and routed between them
4. After duration seconds, statistics appear
5. Terminal shows "Echo-back violations: 0 ✓"

❌ **What shouldn't happen:**
- Errors or crashes
- "Echo-back violations" detected
- Frozen/hanging terminal

---

## Pattern Types Explained

| Pattern | Behavior | Use Case |
|---------|----------|----------|
| **random** | Visitor wanders randomly | General unpredictable movement |
| **circular** | Visitor orbits in a circle | Pacing/looping behavior |
| **square** | Visitor traces a square grid | Structured room exploration |
| **linear** | Visitor moves point A to point B | Simple traverse |

---

## Run Tests (Verify Everything Works)

### Run All 24 Phase 4 Tests
```bash
pytest test_touchdesigner_simulation.py -v
```

Expected output:
```
test_touchdesigner_simulation.py::TestEnvironmentConfig::test_valid_config PASSED
test_touchdesigner_simulation.py::TestInitialization::test_orchestrator_initialization PASSED
...
======================== 24 passed in 8.42s ==========================
```

### Run All Tests (Phases 1-4)
```bash
pytest test_*.py -v
```

Expected output:
```
======================== 105 passed in 84.76s =========================
```

---

## Common Commands

```bash
# Simple run (10 seconds)
python touchdesigner_simulation.py

# 30-second verbose run
python touchdesigner_simulation.py --duration 30 --verbose

# Test everything works
pytest test_touchdesigner_simulation.py -v

# Check Python version
python --version

# See all command options
python touchdesigner_simulation.py --help
```

---

## Troubleshooting

### "Command not found: python"
**Solution:** Activate virtual environment first
```bash
.\venv\Scripts\Activate
```

### "ModuleNotFoundError: No module named 'pytest'"
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### "ImportError: No module named 'communication_refactored'"
**Solution:** Make sure you're in the backend directory
```bash
cd C:\Users\beanb\vscode_projects\between-signals\what-the-ocean-remembers\backend
```

### "OSC messages not arriving"
This is expected in simulation mode (no actual TouchDesigner running).  
✅ **Don't worry** — the simulation works fine locally.  
If you have GRASS.toe and DIRT.toe open in TouchDesigner:
1. Make sure they're listening on ports 7001 and 7002
2. Run with `--verbose` to see OSC send attempts

---

## Next Steps After Running

1. **Understand the output** → Read [PHASE_4_QUICK_REFERENCE.md](/C:/Users/beanb/vscode_projects/between-signals/PHASE_4_QUICK_REFERENCE.md)
2. **Learn how it works** → Read [PHASE_4_COMPLETION.md](/C:/Users/beanb/vscode_projects/between-signals/PHASE_4_COMPLETION.md)
3. **Modify the code** → Check [PHASE_4_DOCUMENTATION_INDEX.md](/C:/Users/beanb/vscode_projects/between-signals/PHASE_4_DOCUMENTATION_INDEX.md)

---

## Example Session

### Open terminal and run:
```bash
# Navigate to backend
cd C:\Users\beanb\vscode_projects\between-signals\what-the-ocean-remembers\backend

# Activate venv
.\venv\Scripts\Activate

# Run simulation for 15 seconds with verbose output
python touchdesigner_simulation.py --duration 15 --verbose

# See output with statistics
# Then press Ctrl+C if it doesn't exit automatically
```

---

## Ready?

**Run this now:**
```bash
cd C:\Users\beanb\vscode_projects\between-signals\what-the-ocean-remembers\backend
.\venv\Scripts\Activate
python touchdesigner_simulation.py --duration 15 --verbose
```

That's it! 🎉
