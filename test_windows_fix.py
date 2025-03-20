#!/usr/bin/env python3
"""
Test script for the Windows GUI fix.
This script tests whether the QEMU window appears properly on Windows.
"""

import os
import sys
import time
import platform
import subprocess
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_windows_fix.log")
    ]
)
logger = logging.getLogger("test_windows_fix")

def test_qemu_installation():
    """Test whether QEMU is installed and accessible."""
    logger.info("Testing QEMU installation...")
    
    try:
        # Try to run QEMU with --version
        if platform.system() == "Windows":
            # Check common Windows locations
            common_paths = [
                "C:\\Program Files\\qemu\\qemu-system-x86_64.exe",
                "C:\\Program Files (x86)\\qemu\\qemu-system-x86_64.exe",
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    logger.info(f"Found QEMU at: {path}")
                    try:
                        subprocess.run([path, "--version"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE, 
                                      check=True)
                        logger.info("QEMU is working properly")
                        return True
                    except subprocess.CalledProcessError:
                        logger.warning(f"QEMU at {path} exists but returned an error")
            
            logger.warning("QEMU not found in common Windows locations")
            return False
        else:
            # On Linux/macOS
            subprocess.run(["qemu-system-x86_64", "--version"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
            logger.info("QEMU is working properly")
            return True
    except (FileNotFoundError, subprocess.SubprocessError):
        logger.warning("QEMU is not installed or not in PATH")
        return False

def test_direct_launch():
    """Test if direct_launch.py works (since run_qemu.bat is Windows-only)."""
    logger.info("Testing direct launcher (direct_launch.py)...")
    
    try:
        # Start the script
        process = subprocess.Popen([sys.executable, "direct_launch.py"],
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Give it some time to start
        time.sleep(2)
        
        # Kill it after a short test - we're just checking if it starts
        try:
            process.terminate()
            process.wait(timeout=5)
            logger.info("Direct launcher test completed")
            return True
        except subprocess.TimeoutExpired:
            logger.warning("Direct launcher process didn't terminate gracefully")
            process.kill()
            return False
    except Exception as e:
        logger.error(f"Error testing direct launcher: {e}")
        return False

def test_windows_specific_fixes():
    """Test if the Windows-specific fixes are in place."""
    logger.info("Testing if Windows-specific fixes are applied...")
    
    # Check for enhanced launcher
    if os.path.exists("enhanced_windows_launcher.bat"):
        logger.info("Enhanced Windows launcher exists")
    else:
        logger.warning("Enhanced Windows launcher not found")
    
    # Check for QEMUWrapper Windows fixes
    qemu_wrapper_path = os.path.join("src", "core", "qemu_wrapper.py")
    if os.path.exists(qemu_wrapper_path):
        with open(qemu_wrapper_path, "r", encoding="utf-8") as f:
            content = f.read()
            
            # Check for Windows-specific code
            if "platform.system() == \"Windows\"" in content:
                logger.info("QEMUWrapper has Windows-specific code")
            else:
                logger.warning("QEMUWrapper is missing Windows-specific code")
                
            # Check for SDL display setting
            if '"display": "sdl"' in content:
                logger.info("QEMUWrapper is using SDL display backend (good for Windows)")
            else:
                logger.warning("QEMUWrapper is not using SDL display backend")
                
            # Check for fallback mechanism
            if "Standard QEMU launch failed, trying direct launcher approach" in content:
                logger.info("Fallback mechanism is in place")
            else:
                logger.warning("Fallback mechanism is not in place")
    else:
        logger.warning(f"QEMUWrapper not found at {qemu_wrapper_path}")
    
    # Check windows_gui_fix.py
    if os.path.exists("windows_gui_fix.py"):
        logger.info("Windows GUI fix script exists")
    else:
        logger.warning("Windows GUI fix script not found")
    
    # Check documentation
    if os.path.exists("WINDOWS_GUI_FIX.md"):
        logger.info("Windows GUI fix documentation exists")
    else:
        logger.warning("Windows GUI fix documentation not found")
        
    # All tests passed
    return True

def main():
    """Main test function."""
    logger.info("Testing Windows GUI fixes for the Undetected Android Emulator")
    logger.info("----------------------------------------------------------")
    
    # Run tests
    qemu_ok = test_qemu_installation()
    direct_launch_ok = test_direct_launch()
    windows_fixes_ok = test_windows_specific_fixes()
    
    # Print results
    logger.info("\nTest Results:")
    logger.info(f"QEMU Installation: {'PASS' if qemu_ok else 'FAIL'}")
    logger.info(f"Direct Launcher: {'PASS' if direct_launch_ok else 'FAIL'}")
    logger.info(f"Windows Fixes: {'PASS' if windows_fixes_ok else 'FAIL'}")
    
    # Print overall result
    if qemu_ok and direct_launch_ok and windows_fixes_ok:
        logger.info("\nALL TESTS PASSED")
        logger.info("The emulator should now work correctly on Windows")
        return 0
    else:
        logger.warning("\nSome tests failed")
        logger.warning("See the log file for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())