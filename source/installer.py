"""
Pack installer.
"""

import zipfile
import shutil
import json
from pathlib import Path
from typing import List, Dict, Optional


class PackInstaller:
    """Installs .mrpack files into game directories."""
    
    def __init__(self, game_dir: str = "build/game"):
        self.game_dir = Path(game_dir)
        self.game_dir.mkdir(parents=True, exist_ok=True)
    
    def install(
        self,
        pack_path: str,
        mod_dir: Optional[str] = None
    ) -> bool:
        """
        Install a pack into the game directory.
        
        Returns True if successful.
        """
        pack_path = Path(pack_path)
        if not pack_path.exists():
            print(f"Pack not found: {pack_path}")
            return False
        
        # Clean game directory
        for path in self.game_dir.rglob("*"):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        
        # Copy files from pack
        with zipfile.ZipFile(pack_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith(".jar") or name.endswith(".jar.txt"):
                    target = self.game_dir / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    
                    if name.endswith(".jar"):
                        zf.extract(name, self.game_dir)
                    else:
                        # Extract metadata
                        target.write_text(zf.read(name).decode())
        
        return True


class ModInstaller:
    """Installs mods from a mod directory."""
    
    def __init__(self, mod_dir: str = "mods"):
        self.mod_dir = Path(mod_dir)
    
    def install_mods(
        self,
        game_dir: Path,
        mod_jars: List[str]
    ) -> bool:
        """Install mod jars into the game directory."""
        for jar in mod_jars:
            jar_path = self.mod_dir / jar
            if jar_path.exists():
                target = game_dir / "mods" / jar_path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(jar_path, target)
        
        return True


class HandPackBuilder:
    """Builds a hand-written .mrpack from a lock file."""
    
    def __init__(self, pack_name: str, minecraft_version: str):
        self.pack_name = pack_name
        self.minecraft_version = minecraft_version
        self.output_path = Path("build/test_pack.mrpack")
    
    def build(
        self,
        mods: List[Dict[str, any]]
    ) -> Optional[str]:
        """
        Build a .mrpack from mod entries.
        
        Returns path to the built pack, or None if failed.
        """
        # Build index
        index = {
            "project_id": "test",
            "game_versions": [self.minecraft_version],
            "minecraft_version": self.minecraft_version,
            "format_version": 1,
            "files": []
        }
        
        # Add mods
        for mod in mods:
            file_entry = {
                "name": mod.get("file_name"),
                "type": "file",
                "method": 1,
                "url": mod.get("download_url")
            }
            index["files"].append(file_entry)
        
        # Write pack
        with zipfile.ZipFile(self.output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.json", json.dumps(index))
            
            for mod in mods:
                jar_path = mod.get("file_name")
                if jar_path:
                    zf.write(jar_path, f"mods/{Path(jar_path).name}")
        
        return str(self.output_path)
    
    def build_from_lock(
        self,
        lock_path: str
    ) -> Optional[str]:
        """Build a pack from a lock file."""
        lock_path = Path(lock_path)
        if not lock_path.exists():
            return None
        
        with open(lock_path) as f:
            lock = json.load(f)
        
        mods = lock.get("mods", [])
        return self.build(mods)


def install_pack(
    pack_path: str,
    game_dir: Optional[str] = None
) -> bool:
    """Install a pack and return success."""
    installer = PackInstaller(game_dir or "build/game")
    return installer.install(pack_path)


def build_hand_pack(
    mods: List[Dict[str, any]],
    pack_name: str = "test",
    minecraft_version: str = "1.20.4"
) -> Optional[str]:
    """Build a hand-written pack from mod entries."""
    builder = HandPackBuilder(pack_name, minecraft_version)
    return builder.build(mods)
