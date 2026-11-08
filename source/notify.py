"""
Notification manager using ntfy.
"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path


class NtfyManager:
    """Manages ntfy notifications."""
    
    def __init__(self, topic: Optional[str] = None, token: Optional[str] = None):
        self.topic = topic or os.environ.get("NTFY_TOPIC")
        self.token = token or os.environ.get("NTFY_TOKEN")
        
        if not self.topic:
            raise ValueError("NTFY_TOPIC not set")
        
        self.base_url = "https://ntfy.sh"
        self.endpoint = f"{self.base_url}/{self.topic}"
    
    def send_alert(
        self,
        title: str,
        message: str,
        priority: int = 0,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Send an alert notification using ntfy."""
        data = {
            "title": title,
            "message": message,
            "priority": priority
        }
        
        if tags:
            data["tags"] = tags
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            import httpx
            client = httpx.Client()
            response = client.post(self.endpoint, json=data, headers=headers)
            client.close()
            return response.status_code == 200
        except ImportError:
            print("httpx not available, using fallback")
            return False
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False
    
    def send_failure(
        self,
        run_type: str,
        minecraft_version: str,
        pack: str,
        failures: List[Dict]
    ) -> bool:
        """Send a failure notification."""
        title = f"⚠️ Build Failed: {pack} - {minecraft_version}"
        message = self._format_failure_message(run_type, failures)
        
        return self.send_alert(title, message, priority=3, tags=["failure"])
    
    def send_success(
        self,
        run_type: str,
        minecraft_version: str,
        pack: str
    ) -> bool:
        """Send a success notification."""
        title = f"✅ Build Complete: {pack} - {minecraft_version}"
        message = f"Build completed successfully for {pack} on Minecraft {minecraft_version}"
        
        return self.send_alert(title, message, priority=1, tags=["success"])
    
    def send_parent_pr(
        self,
        mc_version: str,
        parent_version: str,
        pr_url: Optional[str] = None
    ) -> bool:
        """Send a parent PR notification."""
        if pr_url:
            title = f"📋 Parent PR: {mc_version} -> {parent_version}"
            message = f"Parent pack changed. PR created: {pr_url}"
        else:
            title = f"📋 Parent PR: {mc_version} -> {parent_version}"
            message = "Parent pack changed. PR created. Awaiting review."
        
        return self.send_alert(title, message, priority=2, tags=["parent-change"])
    
    def _format_failure_message(self, run_type: str, failures: List[Dict]) -> str:
        """Format a failure message."""
        lines = [f"Run type: {run_type}"]
        lines.append(f"Failures: {len(failures)}")
        lines.append("")
        
        for i, failure in enumerate(failures, 1):
            lines.append(f"{i}. {failure.get('error', 'Unknown error')}")
            if failure.get('details'):
                lines.append(f"   Details: {failure['details']}")
        
        return "\n".join(lines)
    
    def send_heartbeat(self) -> bool:
        """Send a heartbeat to indicate the service is running."""
        title = "🟢 packtool heartbeat"
        message = "Service is operational"
        
        return self.send_alert(title, message, priority=0, tags=["heartbeat"])
