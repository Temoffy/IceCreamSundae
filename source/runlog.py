"""
Run reports.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class RunLog:
    """Manages run reports."""
    
    def __init__(self, state_dir: str = "state"):
        self.state_dir = Path(state_dir)
        self.runs_path = self.state_dir / "runs.json"
    
    def init(self) -> None:
        """Initialize runs.json."""
        self.runs_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.runs_path.exists():
            with open(self.runs_path, "w") as f:
                json.dump({"runs": []}, f)
    
    def get_runs(self, limit: Optional[int] = None) -> List[Dict]:
        """Get run reports, optionally limited."""
        if not self.runs_path.exists():
            return []
        
        with open(self.runs_path) as f:
            data = json.load(f)
        
        runs = data.get("runs", [])
        if limit:
            return runs[-limit:]
        return runs
    
    def get_latest_run(self) -> Optional[Dict]:
        """Get the latest run report."""
        runs = self.get_runs(limit=1)
        return runs[0] if runs else None
    
    def save_run(self, run: Dict) -> None:
        """Save a run report."""
        runs_path = self.runs_path
        runs_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(runs_path) as f:
            data = json.load(f)
        
        data["runs"].append(run)
        
        with open(runs_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of all runs."""
        runs = self.get_runs()
        if not runs:
            return "No runs yet."
        
        lines = [f"Total runs: {len(runs)}"]
        
        for i, run in enumerate(runs[-10:], 1):
            status = run.get("status", "unknown")
            run_type = run.get("run_type", "unknown")
            started_at = run.get("started_at", "unknown")
            completed_at = run.get("completed_at", "unknown")
            
            lines.append(f"  #{i}: {run_type} - {status} ({started_at})")
        
        return "\n".join(lines)
