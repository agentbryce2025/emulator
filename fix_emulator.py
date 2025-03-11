#!/usr/bin/env python3
"""
Fix script for the Undetected Android Emulator
This script fixes the AttributeError related to SensorSimulator.set_profile
"""

import os
import re
import sys

def fix_emulator_gui():
    """
    Fixes the set_profile error in emulator_gui.py
    """
    # Detect the emulator directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    emulator_gui_path = os.path.join(script_dir, "src", "gui", "emulator_gui.py")
    
    if not os.path.exists(emulator_gui_path):
        print(f"Error: Could not find {emulator_gui_path}")
        print("Make sure you're running this script from the emulator directory.")
        return False
    
    # Read the file
    with open(emulator_gui_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Define the pattern to search for
    pattern = r"""(\s+)sensor_profile = \{
\1\s+"sensors": self\.selected_device_profile\["sensors"\],
\1\s+"device": \{
\1\s+"manufacturer": self\.selected_device_profile\["manufacturer"\],
\1\s+"model": self\.selected_device_profile\["model"\]
\1\s+\}
\1\}
\1self\.sensor_simulator\.set_profile\(sensor_profile\)
\1logger\.info\("Configured sensor simulation from device profile"\)"""
    
    # Define the replacement
    replacement = r"""\1# Create a device profile based on the device type
\1device_type = "smartphone"  # Default device type
\1self.sensor_simulator.create_device_profile(device_type)
\1# We have to manually set the current_profile
\1self.sensor_simulator.current_profile = {
\1    "sensors": self.selected_device_profile["sensors"],
\1    "device": {
\1        "manufacturer": self.selected_device_profile["manufacturer"],
\1        "model": self.selected_device_profile["model"]
\1    }
\1}
\1logger.info("Configured sensor simulation from device profile")"""
    
    # Make the replacement using regex to handle different indentation patterns
    new_content = re.sub(pattern, replacement, content)
    
    # Check if anything was replaced
    if new_content == content:
        # Try a simpler approach if the regex fails
        if "self.sensor_simulator.set_profile(" in content:
            print("Using simple replacement approach...")
            # This is a more direct replacement approach
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
                        }
                    }
                    logger.info("Configured sensor simulation from device profile")'''
            
            new_content = content.replace(old_code, new_code)
            
            # Check if replacement worked
            if new_content == content:
                print("Error: Could not find the code pattern to replace.")
                print("Please apply the fix manually following the instructions in FIX_INSTRUCTIONS.md")
                return False
    
    # Back up the original file
    backup_path = emulator_gui_path + ".bak"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Original file backed up to {backup_path}")
    
    # Write the fixed content
    with open(emulator_gui_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"Fix applied to {emulator_gui_path}")
    print("You can now run the emulator with: python main.py")
    return True

if __name__ == "__main__":
    print("Undetected Android Emulator Fix Utility")
    print("--------------------------------------")
    success = fix_emulator_gui()
    sys.exit(0 if success else 1)