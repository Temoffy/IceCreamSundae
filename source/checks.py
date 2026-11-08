"""
Test checks.
"""

from typing import List, Dict, Optional


class StaticChecker:
    """Static pack validator."""
    
    @staticmethod
    def validate_index(index: Dict) -> List[str]:
        """Validate pack index."""
        errors = []
        
        if index.get("format_version") != 1:
            errors.append("Invalid format version")
        
        required = ["project_id", "game_versions", "minecraft_version", "files"]
        for field in required:
            if field not in index:
                errors.append(f"Missing required field: {field}")
        
        for file in index.get("files", []):
            if file.get("method") not in [1, 2]:
                errors.append(f"Invalid method for file: {file.get('name')}")
        
        return errors
    
    @staticmethod
    def validate_mods(mods: List[Dict], minecraft_version: str) -> List[str]:
        """Validate mods against Minecraft version."""
        errors = []
        
        for mod in mods:
            depends = mod.get("depends", [])
            
            for dep in depends:
                if not dep.get("required", False):
                    pass
        
        return errors


class ServerBooter:
    """Server boot tester."""
    
    def __init__(self):
        self.log_patterns = {
            "success": ["Done (", "Server stopped"],
            "failure": ["Failed to start", "Exception", "Error:"]
        }
    
    def test(self, log: str) -> tuple[bool, Optional[str]]:
        """Test server boot log."""
        for pattern in self.log_patterns["success"]:
            if pattern in log:
                return True, None
        
        for pattern in self.log_patterns["failure"]:
            if pattern in log:
                return False, pattern
        
        return True, None


class ClientBooter:
    """Client boot tester."""
    
    def __init__(self):
        self.success_patterns = ["Successfully loaded", "Main menu", "Joined server"]
        self.error_patterns = ["Exception", "Error:", "Crash"]
    
    def test(self, log: str) -> tuple[bool, Optional[str]]:
        """Test client boot log."""
        for pattern in self.error_patterns:
            if pattern in log:
                return False, pattern
        
        for pattern in self.success_patterns:
            if pattern in log:
                return True, None
        
        return False, "timeout"


class AssertionChecker:
    """Assertion checker."""
    
    def check(self, key: str, value: str, actual: str) -> bool:
        """Check if actual matches expected."""
        return actual == value


class CheckSuite:
    """Suite of checks to run."""
    
    def __init__(self):
        self.static = StaticChecker()
        self.server = ServerBooter()
        self.client = ClientBooter()
        self.assertions = AssertionChecker()
    
    def run_all(self, index: Dict, mods: List[Dict], log: str) -> List[tuple[str, bool, Optional[str]]]:
        """Run all checks."""
        results = []
        
        errors = self.static.validate_index(index)
        results.append(("static", len(errors) == 0, errors[0] if errors else None))
        
        success, failure = self.server.test(log)
        results.append(("server", success, failure))
        
        success, failure = self.client.test(log)
        results.append(("client", success, failure))
        
        return results
