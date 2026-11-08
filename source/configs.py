"""
Config layer management.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConfigManager:
    """Manages config layers for packs."""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
    
    def get_layer_path(self, mc_version: str, layer: str) -> Path:
        """Get the path for a config layer."""
        mc_path = self.config_dir / f"mc-{mc_version}"
        return mc_path / layer
    
    def get_base_path(self) -> Path:
        """Get the base config path."""
        return self.config_dir / "base"
    
    def get_files(self, mc_version: str, layer: str) -> List[Path]:
        """Get all files in a config layer."""
        layer_path = self.get_layer_path(mc_version, layer)
        if not layer_path.exists():
            return []
        
        files = []
        for ext in ["*.json", "*.toml", "*.yml", "*.yaml", "*.properties", "*.txt"]:
            files.extend(layer_path.glob(ext))
        return sorted(files)
    
    def get_options_txt(self, mc_version: str, layer: str) -> Optional[Path]:
        """Get options.txt if it exists in the layer."""
        options_path = self.get_layer_path(mc_version, layer) / "options.txt"
        return options_path if options_path.exists() else None
    
    def merge_options_txt(
        self,
        base_options: Dict[str, str],
        mc_version: str,
        layer: str
    ) -> Dict[str, str]:
        """Merge options.txt fragments by key."""
        merged = base_options.copy()
        
        options_path = self.get_options_txt(mc_version, layer)
        if not options_path:
            return merged
        
        with open(options_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    merged[key] = value
        
        return merged
    
    def get_parent_files(self, mc_version: str) -> List[Path]:
        """Get parent pack files to copy."""
        return []
    
    def remove_parent_files(self, files: List[Path], remove_paths: List[str]) -> List[Path]:
        """Remove files that match remove_paths."""
        cleaned = []
        for path in files:
            should_remove = False
            for pattern in remove_paths:
                if path.match(pattern):
                    should_remove = True
                    break
            if not should_remove:
                cleaned.append(path)
        return cleaned
    
    def get_file_hash(self, path: Path) -> str:
        """Get SHA512 hash of a file."""
        sha512 = hashlib.sha512()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha512.update(chunk)
        
        return sha512.hexdigest()
    
    def compute_content_hash(self, files: List[Path]) -> str:
        """Compute deterministic content hash for a set of files."""
        entries = []
        for path in sorted(files, key=lambda p: str(p)):
            sha512 = self.get_file_hash(path)
            entries.append(f"{path}:{sha512}")
        
        content = "\n".join(entries)
        return hashlib.sha512(content.encode()).hexdigest()
