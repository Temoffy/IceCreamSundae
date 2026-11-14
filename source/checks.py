"""
Test checks for packtool.
Phase 4: Static checks and boot tests.
"""

import json
import zipfile
from typing import List, Dict, Optional, Tuple, Any


class StaticChecker:
    """Static pack validator for Phase 4."""
    
    @staticmethod
    def validate_index(index: Dict) -> List[str]:
        """Validate pack index format."""
        errors = []
        
        # Check format version
        if index.get("format_version") != 1:
            errors.append(f"Invalid format version (expected 1, got: {index.get('format_version')})")
        
        # Check required fields
        required = ["project_id", "game_versions", "minecraft_version", "files"]
        for field in required:
            if field not in index:
                errors.append(f"Missing required field: {field}")
        
        # Validate game_versions is a list
        if not isinstance(index.get("game_versions"), list):
            errors.append("game_versions must be a list")
        
        # Validate files list
        files = index.get("files", [])
        if not isinstance(files, list):
            errors.append("files must be a list")
        else:
            for i, file_entry in enumerate(files):
                # Validate file entry structure
                if not isinstance(file_entry, dict):
                    errors.append(f"file[{i}] must be an object")
                    continue
                
                # Check required file fields
                if "name" not in file_entry:
                    errors.append(f"file[{i}] missing 'name'")
                
                if "type" not in file_entry or file_entry.get("type") != "file":
                    errors.append(f"file[{i}] type must be 'file'")
                
                if "method" not in file_entry:
                    errors.append(f"file[{i}] missing 'method'")
                elif file_entry.get("method") not in [1, 2]:
                    errors.append(f"file[{i}] method must be 1 or 2, got: {file_entry.get('method')}")
        
        return errors
    
    @staticmethod
    def validate_mod_jars(mods: List[Dict], minecraft_version: str) -> List[str]:
        """Validate mods against Minecraft version and loader requirements."""
        errors = []
        
        # In a real implementation, this would:
        # 1. Parse each jar's fabric.mod.json
        # 2. Check depends against Minecraft version
        # 3. Check loader compatibility
        # 4. Check for missing dependencies
        
        # For Phase 4, we do basic validation
        for mod in mods:
            mod_id = mod.get("mod_id", "unknown")
            mod_name = mod.get("mod_name", mod_id)
            
            # Check required field exists
            if "mod_id" not in mod:
                errors.append(f"Missing mod_id for: {mod_name}")
            
            # Check file_name exists
            if "file_name" not in mod:
                errors.append(f"Missing file_name for: {mod_name}")
        
        return errors
    
    @staticmethod
    def validate_pack_structure(pack_path: str) -> List[str]:
        """Validate pack file structure."""
        errors = []
        
        if not zipfile.is_zipfile(pack_path):
            errors.append(f"Not a valid zip file: {pack_path}")
            return errors
        
        with zipfile.ZipFile(pack_path, "r") as zf:
            # Check for index.json
            if "index.json" not in zf.namelist():
                errors.append("Missing index.json")
            else:
                try:
                    index_data = json.loads(zf.read("index.json").decode())
                    # Validate index
                    errors.extend(StaticChecker.validate_index(index_data))
                except json.JSONDecodeError as e:
                    errors.append(f"Invalid JSON in index.json: {e}")
            
            # Check for mods directory
            mod_files = [n for n in zf.namelist() if n.startswith("mods/") and n.endswith(".jar")]
            if mod_files:
                print(f"  Found {len(mod_files)} mod jars")
        
        return errors


