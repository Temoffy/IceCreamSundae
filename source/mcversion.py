"""
Minecraft version handling.
"""

import json
import os
from typing import List, Optional, Dict
from pathlib import Path
from pydantic import BaseModel

from source.models import McVersion


class MojangClient:
    """Client for Mojang's version manifest."""
    
    MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest.json"
    CACHE_DIR = "build/.mojang_cache"
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or self.CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self._cache: Dict[str, str] = {}
        self._cache_path = Path(self.cache_dir) / "manifest.json"
    
    def fetch_manifest(self) -> Dict:
        """Fetch the version manifest from Mojang."""
        if self._cache_path.exists():
            with open(self._cache_path) as f:
                data = json.load(f)
            import time
            cache_mtime = os.path.getmtime(self._cache_path)
            if time.time() - cache_mtime < 86400:
                return data
        
        import httpx
        response = httpx.get(self.MANIFEST_URL)
        response.raise_for_status()
        data = response.json()
        
        with open(self._cache_path, "w") as f:
            json.dump(data, f)
        
        return data
    
    def get_versions(self) -> List[McVersion]:
        """Get all Minecraft versions."""
        data = self.fetch_manifest()
        versions = []
        for entry in data["versions"]:
            if entry["type"] == "release":
                versions.append(McVersion(
                    version=entry["id"],
                    type=entry["type"],
                    release_date=entry.get("releaseTime")
                ))
        return versions
    
    def get_version_info(self, version: str) -> Optional[Dict]:
        """Get detailed info for a version."""
        import httpx
        url = f"https://piston-meta.mojang.com/mc/game/version/{version}/latest.json"
        response = httpx.get(url)
        response.raise_for_status()
        return response.json()
    
    def version_in_range(self, version: str, range_expr: str) -> bool:
        """Check if a version matches a range expression."""
        v_parts = version.split(".")
        v_major = int(v_parts[0])
        v_minor = int(v_parts[1])
        
        if range_expr.startswith(">="):
            target = range_expr[2:]
            t_parts = target.split(".")
            t_major = int(t_parts[0])
            t_minor = int(t_parts[1])
            
            if v_major > t_major:
                return True
            elif v_major == t_major and v_minor >= t_minor:
                return True
            return False
        
        if range_expr.startswith("<="):
            target = range_expr[2:]
            t_parts = target.split(".")
            t_major = int(t_parts[0])
            t_minor = int(t_parts[1])
            
            if v_major < t_major:
                return False
            elif v_major == t_major and v_minor <= t_minor:
                return True
            return True
        
        if range_expr.startswith(">"):
            target = range_expr[1:]
            t_parts = target.split(".")
            t_major = int(t_parts[0])
            t_minor = int(t_parts[1])
            
            if v_major > t_major:
                return True
            elif v_major == t_major and v_minor > t_minor:
                return True
            return False
        
        if range_expr.startswith("<"):
            target = range_expr[1:]
            t_parts = target.split(".")
            t_major = int(t_parts[0])
            t_minor = int(t_parts[1])
            
            if v_major < t_major:
                return False
            elif v_major == t_major and v_minor < t_minor:
                return True
            return True
        
        return version == range_expr


class MojangManifest:
    """Caching wrapper for Mojang manifest."""
    
    def __init__(self):
        self.client = MojangClient()
    
    def get_versions(self) -> List[McVersion]:
        """Get all release versions."""
        return self.client.get_versions()
    
    def parse_range(self, range_expr: str) -> List[str]:
        """Parse a version range expression and return matching versions."""
        versions = self.get_versions()
        matching = []
        for v in versions:
            if self.client.version_in_range(v.version, range_expr):
                matching.append(v.version)
        return matching
