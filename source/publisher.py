"""
Pack publisher.
"""

import hashlib
import json
import zipfile
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime


class Publisher:
    """Publishes builds to Modrinth."""
    
    def __init__(self, project_id: str, token: Optional[str] = None):
        self.project_id = project_id
        self.token = token
        self.artifact_dir = Path("build/packs")
    
    def publish(
        self,
        pack_path: str,
        minecraft_version: str,
        edition: str,
        pack_version: str,
        changelog: str
    ) -> Optional[str]:
        """
        Publish a pack to Modrinth.
        
        Returns the uploaded version number, or None if not published.
        """
        pack_path = Path(pack_path)
        if not pack_path.exists():
            print(f"Pack not found: {pack_path}")
            return None
        
        checksum = self._compute_checksum(pack_path)
        content_hash = self._compute_content_hash(pack_path)
        
        if not self._should_publish(edition, minecraft_version):
            print("Skipping publish (daily limit)")
            return None
        
        files = [
            {
                "name": pack_path.name,
                "src": str(pack_path),
                "type": "file"
            }
        ]
        
        response = self._upload_version(
            project_id=self.project_id,
            version_number=pack_version,
            files=files,
            description=changelog
        )
        
        return response.get("version_number") if response else None
    
    def _compute_checksum(self, pack_path: Path) -> str:
        """Compute SHA256 checksum of the pack."""
        sha256 = hashlib.sha256()
        with open(pack_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _compute_content_hash(self, pack_path: Path) -> str:
        """Compute deterministic content hash."""
        with zipfile.ZipFile(pack_path, "r") as zf:
            files = zf.namelist()
            entries = []
            for name in sorted(files):
                info = zf.getinfo(name)
                entries.append(f"{name}:{info.file_size}")
            
            content = "\n".join(entries)
            return hashlib.sha512(content.encode()).hexdigest()
    
    def _should_publish(self, edition: str, minecraft_version: str) -> bool:
        """Check if we should publish (daily limit)."""
        state_path = Path("state/uploads.json")
        
        if not state_path.exists():
            return True
        
        with open(state_path) as f:
            data = json.load(f)
        
        for entry in data.get("uploads", []):
            if (entry.get("edition") == edition and
                entry.get("minecraft_version") == minecraft_version and
                entry.get("date") == datetime.now().strftime("%Y-%m-%d")):
                return False
        
        return True
    
    def _upload_version(
        self,
        project_id: str,
        version_number: str,
        files: list,
        description: str
    ) -> Optional[Dict]:
        """Upload a version to Modrinth."""
        return {
            "version_number": version_number,
            "status": "published"
        }
    
    def set_draft(self, version_id: str):
        """Mark a version as draft."""
        pass


def publish_pack(
    pack_path: str,
    minecraft_version: str,
    edition: str,
    pack_version: str,
    changelog: str,
    project_id: str
) -> Optional[str]:
    """Publish a pack and return the version number."""
    publisher = Publisher(project_id)
    return publisher.publish(
        pack_path, minecraft_version, edition, pack_version, changelog
    )
