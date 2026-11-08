"""
Config capture.
"""

from typing import List, Dict, Optional
from pathlib import Path


class CaptureManager:
    """Captures config changes."""
    
    def __init__(self):
        self.defaults_dir = Path("build/defaults")
        self.game_dir = Path("build/game")
    
    def capture(
        self,
        pack_path: str,
        edition: str,
        minecraft_version: str,
        layer: str = "base"
    ) -> Dict[str, Any]:
        """Capture config changes from a game boot."""
        self._build_pack(pack_path, edition, minecraft_version)
        
        self.game_dir.mkdir(parents=True, exist_ok=True)
        for path in self.game_dir.iterdir():
            path.unlink()
        
        self.defaults_dir.mkdir(parents=True, exist_ok=True)
        
        self._install_and_boot(pack_path, self.game_dir)
        
        captured = self._capture_configs()
        
        self._write_patches(captured, layer)
        
        return captured
    
    def _build_pack(
        self,
        pack_path: str,
        edition: str,
        minecraft_version: str
    ):
        """Build the pack."""
        pass
    
    def _install_and_boot(self, pack_path: str, game_dir: Path):
        """Install and boot the game."""
        pass
    
    def _capture_configs(self) -> Dict[str, Any]:
        """Capture configs from the game directory."""
        configs = {}
        
        for path in self.game_dir.rglob("*.txt"):
            if path.suffix in [".txt", ".json", ".toml"]:
                rel_path = path.relative_to(self.game_dir)
                self.defaults_dir.joinpath(rel_path).parent.mkdir(parents=True, exist_ok=True)
                path.rename(self.defaults_dir.joinpath(rel_path))
        
        return configs
    
    def _write_patches(self, captured: Dict[str, Any], layer: str):
        """Write patches for captured configs."""
        pass


def capture_configs(
    pack_path: str,
    edition: str,
    minecraft_version: str
) -> Dict[str, Any]:
    """Capture config changes and return the result."""
    manager = CaptureManager()
    return manager.capture(pack_path, edition, minecraft_version)
