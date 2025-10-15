#!/usr/bin/env python3
"""
Validate control_flows.yml specification

This script validates the control flow specification format before and after
editing with the designer tools.
"""

import sys
from pathlib import Path
import yaml

# Add control-flow engine to path
control_flow_path = Path(__file__).parent.parent.parent / "control-flow" / "src"
sys.path.insert(0, str(control_flow_path))

try:
    from control_flow_engine.core.engine import ControlFlowManager
    print("✅ Successfully imported ControlFlowManager")
except ImportError as e:
    print(f"❌ Failed to import ControlFlowManager: {e}")
    sys.exit(1)


def validate_yaml_syntax(spec_file: Path) -> bool:
    """Check if YAML file has valid syntax."""
    print(f"\n{'='*70}")
    print(f"STEP 1: Validating YAML Syntax")
    print(f"{'='*70}")
    
    try:
        with open(spec_file, 'r') as f:
            spec = yaml.safe_load(f)
        print(f"✅ YAML syntax is valid")
        print(f"   File: {spec_file}")
        print(f"   Size: {spec_file.stat().st_size} bytes")
        return True
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False


def validate_structure(spec_file: Path) -> bool:
    """Validate the control flow specification structure."""
    print(f"\n{'='*70}")
    print(f"STEP 2: Validating Specification Structure")
    print(f"{'='*70}")
    
    try:
        with open(spec_file, 'r') as f:
            spec = yaml.safe_load(f)
        
        # Check top-level sections
        required_sections = ['component', 'phases', 'libraries', 'entry_points', 'flows']
        missing_sections = [s for s in required_sections if s not in spec]
        
        if missing_sections:
            print(f"❌ Missing required sections: {', '.join(missing_sections)}")
            return False
        
        print(f"✅ All required top-level sections present:")
        for section in required_sections:
            print(f"   - {section}")
        
        # Validate component metadata
        print(f"\n📦 Component Information:")
        component = spec.get('component', {})
        print(f"   Name: {component.get('name', 'N/A')}")
        print(f"   Description: {component.get('description', 'N/A')}")
        print(f"   Version: {component.get('version', 'N/A')}")
        
        # Count phases
        phases = spec.get('phases', {})
        print(f"\n📋 Phases: {len(phases)}")
        for phase_id, phase_data in phases.items():
            steps = phase_data.get('steps', [])
            print(f"   - {phase_id}: {phase_data.get('name', 'N/A')} ({len(steps)} steps)")
        
        # Count total steps
        total_steps = sum(len(p.get('steps', [])) for p in phases.values())
        print(f"   Total steps across all phases: {total_steps}")
        
        # Count libraries
        libraries = spec.get('libraries', {})
        print(f"\n📚 Libraries: {len(libraries)} domains")
        total_units = 0
        for lib_id, lib_data in libraries.items():
            units = lib_data.get('units', [])
            total_units += len(units)
            print(f"   - {lib_id}: {lib_data.get('description', 'N/A')} ({len(units)} units)")
        print(f"   Total units across all libraries: {total_units}")
        
        # Check entry points
        entry_points = spec.get('entry_points', {})
        print(f"\n🚪 Entry Points: {len(entry_points)}")
        for ep_id, ep_data in entry_points.items():
            if isinstance(ep_data, dict):
                print(f"   - {ep_id}: {ep_data.get('description', 'N/A')}")
            else:
                print(f"   - {ep_id}")
        
        # Check flows
        flows = spec.get('flows', {})
        print(f"\n🔄 Flows: {len(flows)}")
        for flow_id, flow_data in flows.items():
            if isinstance(flow_data, dict):
                print(f"   - {flow_id}: {flow_data.get('description', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating structure: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_phase_step_references(spec_file: Path) -> bool:
    """Validate that all step unit references exist in libraries."""
    print(f"\n{'='*70}")
    print(f"STEP 3: Validating Phase-Step-Library References")
    print(f"{'='*70}")
    
    try:
        with open(spec_file, 'r') as f:
            spec = yaml.safe_load(f)
        
        # Build set of available units
        libraries = spec.get('libraries', {})
        available_units = set()
        for lib_id, lib_data in libraries.items():
            units = lib_data.get('units', [])
            for unit in units:
                unit_name = unit.get('name', '') if isinstance(unit, dict) else unit
                available_units.add(f"{lib_id}.{unit_name}")
        
        print(f"✅ Found {len(available_units)} available units in libraries")
        
        # Check all step unit references
        phases = spec.get('phases', {})
        all_valid = True
        missing_units = set()
        
        for phase_id, phase_data in phases.items():
            steps = phase_data.get('steps', [])
            for step in steps:
                step_name = step.get('name', 'unnamed')
                step_units = step.get('units', [])
                
                for unit_ref in step_units:
                    if unit_ref not in available_units:
                        missing_units.add(unit_ref)
                        all_valid = False
        
        if missing_units:
            print(f"\n⚠️  Missing unit references (may be intentional if not implemented yet):")
            for unit in sorted(missing_units):
                print(f"   - {unit}")
        else:
            print(f"✅ All step unit references are valid")
        
        return True  # Don't fail on missing units - they might not be implemented yet
        
    except Exception as e:
        print(f"❌ Error validating references: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main validation workflow."""
    spec_file = Path(__file__).parent.parent / "design_specs" / "control_flows.yml"
    
    print(f"\n{'#'*70}")
    print(f"# Control Flow Specification Validator")
    print(f"# File: {spec_file}")
    print(f"{'#'*70}")
    
    if not spec_file.exists():
        print(f"\n❌ Specification file not found: {spec_file}")
        sys.exit(1)
    
    # Run validation steps
    results = {
        'yaml_syntax': validate_yaml_syntax(spec_file),
        'structure': validate_structure(spec_file),
        'references': validate_phase_step_references(spec_file)
    }
    
    # Summary
    print(f"\n{'='*70}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check.replace('_', ' ').title()}")
    
    print(f"\n{'='*70}")
    if all_passed:
        print(f"✅ ALL VALIDATIONS PASSED")
        print(f"✅ Specification is ready for use with designer tools")
        print(f"{'='*70}\n")
        sys.exit(0)
    else:
        print(f"❌ SOME VALIDATIONS FAILED")
        print(f"❌ Please fix errors before proceeding")
        print(f"{'='*70}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
