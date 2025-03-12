#!/usr/bin/env python3
"""
Direct launch script for the Android emulator on Windows.
This bypasses all the complexity and just launches QEMU with working parameters.
"""

import os
import subprocess
import sys
import platform
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("direct_launch.log")
    ]
)
logger = logging.getLogger("direct_launch")

def get_config_dir():
    """Get the configuration directory."""
    return os.path.join(os.path.expanduser("~"), ".config", "undetected-emulator")

def get_qemu_path():
    """Get the QEMU executable path."""
    if platform.system() == "Windows":
        # Check common Windows locations
        common_paths = [
            os.path.join("C:", os.sep, "Program Files", "qemu", "qemu-system-x86_64.exe"),
            os.path.join("C:", os.sep, "Program Files (x86)", "qemu", "qemu-system-x86_64.exe"),
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    
    # Default paths for Linux/macOS
    return "qemu-system-x86_64"

def get_latest_iso():
    """Get the most recently modified ISO file in the images directory."""
    images_dir = os.path.join(get_config_dir(), "images")
    if not os.path.exists(images_dir):
        logger.error(f"Images directory not found: {images_dir}")
        return None
        
    iso_files = [f for f in os.listdir(images_dir) if f.endswith('.iso')]
    if not iso_files:
        logger.error("No ISO files found in images directory")
        return None
        
    # Sort by modification time (newest first)
    iso_files.sort(key=lambda f: os.path.getmtime(os.path.join(images_dir, f)), reverse=True)
    return os.path.join(images_dir, iso_files[0])

def get_or_create_disk():
    """Get an existing disk image or create a new one."""
    images_dir = os.path.join(get_config_dir(), "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir, exist_ok=True)
        
    # Check for existing disk images
    img_files = [f for f in os.listdir(images_dir) if f.endswith('.img')]
    if img_files:
        # Use the most recently modified one
        img_files.sort(key=lambda f: os.path.getmtime(os.path.join(images_dir, f)), reverse=True)
        return os.path.join(images_dir, img_files[0])
    
    # Create a new disk image
    disk_path = os.path.join(images_dir, "direct_launch.img")
    logger.info(f"Creating new disk image: {disk_path}")
    
    # For Windows, we might need to use the qemu-img command
    qemu_dir = os.path.dirname(get_qemu_path())
    qemu_img = os.path.join(qemu_dir, "qemu-img.exe" if platform.system() == "Windows" else "qemu-img")
    
    if os.path.exists(qemu_img):
        try:
            # Create an 8GB disk image
            subprocess.run([qemu_img, "create", "-f", "qcow2", disk_path, "8G"], check=True)
            logger.info("Disk image created successfully")
            return disk_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create disk image: {e}")
    else:
        logger.error(f"qemu-img not found at {qemu_img}")
    
    return None

def launch_qemu():
    """Launch QEMU with Android-x86."""
    qemu_path = get_qemu_path()
    if not qemu_path or not os.path.exists(qemu_path):
        logger.error(f"QEMU not found at {qemu_path}")
        return False
        
    iso_path = get_latest_iso()
    if not iso_path:
        logger.error("No Android ISO found")
        return False
        
    disk_path = get_or_create_disk()
    if not disk_path:
        logger.error("Could not get or create disk image")
        return False
    
    # Build the command with Windows-friendly settings
    cmd = [
        qemu_path,
        "-memory", "2048",
        "-smp", "4",
        "-hda", disk_path,
        "-cpu", "host",
        "-vga", "std",  # Standard VGA for compatibility
        "-display", "sdl",  # SDL display backend works better on Windows
        "-net", "user",
        "-usb",
        "-usbdevice", "tablet",
        "-cdrom", iso_path
    ]
    
    cmd_str = " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd)
    logger.info(f"Running QEMU with command: {cmd_str}")
    
    try:
        # Windows-specific process creation
        if platform.system() == "Windows":
            # Create the process in a way that keeps the window open
            startupinfo = None
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
            except (ImportError, AttributeError):
                pass  # Older Python version
                
            # Use CREATE_NEW_CONSOLE to ensure window stays open
            process = subprocess.Popen(
                cmd_str, 
                shell=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Standard process creation for Linux/macOS
            process = subprocess.Popen(cmd)
            
        logger.info(f"Started QEMU with PID: {process.pid}")
        logger.info("If no window appears, check for error messages above.")
        
        # Wait for process to end
        try:
            process.wait()
            logger.info("QEMU process has ended")
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, terminating QEMU")
            process.terminate()
        
        return True
    except Exception as e:
        logger.error(f"Error starting QEMU: {e}")
        import traceback
        logger.error(f"Detailed error: {traceback.format_exc()}")
        return False

def main():
    logger.info("Direct Launch Script for Android Emulator")
    logger.info("----------------------------------------")
    
    try:
        # Launch QEMU directly
        success = launch_qemu()
        if not success:
            logger.error("Failed to launch QEMU. Check the logs for details.")
            return 1
            
        return 0
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        import traceback
        logger.error(f"Detailed error: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())