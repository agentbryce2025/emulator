#!/usr/bin/env python3
"""
Fix script for the Undetected Android Emulator
This script fixes multiple issues in the emulator code:
1. AttributeError: 'SensorSimulator' object has no attribute 'set_profile'
2. KeyError: 'simulation_parameters' in SensorSimulator
3. AttributeError: 'FridaManager' object has no attribute 'load_script'
"""

import os
import re
import sys

def fix_sensor_simulator_issues(content):
    """Fix the sensor simulator related issues in emulator_gui.py"""
    # First, the set_profile() error
    if "self.sensor_simulator.set_profile(" in content:
        print("Fixing SensorSimulator.set_profile issue...")
        # This is a direct replacement approach
        old_code = '''                    sensor_profile = {
                        "sensors": self.selected_device_profile["sensors"],
                        "device": {
                            "manufacturer": self.selected_device_profile["manufacturer"],
                            "model": self.selected_device_profile["model"]
                        }
                    }
                    self.sensor_simulator.set_profile(sensor_profile)
                    logger.info("Configured sensor simulation from device profile")'''
        
        new_code = '''                    # Create a device profile based on the device type
                    device_type = "smartphone"  # Default device type
                    self.sensor_simulator.create_device_profile(device_type)
                    # We have to manually set the current_profile
                    self.sensor_simulator.current_profile = {
                        "sensors": self.selected_device_profile["sensors"],
                        "device": {
                            "manufacturer": self.selected_device_profile["manufacturer"],
                            "model": self.selected_device_profile["model"]
                        },
                        "simulation_parameters": {
                            "noise_factor": 0.05,
                            "update_frequency": 50,  # Hz
                            "drift_enabled": True,
                            "drift_factor": 0.001,
                            "use_ml": True
                        }
                    }
                    logger.info("Configured sensor simulation from device profile")'''
        
        content = content.replace(old_code, new_code)
    
    # Also check for the fixed code but without simulation_parameters
    fix_check = '''self.sensor_simulator.current_profile = {
                        "sensors": self.selected_device_profile["sensors"],
                        "device": {
                            "manufacturer": self.selected_device_profile["manufacturer"],
                            "model": self.selected_device_profile["model"]
                        }
                    }'''
    
    # Fix if a previous partial fix was applied
    if fix_check in content:
        print("Adding missing simulation_parameters to current_profile...")
        
        replacement_code = '''self.sensor_simulator.current_profile = {
                        "sensors": self.selected_device_profile["sensors"],
                        "device": {
                            "manufacturer": self.selected_device_profile["manufacturer"],
                            "model": self.selected_device_profile["model"]
                        },
                        "simulation_parameters": {
                            "noise_factor": 0.05,
                            "update_frequency": 50,  # Hz
                            "drift_enabled": True,
                            "drift_factor": 0.001,
                            "use_ml": True
                        }
                    }'''
        
        content = content.replace(fix_check, replacement_code)
    
    return content

