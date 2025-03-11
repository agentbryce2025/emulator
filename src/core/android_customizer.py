#!/usr/bin/env python3
"""
Android-x86 customization module for the undetected Android emulator.
This module handles customization of Android system files and configurations.
"""

import os
import subprocess
import logging
import shutil
import tempfile
import re
from pathlib import Path

logger = logging.getLogger(__name__)

class AndroidCustomizer:
    """Handles Android system customization for anti-detection."""
    
    def __init__(self, system_path=None):
        """Initialize Android customizer with optional system path."""
        self.system_path = system_path
        self.mount_point = None
        self.is_mounted = False
        
    def set_system_path(self, path):
        """Set the path to the Android system image."""
        self.system_path = path
        logger.info(f"System path set to {path}")
        
    def mount_system(self, mount_point=None):
        """Mount the Android system image for modification."""
        if not self.system_path:
            logger.error("System path not set")
            return False
            
        if not os.path.exists(self.system_path):
            logger.error(f"System image not found at {self.system_path}")
            return False
            
        if self.is_mounted:
            logger.warning("System is already mounted")
            return True
            
        self.mount_point = mount_point or tempfile.mkdtemp(prefix="android_system_")
        
        try:
            # Check if the system image is a directory or an image file
            if os.path.isdir(self.system_path):
                # It's already a directory, just use it directly
                logger.info(f"System path is a directory, using directly")
                self.mount_point = self.system_path
                self.is_mounted = True
                return True
                
            # Determine image type
            if self.system_path.endswith('.img') or self.system_path.endswith('.iso'):
                # It's an image file, mount it
                logger.info(f"Mounting system image to {self.mount_point}")
                
                # Create mount point if it doesn't exist
                os.makedirs(self.mount_point, exist_ok=True)
                
                # Try to mount as ext4 first
                result = subprocess.run(
                    ["mount", "-o", "loop,rw", self.system_path, self.mount_point],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if result.returncode != 0:
                    # Try to mount as an ISO
                    result = subprocess.run(
                        ["mount", "-o", "loop", self.system_path, self.mount_point],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                if result.returncode != 0:
                    logger.error(f"Failed to mount system image: {result.stderr.decode('utf-8', 'ignore')}")
                    return False
                    
                self.is_mounted = True
                logger.info(f"System image mounted successfully")
                return True
            else:
                logger.error(f"Unsupported system image format: {self.system_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error mounting system image: {str(e)}")
            return False
            
    def unmount_system(self):
        """Unmount the Android system image."""
        if not self.is_mounted:
            logger.warning("System is not mounted")
            return True
            
        if os.path.isdir(self.system_path):
            # It was a directory, not a mounted image
            self.is_mounted = False
            return True
            
        try:
            subprocess.run(
                ["umount", self.mount_point],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            self.is_mounted = False
            logger.info("System image unmounted successfully")
            
            # Clean up the temporary mount point
            try:
                os.rmdir(self.mount_point)
            except:
                pass
                
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error unmounting system image: {e.stderr.decode('utf-8', 'ignore')}")
            return False
        except Exception as e:
            logger.error(f"Error unmounting system image: {str(e)}")
            return False
            
    def _find_build_prop(self):
        """Find build.prop file in mounted system."""
        if not self.is_mounted:
            logger.error("System is not mounted")
            return None
            
        # Common locations for build.prop
        build_prop_paths = [
            os.path.join(self.mount_point, "system", "build.prop"),
            os.path.join(self.mount_point, "build.prop"),
        ]
        
        for path in build_prop_paths:
            if os.path.exists(path):
                return path
                
        logger.error("Could not find build.prop file")
        return None
        
    def modify_build_prop(self, properties):
        """Modify build.prop file with custom properties."""
        build_prop_path = self._find_build_prop()
        if not build_prop_path:
            return False
            
        try:
            # Read current build.prop
            with open(build_prop_path, "r") as f:
                build_prop_content = f.read()
                
            # Create backup
            backup_path = f"{build_prop_path}.backup"
            with open(backup_path, "w") as f:
                f.write(build_prop_content)
                
            # Update or add each property
            for key, value in properties.items():
                # Check if property already exists
                pattern = re.compile(f"^{re.escape(key)}=.*$", re.MULTILINE)
                if pattern.search(build_prop_content):
                    # Update existing property
                    build_prop_content = pattern.sub(f"{key}={value}", build_prop_content)
                else:
                    # Add new property
                    build_prop_content += f"\n{key}={value}"
                    
            # Write modified content
            with open(build_prop_path, "w") as f:
                f.write(build_prop_content)
                
            logger.info(f"Modified build.prop with {len(properties)} properties")
            return True
        except Exception as e:
            logger.error(f"Error modifying build.prop: {str(e)}")
            return False
            
    def install_frida_server(self, frida_server_path=None):
        """Install Frida server on the Android system."""
        if not self.is_mounted:
            logger.error("System is not mounted")
            return False
            
        # Default Frida server path if not provided
        if not frida_server_path:
            frida_server_path = os.path.join(
                os.path.expanduser("~"), ".config", "undetected-emulator", "frida-server"
            )
            
        if not os.path.exists(frida_server_path):
            logger.error(f"Frida server not found at {frida_server_path}")
            return False
            
        try:
            # Find a suitable location to install Frida server
            xbin_path = os.path.join(self.mount_point, "system", "xbin")
            bin_path = os.path.join(self.mount_point, "system", "bin")
            
            install_path = None
            if os.path.exists(xbin_path):
                install_path = os.path.join(xbin_path, "frida-server")
            elif os.path.exists(bin_path):
                install_path = os.path.join(bin_path, "frida-server")
            else:
                logger.error("Could not find suitable location for Frida server")
                return False
                
            # Copy Frida server
            shutil.copy2(frida_server_path, install_path)
            
            # Set executable permissions
            os.chmod(install_path, 0o755)
            
            logger.info(f"Installed Frida server to {install_path}")
            
            # Add init script to start Frida on boot
            self._add_frida_init_script()
            
            return True
        except Exception as e:
            logger.error(f"Error installing Frida server: {str(e)}")
            return False
            
    def _add_frida_init_script(self):
        """Add init script to start Frida server on boot."""
        init_rc_paths = [
            os.path.join(self.mount_point, "system", "etc", "init.rc"),
            os.path.join(self.mount_point, "init.rc"),
        ]
        
        init_script = """
# Start Frida server
service frida /system/xbin/frida-server --listen=0.0.0.0:27042
    class late_start
    user root
    group root
    setenv LD_PRELOAD /data/local/tmp/libfrida-gadget.so
"""
        
        for path in init_rc_paths:
            if os.path.exists(path):
                try:
                    with open(path, "a") as f:
                        f.write(init_script)
                    logger.info(f"Added Frida init script to {path}")
                    return True
                except Exception as e:
                    logger.error(f"Error adding Frida init script: {str(e)}")
                    
        logger.error("Could not find suitable init.rc file")
        return False
        
    def install_xposed_framework(self, xposed_path=None):
        """Install Xposed framework on the Android system."""
        if not self.is_mounted:
            logger.error("System is not mounted")
            return False
            
        # This is a placeholder since Xposed installation is complex
        # and would typically involve multiple files and modifications
        logger.info("Xposed framework installation not yet implemented")
        return False
        
    def disable_emulator_properties(self):
        """Disable or modify properties that reveal the system as an emulator."""
        if not self.is_mounted:
            logger.error("System is not mounted")
            return False
            
        # Properties that typically reveal an emulator
        anti_emulator_props = {
            "ro.kernel.qemu": "0",
            "ro.kernel.android.qemud": "0",
            "ro.bootloader": "unknown",
            "ro.hardware": "mt6582",  # Typical hardware for a mid-range device
            "ro.secure": "1",
            "qemu.hw.mainkeys": "0",
            "qemu.sf.fake_camera": "none",
            "qemu.sf.lcd_density": "440",
        }
        
        return self.modify_build_prop(anti_emulator_props)
        
    def customize_system_files(self, hardware_profile):
        """Customize system files based on hardware profile."""
        if not self.is_mounted or not hardware_profile:
            logger.error("System not mounted or no hardware profile provided")
            return False
            
        success = True
        
        # Apply build.prop changes
        if "build_prop" in hardware_profile:
            success = success and self.modify_build_prop(hardware_profile["build_prop"])
            
        # Disable default emulator properties
        success = success and self.disable_emulator_properties()
        
        # TODO: Implement more customizations based on hardware profile
        # - Modify device files for sensors
        # - Update system libraries
        # - Modify framework files
        
        return success


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    
    # Example hardware profile
    hardware_profile = {
        "manufacturer": "Samsung",
        "model": "Galaxy S21",
        "android_version": "12.0",
        "build_prop": {
            "ro.product.manufacturer": "Samsung",
            "ro.product.model": "SM-G991B",
            "ro.product.name": "galaxy_s21",
            "ro.build.id": "SP1A.210812.016",
            "ro.build.version.release": "12",
            "ro.build.version.sdk": "31",
        }
    }
    
    customizer = AndroidCustomizer()
    print("Android Customizer initialized")
    
    # This part would need an actual system image to test
    # customizer.set_system_path("/path/to/system.img")
    # if customizer.mount_system():
    #     customizer.customize_system_files(hardware_profile)
    #     customizer.unmount_system()