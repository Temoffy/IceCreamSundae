"""
GitHub API client for PR creation and updates.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any


class GithubClient:
    """GitHub API client."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN not set")
        
        self.token_header = f"Bearer {self.token}"
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": self.token_header,
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_project_id(self, org: str, repo: str) -> str:
        """Get the GitHub project ID from env."""
        return f"{org}/{repo}"
    
    def push_to_branch(
        self,
        branch_name: str,
        files: Dict[str, str],
        commit_message: str
    ) -> bool:
        """Push files to a branch."""
        try:
            result = subprocess.run(
                ["git", "ls-remote", "origin", f"refs/heads/{branch_name}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            else:
                subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push", "origin", branch_name], check=True)
                
            return True
                
        except subprocess.CalledProcessError as e:
            print(f"Git error: {e}")
            return False
    
    def create_pr(
        self,
        repo: str,
        branch_name: str,
        title: str,
        body: str
    ) -> Optional[Dict[str, Any]]:
        """Create a pull request."""
        parts = repo.split("/")
        if len(parts) != 2:
            raise ValueError("Invalid repo format. Use org/repo")
        
        org, repo_name = parts
        
        url = f"{self.base_url}/repos/{org}/{repo_name}/pulls"
        
        payload = {
            "title": title,
            "head": branch_name,
            "base": "main",
            "body": body
        }
        
        response = subprocess.run(
            ["curl", "-s", "-H", self.token_header, "-H", "Accept: application/vnd.github.v3+json", "-X", "POST", "-d", json.dumps(payload), url],
            capture_output=True,
            text=True
        )
        
        if response.returncode != 0:
            return None
        
        return json.loads(response.stdout)
    
    def get_latest_commit(self, branch: str) -> Optional[str]:
        """Get the latest commit hash for a branch."""
        result = subprocess.run(
            ["git", "rev-parse", f"origin/{branch}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
