# packtool

Modpack automation tool for Fabric modpacks on Modrinth.

## Overview

Automates the creation and publishing of two Fabric modpacks:
- **IceCreamSundae** (full)
- **IceCreamMondae** (lite)

Both are based on the Fabulously Optimized parent pack.

## Development Status

**Phase 4**: Builder and static checks for both editions implemented

- ✅ `pyproject.toml` - dependencies and entry point
- ✅ `models.py` - Pydantic data models
- ✅ `mcversion.py` - Mojang version manifest client
- ✅ `state.py` - State management (uploads, queue, runs, parent)
- ✅ `lock.py` - Lock file management
- ✅ `runlog.py` - Run report management
- ✅ `cli.py` - Command-line interface
- ✅ `manifest/mods.yaml` - Seed mod configuration
- ✅ `modrinth.py` - Modrinth API client (Phase 3)
- ✅ `resolver.py` - Mod list resolver with completeness (Phase 3)
- ✅ `builder.py` - Pack builder for both editions (Phase 4)
- ✅ `checks.py` - Static checks and validation (Phase 4)

## Quick Start

```bash
# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .

# Configure (see .env.example)
cp .env.example ~/.config/packtool/env
nano ~/.config/packtool/env  # Fill in tokens

# Run
packtool --help
```

## Commands

### `packtool --check`
Main automation command. Does:
1. Discovers new Minecraft versions
2. Checks parent pack versions
3. Resolves mod lists
4. Builds packs
5. Tests builds
6. Queues ready builds

### `packtool --discover`
Discover new Minecraft releases from Mojang.

### `packtool --resolve`
Resolve mod list for a specific Minecraft version.

### `packtool --build`
Build .mrpack files for all active versions.

### `packtool --test`
Test builds (static checks, server boot, client boot).

### `packtool --queue`
Queue ready builds.

### `packtool --publish`
Publish queued builds to Modrinth.

### `packtool --capture`
Capture config changes from the game.

### `packtool --status`
Show build status.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MODRINTH_TOKEN` | Yes | Modrinth API token (create versions scope) |
| `GITHUB_TOKEN` | Yes | GitHub token for PR creation |
| `NTFY_TOPIC` | Yes | ntfy topic for alerts |

## Directory Structure

```
.
├── manifest/                 # Version tracking
│   └── mc-versions.yaml     # Active/candidate/retired versions
├── configs/                 # Config layers
│   ├── base/               # Default configs
│   └── mc-<version>/       # Version-specific configs
├── state/                   # Runtime state (gitignored)
│   ├── uploads.json        # Upload tracking
│   ├── queue.json          # Build queue
│   ├── runs.json           # Run reports
│   └── parent/             # Parent pack state
├── lock/                    # Lock files (gitignored)
│   └── <mc>_<edition>.json # Queued mods
├── build/                   # Build outputs (gitignored)
├── source/                  # Source code
└── tests/                   # Tests
```

## Testing

```bash
# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest --cov=source/ -v
```

## License

See LICENSE.md

## Project Phases

This project follows the phases defined in [AutomatedModpackTool.md](AutomatedModpackTool.md):

- **P0 (Completed)**: Spikes S1-S7 for boot testing, parent handling, and pack building
- **P1 (Completed)**: Boot harness on hand-made test pack
- **P2 (Completed)**: Skeleton implementation
  - Core modules: `pyproject`, `models`, `mcversion`, `state`, `runlog`, `lock`, `cli`
  - Seed `mods.yaml` with basic mod configuration
- **P3 (Completed)**: Modrinth API and resolver as read-only report
  - `modrinth.py`: Query Modrinth for mod builds
  - `resolver.py`: Resolve mods with fallbacks, companions, completeness
  - `--report` command: Generate human-readable reports
- **P4 (Completed)**: Builder and static checks for both editions
  - `builder.py`: Build both full and lite editions
  - `checks.py`: Static validation of pack index and structure
  - `--build` command: Build and validate both editions
- **P5-P11**: Remaining phases for parent handling, tests, config, queue, publish, etc.

## Source Modules

| Module | Status | Description |
|--------|--------|-------------|
| `cli.py` | ✅ | Command-line interface |
| `models.py` | ✅ | Pydantic data models |
| `mcversion.py` | ✅ | Mojang version manifest client |
| `modrinth.py` | ✅ | Modrinth API client |
| `resolver.py` | ✅ | Mod list resolver |
| `builder.py` | ✅ | Pack builder for both editions (P4) |
| `checks.py` | ✅ | Static checks and validation (P4) |
| `state.py` | ✅ | State management |
| `lock.py` | ✅ | Lock file management |
| `runlog.py` | ✅ | Run report management |
| `configs.py` | ✅ | Config layer management |
| `launcher.py` | ✅ | Game launcher |
| `installer.py` | ✅ | Pack installer |

## Directory Structure
