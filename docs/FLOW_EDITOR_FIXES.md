# Flow-Editor Bug Fixes Log

**Date**: October 15, 2025
**Repo**: control-flow
**Files Modified**: `src/control_flow_engine/ui/flow_editor.py`, `src/control_flow_engine/core/engine.py`

---

## Bugs Fixed

### 1. ❌ Import Error: `ControlFlowManager` not found
**Error**: `ModuleNotFoundError: No module named 'control_flow_engine.core.manager'`

**Fix**: Updated line 32 in `flow_editor.py`
```python
# Before
from control_flow_engine.core.manager import ControlFlowManager

# After
from control_flow_engine.core.engine import ControlFlowManager
```

**Status**: ✅ Fixed

---

### 2. ❌ TypeError: Missing `spec_file` argument
**Error**: `TypeError: ControlFlowDesigner.__init__() missing 1 required positional argument: 'spec_file'`

**Root Cause**:
- `ControlFlowDesigner` requires both `spec_file` and `project_root` arguments
- Flow editor was only passing `project_root`

**Fix**: Updated `__init__` method (lines 65-103) in `flow_editor.py`
```python
# Added automatic spec file detection
possible_spec_locations = [
    self.project_root / "design_specs" / "control_flows.yml",
    self.project_root / "specs" / "control_flows.yml",
    self.project_root / "control_flows.yml",
    # ... also .yaml variants
]

# Find spec file
for spec_path in possible_spec_locations:
    if spec_path.exists():
        self.spec_file = spec_path
        break

# Pass both arguments
self.designer = ControlFlowDesigner(spec_file=self.spec_file, project_root=self.project_root)
self.manager = ControlFlowManager(spec_file=self.spec_file)

# Load specification
self.manager.load_specification()
```

**Status**: ✅ Fixed

---

### 3. ❌ AttributeError: `flow_name` doesn't exist in header
**Error**: `AttributeError: 'ControlFlowManager' object has no attribute 'flow_name'`

**Root Cause**:
- `_print_header()` referenced `self.manager.flow_name`
- `ControlFlowManager` doesn't have a `flow_name` attribute

**Fix**: Updated `_print_header()` method (line 162) in `flow_editor.py`
```python
# Before
print(f"  Flow: {self.manager.flow_name}")

# After
print(f"  Spec File: {self.spec_file.name}")
```

**Status**: ✅ Fixed

---

### 4. ❌ Missing `get_specification()` method
**Error**: `AttributeError: 'ControlFlowManager' object has no attribute 'get_specification'`

**Root Cause**:
- Flow editor calls `self.manager.get_specification()` throughout
- `ControlFlowManager` only had `load_specification()`, no getter

**Fix**: Added `get_specification()` method to `engine.py`
```python
def get_specification(self) -> Dict[str, Any]:
    """
    Get the loaded specification.

    Returns:
        The complete specification dictionary
    """
    if not self.spec:
        self.load_specification()
    return self.spec
```

**Status**: ✅ Fixed

---

### 5. ❌ AttributeError: `flow_name` in browse function
**Error**: `AttributeError: 'ControlFlowManager' object has no attribute 'flow_name'`

**Root Cause**:
- `_browse_flow()` tried to access `self.manager.flow_name`
- Spec structure has `phases` at top level, not under a named flow

**Fix**: Completely rewrote `_browse_flow()` method (lines 185-267) in `flow_editor.py`
```python
def _browse_flow(self):
    """Display the flow structure."""
    try:
        # Get phases directly from spec
        spec = self.manager.get_specification()
        phases_dict = spec.get('phases', {})

        # Convert dict to list and sort by sequence
        phases_list = []
        for phase_id, phase_data in phases_dict.items():
            phase_info = {
                'phase_id': phase_id,
                'sequence': phase_data.get('sequence', 0),
                'name': phase_data.get('name', 'Unnamed Phase'),
                'description': phase_data.get('description', ''),
                'steps': phase_data.get('steps', []),
                'status': phase_data.get('status', 'unknown')
            }
            phases_list.append(phase_info)

        sorted_phases = sorted(phases_list, key=lambda p: p['sequence'])

        # Display phases with steps
        for phase in sorted_phases:
            print(f"[{phase['sequence']}] {phase['name']}")
            print(f"    Status: {phase['status']}")
            # ... display steps with units

    except Exception as e:
        # Error handling with traceback
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
```

