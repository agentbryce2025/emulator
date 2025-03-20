#!/usr/bin/env python3
"""
QEMU wrapper for the undetected Android emulator.
This module handles QEMU configuration, startup, and control.
"""

import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class QEMUWrapper:
    """Wrapper for QEMU virtualization engine."""
    
    def __init__(self, config_path=None):
        """Initialize QEMU wrapper with optional configuration."""
        self.config_path = config_path or os.path.join(
            os.path.expanduser("~"), ".config", "undetected-emulator", "qemu.conf"
        )
        self.qemu_process = None
        self.is_running = False
        
        # Default QEMU parameters
        self.params = {
            "memory": "2048",
            "smp": "4",
            "hda": "",
            "cpu": "host",
            "vga": "virtio",  # Using virtio again for better performance
            "display": "sdl",  # SDL display for Windows compatibility
            "net": "user",
            "usb": "on",
            "usbdevice": "tablet",
            "audio": "none",  # Disable audio by default to avoid issues
            # Removed accelerate=kvm as it's not available on Windows
        }
        
        # Default QEMU path
        self.qemu_path = "qemu-system-x86_64"
        
        # Load configuration if available
        self._load_config()
        
        # Check for direct path to QEMU on Windows
        import platform
        if platform.system() == "Windows":
            common_paths = [
                "C:\\Program Files\\qemu\\qemu-system-x86_64.exe",
                "C:\\Program Files (x86)\\qemu\\qemu-system-x86_64.exe",
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.environ.get("ProgramW6432", "C:\\Program Files"), "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.path.expanduser("~"), "Desktop", "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.path.expanduser("~"), "Documents", "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.path.expanduser("~"), "Downloads", "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.environ.get("ProgramW6432", "C:\\Program Files"), "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.path.expanduser("~"), "Desktop", "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.path.expanduser("~"), "Documents", "qemu", "qemu-system-x86_64.exe"),
                os.path.join(os.path.expanduser("~"), "Downloads", "qemu", "qemu-system-x86_64.exe"),]
            
            # Check if we loaded a path from config
            if hasattr(self, "qemu_path") and os.path.exists(self.qemu_path):
                pass  # Use the path we already loaded
            else:
                # Try the common paths
                for path in common_paths:
                    if os.path.exists(path):
                        self.qemu_path = path
                        logger.info(f"Using QEMU at: {path}")
                        break
        
    def _load_config(self):
        """Load QEMU configuration from file."""
        config_file = Path(self.config_path)
        if not config_file.exists():
            logger.warning(f"Configuration file {self.config_path} not found, using defaults")
            return
            
        try:
            with open(config_file, "r") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        key, value = line.strip().split("=", 1)
                        if key.strip() == "qemu_path":
                            # Special handling for qemu_path
                            self.qemu_path = value.strip()
                        else:
                            self.params[key.strip()] = value.strip()
            logger.info(f"Loaded configuration from {self.config_path}")
            
            if hasattr(self, "qemu_path") and self.qemu_path:
                logger.info(f"Using QEMU path from config: {self.qemu_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            
    def save_config(self):
        """Save current configuration to file."""
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        try:
            with open(self.config_path, "w") as f:
                f.write("# QEMU configuration for undetected Android emulator\n")
                f.write("# Generated automatically\n\n")
                
                # Save the QEMU path first
                if hasattr(self, "qemu_path") and self.qemu_path:
                    f.write(f"qemu_path={self.qemu_path}\n\n")
                
                # Save other parameters
                for key, value in self.params.items():
                    f.write(f"{key}={value}\n")
                    
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            
    def set_param(self, key, value):
        """Set a QEMU parameter."""
        self.params[key] = value
        
    def get_param(self, key):
        """Get a QEMU parameter."""
        return self.params.get(key)
        
    def build_command(self):
        """Build the QEMU command line."""
        cmd = [self.qemu_path]
        
        for key, value in self.params.items():
            if value == "on":
                cmd.append(f"-{key}")
            elif value:
                cmd.append(f"-{key}")
                cmd.append(value)
                
        return cmd
        
    def start(self):
        """Start the QEMU virtual machine."""
        if self.is_running:
            logger.warning("QEMU is already running")
            return False
            
        cmd = self.build_command()
        logger.info(f"Starting QEMU with command: {' '.join(cmd)}")
        
        try:
            # Check platform for Windows-specific behaviors
            import platform
            if platform.system() == "Windows":
                # Special handling for Windows to ensure the UI displays properly
                
                # Make sure SDL display is explicitly set for Windows
                self.params["display"] = "sdl"
                
                # Regenerate the command with updated display setting
                cmd = self.build_command()
                
                # Format command for Windows shell
                cmd_str = " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd)
                logger.info(f"Windows command string: {cmd_str}")
                
                # Create a visible window that stays open
                import subprocess
                from subprocess import CREATE_NEW_CONSOLE
                
                # Start the process in a way that keeps the window visible
                self.qemu_process = subprocess.Popen(
                    cmd_str,
                    shell=True,
                    creationflags=CREATE_NEW_CONSOLE
                )
            else:
                # On Linux/macOS, use the standard approach
                self.qemu_process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                
            self.is_running = True
            logger.info(f"QEMU started with PID {self.qemu_process.pid}")
            return True
        except Exception as e:
            logger.error(f"Error starting QEMU: {str(e)}")
            # Log more details in case of error
            import traceback
            logger.error(f"Detailed error: {traceback.format_exc()}")
            
            # If the standard launch failed, try an alternative approach for Windows
            if platform.system() == "Windows":
                logger.info("Standard QEMU launch failed, trying alternative approach...")
                
                try:
                    # Try with a different display setting
                    self.params["display"] = "gtk"
                    cmd = self.build_command()
                    
                    # Format command for Windows PowerShell
                    cmd_str = " ".join(f'"{c}"' if " " in str(c) and isinstance(c, str) else str(c) for c in cmd)
                    
                    # Start with maximum visibility
                    import subprocess
                    from subprocess import CREATE_NEW_CONSOLE
                    
                    self.qemu_process = subprocess.Popen(
                        cmd_str,
                        shell=True,
                        creationflags=CREATE_NEW_CONSOLE
                    )
                    
                    self.is_running = True
                    logger.info(f"QEMU started with alternative approach, PID: {self.qemu_process.pid}")
                    return True
                except Exception as e2:
                    logger.error(f"Error during alternative launch: {str(e2)}")
                    
                    # Final fallback to the most basic approach
                    try:
                        # Use the simplest command format with no display redirection
                        self.params["display"] = "none"  # Disable GUI temporarily
                        self.params["vnc"] = ":0"  # Enable VNC server on port 5900
                        cmd = self.build_command()
                        cmd_str = " ".join(f'"{c}"' if " " in str(c) and isinstance(c, str) else str(c) for c in cmd)
                        
                        self.qemu_process = subprocess.Popen(
                            cmd_str,
                            shell=True,
                            creationflags=CREATE_NEW_CONSOLE
                        )
                        
                        self.is_running = True
                        logger.info(f"QEMU started with VNC fallback, PID: {self.qemu_process.pid}")
                        logger.info("Connect to the emulator using a VNC client at localhost:5900")
                        
                        # Show a message about VNC usage (in main thread)
                        return True
                    except Exception as e3:
                        logger.error(f"All launch attempts failed: {str(e3)}")
            
            return False
            
    def stop(self):
        """Stop the QEMU virtual machine."""
        if not self.is_running:
            logger.warning("QEMU is not running")
            return False
            
        try:
            self.qemu_process.terminate()
            self.qemu_process.wait(timeout=5)
            self.is_running = False
            logger.info("QEMU stopped successfully")
            return True
        except subprocess.TimeoutExpired:
            logger.warning("QEMU did not stop gracefully, forcing kill")
            self.qemu_process.kill()
            self.is_running = False
            return True
        except Exception as e:
            logger.error(f"Error stopping QEMU: {str(e)}")
            return False
            
    def is_alive(self):
        """Check if QEMU is still running."""
        if not self.qemu_process:
            return False
            
        return self.qemu_process.poll() is None
            
    def screenshot(self, output_path):
        """Take a screenshot of the current VM state."""
        if not self.is_running:
            logger.warning("Cannot take screenshot: QEMU is not running")
            return False
            
        try:
            # Use QEMU monitor command to take screenshot
            # This is a placeholder and might need adjustment based on actual QEMU version
            # and monitor configuration
            self.qemu_process.stdin.write(b"screendump " + output_path.encode() + b"\n")
            self.qemu_process.stdin.flush()
            logger.info(f"Screenshot saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return False


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    qemu = QEMUWrapper()
    print("QEMU parameters:", qemu.params)
    print("QEMU command:", " ".join(qemu.build_command()))