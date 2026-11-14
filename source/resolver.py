"""
Mod resolver for packtool.
Resolves mod list, handles fallbacks, companions, and computes completeness.
"""

from typing import List, Dict, Set, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from source.models import ModConfig, ModFile, McVersion


class ModResolution(BaseModel):
    """Result of resolving a single mod."""
    mod_id: str
    mod_name: str
    version_id: str
    version_number: str
    version_type: str
    file_name: str
    file_url: str
    sha1: str
    sha512: str
    size: int
    source: str
    client: bool = True
    server: bool = True
    fallback_used: bool = False
    fallback_id: Optional[str] = None
    companions_added: List[str] = Field(default_factory=list)
    dependencies_added: List[str] = Field(default_factory=list)


class ResolutionResult(BaseModel):
    """Result of resolving mods for a Minecraft version."""
    minecraft_version: str
    edition: str
    mods: List[ModResolution] = Field(default_factory=list)
    missing_mods: List[str] = Field(default_factory=list)
    fallbacks_used: List[str] = Field(default_factory=list)
    companions_added: List[str] = Field(default_factory=list)
    dependencies_added: List[str] = Field(default_factory=list)
    completeness: float = 0.0
    completeness_details: Dict[str, Any] = Field(default_factory=dict)
    resolved_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ModResolver:
    """Resolves mod list for a pack."""
    
    def __init__(
        self,
        mods: List[Dict[str, Any]],
        parent_project_id: str,
        manifest_settings: Dict[str, Any]
    ):
        self.mods = mods
        self.parent_project_id = parent_project_id
        self.manifest_settings = manifest_settings
        self.mod_map: Dict[str, Dict[str, Any]] = {}
        self._build_mod_map()
    
    def _build_mod_map(self):
        """Build a map of mod IDs to their configs."""
        for mod in self.mods:
            mod_id = mod.get("id", "")
            if mod_id:
                self.mod_map[mod_id] = mod
    
    def resolve(
        self,
        minecraft_version: str,
        edition: str,
        parent_versions: List[Dict[str, Any]]
    ) -> ResolutionResult:
        """
        Resolve the mod list for a Minecraft version and edition.
        
        Args:
            minecraft_version: The Minecraft version string (e.g., "26.2")
            edition: "full" or "lite"
            parent_versions: List of parent mod dicts with project_id, version_id, etc.
        
        Returns:
            ResolutionResult with all mod details
        """
        wanted_mods = self._get_wanted_mods(minecraft_version)
        parent_mod_ids = {m.get("project_id", m.get("id", "")) for m in parent_versions}
        
        # Filter wanted mods by parent availability
        wanted_ids = [mod_id for mod_id in wanted_mods if mod_id in parent_mod_ids]
        
        # Resolve each mod
        resolved = []
        missing = []
        fallbacks_used = []
        companions_added = []
        dependencies_added = []
        
        for mod_id in wanted_ids:
            result = self._resolve_single_mod(mod_id, minecraft_version, edition, parent_versions)
            if result:
                resolved.append(result)
                if result.fallback_used:
                    fallbacks_used.append(mod_id)
                companions_added.extend(result.companions_added)
                dependencies_added.extend(result.dependencies_added)
            else:
                missing.append(mod_id)
        
        # Compute completeness
        total_wanted = len(wanted_mods)
        if total_wanted == 0:
            completeness = 100.0
        else:
            completeness = (len(resolved) / total_wanted) * 100
        
        return ResolutionResult(
            minecraft_version=minecraft_version,
            edition=edition,
            mods=resolved,
            missing_mods=missing,
            fallbacks_used=fallbacks_used,
            companions_added=companions_added,
            dependencies_added=dependencies_added,
            completeness=completeness,
            completeness_details={
                "total_wanted": total_wanted,
                "resolved": len(resolved),
                "missing": len(missing),
                "fallbacks_used": len(fallbacks_used),
                "companions_added": len(companions_added),
                "dependencies_added": len(dependencies_added),
                "completeness": f"{completeness:.0f}%",
                "threshold": self.manifest_settings.get("completeness", {}).get("alpha_at", 50),
            },
            resolved_at=datetime.now().isoformat()
        )
    
    def _get_wanted_mods(self, minecraft_version: str) -> List[str]:
        """Get the list of wanted mod IDs for a Minecraft version."""
        wanted = []
        
        for mod in self.mods:
            mod_id = mod.get("id", "")
            if not mod_id:
                continue
            
            # Check versions field
            versions = mod.get("versions")
            if versions and minecraft_version not in versions:
                continue
            
            # Skip excluded mods
            if mod.get("exclude", False):
                continue
            
            wanted.append(mod_id)
        
        return wanted
    
    def _resolve_single_mod(
        self,
        mod_id: str,
        minecraft_version: str,
        edition: str,
        parent_versions: List[Dict[str, Any]]
    ) -> Optional[ModResolution]:
        """Resolve a single mod."""
        if mod_id not in self.mod_map:
            return None
        
        mod_config = self.mod_map[mod_id]
        
        # Check lite flag
        if edition == "lite" and not mod_config.get("lite", True):
            return None
        
        # Try to get version from parent first
        for parent_mod in parent_versions:
            parent_id = parent_mod.get("project_id", parent_mod.get("id", ""))
            if parent_id == mod_id:
                return self._create_resolution_from_parent(parent_mod, mod_id)
        
        # Try to get version from manifest
        for mod in self.mods:
            if mod.get("id") != mod_id:
                continue
            
            versions = mod.get("versions")
            if versions and minecraft_version not in versions:
                continue
            
            # Get the build
            build = self._get_build_for_mod(mod, minecraft_version)
            if build:
                return self._create_resolution_from_build(build, mod_id, mod)
            
            # Try fallbacks
            fallbacks = mod.get("fallback", [])
            for fallback_mod in fallbacks:
                fallback_build = self._get_build_for_mod(fallback_mod, minecraft_version)
                if fallback_build:
                    return self._create_resolution_from_build(fallback_build, mod_id, fallback_mod, fallback_used=True)
        
        return None
    
    def _get_build_for_mod(self, mod: Dict[str, Any], minecraft_version: str) -> Optional[Dict[str, Any]]:
        """Get the build for a mod."""
        # Placeholder - in real implementation, this would query Modrinth
        # For now, return None to indicate missing build
        return None
    
    def _create_resolution_from_parent(
        self,
        parent_mod: Dict[str, Any],
        mod_id: str
    ) -> ModResolution:
        """Create a resolution from parent mod data."""
        return ModResolution(
            mod_id=mod_id,
            mod_name=self.mod_map.get(mod_id, {}).get("name", ""),
            version_id=parent_mod.get("version_id", ""),
            version_number=parent_mod.get("version_number", ""),
            version_type="release",
            file_name=parent_mod.get("file_name", ""),
            file_url=parent_mod.get("file_url", ""),
            sha1=parent_mod.get("sha1", ""),
            sha512=parent_mod.get("sha512", ""),
            size=parent_mod.get("size", 0),
            source="parent",
            client=parent_mod.get("client", True),
            server=parent_mod.get("server", True)
        )
    
    def _create_resolution_from_build(
        self,
        build: Dict[str, Any],
        mod_id: str,
        mod_config: Dict[str, Any],
        fallback_used: bool = False
    ) -> ModResolution:
        """Create a resolution from a build."""
        result = ModResolution(
            mod_id=mod_id,
            mod_name=mod_config.get("name", ""),
            version_id=build.get("version_id", ""),
            version_number=build.get("version_number", ""),
            version_type=build.get("version_type", "release"),
            file_name=build.get("file_name", ""),
            file_url=build.get("file_url", ""),
            sha1=build.get("sha1", ""),
            sha512=build.get("sha512", ""),
            size=build.get("size", 0),
            source="manifest",
            client=build.get("client", True),
            server=build.get("server", True)
        )
        
        if fallback_used:
            result.fallback_used = True
            result.fallback_id = mod_id
        
        return result
    
    def resolve_lite(self, result: ResolutionResult) -> ResolutionResult:
        """Derive the lite set from the full result."""
        lite_mods = []
        
        for mod in result.mods:
            if mod.mod_id in self.mod_map:
                mod_config = self.mod_map[mod.mod_id]
                if mod_config.get("lite", True):
                    lite_mods.append(mod)
        
        lite_result = ResolutionResult(
            minecraft_version=result.minecraft_version,
            edition="lite",
            mods=lite_mods,
            missing_mods=result.missing_mods,
            fallbacks_used=[],
            companions_added=[],
            dependencies_added=[],
            completeness=result.completeness,  # Lite has same completeness
            completeness_details={
                "total_wanted": result.completeness_details.get("total_wanted", 0),
                "resolved": len(lite_mods),
                "missing": len(result.missing_mods),
                "fallbacks_used": 0,
                "companions_added": 0,
                "dependencies_added": 0,
                "completeness": f"{result.completeness:.0f}%",
                "threshold": self.manifest_settings.get("completeness", {}).get("alpha_at", 50),
            },
            resolved_at=result.resolved_at
        )
        
        return lite_result


