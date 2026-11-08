"""
Modrinth API client.
"""

import httpx
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from source.models import ModrinthVersion, ModrinthProject


class ModrinthClient:
    """Client for Modrinth API."""
    
    BASE_URL = "https://api.modrinth.com/v2"
    USER_AGENT = "packtool/0.0.1 (contact: TODO)"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        headers = {"User-Agent": self.USER_AGENT}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(headers=headers)
    
    def get_versions(
        self,
        project_id: str,
        loader: str = "fabric",
        game_version: Optional[str] = None,
        order: str = "desc"
    ) -> List[ModrinthVersion]:
        """Get versions for a project."""
        params = {"loaders": loader, "order": order}
        if game_version:
            params["game_versions"] = game_version
        
        response = self.client.get(f"{self.BASE_URL}/project/{project_id}/version", params=params)
        response.raise_for_status()
        data = response.json()
        
        versions = []
        for v in data.get("versions", []):
            v_dict = v.copy()
            v_dict["files"] = v.get("files", [])
            versions.append(ModrinthVersion(**v_dict, project_id=project_id))
        
        return versions
    
    def get_project(self, project_id: str) -> Optional[ModrinthProject]:
        """Get project details."""
        response = self.client.get(f"{self.BASE_URL}/project/{project_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return ModrinthProject(**response.json(), project_id=project_id)
    
    def get_version_files(
        self,
        project_id: str,
        version_id: str
    ) -> Dict[str, ModrinthFile]:
        """Get files for a version."""
        response = self.client.get(f"{self.BASE_URL}/project/{project_id}/version/{version_id}/files")
        response.raise_for_status()
        data = response.json()
        
        files = {}
        for f in data:
            files[f["id"]] = ModrinthFile(**f)
        return files
    
    def upload_version(
        self,
        project_id: str,
        version_number: str,
        files: List[Dict[str, str]],
        description: str = "",
        game_versions: Optional[List[str]] = None,
        draft: bool = True
    ) -> ModrinthVersion:
        """Upload a new version."""
        payload = {
            "name": version_number,
            "description": description,
            "game_versions": game_versions or [],
            "draft": draft
        }
        
        if files:
            files[0]["primary"] = True
        
        response = self.client.post(
            f"{self.BASE_URL}/project/{project_id}/version",
            json=payload,
            files=files
        )
        response.raise_for_status()
        return ModrinthVersion(**response.json(), project_id=project_id)
    
    def get_file_hash(self, project_id: str, version_id: str, file_id: str) -> str:
        """Get the hash of a file."""
        files = self.get_version_files(project_id, version_id)
        if file_id in files:
            return files[file_id].hash
        raise ValueError(f"File {file_id} not found")
    
    def get_version_by_number(
        self,
        project_id: str,
        version_number: str,
        loader: str = "fabric"
    ) -> Optional[ModrinthVersion]:
        """Get a version by number."""
        params = {"loaders": loader, "versions": version_number}
        
        response = self.client.get(f"{self.BASE_URL}/project/{project_id}/version", params=params)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        
        data = response.json()
        if data.get("versions"):
            return ModrinthVersion(**data["versions"][0], project_id=project_id)
        return None
    
    def bulk_get_hashes(self, project_id: str, version_id: str) -> Dict[str, str]:
        """Get hashes for all files in a version."""
        files = self.get_version_files(project_id, version_id)
        return {file_id: file.hash for file_id, file in files.items()}


class ModrinthFile(BaseModel):
    """A file in a Modrinth version."""
    id: str
    name: str
    slug: str
    hash: str
    size: int


class ModrinthAPI:
    """High-level Modrinth API wrapper."""
    
    def __init__(self, token: Optional[str] = None):
        self.client = ModrinthClient(token)
    
    def find_project(self, slug: str) -> Optional[ModrinthProject]:
        """Find a project by slug."""
        project = self.client.get_project(slug)
        if project:
            return project
        
        params = {"q": slug}
        response = self.client.client.get(f"{self.client.BASE_URL}/project", params=params)
        response.raise_for_status()
        data = response.json()
        
        for p in data.get("projects", []):
            if p.get("slug") == slug:
                return ModrinthProject(**p, project_id=p["id"])
        
        return None
    
    def get_project_versions(
        self,
        slug: str,
        loader: str = "fabric",
        game_version: Optional[str] = None
    ) -> List[ModrinthVersion]:
        """Get versions for a project by slug."""
        project = self.find_project(slug)
        if not project:
            return []
        
        return self.client.get_versions(project.project_id, loader, game_version)


_client = None


def get_client(token: Optional[str] = None) -> ModrinthAPI:
    """Get the global client instance."""
    global _client
    if _client is None:
        _client = ModrinthAPI(token)
    return _client