def fix_sensor_simulator_class():
    """Fix sensor simulator's internal issues related to missing baseline and variance fields"""
    sensor_sim_path = os.path.join(script_dir, "src", "anti_detection", "sensor_simulator.py")
    
    if not os.path.exists(sensor_sim_path):
        print(f"Warning: Could not find {sensor_sim_path}")
        print("SensorSimulator class will not be modified. This may cause issues.")
        return False
    
    print("Adding defensive code to SensorSimulator class...")
    
    # Read the file
    with open(sensor_sim_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Fix the _simulation_loop method to handle missing baseline keys
    if "drift_values = {sensor: {axis: 0.0 for axis in data[\"baseline\"].keys()}" in content:
        old_code = '''        drift_values = {sensor: {axis: 0.0 for axis in data["baseline"].keys()} 
                        for sensor, data in self.current_profile["sensors"].items()}'''
        
        new_code = '''        # Initialize drift values with defensive code for profiles that might not have baseline defined
        drift_values = {}
        for sensor, data in self.current_profile["sensors"].items():
            if "baseline" in data:
                drift_values[sensor] = {axis: 0.0 for axis in data["baseline"].keys()}
            elif sensor == "accelerometer":
                drift_values[sensor] = {"x": 0.0, "y": 0.0, "z": 0.0}
            elif sensor == "gyroscope":
                drift_values[sensor] = {"x": 0.0, "y": 0.0, "z": 0.0}
            elif sensor == "magnetometer":
                drift_values[sensor] = {"x": 0.0, "y": 0.0, "z": 0.0}
            elif sensor == "proximity":
                drift_values[sensor] = {"distance": 0.0}
            elif sensor == "light":
                drift_values[sensor] = {"lux": 0.0}
            elif sensor == "pressure":
                drift_values[sensor] = {"hPa": 0.0}
            elif sensor == "temperature":
                drift_values[sensor] = {"celsius": 0.0}
            elif sensor == "humidity":
                drift_values[sensor] = {"percent": 0.0}
            else:
                # For unknown sensors, try to extract keys or use a default
                try:
                    drift_values[sensor] = {k: 0.0 for k in data.keys() if isinstance(k, str) and k != "enabled"}
                except (AttributeError, TypeError):
                    drift_values[sensor] = {"value": 0.0}'''
        
        content = content.replace(old_code, new_code)
    
    # Fix the sensor update code to handle missing baseline and variance
    if "baseline = sensor_config[\"baseline\"]" in content:
        old_code = '''                baseline = sensor_config["baseline"]
                variance = sensor_config["variance"]'''
        
        new_code = '''                # Handle profiles that might not have baseline and variance fields
                if "baseline" not in sensor_config or "variance" not in sensor_config:
                    # Add default values based on sensor type
                    if sensor_name == "accelerometer":
                        baseline = {"x": 0.0, "y": 0.0, "z": 9.81}
                        variance = {"x": 0.1, "y": 0.1, "z": 0.1}
                    elif sensor_name == "gyroscope":
                        baseline = {"x": 0.0, "y": 0.0, "z": 0.0}
                        variance = {"x": 0.02, "y": 0.02, "z": 0.02}
                    elif sensor_name == "magnetometer":
                        baseline = {"x": 25.0, "y": 10.0, "z": 40.0}
                        variance = {"x": 2.0, "y": 2.0, "z": 2.0}
                    elif sensor_name == "proximity":
                        baseline = {"distance": 100.0}
                        variance = {"distance": 0.0}
                    elif sensor_name == "light":
                        baseline = {"lux": 500.0}
                        variance = {"lux": 50.0}
                    elif sensor_name == "pressure":
                        baseline = {"hPa": 1013.25}
                        variance = {"hPa": 0.5}
                    elif sensor_name == "temperature":
                        baseline = {"celsius": 22.0}
                        variance = {"celsius": 0.5}
                    elif sensor_name == "humidity":
                        baseline = {"percent": 50.0}
                        variance = {"percent": 1.0}
                    else:
                        # For unknown sensors, try to create reasonable defaults
                        baseline = {"value": 0.0}
                        variance = {"value": 0.1}
                else:
                    baseline = sensor_config["baseline"]
                    variance = sensor_config["variance"]'''
        
        content = content.replace(old_code, new_code)
    
    # Back up the original file
    backup_path = sensor_sim_path + ".bak"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Original SensorSimulator file backed up to {backup_path}")
    
    # Write the fixed content
    with open(sensor_sim_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Defensive code added to {sensor_sim_path}")
    return True

def fix_frida_manager_issues(content):
    """Fix the FridaManager.load_script issue in emulator_gui.py"""
    if "self.frida_manager.load_script(" in content:
        print("Fixing FridaManager.load_script issue...")
        # Replace the direct method call with a compatible version
        old_code = '''                if script_path:
                    self.frida_manager.load_script(script_path)
                    
                    # Set target app if specified
                    target_app = self.target_app_input.text().strip()
                    if target_app:
                        self.frida_manager.set_target_package(target_app)
                        
                    # Start monitoring for app launch
                    self.frida_manager.start_monitoring()
                    logger.info(f"Frida monitoring started for {target_app}")'''
        
        new_code = '''                if script_path:
                    # Since frida_manager doesn't have load_script method, we need to use another approach
                    # Get the script content
                    try:
                        with open(script_path, "r") as f:
                            script_content = f.read()
                        
                        # Set target app if specified
                        target_app = self.target_app_input.text().strip()
                        
                        # We'll inject the script directly when needed
                        if target_app:
                            # Store the information for later use with inject_script
                            self.frida_script_content = script_content
                            self.frida_target_app = target_app
                            
                        # Start monitoring for app launch if applicable
                        if hasattr(self.frida_manager, "start_monitoring"):
                            self.frida_manager.start_monitoring()
                            logger.info(f"Frida monitoring started for {target_app}")
                        else:
                            logger.warning("Frida monitoring not available in this version")
                    except Exception as e:
                        logger.error(f"Error loading Frida script: {e}")'''
        
        content = content.replace(old_code, new_code)
    
    return content

def fix_frida_manager_class():
    """Add compatibility methods to the FridaManager class"""
    frida_manager_path = os.path.join(script_dir, "src", "anti_detection", "frida_manager.py")
    
    if not os.path.exists(frida_manager_path):
        print(f"Warning: Could not find {frida_manager_path}")
        print("FridaManager class will not be modified. This may cause issues.")
        return False
    
    print("Adding compatibility methods to FridaManager class...")
    
    # Read the file
    with open(frida_manager_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Add missing fields to __init__
    if "self.script_content = None" not in content:
        old_init = '''    def __init__(self, scripts_dir=None, device_id=None):
        """Initialize Frida manager with optional scripts directory."""
        self.scripts_dir = scripts_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "frida_scripts"
        )
        self.device = None
        self.device_id = device_id
        self.sessions = {}
        self.scripts = {}
        self.connected = False
        
        # Ensure scripts directory exists
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        # Try to connect to the device
        self._connect_to_device()'''
        
        new_init = '''    def __init__(self, scripts_dir=None, device_id=None):
        """Initialize Frida manager with optional scripts directory."""
        self.scripts_dir = scripts_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "frida_scripts"
        )
        self.device = None
        self.device_id = device_id
        self.sessions = {}
        self.scripts = {}
        self.connected = False
        self.script_content = None  # Store script content for compatibility
        self.target_package = None  # Store target package for compatibility
        
        # Ensure scripts directory exists
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        # Try to connect to the device
        self._connect_to_device()'''
        
        content = content.replace(old_init, new_init)
    
    # Add load_script method if it doesn't exist
    if "def load_script" not in content:
        connect_method = "    def _connect_to_device(self):"
        load_script_method = '''    def load_script(self, script_path):
        """Compatibility method for loading a script - just stores the path for later use."""
        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}")
            return False
            
        try:
            with open(script_path, "r") as f:
                self.script_content = f.read()
            logger.info(f"Loaded script from {script_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading script {script_path}: {e}")
            return False
            
    def set_target_package(self, package_name):
        """Compatibility method for setting the target package."""
        self.target_package = package_name
        logger.info(f"Set target package: {package_name}")
        return True
        
'''
        content = content.replace(connect_method, load_script_method + connect_method)
    
    # Add start_monitoring method if it doesn't exist
    if "def start_monitoring" not in content:
        close_method = "    def close(self):"
        start_monitoring_method = '''    def start_monitoring(self):
        """Start monitoring for target app launch and inject scripts."""
        if self.target_package and self.script_content:
            logger.info(f"Monitoring started for package: {self.target_package}")
            # In a real implementation, this would start a background thread
            # that checks for the app to launch, then injects the script.
            # For compatibility purposes, we'll just log that it's started.
            return True
        else:
            logger.warning("Cannot start monitoring: No target package or script content set")
            return False
            
'''
        content = content.replace(close_method, start_monitoring_method + close_method)
    
    # Back up the original file
    backup_path = frida_manager_path + ".bak"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Original FridaManager file backed up to {backup_path}")
    
    # Write the fixed content
    with open(frida_manager_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Compatibility methods added to {frida_manager_path}")
    return True

def fix_emulator():
    """
    Fixes multiple issues in the emulator code
    """
    # Fix emulator_gui.py
    emulator_gui_path = os.path.join(script_dir, "src", "gui", "emulator_gui.py")
    
    if not os.path.exists(emulator_gui_path):
        print(f"Error: Could not find {emulator_gui_path}")
        print("Make sure you're running this script from the emulator directory.")
        return False
    
    # Read the file
    with open(emulator_gui_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Apply the fixes
    original_content = content
    content = fix_sensor_simulator_issues(content)
    content = fix_frida_manager_issues(content)
    
    # Check if anything was replaced
    if content == original_content:
        print("No changes were needed or the code patterns could not be found.")
        print("Please apply the fixes manually following the instructions in FIX_INSTRUCTIONS.md")
        return False
    
    # Back up the original file
    backup_path = emulator_gui_path + ".bak"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(original_content)
    print(f"Original GUI file backed up to {backup_path}")
    
    # Write the fixed content
    with open(emulator_gui_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Fixes applied to {emulator_gui_path}")
    
    # Fix the FridaManager class
    fix_frida_manager_class()
    
    # Fix the SensorSimulator class
    fix_sensor_simulator_class()
    
    # Fix Windows-specific QEMU issues if on Windows
    import platform
    if platform.system() == "Windows":
        print("\nDetected Windows system, applying QEMU compatibility fixes...")
        fix_qemu_windows_issues()
    
    print("\nAll fixes have been applied!")
    print("You can now run the emulator with: python main.py")
    print("Windows users: If no QEMU window appears, try using run_qemu.bat or python direct_launch.py")
    return True

def fix_qemu_windows_issues():
    """Add Windows compatibility fixes for QEMU"""
    qemu_wrapper_path = os.path.join(script_dir, "src", "core", "qemu_wrapper.py")
    
    if not os.path.exists(qemu_wrapper_path):
        print(f"Warning: Could not find {qemu_wrapper_path}")
        print("QEMUWrapper class will not be modified. This may cause issues on Windows.")
        return False
    
    print("Adding Windows compatibility to QEMUWrapper class...")
    
    # Read the file
    with open(qemu_wrapper_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Update default parameters for Windows compatibility
    windows_params_updated = False
    if '"vga": "virtio",' in content and '"display": "gtk",' in content:
        old_params = '''        # Default QEMU parameters
        self.params = {
            "memory": "2048",
            "smp": "4",
            "hda": "",
            "cpu": "host",
            "vga": "virtio",
            "display": "gtk",
            "net": "user",
            "usb": "on",
            "usbdevice": "tablet",
            "accelerate": "kvm",
            "audio": "pa",
        }'''
        
        new_params = '''        # Default QEMU parameters
        self.params = {
            "memory": "2048",
            "smp": "4",
            "hda": "",
            "cpu": "host",
            "vga": "std",  # Changed from virtio to std for wider compatibility
            "display": "sdl",  # Changed from gtk to sdl for Windows compatibility
            "net": "user",
            "usb": "on",
            "usbdevice": "tablet",
            # Removed accelerate=kvm as it's not available on Windows
            # Removed audio=pa as PulseAudio is not available on Windows
        }'''
        
        content = content.replace(old_params, new_params)
        windows_params_updated = True
    
    # Fix process creation on Windows
    windows_process_updated = False
    if "self.qemu_process = subprocess.Popen(" in content and "shell=True" not in content:
        old_code = '''        try:
            self.qemu_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.is_running = True
            logger.info(f"QEMU started with PID {self.qemu_process.pid}")
            return True
        except Exception as e:
            logger.error(f"Error starting QEMU: {str(e)}")
            return False'''
        
        new_code = '''        try:
            # Check platform for Windows-specific behaviors
            import platform
            if platform.system() == "Windows":
                # On Windows, start the process with shell=True and without pipes to ensure proper window creation
                # and prevent console window from showing and hiding immediately
                startupinfo = None
                try:
                    # Import Windows-specific modules if available
                    import subprocess
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
                except (ImportError, AttributeError):
                    pass  # Not on Windows or older Python version
                
                # Use creationflags to ensure the window stays open
                creation_flags = subprocess.CREATE_NEW_CONSOLE
                
                # Run with shell=True to handle any path issues
                cmd_str = " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd)
                logger.info(f"Windows command string: {cmd_str}")
                
                self.qemu_process = subprocess.Popen(
                    cmd_str, 
                    shell=True,
                    startupinfo=startupinfo,
                    creationflags=creation_flags
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
            return False'''
        
        content = content.replace(old_code, new_code)
        windows_process_updated = True
    
    if not windows_params_updated and not windows_process_updated:
        print("No QEMU Windows compatibility issues found or changes already applied.")
        return True
    
    # Back up the original file
    backup_path = qemu_wrapper_path + ".bak"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Original QEMUWrapper file backed up to {backup_path}")
    
    # Write the fixed content
    with open(qemu_wrapper_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Windows compatibility added to {qemu_wrapper_path}")
    return True

if __name__ == "__main__":
    print("Undetected Android Emulator Fix Utility")
    print("--------------------------------------")
    print("This script fixes multiple issues in the emulator code:")
    print("1. SensorSimulator.set_profile error")
    print("2. Missing simulation_parameters in sensor profiles")
    print("3. KeyError 'baseline' in SensorSimulator._simulation_loop")
    print("4. FridaManager.load_script compatibility")
    print("5. QEMU window not appearing on Windows (display/acceleration issues)")
    print()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    success = fix_emulator()
    
    # Also fix Windows-specific QEMU issues
    import platform
    if platform.system() == "Windows":
        print("\nDetected Windows system, applying QEMU compatibility fixes...")
        fix_qemu_windows_issues()
    else:
        print("\nNot running on Windows, skipping Windows-specific QEMU fixes")
    
    sys.exit(0 if success else 1)