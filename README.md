# packtool

Modpack automation tool for Fabric modpacks on Modrinth.

## Overview

Automates the creation and publishing of two Fabric modpacks:
- **IceCreamSundae** (full)
- **IceCreamMondae** (lite)

Both are based on the Fabulously Optimized parent pack.

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
├── manifest/                 # What Telos wants
│   └── packs.yaml           # Pack settings
├── configs/                 # Config layers
│   ├── base/               # Default configs
│   └── mc-<version>/       # Version-specific configs
├── state/                   # Runtime state (tracked)
│   ├── uploads.json        # Last uploads
│   ├── queue.json          # Queue items
│   └── runs/               # Run reports
├── lock/                    # Lock files (tracked)
│   └── <mc>_<edition>.json # Queued/uploaded mods
├── build/                   # Build outputs (ignored)
├── source/                  # Source code
└── tests/                   # Tests
```

## Manifest Files

### manifest/packs.yaml
```yaml
settings:
  loader: fabric
  channel: release
  completeness:
    release_at: 95
    beta_at: 70
    alpha_at: 50
publish:
  auto_publish: false  # Upload as draft first
notify:
  ntfy_email: true
packs:
  full:
    name: IceCreamSundae
    modrinth_project_id: TODO  # Fill this in
  lite:
    name: IceCreamMondae
    name_template: "{name} {mc}"
    modrinth_project_id: TODO  # Fill this in
    icon: assets/lite.png
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
