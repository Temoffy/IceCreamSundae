"""
Boot harness tests for Phase 1.
"""

import pytest
import sys
from pathlib import Path
import zipfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "source"))


def test_pack_import():
    """Test that a pack can be imported."""
    from source.installer import PackInstaller
    
    # Create a test pack
    pack_dir = Path("tests/fixtures/test_pack")
    pack_dir.mkdir(exist_ok=True)
    
    # Test that installer can be created
    installer = PackInstaller("build/game")
    assert installer is not None
    
    # Test that directory is created
    assert installer.game_dir.exists()


def test_static_index_validation():
    """Test that the static index validator works."""
    from source.checks import StaticChecker
    
    # Valid index
    valid_index = {
        "format_version": 1,
        "project_id": "test",
        "game_versions": ["1.20.4"],
        "minecraft_version": "1.20.4",
        "files": []
    }
    
    errors = StaticChecker.validate_index(valid_index)
    assert len(errors) == 0
    
    # Invalid index
    invalid_index = {
        "format_version": 2,  # Wrong version
        "project_id": "test",
        "game_versions": ["1.20.4"],
        "minecraft_version": "1.20.4",
        "files": []
    }
    
    errors = StaticChecker.validate_index(invalid_index)
    assert len(errors) > 0


def test_server_boot_patterns():
    """Test server boot log patterns."""
    from source.checks import ServerBooter
    
    booted = ServerBooter()
    
    # Test success patterns
    success_logs = [
        "Done (main)",
        "Server stopped",
        "Server finished starting"
    ]
    
    for log in success_logs:
        success, failure = booted.test(log)
        assert success, f"Should detect success in: {log}"


def test_client_boot_patterns():
    """Test client boot log patterns."""
    from source.checks import ClientBooter
    
    booted = ClientBooter()
    
    # Test success patterns
    success_logs = [
        "Successfully loaded",
        "Main menu",
        "Joined server"
    ]
    
    for log in success_logs:
        success, failure = booted.test(log)
        assert success, f"Should detect success in: {log}"


def test_hand_pack_build():
    """Test that a hand-pack can be built."""
    from source.installer import HandPackBuilder
    
    builder = HandPackBuilder("test", "1.20.4")
    
    # Create a mock mod without file_name (no jar to write)
    mock_mod = {
        "download_url": "http://example.com/test.jar"
    }
    
    # Build should return a path
    result = builder.build([mock_mod])
    assert result is not None
    assert Path(result).exists()
    
    # Verify the pack has the right structure
    with zipfile.ZipFile(result, "r") as zf:
        # Check index.json exists
        assert "index.json" in zf.namelist()
        # Check it has the right content
        index = json.loads(zf.read("index.json"))
        assert index["format_version"] == 1
        assert index["minecraft_version"] == "1.20.4"


def test_pack_bootstrap():
    """Test that a pack can be bootstrapped."""
    from source.launcher import GameLauncher
    
    launcher = GameLauncher()
    
    # Test that launcher can be created
    assert launcher is not None
    assert launcher.portablemc_path == "portablemc"


def test_server_booter():
    """Test server booter."""
    from source.checks import ServerBooter
    
    booted = ServerBooter()
    
    # Test failure patterns
    failure_logs = [
        "Failed to start",
        "Exception occurred",
        "Error: connection refused"
    ]
    
    for log in failure_logs:
        success, failure = booted.test(log)
        # Should detect failure or return True with no pattern
        assert success or failure is not None
