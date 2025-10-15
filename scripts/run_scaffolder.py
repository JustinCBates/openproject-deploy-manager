#!/usr/bin/env python3
"""
Run scaffolder to generate deploy-manager directory structure.

This script uses the control-flow scaffolding generator to create:
- All 6 phase directories
- All 24 step directories
- Library structure with 28 units
- Phase orchestrators
- Step implementation stubs
- README files
"""

import sys
from pathlib import Path

# Add control-flow engine to path
control_flow_path = Path(__file__).parent.parent.parent / "control-flow" / "src"
sys.path.insert(0, str(control_flow_path))

from control_flow_engine.scaffolding.generator import ScaffoldGenerator


def main():
    """Run the scaffolder."""
    # Paths
    project_root = Path(__file__).parent.parent
    spec_file = project_root / "design_specs" / "control_flows.yml"
    output_dir = project_root
    
    print("\n" + "=" * 70)
    print("  Deploy-Manager Scaffolding Generator")
    print("=" * 70)
    print(f"  Spec file: {spec_file}")
    print(f"  Output directory: {output_dir}")
    print("=" * 70 + "\n")
    
    # Verify spec file exists
    if not spec_file.exists():
        print(f"❌ Error: Specification file not found: {spec_file}")
        sys.exit(1)
    
    # Create generator
    generator = ScaffoldGenerator(spec_file=spec_file, output_dir=output_dir)
    
    # First, do a dry run to show what will be generated
    print("📋 Preview (dry run):\n")
    
    try:
        preview = generator.generate_scaffolding(dry_run=True)
        
        print(f"Directories to create: {len(preview.get('directories', []))}")
        print(f"Phase files to create: {len(preview.get('phase_files', []))}")
        print(f"Step files to create: {len(preview.get('step_files', []))}")
        print(f"Output files to create: {len(preview.get('output_files', []))}")
        print(f"Test files to create: {len(preview.get('test_files', []))}")
        
        print("\n" + "-" * 70)
        print("Directory structure:")
        print("-" * 70)
        
        for directory in preview.get('directories', [])[:20]:  # Show first 20
            print(f"  {directory}")
        
        if len(preview.get('directories', [])) > 20:
            print(f"  ... and {len(preview.get('directories', [])) - 20} more")
        
        print("\n" + "-" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during preview: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Ask for confirmation
    print("\n" + "=" * 70)
    response = input("Proceed with scaffolding? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n⚠️  Scaffolding cancelled by user.")
        sys.exit(0)
    
    # Generate actual scaffolding
    print("\n⏳ Generating scaffolding...\n")
    
    try:
        result = generator.generate_scaffolding(dry_run=False)
        
        print("\n" + "=" * 70)
        print("  Scaffolding Complete!")
        print("=" * 70)
        
        print(f"\n📁 Created {len(result.get('directories', []))} directories")
        print(f"📄 Created {len(result.get('phase_files', []))} phase files")
        print(f"📄 Created {len(result.get('step_files', []))} step files")
        print(f"📄 Created {len(result.get('output_files', []))} output files")
        print(f"🧪 Created {len(result.get('test_files', []))} test files")
        
        if result.get('entry_point'):
            print(f"🚪 Created {len(result['entry_point'])} entry point(s)")
        
        if result.get('metadata'):
            print(f"📋 Created {len(result['metadata'])} metadata file(s)")
        
        print("\n" + "=" * 70)
        print("✅ Scaffolding generation successful!")
        print("=" * 70)
        
        print("\nNext steps:")
        print("  1. Review generated structure in phases/")
        print("  2. Implement units in phases/libraries/")
        print("  3. Implement step logic in phase_*/steps/")
        print("  4. Implement phase orchestrators")
        print("  5. Implement global orchestrator")
        print("  6. Create CLI wrapper")
        
    except Exception as e:
        print(f"\n❌ Error during scaffolding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
