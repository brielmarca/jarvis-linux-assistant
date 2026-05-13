# Workflows

## Overview

Workflows allow you to chain multiple actions into reusable automation sequences. Each workflow consists of named steps with actions, parameters, and optional scheduling.

## Built-in Templates

### Programming Mode
Opens terminal, VSCode, and launches a coding session.
```
steps:
  - action: command
    params: {command: "open terminal"}
  - action: command
    params: {command: "open vscode"}
  - action: command
    params: {command: "programming mode"}
```

### Streaming Mode
Opens OBS and starts streaming configuration.
```
steps:
  - action: command
    params: {command: "open obs"}
  - action: command
    params: {command: "start streaming"}
  - action: command
    params: {command: "set volume 80"}
```

### Morning Routine
Shows system info and prepares the workspace.
```
steps:
  - action: command
    params: {command: "system info"}
  - action: wait
    params: {seconds: 2}
  - action: command
    params: {command: "open terminal"}
  - action: command
    params: {command: "open firefox"}
```

## Custom Workflows

Create from the Workflows tab in the UI:
1. Click "+ New Workflow"
2. Enter name and description
3. Add steps (one per line):
   - `open terminal` — opens an app
   - `run: ls -la` — executes a command
   - `wait: 2` — waits N seconds
4. Click Save

## Workflow Engine

### `Workflow` class
- `name`: Unique identifier
- `steps`: List of `WorkflowStep` objects
- `description`: Human-readable description
- `schedule`: Optional cron-like schedule

### `WorkflowStep` class
- `action`: Action type (command, wait, open, etc.)
- `params`: Dictionary of action parameters
- `order`: Step sequence number

### `WorkflowExecutor`
- Runs steps sequentially
- Supports async execution
- Reports step completion via events

### `WorkflowManager`
- CRUD operations (create, read, update, delete)
- JSON persistence in `~/.jarvis/workflows/`
- Listing and searching workflows
- Loading default templates

## Storage

Workflows are stored as individual JSON files:
```
~/.jarvis/workflows/
├── programming_mode.json
├── streaming_mode.json
├── morning_routine.json
└── my_custom_workflow.json
```

## API

```python
from jarvis.automation.workflows import WorkflowManager, WorkflowExecutor

mgr = WorkflowManager()

# List workflows
workflows = mgr.list_workflows()

# Create workflow
mgr.create_workflow("my_wf", steps, description="Custom workflow")

# Get workflow
wf = mgr.get_workflow("my_wf")

# Execute workflow
executor = WorkflowExecutor(wf)
executor.run()

# Delete workflow
mgr.delete_workflow("my_wf")

# Load default templates
from jarvis.automation.workflows import load_default_templates
load_default_templates()
```
