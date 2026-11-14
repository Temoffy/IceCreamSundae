"""
Lock file management.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from source.models import ModFile, LockFile


class LockFileManager:
    """Manages lock files for queued/uploaded builds."""
    
    def __init__(self, lock_dir: str = "lock"):
        self.lock_dir = Path(lock_dir)
    
    def get_lock_path(self, minecraft_version: str, edition: str) -> Path:
        """Get the path for a lock file."""
        return self.lock_dir / f"{minecraft_version}_{edition}.json"
    
    def get_lock(self, minecraft_version: str, edition: str) -> Optional[LockFile]:
        """Get a lock file for a Minecraft version and edition."""
        path = self.get_lock_path(minecraft_version, edition)
        if not path.exists():
            return None
        
        with open(path) as f:
            data = json.load(f)
        
        return LockFile(**data)
    
    def save_lock(
        self,
        minecraft_version: str,
        edition: str,
        lock: LockFile
    ) -> None:
        """Save a lock file."""
        path = self.get_lock_path(minecraft_version, edition)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = lock.model_dump(mode="json", by_alias=True, exclude_none=True)
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_all_locks(self) -> List[LockFile]:
        """Get all lock files."""
        locks = []
        for path in self.lock_dir.glob("*.json"):
            with open(path) as f:
                data = json.load(f)
            lock = LockFile(**data)
            locks.append(lock)
        return locks
    
    def get_latest_lock(
        self,
        minecraft_version: str,
        edition: str
    ) -> Optional[LockFile]:
        """Get the latest lock file for a Minecraft version and edition."""
        return self.get_lock(minecraft_version, edition)
    
    def lock_exists(self, minecraft_version: str, edition: str) -> bool:
        """Check if a lock file exists."""
        path = self.get_lock_path(minecraft_version, edition)
        return path.exists()
    
    def get_content_hash(self, minecraft_version: str, edition: str) -> Optional[str]:
        """Get the content hash from a lock file."""
        lock = self.get_lock(minecraft_version, edition)
        return lock.content_hash if lock else None
