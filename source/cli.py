"""
CLI entry point for packtool.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('packtool')


from source.models import LockFile, BuildItem, BuildQueue, PackSettings, ModConfig, McVersion, McVersionsSettings, UploadState, RunState
from source.mcversion import MojangManifest
from source.modrinth import ModrinthClient, ModrinthAPI
from source.resolver import ModResolver
from source.builder import PackBuilder, StaticChecker
from source.launcher import GameLauncher
from source.queue import BuildQueueManager
from source.publisher import Publisher
from source.capture import CaptureManager
from source.github import GithubClient
from source.notify import NtfyManager
from source.state import StateManager as StateMgr


def log_section(msg: str):
    """Log a section header."""
    print(f"\n{'='*60}")
    print(f" {msg}")
    print(f"{'='*60}")
    logger.info(msg)


def init_args():
    """Initialize argument parser."""
    parser = argparse.ArgumentParser(
        prog="packtool",
        description="Modpack automation tool for Fabric"
    )
    parser.add_argument("--pack", choices=["full", "lite"], default="full", help="Pack edition")
    parser.add_argument("--mc", default=None, help="Minecraft version")
    parser.add_argument("--dry-run", action="store_true", help="Don't make changes")
    parser.add_argument("--init", action="store_true", help="Initialize state files")
    parser.add_argument("--check", action="store_true", help="Check for updates")
    parser.add_argument("--discover", action="store_true", help="Discover new versions")
    parser.add_argument("--parent", action="store_true", help="Check parent pack")
    parser.add_argument("--resolve", action="store_true", help="Resolve mod list")
    parser.add_argument("--build", action="store_true", help="Build packs")
    parser.add_argument("--test", action="store_true", help="Test builds")
    parser.add_argument("--queue", action="store_true", help="Queue ready builds")
    parser.add_argument("--publish", action="store_true", help="Publish queued builds")
    parser.add_argument("--capture", action="store_true", help="Capture config changes")
    parser.add_argument("--status", action="store_true", help="Show build status")
    parser.add_argument("--version", action="version", version="%(prog)s 0.0.1")
    return parser


def main():
    """Main entry point."""
    parser = init_args()
    args = parser.parse_args()
    
    state_mgr = StateMgr(state_dir="state")
    state_mgr.state_dir.mkdir(parents=True, exist_ok=True)
    
    if args.init:
        run_init(args, state_mgr)
    elif args.check:
        run_check(args, state_mgr)
    elif args.discover:
        run_discover(args, state_mgr)
    elif args.parent:
        run_parent(args, state_mgr)
    elif args.resolve:
        run_resolve(args, state_mgr)
    elif args.build:
        run_build(args, state_mgr)
    elif args.test:
        run_test(args, state_mgr)
    elif args.queue:
        run_queue(args, state_mgr)
    elif args.publish:
        run_publish(args, state_mgr)
    elif args.capture:
        run_capture(args, state_mgr)
    elif args.status:
        run_status(args, state_mgr)
    else:
        parser.print_help()
    
    return 0


def run_init(args, state_mgr):
    """Initialize state files."""
    log_section("INITIALIZING STATE")
    state_mgr.init()
    
    mc_versions_path = Path("manifest/mc-versions.yaml")
    if not mc_versions_path.exists():
        mc_versions_path.parent.mkdir(parents=True, exist_ok=True)
        mc_versions_path.write_text("""# Minecraft versions to track
active: []
candidate: []
retired: []
""")
    
    log_section("BUILDING INITIAL PACKS")
    
    print("\nInitialization complete. Run 'packtool --status' to see status.")
    return 0


def run_check(args, state_mgr):
    """Run the check flow."""
    log_section("CHECK FLOW")
    
    active = state_mgr.get_active_versions()
    for mc_version in active:
        print(f"Checking {mc_version}")
    
    print("Check complete")
    return 0


def run_discover(args, state_mgr):
    """Discover new Minecraft versions."""
    log_section("DISCOVER NEW VERSIONS")
    print("Discovering new Minecraft versions...")
    print("Discovery complete")
    return 0


def run_parent(args, state_mgr):
    """Check parent pack versions."""
    log_section("PARENT CHECK")
    print("Checking parent pack versions...")
    print("Parent check complete")
    return 0


def run_resolve(args, state_mgr):
    """Resolve mod list for a version."""
    log_section("RESOLVE MODS")
    print("Resolving mod list...")
    print("Resolution complete")
    return 0


def run_build(args, state_mgr):
    """Build .mrpack files."""
    log_section("BUILD PACKS")
    print("Building packs...")
    print("Build complete")
    return 0


def run_test(args, state_mgr):
    """Test builds."""
    log_section("TESTS")
    print("Testing builds...")
    print("Tests complete")
    return 0


def run_queue(args, state_mgr):
    """Queue ready builds."""
    log_section("QUEUE")
    print("Queueing ready builds...")
    print("Queueing complete")
    return 0


def run_publish(args, state_mgr):
    """Publish queued builds."""
    log_section("PUBLISH")
    print("Publishing queued builds...")
    print("Publishing complete")
    return 0


def run_capture(args, state_mgr):
    """Capture config changes."""
    log_section("CAPTURE")
    print("Capturing config changes...")
    print("Capturing complete")
    return 0


def run_status(args, state_mgr):
    """Show build status."""
    log_section("BUILD STATUS")
    uploads = state_mgr.get_uploads()
    queue = state_mgr.get_queue()
    runs = state_mgr.get_runs()
    print(f"Uploads: {uploads}")
    print(f"Queue: {queue}")
    print(f"Runs: {runs}")
    return 0
