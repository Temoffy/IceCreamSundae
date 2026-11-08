"""
State management.
"""

import json
from pathlib import Path
from datetime import datetime

from source.models import UploadState, BuildItem, RunState


class StateManager:
    """Manages state files."""
    
    def __init__(self, state_dir: str = "state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def init(self):
        """Initialize state files."""
        uploads_path = self.state_dir / "uploads.json"
        if not uploads_path.exists():
            with open(uploads_path, "w") as f:
                json.dump({"uploads": []}, f)
        
        queue_path = self.state_dir / "queue.json"
        if not queue_path.exists():
            with open(queue_path, "w") as f:
                json.dump({"items": []}, f)
        
        (self.state_dir / "parent").mkdir(exist_ok=True)
        
        runs_path = self.state_dir / "runs.json"
        if not runs_path.exists():
            with open(runs_path, "w") as f:
                json.dump({"runs": []}, f)
    
    def get_uploads(self) -> Dict:
        """Get upload state."""
        path = self.state_dir / "uploads.json"
        if not path.exists():
            return {"uploads": []}
        
        with open(path) as f:
            return json.load(f)
    
    def save_uploads(self, data: Dict):
        """Save upload state."""
        path = self.state_dir / "uploads.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_queue(self) -> Dict:
        """Get queue state."""
        path = self.state_dir / "queue.json"
        if not path.exists():
            return {"items": []}
        
        with open(path) as f:
            return json.load(f)
    
    def save_queue(self, data: Dict):
        """Save queue state."""
        path = self.state_dir / "queue.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_parent(self, minecraft_version: str) -> Optional[Dict]:
        """Get parent state for a Minecraft version."""
        path = self.state_dir / "parent" / f"{minecraft_version}.json"
        if not path.exists():
            return None
        
        with open(path) as f:
            return json.load(f)
    
    def save_parent(self, minecraft_version: str, data: Dict):
        """Save parent state for a Minecraft version."""
        path = self.state_dir / "parent" / f"{minecraft_version}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_runs(self) -> List[Dict]:
        """Get run reports."""
        runs_path = self.state_dir / "runs.json"
        if not runs_path.exists():
            return []
        
        with open(runs_path) as f:
            data = json.load(f)
            return data.get("runs", [])
    
    def save_run(self, run: Dict):
        """Save a run report."""
        runs_path = self.state_dir / "runs.json"
        if not runs_path.exists():
            with open(runs_path, "w") as f:
                json.dump({"runs": []}, f)
            return
        
        with open(runs_path) as f:
            data = json.load(f)
        
        data["runs"].append(run)
        
        with open(runs_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_active_versions(self) -> List[str]:
        """Get active Minecraft versions from manifest."""
        manifest_path = Path("manifest/mc-versions.yaml")
        if not manifest_path.exists():
            return []
        
        with open(manifest_path) as f:
            content = f.read()
        
        in_active = False
        versions = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('active:'):
                in_active = True
                continue
            if in_active:
                if line.startswith('candidate:') or line.startswith('retired:'):
                    break
                if line.startswith('- '):
                    versions.append(line[2:].strip('"\''))
        
        return versions
    
    def get_lock(self, minecraft_version: str, edition: str) -> Optional[Dict]:
        """Get lock file for a Minecraft version and edition."""
        path = Path("lock") / f"{minecraft_version}_{edition}.json"
        if not path.exists():
            return None
        
        with open(path) as f:
            return json.load(f)
    
    def save_lock(self, minecraft_version: str, edition: str, data: Dict):
        """Save lock file."""
        path = Path("lock") / f"{minecraft_version}_{edition}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
