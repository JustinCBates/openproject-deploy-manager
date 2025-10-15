# Template Rendering

**Sequence**: 20  
**Status**: PLANNED  

## Description

Render deployment templates with configuration values

## Steps

### [10] Extract Template Variables
**Status**: PLANNED  
Extract and prepare variables for template rendering

**Units**: `config.variable_extractor`

### [20] Render Caddyfile
**Status**: PLANNED  
Render Caddyfile template for reverse proxy

**Units**: `templates.jinja_renderer, templates.template_filters`

### [30] Render Docker Compose Override
**Status**: PLANNED  
Render docker-compose.override.yml with dynamic settings

**Units**: `templates.jinja_renderer`

### [40] Validate Rendered Templates
**Status**: PLANNED  
Validate syntax and completeness of rendered templates

**Units**: `templates.template_validator`


## Outputs

Directory: `outputs/templates`

- `Caddyfile`
- `docker-compose.override.yml`
- `rendered_templates/`

## Usage

```python
from phases.phase_2_template_rendering.phase_2_template_rendering_orchestrator import Phase2TemplateRenderingOrchestrator

orchestrator = Phase2TemplateRenderingOrchestrator(project_root, config)
result = orchestrator.execute(context)
```
