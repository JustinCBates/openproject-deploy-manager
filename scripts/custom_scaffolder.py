#!/usr/bin/env python3
"""
Custom scaffolder for deploy-manager control_flows.yml format.

Our spec has phases as top-level dict (not under flows), so we need
a custom scaffolder to handle this structure.
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any


def load_spec(spec_file: Path) -> Dict[str, Any]:
    """Load control flow specification."""
    with open(spec_file, 'r') as f:
        return yaml.safe_load(f)


def create_phase_structure(
    project_root: Path,
    phase_id: str,
    phase_data: Dict[str, Any],
    dry_run: bool = False
) -> Dict[str, List[Path]]:
    """Create directory structure for a single phase."""
    
    sequence = phase_data.get('sequence', 0)
    name = phase_data.get('name', 'Unnamed Phase')
    description = phase_data.get('description', '')
    status = phase_data.get('status', 'PLANNED')
    steps = phase_data.get('steps', [])
    outputs_dir = phase_data.get('outputs', {}).get('directory', f'outputs/{phase_id}')
    
    # Phase directory
    phase_dir = project_root / "phases" / phase_id
    
    result = {
        'directories': [phase_dir],
        'files': []
    }
    
    # Create phase directory
    if not dry_run:
        phase_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {phase_dir}")
    else:
        print(f"   Would create: {phase_dir}")
    
    # Create outputs directory
    outputs_path = phase_dir / "outputs"
    result['directories'].append(outputs_path)
    if not dry_run:
        outputs_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {outputs_path}")
    else:
        print(f"   Would create: {outputs_path}")
    
    # Create phase orchestrator
    orchestrator_file = phase_dir / f"{phase_id}_orchestrator.py"
    orchestrator_content = f'''#!/usr/bin/env python3
"""
{name}
Sequence: {sequence}
Status: {status}

{description}
"""

from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class {to_class_name(phase_id)}Orchestrator:
    """
    {name}
    
    Status: {status}
    Sequence: {sequence}
    
    {description}
    """
    
    PHASE_ID = "{phase_id}"
    PHASE_SEQUENCE = {sequence}
    PHASE_NAME = "{name}"
    
    def __init__(self, project_root: Path, config: Dict[str, Any]):
        """
        Initialize {name}.
        
        Args:
            project_root: Root directory of the project
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config
        self.phase_dir = project_root / "phases" / "{phase_id}"
        self.outputs_dir = self.phase_dir / "outputs"
        
        # Ensure outputs directory exists
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute {name}.
        
        Args:
            context: Execution context from previous phases
            
        Returns:
            Dict with phase results and artifacts
        """
        logger.info("=" * 70)
        logger.info(f"{{self.PHASE_NAME}}")
        logger.info("=" * 70)
        
        result = {{
            "phase_id": self.PHASE_ID,
            "status": "success",
            "artifacts": {{}},
            "messages": []
        }}
        
        # TODO: Implement phase logic
        # Execute steps in sequence:
{generate_step_calls(steps)}
        
        return result
    
{generate_step_methods(steps)}

def main():
    """Test the phase orchestrator."""
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent.parent
    config = {{}}
    context = {{}}
    
    orchestrator = {to_class_name(phase_id)}Orchestrator(project_root, config)
    result = orchestrator.execute(context)
    
    print(f"Phase result: {{result}}")


if __name__ == '__main__':
    main()
'''
    
    result['files'].append(orchestrator_file)
    if not dry_run:
        orchestrator_file.write_text(orchestrator_content)
        print(f"✅ Created file: {orchestrator_file}")
    else:
        print(f"   Would create: {orchestrator_file}")
    
    # Create README for phase
    readme_file = phase_dir / "README.md"
    readme_content = f'''# {name}

**Sequence**: {sequence}  
**Status**: {status}  

## Description

{description}

## Steps

{generate_steps_readme(steps)}

## Outputs

Directory: `{outputs_dir}`

{generate_outputs_readme(phase_data.get('outputs', {}))}

## Usage

```python
from phases.{phase_id}.{phase_id}_orchestrator import {to_class_name(phase_id)}Orchestrator

orchestrator = {to_class_name(phase_id)}Orchestrator(project_root, config)
result = orchestrator.execute(context)
```
'''
    
    result['files'].append(readme_file)
    if not dry_run:
        readme_file.write_text(readme_content)
        print(f"✅ Created file: {readme_file}")
    else:
        print(f"   Would create: {readme_file}")
    
    # Create __init__.py
    init_file = phase_dir / "__init__.py"
    init_content = f'''"""
{name}
"""

from .{phase_id}_orchestrator import {to_class_name(phase_id)}Orchestrator

__all__ = ['{to_class_name(phase_id)}Orchestrator']
'''
    
    result['files'].append(init_file)
    if not dry_run:
        init_file.write_text(init_content)
        print(f"✅ Created file: {init_file}")
    else:
        print(f"   Would create: {init_file}")
    
    return result


def create_libraries_structure(
    project_root: Path,
    libraries: Dict[str, Any],
    dry_run: bool = False
) -> Dict[str, List[Path]]:
    """Create library structure."""
    
    libraries_dir = project_root / "phases" / "libraries"
    
    result = {
        'directories': [libraries_dir],
        'files': []
    }
    
    if not dry_run:
        libraries_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {libraries_dir}")
    else:
        print(f"   Would create: {libraries_dir}")
    
    # Create main __init__.py
    main_init = libraries_dir / "__init__.py"
    main_init_content = '''"""
