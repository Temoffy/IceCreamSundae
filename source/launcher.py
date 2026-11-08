"""
Game launcher for testing.
"""

import subprocess
import time
from typing import Optional
from pathlib import Path


class GameLauncher:
    """Launcher for Minecraft games."""
    
    def __init__(self, portablemc_path: Optional[str] = None):
        self.portablemc_path = portablemc_path or "portablemc"
    
    def boot(
        self,
        game_dir: str,
        mod_dir: str,
        java_args: Optional[str] = None,
        timeout: int = 60
    ) -> tuple[bool, str, str]:
        """
        Boot the game.
        
        Returns:
            Tuple of (success, client_log, server_log)
        """
        Path(game_dir).mkdir(parents=True, exist_ok=True)
        
        cmd = [self.portablemc_path, "--gameDir", game_dir]
        
        if mod_dir:
            cmd.extend(["--modDir", mod_dir])
        
        if java_args:
            cmd.extend(java_args.split())
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        output = []
        while proc.poll() is None:
            line = proc.stdout.readline().decode() if proc.stdout else ""
            if line:
                output.append(line)
            time.sleep(0.1)
        
        proc.wait(timeout=timeout)
        
        success = proc.returncode == 0
        return success, "".join(output), ""
    
    def boot_with_xvfb(
        self,
        game_dir: str,
        mod_dir: str,
        java_args: Optional[str] = None,
        timeout: int = 60
    ) -> tuple[bool, str, str]:
        """Boot the game with xvfb."""
        cmd = ["xvfb-run", "-a", self.portablemc_path, "--gameDir", game_dir]
        
        if mod_dir:
            cmd.extend(["--modDir", mod_dir])
        
        if java_args:
            cmd.extend(java_args.split())
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        output = []
        while proc.poll() is None:
            line = proc.stdout.readline() if proc.stdout else ""
            if line:
                output.append(line)
            time.sleep(0.1)
        
        proc.wait(timeout=timeout)
        
        success = proc.returncode == 0
        return success, "".join(output), ""


def wait_for_main_menu(
    game_dir: str,
    timeout: int = 60
) -> tuple[bool, str]:
    """
    Wait for the game to reach main menu.
    
    Returns (success, log).
    """
    import glob
    
    log_dir = Path(game_dir) / "logs"
    logs = list(log_dir.glob("*.log"))
    
    if not logs:
        return False, "No logs found"
    
    latest_log = max(logs, key=lambda p: p.stat().st_mtime)
    
    with open(latest_log) as f:
        log = f.read()
    
    success_patterns = ["Done (", "Server stopped", "Main menu"]
    
    for pattern in success_patterns:
        if pattern in log:
            return True, log
    
    return False, log


def wait_for_player_join(
    server_log: str,
    timeout: int = 30
) -> tuple[bool, str]:
    """
    Wait for a player to join the server.
    
    Returns (success, log).
    """
    patterns = ["Player joined", "Joined server"]
    
    for pattern in patterns:
        if pattern in server_log:
            return True, server_log
    
    return False, server_log
