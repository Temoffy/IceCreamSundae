"""
Modrinth API client for querying mod builds and project metadata.
"""

import httpx
import json
from typing import List, Dict, Optional, Any, Set
from pydantic import BaseModel, Field
from datetime import datetime

from source.models import ModrinthVersion, ModrinthProject


class ModrinthClient:
    """Client for Modrinth API v2."""
    
    BASE_URL = "https://api.modrinth.com/v2"
    USER_AGENT = "packtool/0.0.1 (contact: TODO)"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        headers = {"User-Agent": self.USER_AGENT}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(headers=headers, timeout=30.0)
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make an API request with retry logic."""
        for attempt in range(3):
            try:
                response = self.client.request(method, self.BASE_URL + endpoint, params=params)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    retry_after = response.headers.get("Retry-After", "2")
                    import time
                    time.sleep(float(retry_after))
                    continue
                elif response.status_code == 404:
                    return {"error": "not_found"}
                else:
                    response.raise_for_status()
            except httpx.RequestError as e:
                if attempt == 2:
                    raise
                import time
                time.sleep(2 ** attempt)
        raise RuntimeError("Failed to query Modrinth API after retries")
    
    def get_versions(
        self,
        project_id: str,
        loader: str = "fabric",
        game_version: Optional[str] = None,
        order: str = "desc",
        status: str = "release"
    ) -> List[ModrinthVersion]:
        """Get versions for a project."""
        params = {"loaders": loader, "order": order, "status": status}
        if game_version:
            params["game_versions"] = game_version
        
        data = self._request("GET", f"/project/{project_id}/version", params)
        
        versions = []
        for v in data.get("versions", []):
            v_dict = v.copy()
            v_dict["files"] = v.get("files", [])
            versions.append(ModrinthVersion(**v_dict, project_id=project_id))
        
        return versions
    
    def get_project(self, project_id: str) -> Optional[ModrinthProject]:
        """Get project details by ID."""
        data = self._request("GET", f"/project/{project_id}")
        if data.get("error") == "not_found":
            return None
        return ModrinthProject(**data, project_id=project_id)
    
    def get_project_by_slug(self, slug: str) -> Optional[ModrinthProject]:
        """Find a project by slug."""
        params = {"q": slug}
        data = self._request("GET", "/project", params=params)
        
        for p in data.get("projects", []):
            if p.get("slug") == slug:
                return ModrinthProject(**p, project_id=p["id"])
        return None
    
    def get_version_files(self, project_id: str, version_id: str) -> Dict[str, Dict[str, Any]]:
        """Get files for a version."""
        data = self._request("GET", f"/project/{project_id}/version/{version_id}/files")
        return {f["id"]: f for f in data}
    
    def get_file_hash(self, project_id: str, version_id: str, file_id: str) -> str:
        """Get the hash of a file."""
        files = self.get_version_files(project_id, version_id)
        if file_id in files:
            return files[file_id].get("hash", "")
        raise ValueError(f"File {file_id} not found in version {version_id}")
    
    def get_newest_build(
        self,
        project_id: str,
        game_version: Optional[str] = None,
        loader: str = "fabric",
        channel: str = "release"
    ) -> Optional[ModrinthVersion]:
        """Get the newest build for a project."""
        order = "desc" if channel == "release" else "asc"
        versions = self.get_versions(project_id, loader, game_version, order=order, status=channel)
        
        # Filter to the requested channel type
        channel_map = {"release": "release", "beta": "beta", "alpha": "alpha"}
        channel_type = channel_map.get(channel, "release")
        filtered = [v for v in versions if v.version_type == channel_type]
        
        if not filtered:
            return None
        return filtered[0]
    
    def get_newest_build_by_number(
        self,
        project_id: str,
        version_number: str,
        loader: str = "fabric"
    ) -> Optional[ModrinthVersion]:
        """Get a specific version by number."""
        params = {"loaders": loader, "versions": version_number}
        
        data = self._request("GET", f"/project/{project_id}/version", params=params)
        
        if data.get("versions"):
            return ModrinthVersion(**data["versions"][0], project_id=project_id)
        return None
    
    def get_all_project_versions(self, project_id: str) -> List[ModrinthVersion]:
        """Get all versions without filtering."""
        params = {"order": "desc"}
        data = self._request("GET", f"/project/{project_id}/version", params=params)
        
        versions = []
        for v in data.get("versions", []):
            v_dict = v.copy()
            v_dict["files"] = v.get("files", [])
            versions.append(ModrinthVersion(**v_dict, project_id=project_id))
        
        return versions
    
    def search_mods(self, query: str) -> List[Dict[str, Any]]:
        """Search for mods by name."""
        params = {"q": query}
        data = self._request("GET", "/mod", params=params)
        return data.get("results", [])


class ModrinthAPI:
    """High-level Modrinth API wrapper for packtool."""
    
    def __init__(self, token: Optional[str] = None):
        self.client = ModrinthClient(token)
        self._project_cache: Dict[str, ModrinthProject] = {}
        self._version_cache: Dict[str, List[ModrinthVersion]] = {}
    
    def get_project(self, slug: str) -> Optional[ModrinthProject]:
        """Get or cache a project by slug."""
        if slug in self._project_cache:
            return self._project_cache[slug]
        
        project = self.client.get_project_by_slug(slug)
        if project:
            self._project_cache[slug] = project
        return project
    
    def get_versions(
        self,
        slug: str,
        loader: str = "fabric",
        game_version: Optional[str] = None,
        channel: str = "release"
    ) -> List[ModrinthVersion]:
        """Get versions for a project by slug."""
        project = self.get_project(slug)
        if not project:
            return []
        
        return self.client.get_versions(project.id, loader, game_version, channel)
    
    def get_newest_version(
        self,
        slug: str,
        game_version: Optional[str] = None,
        loader: str = "fabric",
        channel: str = "release"
    ) -> Optional[ModrinthVersion]:
        """Get the newest version for a project."""
        versions = self.get_versions(slug, loader, game_version, channel)
        return versions[0] if versions else None
    
    def get_all_versions(self, slug: str) -> List[ModrinthVersion]:
        """Get all versions for a project."""
        project = self.get_project(slug)
        if not project:
            return []
        return self.client.get_all_project_versions(project.id)
    
    def get_mod(self, project_id: str, version_number: str) -> Optional[ModrinthVersion]:
        """Get a specific mod version by number."""
        return self.client.get_newest_build_by_number(project_id, version_number)
    
    def get_mod_by_id(self, project_id: str) -> Optional[ModrinthProject]:
        """Get a project by ID."""
        return self.client.get_project(project_id)


def get_client(token: Optional[str] = None) -> ModrinthAPI:
    """Get the global client instance."""
    return ModrinthAPI(token)


# Test data for offline testing
MOCK_MODRINTH_RESPONSES: Dict[str, Any] = {}

def set_mock_response(project_id: str, data: Any):
    """Set a mock response for testing."""
    MOCK_MODRINTH_RESPONSES[project_id] = data


def get_mock_response(project_id: str) -> Any:
    """Get a mock response for testing."""
    return MOCK_MODRINTH_RESPONSES.get(project_id)


class MockModrinthClient(ModrinthClient):
    """Mock client for testing without network calls."""
    
    def __init__(self, mock_data: Optional[Dict] = None):
        super().__init__(token=None)
        self.mock_data = mock_data or {}
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        # Simple mock implementation
        if method == "GET" and endpoint.startswith("/project/"):
            project_id = endpoint.split("/")[2]
            return self.mock_data.get(project_id, {"error": "not_found"})
        return {"error": "not_implemented"}


def get_mock_client(data: Optional[Dict] = None) -> MockModrinthClient:
    """Get a mock client for testing."""
    return MockModrinthClient(data)