Reusable library units for deploy-manager.
"""
'''
    
    result['files'].append(main_init)
    if not dry_run:
        main_init.write_text(main_init_content)
        print(f"✅ Created file: {main_init}")
    else:
        print(f"   Would create: {main_init}")
    
    # Create each library domain
    for lib_id, lib_data in libraries.items():
        lib_dir = libraries_dir / lib_id
        description = lib_data.get('description', '')
        units = lib_data.get('units', [])
        
        result['directories'].append(lib_dir)
        if not dry_run:
            lib_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {lib_dir}")
        else:
            print(f"   Would create: {lib_dir}")
        
        # Create domain __init__.py
        domain_init = lib_dir / "__init__.py"
        domain_init_content = f'''"""
{description}
"""

# Import all units
{generate_unit_imports(units)}

__all__ = [
{generate_unit_exports(units)}
]
'''
        
        result['files'].append(domain_init)
        if not dry_run:
            domain_init.write_text(domain_init_content)
            print(f"✅ Created file: {domain_init}")
        else:
            print(f"   Would create: {domain_init}")
        
        # Create each unit file
        for unit in units:
            if isinstance(unit, dict):
                unit_name = unit.get('name', 'unnamed')
                unit_desc = unit.get('description', '')
                unit_methods = unit.get('methods', [])
            else:
                unit_name = unit
                unit_desc = ''
                unit_methods = []
            
            unit_file = lib_dir / f"{unit_name}.py"
            unit_content = generate_unit_file(unit_name, unit_desc, unit_methods)
            
            result['files'].append(unit_file)
            if not dry_run:
                unit_file.write_text(unit_content)
                print(f"✅ Created file: {unit_file}")
            else:
                print(f"   Would create: {unit_file}")
    
    return result


def generate_unit_file(unit_name: str, description: str, methods: List[str]) -> str:
    """Generate unit implementation file."""
    class_name = to_class_name(unit_name)
    
    methods_code = ""
    for method_sig in methods:
        # Parse method signature like "load(path: Path) -> Dict"
        if '(' in method_sig:
            method_name = method_sig.split('(')[0].strip()
            full_sig = method_sig
        else:
            method_name = method_sig
            full_sig = f"{method_name}()"
        
        methods_code += f'''
    def {full_sig}:
        """
        {method_name.replace('_', ' ').title()}
        
        TODO: Implement this method
        """
        raise NotImplementedError("TODO: Implement {method_name}")
'''
    
    return f'''#!/usr/bin/env python3
"""
{class_name} Unit

{description}
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class {class_name}:
    """
    {description}
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize {class_name}.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {{}}
{methods_code}


def main():
    """Test the unit."""
    unit = {class_name}()
    print(f"{{unit.__class__.__name__}} initialized")


if __name__ == '__main__':
    main()
'''


def generate_unit_imports(units: List) -> str:
    """Generate import statements for units."""
    imports = []
    for unit in units:
        if isinstance(unit, dict):
            unit_name = unit.get('name', 'unnamed')
        else:
            unit_name = unit
        
        class_name = to_class_name(unit_name)
        imports.append(f"from .{unit_name} import {class_name}")
    
    return '\n'.join(imports)


def generate_unit_exports(units: List) -> str:
    """Generate __all__ list for units."""
    exports = []
    for unit in units:
        if isinstance(unit, dict):
            unit_name = unit.get('name', 'unnamed')
        else:
            unit_name = unit
        
        class_name = to_class_name(unit_name)
        exports.append(f"    '{class_name}'")
    
    return ',\n'.join(exports)


def to_class_name(identifier: str) -> str:
    """Convert snake_case to PascalCase."""
    return ''.join(word.capitalize() for word in identifier.split('_'))


def generate_step_calls(steps: List[Dict[str, Any]]) -> str:
    """Generate step execution calls for orchestrator."""
    if not steps:
        return "        # No steps defined yet"
    
    calls = []
    for step in steps:
        seq = step.get('sequence', '?')
        name = step.get('name', 'unnamed')
        calls.append(f"        # Step {seq}: {name}")
        # Generate method call (sanitize name for method)
        method_name = name.lower().replace(' ', '_').replace('-', '_')
        calls.append(f"        step_result = self._step_{seq}_{method_name}(context)")
        calls.append(f"        result['artifacts'].update(step_result.get('artifacts', {{}}))")
        calls.append("")
    
    return '\n'.join(calls)


def generate_step_methods(steps: List[Dict[str, Any]]) -> str:
    """Generate step method stubs for orchestrator."""
    if not steps:
        return ""
    
    methods = []
    for step in steps:
        seq = step.get('sequence', '?')
        name = step.get('name', 'unnamed')
        description = step.get('description', '')
        units = step.get('units', [])
        
        method_name = name.lower().replace(' ', '_').replace('-', '_')
        
        units_import = ""
        if units:
            units_import = f"\n        # Required units: {', '.join(units)}\n        # TODO: Import and use these units"
        
        method_code = f'''
    def _step_{seq}_{method_name}(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step {seq}: {name}
        
        {description}{units_import}
        """
        logger.info(f"  Step {seq}: {name}")
        
        # TODO: Implement step logic
        
        return {{
            "status": "success",
            "artifacts": {{}},
            "messages": []
        }}
