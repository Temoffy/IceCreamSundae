"""
Model tests.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "source"))


def test_pack_settings():
    """Test PackSettings model."""
    from source.models import PackSettings
    
    settings = PackSettings(
        loader="fabric",
        channel="release",
        completeness={"release_at": 95, "beta_at": 70, "alpha_at": 50}
    )
    assert settings.loader == "fabric"
    assert settings.channel == "release"


def test_mod_config():
    """Test ModConfig model."""
    from source.models import ModConfig
    
    mod = ModConfig(
        id="fabric-api",
        name="Fabric API",
        lite=True,
        required=True
    )
    assert mod.id == "fabric-api"
    assert mod.required == True


def test_minecraft_version():
    """Test McVersion model."""
    from source.models import McVersion
    
    version = McVersion(version="1.20.4", type="release")
    assert version.version == "1.20.4"
    assert version.type == "release"


def test_mojang_manifest():
    """Test MojangManifest can be instantiated."""
    from source.mcversion import MojangManifest
    
    manifest = MojangManifest()
    assert manifest is not None


def test_build_item():
    """Test BuildItem model."""
    from source.models import BuildItem
    
    item = BuildItem(
        pack="full",
        minecraft_version="1.20.4",
        pack_version="1.0.0",
        artifact_path="build/packs/full_1.20.4.mrpack",
        checksum="abc123",
        content_hash="def456"
    )
    assert item.pack == "full"
    assert item.status == "ready"


def test_build_queue():
    """Test BuildQueue model."""
    from source.models import BuildQueue
    
    queue = BuildQueue(items=[
        {
            "pack": "full",
            "minecraft_version": "1.20.4",
            "pack_version": "1.0.0",
            "artifact_path": "build/packs/full_1.20.4.mrpack",
            "checksum": "abc123",
            "content_hash": "def456",
            "status": "ready"
        }
    ])
    assert len(queue.items) == 1
    assert queue.items[0].pack == "full"
