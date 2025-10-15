#!/usr/bin/env python3
"""
Test flow-editor browse functionality without interactive UI
"""

import sys
from pathlib import Path

# Add control-flow engine to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "control-flow" / "src"))

from control_flow_engine.core.engine import ControlFlowManager

def test_browse():
    """Test that we can load and browse the spec."""
    spec_file = Path(__file__).parent.parent / "design_specs" / "control_flows.yml"
    
    print(f"Loading spec from: {spec_file}")
    
    manager = ControlFlowManager(spec_file=spec_file)
    manager.load_specification()
    
    spec = manager.get_specification()
    
    print("\n" + "=" * 70)
    print("  Specification Loaded Successfully")
    print("=" * 70)
    
    # Test structure
    print(f"\nTop-level keys: {list(spec.keys())}")
    
    phases_dict = spec.get('phases', {})
    print(f"\nPhases found: {len(phases_dict)}")
    
    for phase_id, phase_data in phases_dict.items():
        seq = phase_data.get('sequence', 0)
        name = phase_data.get('name', 'Unknown')
        steps = phase_data.get('steps', [])
        print(f"  [{seq}] {name} ({len(steps)} steps)")
    
    print("\n✅ Browse test passed!")
    return True

if __name__ == '__main__':
    try:
        test_browse()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
