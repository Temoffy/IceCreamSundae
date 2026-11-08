"""
Mod resolver.
"""

from typing import List, Dict, Set, Optional
from pydantic import BaseModel

from source.models import ModFile, ModConfig


class ModResolver:
    """Resolves mod list for a pack."""
    
    def __init__(self, mods: List[Dict[str, any]]):
        self.mods = mods
        self.mod_map: Dict[str, Dict[str, any]] = {}
        self._build_mod_map()
    
    def _build_mod_map(self):
        """Build a map of mod IDs to their configs."""
        for mod in self.mods:
            self.mod_map[mod["id"]] = mod
    
    def resolve(
        self,
        minecraft_version: str,
        parent_mods: List[Dict[str, any]],
        exclude: List[str] = []
    ) -> tuple[List[ModFile], float]:
        """
        Resolve the mod list for a Minecraft version.
        
        Returns:
            Tuple of (resolved mods, completeness_percent)
        """
        wanted = set()
        for mod in self.mods:
            versions = mod.get("versions")
            if versions and minecraft_version not in versions:
                continue
            
            if mod.get("exclude", False):
                continue
            
            wanted.add(mod["id"])
        
        for mod in parent_mods:
            mod_id = mod.get("project_id", mod.get("id"))
            if mod_id not in exclude:
                wanted.add(mod_id)
        
        resolved = []
        for mod_id in sorted(wanted):
            if not self._resolve_mod(mod_id, minecraft_version):
                continue
            
            resolved.append(mod)
        
        completeness = len(resolved) / len(wanted) * 100 if wanted else 0
        
        return resolved, completeness
    
    def _resolve_mod(self, mod_id: str, minecraft_version: str) -> Optional[ModFile]:
        """Resolve a single mod."""
        if mod_id in self.mod_map:
            return self._resolve_manifest_mod(mod_id, minecraft_version)
        
        return None
    
    def _resolve_manifest_mod(
        self,
        mod_id: str,
        minecraft_version: str
    ) -> Optional[ModFile]:
        """Resolve a manifest mod."""
        mod = self.mod_map[mod_id]
        
        versions = mod.get("versions")
        if versions and minecraft_version not in versions:
            return None
        
        return None
    
    def resolve_lite(self, resolved: List[ModFile]) -> List[ModFile]:
        """Derive the lite set from the full result."""
        lite = []
        for mod in resolved:
            for mod_cfg in self.mod_map.values():
                if mod_cfg["id"] == mod.project_id:
                    if not mod_cfg.get("lite", True):
                        continue
                    break
            lite.append(mod)
        
        return lite
    
    def compute_dependencies(self, mod_id: str) -> Set[str]:
        """Compute dependencies for a mod."""
        return set()
    
    def compute_completeness(
        self,
        minecraft_version: str,
        resolved: List[ModFile],
        wanted: List[str]
    ) -> float:
        """Compute completeness percentage."""
        if not wanted:
            return 100.0
        
        return len(resolved) / len(wanted) * 100
