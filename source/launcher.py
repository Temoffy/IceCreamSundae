"""
Game launcher.
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
