# Firefly Studio

**Visual agent IDE for the Firefly GenAI framework.**

Firefly Studio is a browser-based development environment for building,
testing, and debugging GenAI agent pipelines. It provides a visual canvas
where you drag and connect agent nodes, configure them through a side panel,
and see generated Python code update in real time. An integrated AI assistant
helps you build pipelines through natural language.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [The Canvas](#the-canvas)
- [Node Types](#node-types)
- [Code Generation](#code-generation)
- [AI Assistant](#ai-assistant)
- [Project Management](#project-management)
- [Pipeline Execution](#pipeline-execution)
- [Checkpoints & Time-Travel Debugging](#checkpoints--time-travel-debugging)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [REST API Reference](#rest-api-reference)
- [WebSocket API Reference](#websocket-api-reference)
- [Programmatic Usage](#programmatic-usage)
- [Frontend Development](#frontend-development)

---

## Installation

Firefly Studio is included in the `[studio]` extra:

```bash
# Install with Studio support
pip install "fireflyframework-genai[studio]"

# Or with UV
uv add "fireflyframework-genai[studio]"

# Or install everything
pip install "fireflyframework-genai[all]"
```

The `[studio]` extra installs:

| Dependency | Purpose |
|---|---|
| `fastapi` | REST API and WebSocket server |
| `uvicorn[standard]` | ASGI server |
| `httpx` | HTTP client for internal API calls |

The Studio frontend is pre-built and bundled inside the Python package.
No Node.js is required to run Studio.

---

## Quick Start

```bash
# Launch Studio (opens browser automatically)
firefly studio

# Or from Python
python -c "from fireflyframework_genai.studio import launch_studio; launch_studio()"
```

Studio starts at `http://127.0.0.1:8470` by default and opens your browser.
You'll see a dark-themed IDE with a visual canvas, a component palette on
the left, a configuration panel on the right, and a bottom panel with code
generation, console, timeline, and AI assistant tabs.

---

## CLI Reference

The `firefly` command is installed as a console script entry point.

```
firefly studio [OPTIONS]
firefly [OPTIONS]          # "studio" is the default subcommand
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--port PORT` | `8470` | Port the Studio server listens on |
| `--host HOST` | `127.0.0.1` | Address the server binds to |
| `--no-browser` | `false` | Do not open the browser automatically |
| `--dev` | `false` | Enable development mode (verbose logging) |

### Examples

```bash
# Default launch
firefly studio

# Custom port, no browser
firefly studio --port 9000 --no-browser

# Bind to all interfaces (for remote access)
firefly studio --host 0.0.0.0

# Shorthand (omit "studio")
firefly --port 9000
```

---

## Configuration

Studio uses Pydantic Settings with the `FIREFLY_STUDIO_` prefix for
environment variable overrides.

### StudioConfig Fields

| Field | Type | Default | Env Variable |
|---|---|---|---|
| `host` | `str` | `"127.0.0.1"` | `FIREFLY_STUDIO_HOST` |
| `port` | `int` | `8470` | `FIREFLY_STUDIO_PORT` |
| `open_browser` | `bool` | `True` | `FIREFLY_STUDIO_OPEN_BROWSER` |
| `dev_mode` | `bool` | `False` | `FIREFLY_STUDIO_DEV_MODE` |
| `projects_dir` | `Path` | `~/.firefly-studio/projects` | `FIREFLY_STUDIO_PROJECTS_DIR` |
| `log_level` | `str` | `"info"` | `FIREFLY_STUDIO_LOG_LEVEL` |

### Environment Variable Example

```bash
export FIREFLY_STUDIO_PORT=9000
export FIREFLY_STUDIO_PROJECTS_DIR=/data/studio/projects
export FIREFLY_STUDIO_DEV_MODE=true
firefly studio
```

---

## Architecture

Studio is composed of a Python backend (FastAPI) and a SvelteKit 5 frontend
that compiles to a static SPA and is bundled inside the Python package.

```
                   Browser
                     |
          +---------+---------+
          |  SvelteKit SPA    |   (bundled in studio/static/)
          |  @xyflow/svelte   |
          |  Svelte 5 runes   |
          +---------+---------+
                     |
           REST + WebSocket
                     |
          +---------+---------+
          |  FastAPI Backend   |
          |                    |
          |  /api/projects     |   Project CRUD
          |  /api/registry     |   Agent/tool/pattern discovery
          |  /api/codegen      |   Python code generation
          |  /api/monitoring   |   Usage metrics
          |  /api/checkpoints  |   Checkpoint management
          |  /ws/execution     |   Pipeline execution (WebSocket)
          |  /ws/assistant     |   AI assistant chat (WebSocket)
          +---------+---------+
                     |
          +---------+---------+
          |  Framework Core    |
          |  Agents, Tools,    |
          |  Pipelines, etc.   |
          +--------------------+
```

### Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Frontend framework | SvelteKit 5 | Runes reactivity, small bundles, excellent DX |
| Canvas library | @xyflow/svelte | Mature node graph library with drag/drop, zoom |
| Backend | FastAPI | Async, WebSocket support, Pydantic integration |
| Delivery | Bundled SPA | Single `pip install`, no Node.js in production |
| Real-time | WebSocket | Bidirectional execution events and AI chat |

---

## The Canvas

The canvas is the central workspace. Nodes represent pipeline components
and edges represent data flow between them.

### Interactions

- **Add nodes** -- Drag from the left palette, or press `Cmd+K` and type
- **Connect** -- Drag from a source handle to a target handle
- **Select** -- Click a node to open its configuration in the right panel
- **Delete** -- Select a node and press `Delete` or `Backspace`
- **Pan** -- Click and drag on empty canvas space
- **Zoom** -- Scroll wheel or pinch gesture
- **Minimap** -- Bottom-right corner for overview navigation

### Empty State

When the canvas has no nodes, an overlay displays a call-to-action
prompting you to drag components or use the command palette.

### Execution Visualization

During pipeline execution, nodes show real-time state:

| State | Visual |
|---|---|
| Idle | Default appearance |
| Running | Rotating conic-gradient border |
| Complete | Green checkmark badge |
| Error | Red error indicator |

---

## Node Types

Studio supports four node types that map to framework components:

| Node Type | Framework Class | Description |
|---|---|---|
| **Agent** | `FireflyAgent` | An LLM-powered agent with model, instructions, and tools |
| **Tool** | `BaseTool` | A tool that an agent can invoke |
| **Reasoning** | `ReasoningPattern` | A reasoning pattern (ReAct, CoT, etc.) |
| **Condition** | Conditional edge | A branching condition in the pipeline |

### Node Configuration

Click a node to open the configuration panel on the right. Available fields
depend on the node type:

- **Label** -- Display name
- **Model** -- LLM model string (e.g., `openai:gpt-4o`)
- **Instructions** -- System prompt / instructions
- **Additional fields** -- Type-specific configuration

---

## Code Generation

The **Code** tab in the bottom panel shows Python code generated from
the current canvas graph. Code updates automatically when nodes or edges
change (debounced by 800ms).

### Features

- **Auto-sync** -- Toggle on/off with the Auto button
- **Manual regenerate** -- Click the refresh button
- **Copy to clipboard** -- Click the copy button
- **Syntax highlighting** -- Python-aware syntax coloring (One Dark theme)
- **Line numbers** -- Numbered lines for easy reference

### Generated Code Structure

```python
from fireflyframework_genai.agents import FireflyAgent

# Agent definitions
agent_1 = FireflyAgent(
    name="agent-1",
    model="openai:gpt-4o",
    instructions="...",
)

# Pipeline (when edges exist)
from fireflyframework_genai.pipeline.builder import PipelineBuilder

pipeline = (
    PipelineBuilder("studio-pipeline")
    .add_node("agent-1", AgentStep(agent_1))
    .add_node("agent-2", AgentStep(agent_2))
    .chain("agent-1", "agent-2")
    .build()
)
```

---

## AI Assistant

The **Chat** tab in the bottom panel provides an AI-powered assistant that
can help you build pipelines through natural language conversation.

### Capabilities

The assistant can:
- Add, remove, and configure nodes on the canvas
- Connect nodes with edges
- List current nodes and edges
- Explain pipeline concepts
- Suggest pipeline architectures

### Requirements

The AI assistant requires a configured LLM provider. Set one of these
environment variables:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

The assistant uses the framework's default model (`FIREFLY_GENAI_DEFAULT_MODEL`).

### Canvas Tools

The assistant has access to six canvas manipulation tools:

| Tool | Description |
|---|---|
| `add_node` | Add a node (agent, tool, reasoning, condition) |
| `connect_nodes` | Create an edge between two nodes |
| `configure_node` | Update a node's model, instructions, or label |
| `remove_node` | Remove a node from the canvas |
| `list_nodes` | List all current nodes |
| `list_edges` | List all current edges |

---

## Project Management

Studio persists projects as directories on disk under the configured
`projects_dir` (default: `~/.firefly-studio/projects/`).

### Project Structure

```
~/.firefly-studio/projects/
  my-project/
    project.json          # name, description, created_at
    pipelines/
      main-pipeline.json  # saved graph (nodes + edges)
      backup.json
  another-project/
    project.json
    pipelines/
```

### Operations

| Action | API | Description |
|---|---|---|
| List | `GET /api/projects` | List all projects |
| Create | `POST /api/projects` | Create a new project |
| Delete | `DELETE /api/projects/{name}` | Delete a project |
| Save pipeline | `POST /api/projects/{project}/pipelines/{name}` | Save graph |
| Load pipeline | `GET /api/projects/{project}/pipelines/{name}` | Load graph |

---

## Pipeline Execution

The execution system uses a WebSocket connection at `/ws/execution` for
real-time pipeline execution with event streaming.

### Event Types

| Event | Fields | Description |
|---|---|---|
| `node_start` | `node_id`, `pipeline_name` | Node began executing |
| `node_complete` | `node_id`, `pipeline_name`, `latency_ms` | Node finished |
| `node_error` | `node_id`, `pipeline_name`, `error` | Node failed |
| `node_skip` | `node_id`, `pipeline_name`, `reason` | Node skipped |
| `pipeline_complete` | `pipeline_name`, `success`, `duration_ms` | Pipeline finished |

> **Note:** Pipeline execution is currently a stub. The WebSocket endpoint
> accepts connections and responds to `run`/`debug` actions, but full
> `PipelineEngine` integration is pending.

---

## Checkpoints & Time-Travel Debugging

The checkpoint system captures pipeline state at each node for debugging
and replay.

### Checkpoint API

| Endpoint | Description |
|---|---|
| `GET /api/checkpoints` | List all checkpoints |
| `GET /api/checkpoints/{index}` | Get a specific checkpoint |
| `POST /api/checkpoints/fork` | Fork execution from a checkpoint |
| `POST /api/checkpoints/diff` | Diff two checkpoints |
| `DELETE /api/checkpoints` | Clear all checkpoints |

### Checkpoint Data

Each checkpoint captures:
- `index` -- Sequential checkpoint number
- `node_id` -- Node that created it
- `state` -- Captured pipeline state
- `inputs` -- Node inputs at that point
- `timestamp` -- ISO 8601 timestamp
- `branch_id` -- Branch identifier (for forked executions)
- `parent_index` -- Parent checkpoint (for forks)

---

## Keyboard Shortcuts

### General

| Shortcut | Action |
|---|---|
| `Cmd/Ctrl + K` | Open command palette |
| `?` | Toggle keyboard shortcuts help |
| `Cmd/Ctrl + /` | Toggle AI assistant panel |

### Pipeline

| Shortcut | Action |
|---|---|
| `Cmd/Ctrl + Enter` | Run pipeline |
| `Cmd/Ctrl + Shift + D` | Debug pipeline |

### Canvas

| Shortcut | Action |
|---|---|
| `Delete` / `Backspace` | Delete selected node |
| `Cmd/Ctrl + D` | Duplicate selected node |
| `Cmd/Ctrl + +` | Zoom in |
| `Cmd/Ctrl + -` | Zoom out |

### Command Palette

The command palette (`Cmd+K`) provides fuzzy search across 25 commands
in four categories: Navigation, Add Node, Pipeline Actions, and View.

---

## REST API Reference

All REST endpoints are prefixed with `/api/`.

### Health

```
GET /api/health
```

Returns `{"status": "ok", "version": "26.02.07"}`.

### Registry

```
GET /api/registry/agents     # List registered agents
GET /api/registry/tools      # List registered tools
GET /api/registry/patterns   # List registered reasoning patterns
```

### Projects

```
GET    /api/projects                                    # List all
POST   /api/projects                                    # Create
DELETE /api/projects/{name}                             # Delete
POST   /api/projects/{project}/pipelines/{pipeline}     # Save pipeline
GET    /api/projects/{project}/pipelines/{pipeline}     # Load pipeline
```

#### Create Project Request

```json
{"name": "my-project", "description": "Optional description"}
```

#### Save Pipeline Request

```json
{"graph": {"nodes": [...], "edges": [...]}}
```

### Code Generation

```
POST /api/codegen/to-code
```

#### Request Body

```json
{
  "nodes": [
    {"id": "agent-1", "type": "agent", "label": "Classifier", "data": {"model": "openai:gpt-4o"}}
  ],
  "edges": [
    {"id": "e1", "source": "agent-1", "target": "agent-2"}
  ]
}
```

#### Response

```json
{"code": "from fireflyframework_genai.agents import FireflyAgent\n..."}
```

### Monitoring

```
GET /api/monitoring/usage    # Token usage, costs, latency summary
```

### Checkpoints

```
GET    /api/checkpoints              # List all
GET    /api/checkpoints/{index}      # Get by index
POST   /api/checkpoints/fork         # Fork from checkpoint
POST   /api/checkpoints/diff         # Diff two checkpoints
DELETE /api/checkpoints              # Clear all
```

---

## WebSocket API Reference

### Execution WebSocket

```
WS /ws/execution
```

#### Send

```json
{"action": "run", "pipeline": "my-pipeline"}
{"action": "debug", "pipeline": "my-pipeline"}
```

#### Receive

```json
{"type": "node_start", "node_id": "agent-1", "pipeline_name": "my-pipeline"}
{"type": "node_complete", "node_id": "agent-1", "pipeline_name": "my-pipeline", "latency_ms": 1234.5}
{"type": "node_error", "node_id": "agent-1", "pipeline_name": "my-pipeline", "error": "..."}
{"type": "pipeline_complete", "pipeline_name": "my-pipeline", "success": true, "duration_ms": 5678.9}
```

### Assistant WebSocket

```
WS /ws/assistant
```

#### Send

```json
{"action": "chat", "message": "Add an agent node for classification"}
{"action": "clear_history"}
```

#### Receive (streaming)

```json
{"type": "token", "content": "I'll"}
{"type": "token", "content": " add"}
{"type": "tool_call", "tool": "add_node", "args": {"type": "agent", "label": "Classifier"}}
{"type": "tool_result", "tool": "add_node", "result": "Added node agent-1"}
{"type": "done"}
```

---

## Programmatic Usage

### Launch Studio from Python

```python
from fireflyframework_genai.studio import launch_studio

# Starts the server and opens the browser
launch_studio()
```

### Embed the Studio App

```python
from fireflyframework_genai.studio.config import StudioConfig
from fireflyframework_genai.studio.server import create_studio_app

# Create a configured app instance
config = StudioConfig(port=9000, open_browser=False)
app = create_studio_app(config=config)

# Use with any ASGI server
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=9000)
```

### Use Studio with Custom Projects Directory

```python
from fireflyframework_genai.studio.config import StudioConfig
from fireflyframework_genai.studio.server import create_studio_app

config = StudioConfig(projects_dir="/data/my-studio-projects")
app = create_studio_app(config=config)
```

### Use the ProjectManager Directly

```python
from pathlib import Path
from fireflyframework_genai.studio.projects import ProjectManager

manager = ProjectManager(Path("/data/projects"))

# Create a project
info = manager.create("my-project", description="A new project")

# Save a pipeline
graph = {"nodes": [...], "edges": [...]}
manager.save_pipeline("my-project", "main", graph)

# Load it back
loaded = manager.load_pipeline("my-project", "main")
```

---

## Frontend Development

The frontend source lives in `studio-frontend/` and is a SvelteKit 5 SPA.

### Prerequisites

- Node.js 20+
- npm or pnpm

### Setup

```bash
cd studio-frontend
npm install
```

### Development Server

```bash
npm run dev
```

This starts the Vite dev server at `http://localhost:5173` with hot module
replacement. The backend CORS middleware allows this origin.

### Build for Production

```bash
npm run build
```

Output goes to `studio-frontend/build/`. Copy to the Python package:

```bash
cp -r studio-frontend/build/* src/fireflyframework_genai/studio/static/
```

### Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| SvelteKit | 2.x | Application framework |
| Svelte | 5.x | UI components (runes syntax) |
| @xyflow/svelte | 1.x | Node graph canvas |
| Tailwind CSS | 4.x | Utility-first styling |
| Lucide Svelte | Latest | Icon library |
| Vite | 7.x | Build tool |

### Project Structure

```
studio-frontend/
  src/
    routes/
      +page.svelte           # Redirect to /build
      +layout.svelte          # App shell wrapper
      build/+page.svelte      # Visual canvas (main workspace)
      evaluate/+page.svelte   # Evaluation page
      experiments/+page.svelte
      deploy/+page.svelte
      monitor/+page.svelte
      files/+page.svelte
    lib/
      components/
        layout/               # AppShell, Sidebar, TopBar, CommandPalette
        canvas/               # Canvas, NodePalette, node components
        panels/               # BottomPanel, ConfigPanel, ChatTab, CodeTab
      stores/                 # Svelte stores (pipeline, execution, ui, chat)
      api/                    # REST client, WebSocket client
      execution/              # Execution bridge
      types/                  # TypeScript type definitions
    app.css                   # Global styles and CSS custom properties
```

### Design Language

Studio uses a dark, premium developer-tool aesthetic:

- **Background:** `#0f0f17` (deep blue-black)
- **Surface:** `#16161e` (card backgrounds)
- **Accent:** `#ff6b35` (warm orange)
- **Font:** JetBrains Mono (monospace), Inter (UI)
- **Icons:** Lucide (no emojis)
- **Borders:** `1px solid #2a2a3a`
- **Reduced motion:** Respects `prefers-reduced-motion`

---

*Copyright 2026 Firefly Software Solutions Inc. Licensed under the Apache License 2.0.*