class ReportFormatter:
    """Formats resolution results as human-readable reports."""
    
    @staticmethod
    def format_resolution(result: ResolutionResult) -> str:
        """Format a resolution result as a readable report."""
        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f" Minecraft Version: {result.minecraft_version}")
        lines.append(f" Edition: {result.edition}")
        lines.append(f"{'='*70}")
        lines.append(f"\nCompleteness: {result.completeness:.0f}%")
        lines.append(f"  - Total wanted: {result.completeness_details.get('total_wanted', 'N/A')}")
        lines.append(f"  - Resolved: {result.completeness_details.get('resolved', 'N/A')}")
        lines.append(f"  - Missing: {len(result.missing_mods)}")
        lines.append(f"  - Threshold: {result.completeness_details.get('threshold', 'N/A')}")
        
        if result.missing_mods:
            lines.append(f"\nMISSING MODS ({len(result.missing_mods)}):")
            for mod_id in result.missing_mods:
                lines.append(f"  - {mod_id}")
        
        lines.append(f"\nRESOLVED MODS ({len(result.mods)}):")
        for mod in result.mods:
            source = mod.source
            if mod.fallback_used:
                source += " (FALLBACK)"
            elif mod.mod_id != mod.mod_name:
                source += " (fallback)"
            lines.append(f"  {mod.mod_name:30} [{source:15}] {mod.version_number}")
        
        if result.fallbacks_used:
            lines.append(f"\nFALLBACKS USED ({len(result.fallbacks_used)}):")
            for mod_id in result.fallbacks_used:
                lines.append(f"  - {mod_id}")
        
        if result.companions_added:
            lines.append(f"\nCOMPANIONS ADDED ({len(result.companions_added)}):")
            for companion in result.companions_added:
                lines.append(f"  - {companion}")
        
        if result.dependencies_added:
            lines.append(f"\nDEPENDENCIES ADDED ({len(result.dependencies_added)}):")
            for dep in result.dependencies_added:
                lines.append(f"  - {dep}")
        
        lines.append(f"\nGenerated: {result.resolved_at}")
        lines.append(f"{'='*70}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_report(results: List[ResolutionResult]) -> str:
        """Format multiple resolution results."""
        lines = []
        lines.append("\n" + "="*70)
        lines.append("                  MOD RESOLUTION REPORT")
        lines.append("="*70)
        lines.append(f"\nTotal Minecraft versions: {len(results)}")
        
        for result in results:
            lines.append(ReportFormatter.format_resolution(result))
        
        return "\n".join(lines)
    
    @staticmethod
    def format_summary(results: List[ResolutionResult]) -> str:
        """Format a concise summary of all results."""
        lines = []
        lines.append("\n" + "="*70)
        lines.append("                  MOD RESOLUTION SUMMARY")
        lines.append("="*70)
        
        for result in results:
            lines.append(f"\n{result.minecraft_version} ({result.edition}): {result.completeness:.0f}%")
            if result.missing_mods:
                lines.append(f"  Missing: {', '.join(result.missing_mods)}")
            if result.completeness < 50:
                lines.append(f"  WARNING: Below alpha threshold!")
        
        return "\n".join(lines)