'''
        methods.append(method_code)
    
    return ''.join(methods)


def generate_steps_readme(steps: List[Dict[str, Any]]) -> str:
    """Generate steps section for README."""
    if not steps:
        return "No steps defined yet."
    
    lines = []
    for step in steps:
        seq = step.get('sequence', '?')
        name = step.get('name', 'unnamed')
        description = step.get('description', '')
        status = step.get('status', 'PLANNED')
        units = step.get('units', [])
        
        lines.append(f"### [{seq}] {name}")
        lines.append(f"**Status**: {status}  ")
        lines.append(f"{description}")
        if units:
            lines.append(f"\n**Units**: `{', '.join(units)}`")
        lines.append("")
    
    return '\n'.join(lines)


def generate_outputs_readme(outputs: Dict[str, Any]) -> str:
    """Generate outputs section for README."""
    files = outputs.get('files', [])
    if not files:
        return "No specific output files defined."
    
    lines = []
    for file_name in files:
        lines.append(f"- `{file_name}`")
    
    return '\n'.join(lines)


def main():
    """Run the custom scaffolder."""
    project_root = Path(__file__).parent.parent
    spec_file = project_root / "design_specs" / "control_flows.yml"
    
    print("\n" + "=" * 70)
    print("  Deploy-Manager Custom Scaffolder")
    print("=" * 70)
    print(f"  Spec file: {spec_file}")
    print(f"  Output directory: {project_root}")
    print("=" * 70 + "\n")
    
    if not spec_file.exists():
        print(f"❌ Error: Specification file not found: {spec_file}")
        sys.exit(1)
    
    # Load spec
    spec = load_spec(spec_file)
    
    phases = spec.get('phases', {})
    libraries = spec.get('libraries', {})
    
    print(f"📋 Found {len(phases)} phases and {len(libraries)} library domains\n")
    
    # Dry run first
    print("=" * 70)
    print("DRY RUN - Preview")
    print("=" * 70 + "\n")
    
    total_dirs = 0
    total_files = 0
    
    # Preview phases
    print("Phases:")
    for phase_id, phase_data in sorted(phases.items(), key=lambda x: x[1].get('sequence', 0)):
        result = create_phase_structure(project_root, phase_id, phase_data, dry_run=True)
        total_dirs += len(result['directories'])
        total_files += len(result['files'])
        print()
    
    # Preview libraries
    print("\nLibraries:")
    result = create_libraries_structure(project_root, libraries, dry_run=True)
    total_dirs += len(result['directories'])
    total_files += len(result['files'])
    
    print("\n" + "=" * 70)
    print(f"Summary: {total_dirs} directories, {total_files} files")
    print("=" * 70)
    
    # Ask for confirmation
    response = input("\nProceed with scaffolding? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n⚠️  Scaffolding cancelled by user.")
        sys.exit(0)
    
    # Actual generation
    print("\n" + "=" * 70)
    print("GENERATING SCAFFOLDING")
    print("=" * 70 + "\n")
    
    # Generate phases
    print("Creating phases:")
    for phase_id, phase_data in sorted(phases.items(), key=lambda x: x[1].get('sequence', 0)):
        create_phase_structure(project_root, phase_id, phase_data, dry_run=False)
        print()
    
    # Generate libraries
    print("Creating libraries:")
    create_libraries_structure(project_root, libraries, dry_run=False)
    
    print("\n" + "=" * 70)
    print("✅ SCAFFOLDING COMPLETE!")
    print("=" * 70)
    
    print("\nNext steps:")
    print("  1. Review generated structure in phases/")
    print("  2. Implement units in phases/libraries/")
    print("  3. Implement step logic in phase orchestrators")
    print("  4. Create global orchestrator (phases/global_orchestrator.py)")
    print("  5. Create CLI wrapper (cli/deploy_cli.py)")


if __name__ == '__main__':
    main()
