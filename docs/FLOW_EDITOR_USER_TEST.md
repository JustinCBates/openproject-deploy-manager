# Flow-Editor User Testing Guide

## ✅ STATUS: BROWSE FUNCTION WORKING

**Launch Command:**

```bash
cd /opt/openproject/external/control-flow && python3 bin/flow-editor /opt/openproject/external/deploy-manager
```

### Fixes Applied (6 bugs fixed)
- ✅ Fixed import bug (manager → engine)
- ✅ Fixed spec_file argument missing
- ✅ Added automatic control_flows.yml detection
- ✅ Fixed flow_name attribute error in header
- ✅ Added get_specification() method to ControlFlowManager
- ✅ Rewrote _browse_flow() to handle deploy-manager spec structure
- ✅ Enhanced error handling to prevent terminal corruption

### ✅ Tested & Working
- **Browse Flow Structure** - Displays all 6 phases with 24 steps correctly

### ⚠️ Not Yet Tested
- Renumber Sequences
- Insert Phase/Step
- Delete Phase/Step
- View History
- Rollback Changes

**Please test the remaining menu options and report any errors!**

---

## What to Test

### 1. **Navigation & Browsing**
- Browse through the 6 phases
- View the 24 steps across phases
- Navigate the menu system
- Check if the structure is clear and intuitive

### 2. **Visualization**
- How are phases displayed?
- How are steps displayed within phases?
- Can you see the flow sequence clearly?
- Is the relationship between phases/steps/units visible?

### 3. **Information Display**
- Are descriptions helpful?
- Can you see step metadata (sequence, status, units)?
- Is library/unit information accessible?
- Are entry points and flows visible?

### 4. **Editing Features (if available)**
- Can you add/edit/delete phases?
- Can you add/edit/delete steps?
- Can you reorder steps?
- Can you change step properties?

### 5. **Usability**
- Is the interface intuitive?
- Are the keyboard shortcuts clear?
- Is help documentation available?
- How easy is it to accomplish tasks?

---

## Discussion Topics

After testing, we'll discuss:

### ✅ What Works Well
- Features that are useful
- UI elements that are clear
- Workflows that feel natural

### ⚠️ What's Confusing
- Unclear navigation
- Missing context
- Unexpected behavior

### 🎯 Features to Add to Control-Flow Backlog
Priority features for enhancement:

1. **Visualization Improvements**
   - [ ] Flow diagram/graph view
   - [ ] Step dependency visualization
   - [ ] Library unit usage heatmap
   - [ ] Phase timeline view

2. **Editing Capabilities**
   - [ ] Bulk operations (move/copy multiple steps)
   - [ ] Template-based step creation
   - [ ] Duplicate detection
   - [ ] Validation on save

3. **Search & Filter**
   - [ ] Search across all phases/steps
   - [ ] Filter by status (planned/in-progress/implemented)
   - [ ] Filter by library usage
   - [ ] Jump to definition

4. **Documentation**
   - [ ] Inline help for each section
   - [ ] Examples and templates
   - [ ] Best practices guide
   - [ ] Export to different formats

5. **Integration Features**
   - [ ] Git integration (see changes)
   - [ ] Export to Markdown/HTML
   - [ ] Import from other formats
   - [ ] Diff viewer

6. **Analysis Tools**
   - [ ] Complexity metrics
   - [ ] Coverage reports (implemented vs planned)
   - [ ] Dependency analysis
   - [ ] Dead code detection

### 🔧 UX Improvements
- Color scheme preferences
- Keyboard shortcut customization
- Multi-panel view
- Breadcrumb navigation
- Undo/redo functionality

---

## Notes Template

Use this to capture your observations:

### Initial Impressions
```
First reaction:
Ease of launch:
Initial confusion:
```

### Feature Testing

#### Navigation
```
✅ Works well:
❌ Doesn't work:
💡 Suggestions:
```

#### Display/Visualization
```
✅ Works well:
❌ Doesn't work:
💡 Suggestions:
```

#### Editing
```
✅ Works well:
❌ Doesn't work:
💡 Suggestions:
```

### Priority Feature Requests
```
1. [High Priority]
2. [High Priority]
3. [Medium Priority]
4. [Medium Priority]
5. [Low Priority]
```

### Bugs Found
```
1.
2.
3.
```

---

## After Testing

We'll create:
1. **Bug reports** for any issues found
2. **Feature backlog** for control-flow repo
3. **UX improvement plan** based on feedback
4. **Documentation updates** if needed

---

## Quick Reference: Current Spec Stats

- **Phases**: 6 (Preflight, Template Rendering, Snapshot, Deployment, Health Verification, Post-Deployment)
- **Steps**: 24 total across all phases
- **Libraries**: 10 domains (config, docker, templates, health, network, system, snapshot, prober, reporting, cleanup)
- **Units**: 28 reusable units
- **Entry Points**: 7 (cli, deploy, rollback, health, validate, template, status)
- **Flows**: 3 (main_deployment_flow, rollback_flow, validation_only_flow)

This should give you a baseline to compare what the tool displays.

---

**Ready to test!** 🚀

Run the command and explore the interface. Take notes on what you find!
