#!/usr/bin/env python3
"""
Simple numbered menu version of flow-editor for terminal compatibility.
"""

import sys
from pathlib import Path

# Add control-flow engine to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "control-flow" / "src"))

from control_flow_engine.core.engine import ControlFlowManager

class SimpleFlowEditor:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
        # Find spec file
        possible_locations = [
            project_root / "design_specs" / "control_flows.yml",
            project_root / "specs" / "control_flows.yml",
            project_root / "control_flows.yml",
        ]
        
        self.spec_file = None
        for spec_path in possible_locations:
            if spec_path.exists():
                self.spec_file = spec_path
                print(f"✅ Found spec file: {spec_path}")
                break
        
        if not self.spec_file:
            print("❌ Error: Could not find control_flows.yml")
            sys.exit(1)
        
        self.manager = ControlFlowManager(spec_file=self.spec_file)
        self.manager.load_specification()
    
    def print_header(self):
        print("\n" + "=" * 70)
        print("  Control Flow Editor - Simple Menu Version")
        print("=" * 70)
        print(f"  Project: {self.project_root.name}")
        print(f"  Spec File: {self.spec_file.name}")
        print("=" * 70 + "\n")
    
    def main_menu(self):
        while True:
            print("\n" + "=" * 70)
            print("  MAIN MENU")
            print("=" * 70)
            print("  1. Browse Flow Structure")
            print("  2. Show Component Info")
            print("  3. List All Phases")
            print("  4. List All Libraries")
            print("  5. List Entry Points")
            print("  6. List Flows")
            print("  0. Exit")
            print("=" * 70)
            
            choice = input("\nEnter your choice (0-6): ").strip()
            
            if choice == '0':
                print("\n✅ Goodbye!")
                break
            elif choice == '1':
                self.browse_structure()
            elif choice == '2':
                self.show_component_info()
            elif choice == '3':
                self.list_phases()
            elif choice == '4':
                self.list_libraries()
            elif choice == '5':
                self.list_entry_points()
            elif choice == '6':
                self.list_flows()
            else:
                print("❌ Invalid choice. Please enter 0-6.")
    
    def browse_structure(self):
        try:
            print("\n" + "=" * 70)
            print("  FLOW STRUCTURE")
            print("=" * 70 + "\n")
            
            spec = self.manager.get_specification()
            phases_dict = spec.get('phases', {})
            
            if not phases_dict:
                print("⚠️  No phases found.")
                return
            
            # Convert to list and sort
            phases_list = []
            for phase_id, phase_data in phases_dict.items():
                phases_list.append({
                    'id': phase_id,
                    'seq': phase_data.get('sequence', 0),
                    'name': phase_data.get('name', 'Unknown'),
                    'desc': phase_data.get('description', ''),
                    'status': phase_data.get('status', 'unknown'),
                    'steps': phase_data.get('steps', [])
                })
            
            phases_list.sort(key=lambda p: p['seq'])
            
            for phase in phases_list:
                print(f"\n[{phase['seq']}] {phase['name']}")
                print(f"    ID: {phase['id']}")
                print(f"    Status: {phase['status']}")
                print(f"    Description: {phase['desc']}")
                
                steps = phase['steps']
                if steps:
                    print(f"    Steps ({len(steps)}):")
                    sorted_steps = sorted(steps, key=lambda s: s.get('sequence', 0))
                    for step in sorted_steps:
                        seq = step.get('sequence', '?')
                        name = step.get('name', 'Unknown')
                        status = step.get('status', 'unknown')
                        units = step.get('units', [])
                        
                        print(f"      [{seq}] {name} ({status})")
                        if units:
                            print(f"          Units: {', '.join(units)}")
                else:
                    print("    (no steps)")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPress Enter to continue...")
    
    def show_component_info(self):
        try:
            spec = self.manager.get_specification()
            component = spec.get('component', {})
            
            print("\n" + "=" * 70)
            print("  COMPONENT INFORMATION")
            print("=" * 70)
            print(f"  Name: {component.get('name', 'N/A')}")
            print(f"  Version: {component.get('version', 'N/A')}")
            print(f"  Description: {component.get('description', 'N/A')}")
            print(f"  Repository: {component.get('repository', 'N/A')}")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def list_phases(self):
        try:
            spec = self.manager.get_specification()
            phases = spec.get('phases', {})
            
            print("\n" + "=" * 70)
            print(f"  PHASES ({len(phases)} total)")
            print("=" * 70)
            
            phases_list = [(pid, pdata.get('sequence', 0), pdata.get('name', 'Unknown')) 
                          for pid, pdata in phases.items()]
            phases_list.sort(key=lambda x: x[1])
            
            for pid, seq, name in phases_list:
                print(f"  [{seq:2}] {name} (ID: {pid})")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def list_libraries(self):
        try:
            spec = self.manager.get_specification()
            libraries = spec.get('libraries', {})
            
            print("\n" + "=" * 70)
            print(f"  LIBRARIES ({len(libraries)} domains)")
            print("=" * 70)
            
            for lib_id, lib_data in libraries.items():
                desc = lib_data.get('description', 'No description')
                units = lib_data.get('units', [])
                print(f"\n  {lib_id}: {desc}")
                print(f"    Units ({len(units)}): {', '.join([u.get('name', '?') if isinstance(u, dict) else u for u in units])}")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def list_entry_points(self):
        try:
            spec = self.manager.get_specification()
            entry_points = spec.get('entry_points', {})
            
            print("\n" + "=" * 70)
            print(f"  ENTRY POINTS ({len(entry_points)} total)")
            print("=" * 70)
            
            for ep_id, ep_data in entry_points.items():
                if isinstance(ep_data, dict):
                    desc = ep_data.get('description', 'No description')
                    status = ep_data.get('status', 'unknown')
                    print(f"  {ep_id}: {desc} [{status}]")
                else:
                    print(f"  {ep_id}")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def list_flows(self):
        try:
            spec = self.manager.get_specification()
            flows = spec.get('flows', {})
            
            print("\n" + "=" * 70)
            print(f"  FLOWS ({len(flows)} total)")
            print("=" * 70)
            
            for flow_id, flow_data in flows.items():
                if isinstance(flow_data, dict):
                    desc = flow_data.get('description', 'No description')
                    print(f"\n  {flow_id}:")
                    print(f"    Description: {desc}")
                    
                    phases = flow_data.get('phases', [])
                    if phases:
                        print(f"    Phases: {', '.join(phases)}")
                    
                    steps = flow_data.get('steps', [])
                    if steps:
                        print(f"    Steps: {', '.join(steps)}")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        input("\nPress Enter to continue...")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 simple_flow_editor.py <project_root>")
        sys.exit(1)
    
    project_root = Path(sys.argv[1])
    if not project_root.exists():
        print(f"❌ Error: Project root not found: {project_root}")
        sys.exit(1)
    
    editor = SimpleFlowEditor(project_root)
    editor.print_header()
    editor.main_menu()

if __name__ == '__main__':
    main()
