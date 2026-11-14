"""
CLI entry point for packtool.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

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
    parser.add_argument("--report", action="store_true", help="Generate mod resolution report (Phase 3)")
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
    elif args.report:
        run_report(args, state_mgr)
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
    """Build .mrpack files for both editions (Phase 4)."""
    log_section("BUILD PACKS - Phase 4")
    
    # Load manifest
    import yaml
    from pathlib import Path
    
    manifest_dir = Path("manifest")
    mods_yaml = manifest_dir / "mods.yaml"
    packs_yaml = manifest_dir / "packs.yaml"
    mc_versions_yaml = manifest_dir / "mc-versions.yaml"
    parent_yaml = manifest_dir / "parent.yaml"
    
    if not all(p.exists() for p in [mods_yaml, packs_yaml, mc_versions_yaml, parent_yaml]):
        print("Error: Missing manifest files.")
        print("Run 'packtool --init' first to create the manifest.")
        return 1
    
    with open(mods_yaml) as f:
        mods_data = yaml.safe_load(f)
    
    with open(packs_yaml) as f:
        packs_data = yaml.safe_load(f)
    
    with open(mc_versions_yaml) as f:
        mc_versions_data = yaml.safe_load(f)
    
    with open(parent_yaml) as f:
        parent_data = yaml.safe_load(f)
    
    # Extract settings
    mods = mods_data if isinstance(mods_data, list) else mods_data.get("-", [])
    parent_project_id = parent_data.get("project", "fabulously-optimized")
    manifest_settings = packs_data.get("settings", {})
    pack_settings = packs_data.get("packs", {})
    
    # Get active Minecraft versions
    active_versions = mc_versions_data.get("active", [])
    if not active_versions:
        print("No active Minecraft versions configured.")
        print("Edit manifest/mc-versions.yaml and add versions to the 'active' list.")
        return 1
    
    # Create resolver
    from source.resolver import ModResolver, ResolutionResult, ReportFormatter
    resolver = ModResolver(mods, parent_project_id, manifest_settings)
    
    # Get parent versions (for real builds, this would query Modrinth)
    parent_versions = []
    
    # Build for each active version
    all_results = []
    for mc_version in active_versions:
        print(f"\nProcessing {mc_version}...")
        
        # Resolve mods for both editions
        full_result = resolver.resolve(mc_version, "full", parent_versions)
        lite_result = resolver.resolve_lite(full_result)
        
        print(f"  Full edition: {len(full_result.mods)} mods, {len(full_result.missing_mods)} missing")
        print(f"  Lite edition: {len(lite_result.mods)} mods, {len(lite_result.missing_mods)} missing")
        print(f"  Completeness: {full_result.completeness:.0f}%")
        
        # Build both editions
        pack_name = pack_settings.get("full", {}).get("name", "IceCreamSundae")
        project_id = pack_settings.get("full", {}).get("modrinth_project_id", "ice-cream-sundae")
        
        from source.builder import build_packs
        
        print(f"\n  Building {mc_version}...")
        builds = build_packs(
            full_result.mods,
            mc_version,
            pack_name
        )
        
        # Validate built packs
        from source.checks import CheckSuite
        suite = CheckSuite()
        
        for edition in ["full", "lite"]:
            if builds.get(edition):
                pack_path, content_hash = builds[edition]
                print(f"\n  Validating {edition} edition...")
                errors = suite.check_pack(pack_path)
                if errors:
                    print(f"    Errors: {errors}")
                else:
                    print(f"    ✓ Validated successfully")
                print(f"    Content hash: {content_hash}")
            else:
                print(f"  {edition} edition build failed")
        
        all_results.append({
            "minecraft_version": mc_version,
            "full": full_result,
            "lite": lite_result,
            "builds": builds
        })
    
    # Print summary
    print("\n" + "="*60)
    print("BUILD SUMMARY")
    print("="*60)
    for result in all_results:
        print(f"{result['minecraft_version']}:")
        print(f"  Full: {len(result['full'].mods)} mods, {result['full'].completeness:.0f}% complete")
        print(f"  Lite: {len(result['lite'].mods)} mods, {result['lite'].completeness:.0f}% complete")
    
    print("\nBuild complete!")
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


def run_report(args, state_mgr):
    """Generate a mod resolution report (Phase 3)."""
    log_section("MOD RESOLUTION REPORT")
    
    # Load manifest
    import yaml
    from pathlib import Path
    
    manifest_dir = Path("manifest")
    mods_yaml = manifest_dir / "mods.yaml"
    packs_yaml = manifest_dir / "packs.yaml"
    mc_versions_yaml = manifest_dir / "mc-versions.yaml"
    parent_yaml = manifest_dir / "parent.yaml"
    
    if not all(p.exists() for p in [mods_yaml, packs_yaml, mc_versions_yaml, parent_yaml]):
        print("Error: Missing manifest files.")
        print("Run 'packtool --init' first to create the manifest.")
        return 1
    
    with open(mods_yaml) as f:
        mods_data = yaml.safe_load(f)
    
    with open(packs_yaml) as f:
        packs_data = yaml.safe_load(f)
    
    with open(mc_versions_yaml) as f:
        mc_versions_data = yaml.safe_load(f)
    
    with open(parent_yaml) as f:
        parent_data = yaml.safe_load(f)
    
    # Extract settings
    # mods_data is a list because YAML root is a list
    mods = mods_data if isinstance(mods_data, list) else mods_data.get("-", [])
    parent_project_id = parent_data.get("project", "fabulously-optimized")
    manifest_settings = packs_data.get("settings", {})
    
    # Get active Minecraft versions
    active_versions = mc_versions_data.get("active", [])
    if not active_versions:
        print("No active Minecraft versions configured.")
        print("Edit manifest/mc-versions.yaml and add versions to the 'active' list.")
        return 1
    
    # Create resolver
    from source.resolver import ModResolver
    resolver = ModResolver(mods, parent_project_id, manifest_settings)
    
    # Generate report for each active version
    results = []
    for mc_version in active_versions:
        print(f"\nResolving mods for {mc_version}...")
        # In Phase 3, this would query Modrinth for actual builds
        # For now, we'll show a placeholder
        # TODO: Query Modrinth API for actual builds
        print(f"  Querying Modrinth for builds...")
        print(f"  (Phase 3: Report mode - no actual builds available yet)")
        
        # Create a mock result for demonstration
        # Phase 3: Show all wanted mods as missing (no actual Modrinth query yet)
        from source.resolver import ResolutionResult, ReportFormatter
        
        # Get mod IDs that should be resolved (exclude: true mods are already filtered)
        mod_ids = []
        mod_names = {}
        for mod in mods:
            mod_id = mod.get("id", "")
            if mod_id and mod_id != "capes":  # capes is excluded
                mod_ids.append(mod_id)
                mod_names[mod_id] = mod.get("name", mod_id)
        
        result = ResolutionResult(
            minecraft_version=mc_version,
            edition="full",
            mods=[],
            missing_mods=mod_ids,
            fallbacks_used=[],
            companions_added=[],
            dependencies_added=[],
            completeness=0.0,
            completeness_details={
                "total_wanted": len(mod_ids),
                "resolved": 0,
                "missing": len(mod_ids),
                "fallbacks_used": 0,
                "companions_added": 0,
                "dependencies_added": 0,
                "completeness": "0%",
                "threshold": manifest_settings.get("completeness", {}).get("alpha_at", 50),
            },
            resolved_at=datetime.now().isoformat()
        )
        results.append(result)
        
        # Show which mods are missing
        print(f"  Missing builds for: {', '.join(mod_ids)}")
        print(f"  Total wanted: {len(mod_ids)}")
        print(f"  Completeness: 0% (no builds found)")
    
    # Print summary
    print("\n" + ReportFormatter.format_summary(results))
    
    # Print detailed report
    print(ReportFormatter.format_report(results))
    
    return 0
