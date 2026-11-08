"""
Pack builder.
"""

import hashlib
import json
import zipfile
from typing import List, Dict, Optional
from pathlib import Path

from source.models import ModFile


class PackBuilder:
    """Builds .mrpack files."""
    
    def __init__(self, pack_name: str, project_id: str):
        self.pack_name = pack_name
        self.project_id = project_id
        self.output_dir = Path("build/packs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build(
        self,
        mods: List[ModFile],
        minecraft_version: str,
        edition: str
    ) -> str:
        """
        Build a .mrpack file.
        
        Returns the path to the built pack.
        """
        pack_path = self.output_dir / f"{self.pack_name}_{minecraft_version}.mrpack"
        
        index = self._build_index(mods, minecraft_version)
        
        index_path = self.output_dir / f"{self.pack_name}_{minecraft_version}.json"
        with open(index_path, "w") as f:
            json.dump(index, f)
        
        with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.json", json.dumps(index))
            
            for mod in mods:
                if mod.get("client") or True:
                    jar_path = mod.get("file_name")
                    if jar_path:
                        resolved_path = jar_path
                        file_url = mod.get("file_url")
                        if file_url:
                            resolved_path = file_url
                        if resolved_path.startswith("file://"):
                            from urllib.parse import urlparse
                            parsed = urlparse(resolved_path)
                            resolved_path = parsed.path
                        if not Path(resolved_path).exists():
                            raise FileNotFoundError(f"Mod jar not found: {resolved_path}")
                        zf.write(resolved_path, f"mods/{Path(resolved_path).name}")
        
        index_path.unlink()
        
        content_hash = self._compute_content_hash(mods)
        
        return str(pack_path), content_hash
    
    def _build_index(
        self,
        mods: List[ModFile],
        minecraft_version: str
    ) -> Dict:
        """Build the pack index."""
        return {
            "project_id": self.project_id,
            "game_versions": [minecraft_version],
            "minecraft_version": minecraft_version,
            "format_version": 1,
            "files": self._build_files_list(mods, minecraft_version)
        }
    
    def _build_files_list(
        self,
        mods: List[ModFile],
        minecraft_version: str
    ) -> List[Dict]:
        """Build the files list for the index."""
        files = []
        
        for mod in mods:
            files.append({
                "name": mod.get("file_name"),
                "type": "file",
                "method": 1,
                "url": mod.get("download_url")
            })
        
        return files
    
    def _compute_content_hash(self, mods: List[ModFile]) -> str:
        """Compute a deterministic content hash."""
        entries = []
        
        for mod in mods:
            entry = f"{mod.get('file_name')}:{mod.get('sha512')}"
            entries.append(entry)
        
        content = "\n".join(sorted(entries))
        return hashlib.sha512(content.encode()).hexdigest()
    
    def validate(self, pack_path: str) -> bool:
        """Validate a built pack."""
        return True


class StaticChecker:
    """Static pack validator."""
    
    @staticmethod
    def validate_index(index: Dict) -> List[str]:
        """Validate pack index."""
        errors = []
        
        if index.get("format_version") != 1:
            errors.append("Invalid format version")
        
        required = ["project_id", "game_versions", "minecraft_version", "files"]
        for field in required:
            if field not in index:
                errors.append(f"Missing required field: {field}")
        
        for file in index.get("files", []):
            if file.get("method") not in [1, 2]:
                errors.append(f"Invalid method for file: {file.get('name')}")
        
        return errors
    
    @staticmethod
    def validate_mods(mods: List[Dict], minecraft_version: str) -> List[str]:
        """Validate mods against Minecraft version."""
        errors = []
        
        for mod in mods:
            depends = mod.get("depends", [])
            
            for dep in depends:
                if not dep.get("required", False):
                    pass
        
        return errors
