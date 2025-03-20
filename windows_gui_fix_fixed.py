#!/usr/bin/env python3
"""
Windows-specific GUI fix for the Undetected Android Emulator
This script modifies the emulator to use an alternative QEMU launching strategy on Windows
that ensures the QEMU window appears properly.
"""

import os
import re
import sys
import platform
import shutil
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("windows_gui_fix.log")
    ]
)
logger = logging.getLogger("windows_gui_fix")

def make_backup(file_path):
    """Create a backup of the specified file."""
    backup_path = file_path + ".backup"
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
    return backup_path

def fix_qemu_wrapper():
    """Add additional Windows-specific fixes to the QEMUWrapper class."""
    qemu_wrapper_path = os.path.join("src", "core", "qemu_wrapper.py")
    
    if not os.path.exists(qemu_wrapper_path):
        logger.error(f"Could not find {qemu_wrapper_path}")
        return False

    # Make a backup
    make_backup(qemu_wrapper_path)
    
    with open(qemu_wrapper_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Enhance Windows path finding for QEMU
    if "common_paths = [" in content:
        # Find the Windows paths section
        path_pattern = r"common_paths = \[(.*?)\]"
        path_match = re.search(path_pattern, content, re.DOTALL)
        
        if path_match:
            current_paths = path_match.group(1)
            enhanced_paths = current_paths + ',\n                os.path.join(os.environ.get("ProgramFiles", "C:\\\\Program Files"), "qemu", "qemu-system-x86_64.exe"),\n                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\\\Program Files (x86)"), "qemu", "qemu-system-x86_64.exe"),\n                os.path.join(os.environ.get("ProgramW6432", "C:\\\\Program Files"), "qemu", "qemu-system-x86_64.exe"),\n                os.path.join(os.path.expanduser("~"), "Desktop", "qemu", "qemu-system-x86_64.exe"),\n                os.path.join(os.path.expanduser("~"), "Documents", "qemu", "qemu-system-x86_64.exe"),\n                os.path.join(os.path.expanduser("~"), "Downloads", "qemu", "qemu-system-x86_64.exe"),'
            content = content.replace(path_match.group(0), "common_paths = [" + enhanced_paths + "]")
            logger.info("Enhanced QEMU path detection for Windows")
    
    # 2. Add fallback mechanism
    # Find the function where we catch errors
    if "logger.error(f\"Error starting QEMU: {str(e)}\")" in content:
        original = "            logger.error(f\"Error starting QEMU: {str(e)}\")\n            # Log more details in case of error\n            import traceback\n            logger.error(f\"Detailed error: {traceback.format_exc()}\")\n            return False"
        replacement = """            logger.error(f"Error starting QEMU: {str(e)}")
            # Log more details in case of error
            import traceback
            logger.error(f"Detailed error: {traceback.format_exc()}")
            
            # If the standard launch failed, try the direct_launch approach
            if platform.system() == "Windows":
                logger.info("Standard QEMU launch failed, trying direct launcher approach...")
                
                try:
                    # Construct command parameters from our current params
                    cmd = self.build_command()
                    cmd_str = " ".join(f'"{c}"' if " " in str(c) and isinstance(c, str) else str(c) for c in cmd)
                    
                    # Use the direct launcher technique of creating a fully visible process
                    # This is a more aggressive approach for Windows
                    import subprocess
                    from subprocess import CREATE_NEW_CONSOLE
                    
                    self.qemu_process = subprocess.Popen(
                        cmd_str,
                        shell=True,
                        creationflags=CREATE_NEW_CONSOLE
                    )
                    
                    self.is_running = True
                    logger.info(f"QEMU started with direct launcher, PID: {self.qemu_process.pid}")
                    return True
                except Exception as e2:
                    logger.error(f"Error during fallback launch: {str(e2)}")
            
            return False"""
        
        content = content.replace(original, replacement)
        logger.info("Added fallback launcher for Windows QEMU start failures")
    
    # Write the updated content
    with open(qemu_wrapper_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Updated {qemu_wrapper_path} with Windows-specific fixes")
    return True

def modify_main_py():
    """Modify main.py to handle Windows-specific workarounds."""
    main_py_path = "main.py"
    
    if not os.path.exists(main_py_path):
        logger.error(f"Could not find {main_py_path}")
        return False
    
    # Make a backup
    make_backup(main_py_path)
    
    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Add Windows-specific imports and handling
    if "def run_gui(args=None):" in content:
        # Find the return statement and add Windows-specific code before it
        pattern = r"return app\.exec_\(\) if hasattr\(app, 'exec_'\) else app\.exec\(\)"
        if re.search(pattern, content):
            replacement = """    # Windows-specific handling to ensure the QEMU window appears
    import platform
    if platform.system() == "Windows":
        # Monitor if QEMU actually shows its window
        logger.info("Running on Windows - will monitor for QEMU window appearance")
        
        # Connect a special signal for Windows QEMU window monitoring
        if hasattr(window, 'qemu') and hasattr(window.qemu, 'is_running') and window.qemu.is_running:
            logger.info("QEMU is detected as running, will monitor for window visibility")
            
            # We'll set up a timer to check if QEMU window has appeared
            import threading
            import time
            
            def check_qemu_window():
                # Check if QEMU window has appeared after 5 seconds
                time.sleep(5)
                if hasattr(window, 'qemu') and window.qemu.is_running:
                    if not window.qemu.is_alive():
                        logger.warning("QEMU is no longer running - window might have failed to appear")
                        
                        # Show a message to the user
                        from PyQt5.QtWidgets import QMessageBox
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setWindowTitle("QEMU Window Issue")
                        msg.setText("The QEMU window may not be appearing correctly.")
                        msg.setInformativeText("Try using the direct launcher: Run 'run_qemu.bat' or 'python direct_launch.py'")
                        msg.setStandardButtons(QMessageBox.Ok)
                        # Use a timer to show the message box after a slight delay
                        from PyQt5.QtCore import QTimer
                        timer = QTimer()
                        timer.singleShot(100, msg.exec_)
            
            # Start the monitoring thread
            monitor_thread = threading.Thread(target=check_qemu_window)
            monitor_thread.daemon = True
            monitor_thread.start()
    
    return app.exec_() if hasattr(app, 'exec_') else app.exec()"""
            
            content = content.replace(pattern, replacement)
            logger.info("Added Windows-specific QEMU window monitoring to main.py")
            
    # Write the updated content
    with open(main_py_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Updated {main_py_path} with Windows-specific handling")
    return True

def create_alternative_launcher():
    """Create an enhanced Windows launcher script."""
    launcher_path = "enhanced_windows_launcher.bat"
    
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write("""@echo off
REM Enhanced Windows Launcher for the Undetected Android Emulator
ECHO Undetected Android Emulator - Enhanced Windows Launcher
ECHO ----------------------------------------
ECHO.

REM Check Python installation
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python not found. Please install Python 3.7 or higher.
    ECHO You can download it from https://www.python.org/downloads/
    PAUSE
    EXIT /B 1
)

ECHO Checking and creating environment...
IF NOT EXIST venv (
    ECHO Creating Python virtual environment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        ECHO Error creating virtual environment. Please install venv with:
        ECHO python -m pip install virtualenv
        PAUSE
        EXIT /B 1
    )
)

ECHO Activating virtual environment...
CALL venv\\Scripts\\activate
IF %ERRORLEVEL% NEQ 0 (
    ECHO Error activating virtual environment.
    PAUSE
    EXIT /B 1
)

ECHO Installing required packages...
pip install -e . >nul 2>&1

:Start
ECHO.
ECHO Choose launch option:
ECHO 1 - Launch with standard GUI (Recommended first try)
ECHO 2 - Launch with direct QEMU (For QEMU window issues)
ECHO 3 - Troubleshoot and fix common issues
ECHO 4 - Exit
ECHO.

SET /P OPTION="Enter option (1-4): "

IF "%OPTION%"=="1" (
    ECHO.
    ECHO Launching emulator with standard GUI...
    python main.py
    GOTO End
)

IF "%OPTION%"=="2" (
    ECHO.
    ECHO Launching emulator with direct QEMU...
    ECHO Note: You should have run the GUI at least once to set up images.
    python direct_launch.py
    GOTO End
)

IF "%OPTION%"=="3" (
    ECHO.
    ECHO Running troubleshooter...
    ECHO 1. Fixing issues in emulator core...
    python fix_emulator.py
    ECHO.
    ECHO 2. Applying Windows-specific GUI fixes...
    python windows_gui_fix_fixed.py
    ECHO.
    ECHO Done! Try launching the emulator again with option 1.
    PAUSE
    GOTO Start
)

IF "%OPTION%"=="4" (
    ECHO Exiting...
    GOTO End
)

ECHO Invalid option selected.

:End
ECHO.
ECHO Thank you for using the Undetected Android Emulator.
PAUSE
""")
    
    logger.info(f"Created enhanced Windows launcher at {launcher_path}")
    return True

def main():
    """Main function to apply Windows-specific fixes."""
    logger.info("Windows GUI Fix Tool for Undetected Android Emulator")
    logger.info("---------------------------------------------------")
    
    # Only apply fixes on Windows or when forced
    is_windows = platform.system() == "Windows"
    force_apply = "--force" in sys.argv
    
    if not is_windows and not force_apply:
        logger.info("This tool is intended for Windows. Use --force to apply on other platforms.")
        return 0
    
    logger.info("Applying Windows-specific fixes...")
    
    # Apply fixes
    fix_qemu_wrapper()
    modify_main_py()
    create_alternative_launcher()
    
    logger.info("Windows GUI fixes have been applied!")
    logger.info("For best results on Windows:")
    logger.info("1. Use the new enhanced_windows_launcher.bat")
    logger.info("2. If the QEMU window still doesn't appear, try direct_launch.py")
    logger.info("3. Make sure your Windows has the latest graphics drivers")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())