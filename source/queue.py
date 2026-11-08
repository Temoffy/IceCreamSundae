"""
Build queue management.
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from source.models import BuildItem, BuildQueue


class BuildQueueManager:
    """Manages the build queue."""
    
    def __init__(self, queue_path: str = "state/queue.json"):
        self.queue_path = Path(queue_path)
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.queue: List[BuildItem] = self._load()
    
    def _load(self) -> List[BuildItem]:
        """Load queue from file."""
        if self.queue_path.exists():
            with open(self.queue_path) as f:
                data = __import__("json").load(f)
                return [BuildItem(**item) for item in data.get("items", [])]
        return []
    
    def _save(self):
        """Save queue to file."""
        data = {"items": [item.model_dump() for item in self.queue]}
        with open(self.queue_path, "w") as f:
            __import__("json").dump(data, f, indent=2)
    
    def add(self, item: BuildItem):
        """Add an item to the queue."""
        for existing in self.queue:
            if existing.pack == item.pack and existing.minecraft_version == item.minecraft_version:
                idx = self.queue.index(existing)
                self.queue[idx] = item
                break
        else:
            self.queue.append(item)
        
        self.queue.sort(key=lambda x: x.added_at, reverse=True)
        self.queue = self.queue[:8]
        
        self._save()
    
    def get_ready(self, pack: str, minecraft_version: str) -> Optional[BuildItem]:
        """Get the next ready item."""
        for item in self.queue:
            if item.pack == pack and item.minecraft_version == minecraft_version and item.status == "ready":
                return item
        return None
    
    def update_status(self, pack: str, minecraft_version: str, status: str):
        """Update item status."""
        for item in self.queue:
            if item.pack == pack and item.minecraft_version == minecraft_version:
                item.status = status
                self._save()
                return
        
        self.queue.append(BuildItem(
            pack=pack,
            minecraft_version=minecraft_version,
            status=status
        ))
        self._save()
    
    def is_full(self, pack: str, minecraft_version: str) -> bool:
        """Check if queue is full for this pack/version."""
        return len(self.queue) >= 8 or self.get_ready(pack, minecraft_version) is not None
    
    def get_all_ready(self) -> List[BuildItem]:
        """Get all ready items."""
        return [item for item in self.queue if item.status == "ready"]