class ServerBooter:
    """Server boot tester for Phase 4."""
    
    def __init__(self):
        self.log_patterns = {
            "success": [
                "Done (main)",
                "Server stopped",
                "Server finished starting",
                "Finished loading",
                "Preparing spawn",
            ],
            "failure": [
                "Failed to start",
                "Exception",
                "Error:",
                "crashed",
                "terminated",
            ]
        }
    
    def test(self, log: str) -> Tuple[bool, Optional[str]]:
        """Test server boot log."""
        for pattern in self.log_patterns["success"]:
            if pattern in log:
                return True, None
        
        for pattern in self.log_patterns["failure"]:
            if pattern in log:
                return False, pattern
        
        # No pattern matched - consider as unknown
        return True, None


class ClientBooter:
    """Client boot tester for Phase 4."""
    
    def __init__(self):
        self.success_patterns = [
            "Successfully loaded",
            "Main menu",
            "Joined server",
            "Player joined",
            "Resource pack installed",
        ]
        self.error_patterns = [
            "Exception",
            "Error:",
            "Crash",
            "crashed",
            "terminated",
            "failed to start",
        ]
    
    def test(self, log: str) -> Tuple[bool, Optional[str]]:
        """Test client boot log."""
        for pattern in self.error_patterns:
            if pattern in log:
                return False, pattern
        
        for pattern in self.success_patterns:
            if pattern in log:
                return True, None
        
        # No pattern matched - consider as timeout
        return False, "timeout"


class AssertionChecker:
    """Assertion checker for config and game state."""
    
    def __init__(self):
        self.checks: List[Dict[str, Any]] = []
    
    def add_check(self, key: str, expected: str, condition: str = "equals"):
        """Add an assertion check."""
        self.checks.append({
            "key": key,
            "expected": expected,
            "condition": condition
        })
    
    def check(self, key: str, expected: str, actual: str) -> bool:
        """Check if actual matches expected."""
        if condition == "equals":
            return actual == expected
        elif condition == "exists":
            return actual is not None
        return False
    
    def run_checks(self, actual_values: Dict[str, str]) -> List[Dict[str, Any]]:
        """Run all assertion checks."""
        failures = []
        
        for check in self.checks:
            key = check["key"]
            expected = check["expected"]
            condition = check["condition"]
            
            actual = actual_values.get(key, "")
            
            if not self.check(key, expected, actual):
                failures.append({
                    "key": key,
                    "expected": expected,
                    "actual": actual,
                    "condition": condition
                })
        
        return failures


class CheckSuite:
    """Suite of checks to run for Phase 4."""
    
    def __init__(self):
        self.static = StaticChecker()
        self.server = ServerBooter()
        self.client = ClientBooter()
        self.assertions = AssertionChecker()
    
    def run_all(
        self,
        index: Dict,
        mods: List[Dict],
        log: Optional[str] = None
    ) -> List[Tuple[str, bool, Optional[str]]]:
        """Run all checks and return results."""
        results = []
        
        # Static checks
        errors = self.static.validate_index(index)
        results.append(("static_index", len(errors) == 0, errors[0] if errors else None))
        
        errors = self.static.validate_mod_jars(mods)
        results.append(("static_mods", len(errors) == 0, errors[0] if errors else None))
        
        # Server boot check (if log provided)
        if log:
            success, failure = self.server.test(log)
            results.append(("server_boot", success, failure))
        
        # Client boot check (if log provided)
        if log:
            success, failure = self.client.test(log)
            results.append(("client_boot", success, failure))
        
        return results
    
    def check_pack(self, pack_path: str) -> List[str]:
        """Check a complete pack file."""
        return self.static.validate_pack_structure(pack_path)


def validate_pack(pack_path: str) -> Tuple[bool, List[str]]:
    """Validate a complete pack file."""
    suite = CheckSuite()
    errors = suite.check_pack(pack_path)
    return len(errors) == 0, errors


def run_tests(
    index: Dict,
    mods: List[Dict],
    server_log: Optional[str] = None,
    client_log: Optional[str] = None
) -> List[Tuple[str, bool, Optional[str]]]:
    """Run all test tiers."""
    suite = CheckSuite()
    return suite.run_all(index, mods, server_log or client_log)