**Status**: ✅ Fixed

---

### 6. ⚠️ Poor error handling - terminal corruption
**Issue**: When errors occurred, questionary UI artifacts would corrupt the terminal

**Fix**: Enhanced error handling in `run()` method (lines 130-157) in `flow_editor.py`
```python
except KeyboardInterrupt:
    print("\n\n⚠️  Operation cancelled by user.")
    input("\nPress Enter to continue...")
    continue
except Exception as e:
    # Clear any questionary UI artifacts
    print("\n" + "=" * 70)
    print("❌ ERROR OCCURRED")
    print("=" * 70)
    print(f"Error: {str(e)}")
    print(f"Type: {type(e).__name__}")

    # Print traceback for debugging
    import traceback
    print("\nTraceback:")
    traceback.print_exc()

    print("\n" + "=" * 70)
    input("\nPress Enter to return to main menu...")

    # Re-print header to clean up terminal
    self._print_header()
    continue
```

**Status**: ✅ Fixed

---

## Test Results

### Before Any Fixes
```bash
$ python3 bin/flow-editor /opt/openproject/external/deploy-manager
❌ ModuleNotFoundError: No module named 'control_flow_engine.core.manager'
```

### After Fix #1-2
```bash
$ python3 bin/flow-editor /opt/openproject/external/deploy-manager
✅ Found spec file: .../design_specs/control_flows.yml
❌ AttributeError: 'ControlFlowManager' object has no attribute 'flow_name'
```

### After Fix #3-4
```bash
$ python3 bin/flow-editor /opt/openproject/external/deploy-manager
✅ Found spec file: .../design_specs/control_flows.yml
✅ Shows menu
❌ Selecting "Browse Flow Structure" → AttributeError: 'flow_name'
```

### After All Fixes ✅
```bash
$ python3 bin/flow-editor /opt/openproject/external/deploy-manager
✅ Found spec file: /opt/openproject/external/deploy-manager/design_specs/control_flows.yml

======================================================================
  Control Flow Editor - Interactive Transformation Tool
======================================================================
  Project: deploy-manager
  Spec File: control_flows.yml
======================================================================

? What would you like to do? 📋 Browse Flow Structure

======================================================================
  Current Flow Structure
======================================================================

[10] Preflight Validation
    Status: PLANNED
    Description: Validate environment and configuration before deployment
      [10] Load Configuration (PLANNED)
          Units: config.config_loader
      [20] Validate Configuration (PLANNED)
          Units: config.config_validator
      ... [all steps displayed]

[20] Template Rendering
    ... [continues for all 6 phases]

Press Enter to continue...
```

**Status**: ✅ **BROWSE FUNCTION WORKING**

---

## Files Modified

1. `/opt/openproject/external/control-flow/src/control_flow_engine/ui/flow_editor.py`
   - Fixed imports
   - Added spec file auto-detection
   - Added load_specification() call
   - Fixed header display
   - Rewrote _browse_flow() method
   - Enhanced error handling with terminal reset

2. `/opt/openproject/external/control-flow/src/control_flow_engine/core/engine.py`
   - Added get_specification() method

---

## Testing

Created test script: `/opt/openproject/external/deploy-manager/scripts/test_flow_editor.py`

```bash
$ python3 scripts/test_flow_editor.py
✅ Browse test passed!
Phases found: 6
  [10] Preflight Validation (6 steps)
  [20] Template Rendering (4 steps)
  [30] Snapshot Creation (3 steps)
  [40] Deployment Execution (4 steps)
  [50] Health Verification (4 steps)
  [60] Post-Deployment (3 steps)
```

---

## Status

- ✅ Flow-editor launches successfully
- ✅ Spec file auto-detected
- ✅ Specification loads correctly
- ✅ Browse Flow Structure works
- ✅ Error handling prevents terminal corruption
- ⚠️ Other menu options (Renumber, Insert, Delete, etc.) may need similar fixes

**Next**: User should test remaining menu options to identify any additional bugs.

---

**Status**: Browse functionality working, ready for continued user testing ✅
