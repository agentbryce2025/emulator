#!/usr/bin/env python3
"""
Improved Windows launcher for the undetected Android emulator.
This script provides special Windows-specific handling to ensure the emulator UI
displays correctly.
"""

import os
import sys
import logging
import subprocess
import platform
import time
import winreg

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("emulator_launcher.log")
    ]
)

logger = logging.getLogger("windows_launcher")

def check_qemu_installed():
    """Check if QEMU is installed and accessible, return path if found."""
    possible_paths = [
        "C:\\Program Files\\qemu\\qemu-system-x86_64.exe",
        "C:\\Program Files (x86)\\qemu\\qemu-system-x86_64.exe",
        os.path.expanduser("~\\qemu\\qemu-system-x86_64.exe"),
        os.path.expanduser("~\\Desktop\\qemu\\qemu-system-x86_64.exe"),
        os.path.expanduser("~\\Documents\\qemu\\qemu-system-x86_64.exe"),
        os.path.expanduser("~\\Downloads\\qemu\\qemu-system-x86_64.exe"),
    ]
    
    # Try direct command first
    try:
        result = subprocess.run(["qemu-system-x86_64", "--version"], 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                            shell=True)
        if result.returncode == 0:
            logger.info("QEMU found in PATH")
            return "qemu-system-x86_64"
    except:
        pass
    
    # Check the common installation locations
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found QEMU at: {path}")
            return path
    
    # Look in registry for QEMU installation
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\QEMU") as key:
            install_path, _ = winreg.QueryValueEx(key, "Install_Dir")
            qemu_path = os.path.join(install_path, "qemu-system-x86_64.exe")
            if os.path.exists(qemu_path):
                logger.info(f"Found QEMU in registry at: {qemu_path}")
                return qemu_path
    except:
        pass
    
    return None

def prepare_environment():
    """Prepare the environment for running the emulator."""
    # Create config directory if it doesn't exist
    config_dir = os.path.expanduser("~/.config/undetected-emulator")
    os.makedirs(config_dir, exist_ok=True)
    
    # Check if QEMU is installed
    qemu_path = check_qemu_installed()
    if not qemu_path:
        logger.error("QEMU not found. Please install QEMU to run the emulator.")
        print("ERROR: QEMU not found. Please install QEMU from https://www.qemu.org/download/")
        print("Press Enter to exit...")
        input()
        sys.exit(1)
    
    # Save QEMU path to config
    try:
        with open(os.path.join(config_dir, "qemu.conf"), "w") as f:
            f.write(f"qemu_path={qemu_path}\n")
            f.write("display=sdl\n")
            f.write("vga=virtio\n")
            f.write("audio=none\n")
        logger.info("Saved QEMU configuration")
    except Exception as e:
        logger.error(f"Error saving QEMU configuration: {e}")
    
    return qemu_path

def main():
    """Main function."""
    logger.info("Windows emulator launcher starting")
    
    if platform.system() != "Windows":
        logger.error("This script is intended for Windows systems only")
        sys.exit(1)
    
    # Prepare environment
    qemu_path = prepare_environment()
    
    # Launch the main emulator application
    try:
        main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        if not os.path.exists(main_script):
            logger.error(f"Main script not found: {main_script}")
            print(f"ERROR: Cannot find main.py in {os.path.dirname(os.path.abspath(__file__))}")
            print("Press Enter to exit...")
            input()
            sys.exit(1)
        
        # Use explicit path to python executable to avoid environment issues
        python_exe = sys.executable
        
        # Run the main script with specific display settings for Windows
        cmd = [python_exe, main_script, "--qemu-path", qemu_path]
        logger.info(f"Launching emulator with command: {' '.join(cmd)}")
        
        subprocess.Popen(cmd)
        logger.info("Emulator launched successfully")
    except Exception as e:
        logger.error(f"Error launching emulator: {e}")
        print(f"ERROR: Failed to launch emulator: {e}")
        print("Check emulator_launcher.log for details")
        print("Press Enter to exit...")
        input()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        print(f"ERROR: {e}")
        print("Check emulator_launcher.log for details")
        print("Press Enter to exit...")
        input()
        sys.exit(1)