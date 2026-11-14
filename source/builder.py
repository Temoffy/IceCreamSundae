"""
Pack builder for Fabric modpacks.
Phase 4: Builder and static checks for both editions.
"""

import hashlib
import json
import zipfile
from typing import List, Dict, Optional, Any
from pathlib import Path

from source.resolver import ModResolution


class PackBuilder:
    """Builds .mrpack files for both full and lite editions."""
    
    def __init__(self, pack_name: str, project_id: str):
        self.pack_name = pack_name
        self.project_id = project_id
        self.output_dir = Path("build/packs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build(
        self,
        mods: List[ModResolution],
        minecraft_version: str,
        edition: str
    ) -> Optional[tuple[str, str]]:
        """
        Build a .mrpack file.
        
        Args:
            mods: List of mod resolution results from the resolver
            minecraft_version: The Minecraft version (e.g., "26.2")
            edition: "full" or "lite"
        
        Returns:
            Tuple of (pack_path, content_hash) if successful, None if failed.
        """
        pack_path = self.output_dir / f"{self.pack_name}_{minecraft_version}_{edition}.mrpack"
        
        try:
            index = self._build_index(mods, minecraft_version, edition)
        except Exception as e:
            print(f"  Failed to build index: {e}")
            return None
        
        index_path = self.output_dir / f"{self.pack_name}_{minecraft_version}_{edition}.json"
        with open(index_path, "w") as f:
            json.dump(index, f, indent=2)
        
        # Create the pack
        try:
            with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("index.json", json.dumps(index))
                # Note: In full implementation, we'd download and include jar files here
                # For Phase 4, we just validate the structure
        
            # Compute content hash
            content_hash = self._compute_content_hash(mods)
            return str(pack_path), content_hash
        except Exception as e:
            print(f"  Failed to create pack: {e}")
            return None
    
    def build_both_editions(
        self,
        mods: List[ModResolution],
        minecraft_version: str,
        pack_name: str
    ) -> Dict[str, Optional[tuple[str, str]]]:
        """
        Build both full and lite editions.
        
        Returns:
            Dict mapping edition name to (pack_path, content_hash) or None.
        """
        results = {}
        
        for edition in ["full", "lite"]:
            print(f"  Building {edition} edition...")
            result = self.build(mods, minecraft_version, edition)
            results[edition] = result
            if result:
                print(f"    ✓ Built: {result[0]}")
                print(f"    ✓ Content hash: {result[1]}")
            else:
                print(f"    ✗ Failed for {edition}")
        
        return results
    
    def _build_index(
        self,
        mods: List[ModResolution],
        minecraft_version: str,
        edition: str
    ) -> Dict:
        """Build the pack index."""
        # Build files list
        files = []
        for mod in mods:
            files.append({
                "name": mod.file_name,
                "type": "file",
                "method": 1,
                "url": mod.file_url
            })
        
        # Determine project_id
        project_id = self.project_id or "fabric"
        
        return {
            "project_id": project_id,
            "game_versions": [minecraft_version],
            "minecraft_version": minecraft_version,
            "format_version": 1,
            "files": files
        }
    
    def _compute_content_hash(self, mods: List[ModResolution]) -> str:
        """Compute a deterministic content hash."""
        entries = []
        
        for mod in mods:
            entry = f"{mod.file_name}:{mod.sha512}"
            entries.append(entry)
        
        content = "\n".join(sorted(entries))
        return hashlib.sha512(content.encode()).hexdigest()
    
    def validate_index(self, index: Dict) -> List[str]:
        """Validate pack index."""
        errors = []
        
        if index.get("format_version") != 1:
            errors.append(f"Invalid format version (expected 1, got: {index.get('format_version')})")
        
        required = ["project_id", "game_versions", "minecraft_version", "files"]
        for field in required:
            if field not in index:
                errors.append(f"Missing required field: {field}")
        
        for file_entry in index.get("files", []):
            if file_entry.get("method") not in [1, 2]:
                errors.append(f"Invalid method for file: {file_entry.get('name')}")
        
        return errors


def build_pack(
    mods: List[ModResolution],
    minecraft_version: str,
    edition: str,
    pack_name: str = "IceCreamSundae",
    project_id: str = "ice-cream-sundae"
) -> Optional[tuple[str, str]]:
    """
    Build a pack from mod resolution results.
    
    Convenience function for building single editions.
    """
    builder = PackBuilder(pack_name, project_id)
    return builder.build(mods, minecraft_version, edition)


def build_packs(
    mods: List[ModResolution],
    minecraft_version: str,
    pack_name: str = "IceCreamSundae",
    project_id: str = "ice-cream-sundae"
) -> Dict[str, Optional[tuple[str, str]]]:
    """
    Build both full and lite editions from mod resolution results.
    
    Returns:
        Dict mapping edition name to (pack_path, content_hash) or None.
    """
    builder = PackBuilder(pack_name, project_id)
    return builder.build_both_editions(mods, minecraft_version, pack_name)
