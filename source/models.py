"""
Pydantic models for packtool data structures.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PackSettings(BaseModel):
    """Settings for the modpack."""
    loader: str = "fabric"
    channel: str = "release"
    version_format: str = "{mc}-{major}.{minor}"
    completeness: Dict[str, int] = {
        "release_at": 95,
        "beta_at": 70,
        "alpha_at": 50
    }
    publish: Dict[str, bool] = {
        "auto_publish": False,
        "min_days_between": 1
    }
    notify: Dict[str, bool] = {
        "ntfy_email": True
    }


class ModConfig(BaseModel):
    """Configuration for a mod."""
    id: str
    name: Optional[str] = None
    lite: bool = True
    required: bool = False
    fallback: List["ModConfig"] = Field(default_factory=list)
    companions: List["ModConfig"] = Field(default_factory=list)
    exclude: bool = False
    versions: Optional[List[str]] = None
    pin: Optional[Dict[str, str]] = None


class McVersion(BaseModel):
    """Minecraft version."""
    version: str
    type: str = "release"
    release_date: Optional[str] = None


class McVersionsSettings(BaseModel):
    """Minecraft versions configuration."""
    active: List[str] = Field(default_factory=list)
    candidate: List[str] = Field(default_factory=list)
    retired: List[str] = Field(default_factory=list)


class ParentSettings(BaseModel):
    """Parent pack configuration."""
    project: str = "fabulously-optimized"
    remove_files: List[str] = Field(default_factory=list)
    rename_in_files: Dict[str, str] = Field(default_factory=dict)


class ModFile(BaseModel):
    """A single mod file."""
    project_id: str
    slug: str
    version_id: str
    version_number: str
    version_type: str
    file_name: str
    sha1: str
    sha512: str
    size: int
    download_url: str
    client: bool = True
    server: bool = True
    source: str = "manifest"
    dependency_ids: List[str] = Field(default_factory=list)


class LockFile(BaseModel):
    """Lock file for queued/uploaded builds."""
    edition: str
    minecraft_version: str
    loader_version: str
    parent_version_id: str
    mods: List[ModFile] = Field(default_factory=list)
    content_hash: Optional[str] = None


class UploadState(BaseModel):
    """Upload state tracking."""
    edition: str
    minecraft_version: str
    last_upload_version: Optional[str] = None
    last_upload_time: Optional[str] = None
    last_content_hash: Optional[str] = None


class ModrinthVersion(BaseModel):
    """A Modrinth version."""
    id: str
    name: str
    slug: str
    version_number: str
    version_type: str
    description: str = ""
    changelog: str = ""
    loaders: List[str] = Field(default_factory=list)
    game_versions: List[str] = Field(default_factory=list)
    authors: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    files: List[Dict[str, Any]] = Field(default_factory=list)
    project_id: str = ""
    draft: bool = False


class ModrinthProject(BaseModel):
    """A Modrinth project."""
    id: str
    slug: str
    name: str
    description: str = ""
    project_type: str = "modpack"
    authors: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    folders: List[Dict[str, Any]] = Field(default_factory=list)
    featured_image: Optional[str] = None
    downloads: int = 0
    users: int = 0
    versions: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: Optional[str] = None
    created_at: Optional[str] = None


class BuildItem(BaseModel):
    """A queued build."""
    pack: str
    minecraft_version: str
    pack_version: str
    artifact_path: str
    checksum: str
    content_hash: str
    status: str = "ready"
    added_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    uploaded_at: Optional[str] = None


class BuildQueue(BaseModel):
    """Queue state."""
    items: List[BuildItem] = Field(default_factory=list)


class RunState(BaseModel):
    """Run state tracking."""
    run_id: str
    run_type: str
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    status: str = "running"
    results: Dict[str, Any] = Field(default_factory=dict)
    failures: List[Dict[str, Any]] = Field(default_factory=list)
