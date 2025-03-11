#!/usr/bin/env python3
"""
Device profile database for the undetected Android emulator.
This module manages a database of real device profiles for emulation.
"""

import os
import json
import logging
import random
import re
from pathlib import Path

logger = logging.getLogger(__name__)

class DeviceProfileDatabase:
    """Manages a database of real device hardware profiles."""
    
    DEFAULT_PROFILES = {
        "samsung_galaxy_s21": {
            "manufacturer": "Samsung",
            "model": "SM-G991B",
            "brand": "samsung",
            "product": "galaxy_s21",
            "device": "g991b",
            "board": "exynos2100",
            "hardware": "exynos2100",
            "platform": "exynos2100",
            "android_version": "12",
            "sdk": "31",
            "build_id": "SP1A.210812.016",
            "fingerprint": "samsung/galaxy_s21/g991b:12/SP1A.210812.016/G991BXXU4CVFD:user/release-keys",
            "build_time": "1645754400000",
            "security_patch": "2022-03-01",
            "build_description": "galaxy_s21-user 12 SP1A.210812.016 G991BXXU4CVFD release-keys",
            "sensors": {
                "accelerometer": {
                    "name": "LSM6DSO Accelerometer",
                    "vendor": "STMicroelectronics",
                    "resolution": 0.0012,
                    "max_range": 39.2266,
                    "power": 0.58,
                    "min_delay": 10000
                },
                "gyroscope": {
                    "name": "LSM6DSO Gyroscope",
                    "vendor": "STMicroelectronics",
                    "resolution": 0.00106,
                    "max_range": 34.906586,
                    "power": 0.58,
                    "min_delay": 10000
                },
                "magnetometer": {
                    "name": "AK09918 Magnetometer",
                    "vendor": "AKM",
                    "resolution": 0.15,
                    "max_range": 4912,
                    "power": 1.1,
                    "min_delay": 10000
                },
                "light": {
                    "name": "TMD4910 Light sensor",
                    "vendor": "AMS",
                    "resolution": 1.0,
                    "max_range": 65535,
                    "power": 0.15,
                    "min_delay": 0
                },
                "proximity": {
                    "name": "TMD4910 Proximity sensor",
                    "vendor": "AMS",
                    "resolution": 1.0,
                    "max_range": 5,
                    "power": 0.75,
                    "min_delay": 0
                },
                "gravity": {
                    "name": "Gravity",
                    "vendor": "Samsung",
                    "resolution": 0.0012,
                    "max_range": 39.2266,
                    "power": 0.58,
                    "min_delay": 10000
                },
                "pressure": {
                    "name": "LPS22HH Pressure sensor",
                    "vendor": "STMicroelectronics",
                    "resolution": 0.0012,
                    "max_range": 1100,
                    "power": 0.58,
                    "min_delay": 10000
                }
            },
            "cpu": {
                "processors": 8,
                "architecture": "arm64-v8a",
                "features": [
                    "neon", "aes", "pmull", "sha1", "sha2", "crc32", "atomics", "fphp", "asimdhp"
                ],
                "governor": "schedutil",
                "min_freq": 300000,
                "max_freq": 2900000,
                "abi_list": ["arm64-v8a", "armeabi-v7a", "armeabi"]
            },
            "gpu": {
                "vendor": "ARM",
                "renderer": "Mali-G78 MP14",
                "version": "OpenGL ES 3.2",
                "extensions": [
                    "GL_OES_EGL_image",
                    "GL_OES_EGL_image_external",
                    "GL_OES_EGL_sync",
                    "GL_OES_vertex_half_float",
                    "GL_OES_framebuffer_object",
                    "GL_OES_compressed_ETC1_RGB8_texture",
                    "GL_AMD_performance_monitor",
                    "GL_EXT_debug_label",
                    "GL_EXT_debug_marker"
                ]
            },
            "battery": {
                "capacity": 4000,
                "technology": "Li-ion"
            },
            "screen": {
                "density": 440,
                "width": 1440,
                "height": 3200,
                "refresh_rate": 120,
                "sizeCategory": 4
            },
            "camera": {
                "back": {
                    "model": "GH1",
                    "vendor": "Samsung",
                    "resolution": "64MP",
                    "aperture": "f/1.8",
                    "features": ["OIS", "PDAF"]
                },
                "front": {
                    "model": "SLSI_S5KGD2",
                    "vendor": "Samsung",
                    "resolution": "10MP",
                    "aperture": "f/2.2"
                }
            },
            "network": {
                "imei_prefix": "35429010",
                "sim_operator": "310260",
                "cell_operator": "T-Mobile",
                "network_types": ["5G", "LTE", "HSDPA", "HSUPA", "UMTS", "EDGE", "GPRS"]
            },
            "build_prop": {}  # Will be filled programmatically
        },
        "google_pixel_6": {
            "manufacturer": "Google",
            "model": "Pixel 6",
            "brand": "google",
            "product": "raven",
            "device": "raven",
            "board": "gs101",
            "hardware": "gs101",
            "platform": "gs101",
            "android_version": "12",
            "sdk": "31",
            "build_id": "SD1A.210817.036",
            "fingerprint": "google/raven/raven:12/SD1A.210817.036/8082104:user/release-keys",
            "build_time": "1634774400000",
            "security_patch": "2021-11-01",
            "build_description": "raven-user 12 SD1A.210817.036 8082104 release-keys",
            "sensors": {
                "accelerometer": {
                    "name": "BMI260 Accelerometer",
                    "vendor": "Bosch",
                    "resolution": 0.0017,
                    "max_range": 156.9064,
                    "power": 0.15,
                    "min_delay": 5000
                },
                "gyroscope": {
                    "name": "BMI260 Gyroscope",
                    "vendor": "Bosch",
                    "resolution": 0.0006,
                    "max_range": 34.906586,
                    "power": 0.2,
                    "min_delay": 5000
                },
                "magnetometer": {
                    "name": "MMC5603 Magnetometer",
                    "vendor": "MEMSIC",
                    "resolution": 0.0625,
                    "max_range": 4800,
                    "power": 0.1,
                    "min_delay": 10000
                },
                "light": {
                    "name": "TCS3701 Light sensor",
                    "vendor": "AMS",
                    "resolution": 1.0,
                    "max_range": 60000,
                    "power": 0.1,
                    "min_delay": 0
                },
                "proximity": {
                    "name": "TCS3701 Proximity sensor",
                    "vendor": "AMS",
                    "resolution": 1.0,
                    "max_range": 5,
                    "power": 0.1,
                    "min_delay": 0
                },
                "barometer": {
                    "name": "BMP390 Pressure sensor",
                    "vendor": "Bosch",
                    "resolution": 0.0018,
                    "max_range": 1100,
                    "power": 0.004,
                    "min_delay": 10000
                }
            },
            "cpu": {
                "processors": 8,
                "architecture": "arm64-v8a",
                "features": ["neon", "aes", "pmull", "sha1", "sha2", "crc32"],
                "governor": "schedutil",
                "min_freq": 300000,
                "max_freq": 2800000,
                "abi_list": ["arm64-v8a", "armeabi-v7a", "armeabi"]
            },
            "gpu": {
                "vendor": "ARM",
                "renderer": "Mali-G78 MP20",
                "version": "OpenGL ES 3.2",
                "extensions": []
            },
            "battery": {
                "capacity": 4614,
                "technology": "Li-Po"
            },
            "screen": {
                "density": 420,
                "width": 1080,
                "height": 2400,
                "refresh_rate": 90,
                "sizeCategory": 4
            },
            "camera": {
                "back": {
                    "model": "GN1",
                    "vendor": "Samsung",
                    "resolution": "50MP",
                    "aperture": "f/1.85",
                    "features": ["OIS", "PDAF"]
                },
                "front": {
                    "model": "IMX663",
                    "vendor": "Sony",
                    "resolution": "8MP",
                    "aperture": "f/2.0"
                }
            },
            "network": {
                "imei_prefix": "35833811",
                "sim_operator": "310120",
                "cell_operator": "Sprint",
                "network_types": ["5G", "LTE", "HSDPA", "HSUPA", "UMTS", "EDGE", "GPRS"]
            },
            "build_prop": {}  # Will be filled programmatically
        },
        "xiaomi_redmi_note_10": {
            "manufacturer": "Xiaomi",
            "model": "Redmi Note 10",
            "brand": "redmi",
            "product": "mojito",
            "device": "mojito",
            "board": "mojito",
            "hardware": "qcom",
            "platform": "bengal",
            "android_version": "11",
            "sdk": "30",
            "build_id": "RKQ1.201004.002",
            "fingerprint": "redmi/mojito/mojito:11/RKQ1.201004.002/V12.0.8.0:user/release-keys",
            "build_time": "1626271036000",
            "security_patch": "2021-07-01",
            "build_description": "mojito-user 11 RKQ1.201004.002 V12.0.8.0 release-keys",
            "sensors": {
                "accelerometer": {
                    "name": "ICP10100 Accelerometer",
                    "vendor": "TDK-InvenSense",
                    "resolution": 0.0012,
                    "max_range": 78.4532,
                    "power": 0.25,
                    "min_delay": 10000
                },
                "gyroscope": {
                    "name": "ICP10100 Gyroscope",
                    "vendor": "TDK-InvenSense",
                    "resolution": 0.0012,
                    "max_range": 34.906586,
                    "power": 0.25,
                    "min_delay": 10000
                },
                "magnetometer": {
                    "name": "AK09918 Magnetometer",
                    "vendor": "AKM",
                    "resolution": 0.15,
                    "max_range": 4800,
                    "power": 0.15,
                    "min_delay": 20000
                },
                "light": {
                    "name": "STK3A5X Light sensor",
                    "vendor": "Sensortek",
                    "resolution": 1.0,
                    "max_range": 10000,
                    "power": 0.09,
                    "min_delay": 0
                },
                "proximity": {
                    "name": "STK3A5X Proximity sensor",
                    "vendor": "Sensortek",
                    "resolution": 1.0,
                    "max_range": 5,
                    "power": 0.12,
                    "min_delay": 0
                }
            },
            "cpu": {
                "processors": 8,
                "architecture": "arm64-v8a",
                "features": ["neon", "aes", "pmull", "sha1", "sha2", "crc32"],
                "governor": "schedutil",
                "min_freq": 300000,
                "max_freq": 2000000,
                "abi_list": ["arm64-v8a", "armeabi-v7a", "armeabi"]
            },
            "gpu": {
                "vendor": "Qualcomm",
                "renderer": "Adreno 618",
                "version": "OpenGL ES 3.2",
                "extensions": []
            },
            "battery": {
                "capacity": 5000,
                "technology": "Li-Po"
            },
            "screen": {
                "density": 395,
                "width": 1080,
                "height": 2400,
                "refresh_rate": 60,
                "sizeCategory": 3
            },
            "camera": {
                "back": {
                    "model": "S5KGW3",
                    "vendor": "Samsung",
                    "resolution": "48MP",
                    "aperture": "f/1.8",
                    "features": ["PDAF"]
                },
                "front": {
                    "model": "OV13B10",
                    "vendor": "OmniVision",
                    "resolution": "13MP",
                    "aperture": "f/2.5"
                }
            },
            "network": {
                "imei_prefix": "86765403",
                "sim_operator": "310410",
                "cell_operator": "AT&T",
                "network_types": ["LTE", "HSDPA", "HSUPA", "UMTS", "EDGE", "GPRS"]
            },
            "build_prop": {}  # Will be filled programmatically
        }
    }
    
    def __init__(self, profiles_dir=None):
        """Initialize the device profile database."""
        if profiles_dir:
            self.profiles_dir = Path(profiles_dir)
        else:
            # Default to ~/.config/undetected-emulator/device_profiles
            self.profiles_dir = Path.home() / ".config" / "undetected-emulator" / "device_profiles"
            
        # Create profiles directory if it doesn't exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create default profiles
        self._ensure_default_profiles()
        
    def _ensure_default_profiles(self):
        """Ensure default profiles are available in the profiles directory."""
        for profile_name, profile_data in self.DEFAULT_PROFILES.items():
            # Generate build.prop entries from profile data
            profile_data["build_prop"] = self._generate_build_prop(profile_data)
            
            # Save profile to file if it doesn't exist
            profile_path = self.profiles_dir / f"{profile_name}.json"
            if not profile_path.exists():
                with open(profile_path, "w") as f:
                    json.dump(profile_data, f, indent=2)
                    
                logger.info(f"Created default profile: {profile_name}")
                
    def _generate_build_prop(self, profile):
        """Generate build.prop entries from profile data."""
        build_prop = {}
        
        # Basic device identifiers
        build_prop["ro.product.manufacturer"] = profile["manufacturer"]
        build_prop["ro.product.model"] = profile["model"]
        build_prop["ro.product.brand"] = profile["brand"]
        build_prop["ro.product.name"] = profile["product"]
        build_prop["ro.product.device"] = profile["device"]
        build_prop["ro.product.board"] = profile["board"]
        build_prop["ro.hardware"] = profile["hardware"]
        build_prop["ro.product.cpu.abi"] = "arm64-v8a"
        build_prop["ro.product.cpu.abilist"] = ",".join(profile["cpu"]["abi_list"])
        
        # Build information
        build_prop["ro.build.id"] = profile["build_id"]
        build_prop["ro.build.display.id"] = profile["build_id"]
        build_prop["ro.build.version.release"] = profile["android_version"]
        build_prop["ro.build.version.sdk"] = profile["sdk"]
        build_prop["ro.build.date.utc"] = profile["build_time"]
        build_prop["ro.build.type"] = "user"
        build_prop["ro.build.user"] = "android-build"
        build_prop["ro.build.host"] = "android-build"
        build_prop["ro.build.tags"] = "release-keys"
        build_prop["ro.build.fingerprint"] = profile["fingerprint"]
        build_prop["ro.build.description"] = profile["build_description"]
        build_prop["ro.build.version.security_patch"] = profile["security_patch"]
        
        # System properties
        build_prop["ro.sf.lcd_density"] = str(profile["screen"]["density"])
        build_prop["ro.crypto.state"] = "encrypted"
        build_prop["ro.crypto.type"] = "file"
        build_prop["ro.config.ringtone"] = "Ring_Synth_04.ogg"
        build_prop["ro.config.notification_sound"] = "pixiedust.ogg"
        build_prop["ro.carrier"] = "unknown"
        
        # Anti-detection properties
        build_prop["ro.kernel.qemu"] = "0"
        build_prop["ro.hardware.sensors"] = profile["sensors"]["accelerometer"]["vendor"].lower()
        build_prop["ro.boot.hardware"] = profile["hardware"]
        build_prop["ro.bootloader"] = f"{profile['manufacturer'].upper()}-{profile['board'].upper()}"
        build_prop["ro.build.characteristics"] = "default"
        build_prop["ro.radio.noril"] = "no"
        
        # Battery properties
        build_prop["ro.battery.capacity"] = str(profile["battery"]["capacity"])
        
        return build_prop
        
    def get_profile_names(self):
        """Get names of all available profiles."""
        profiles = []
        
        for profile_path in self.profiles_dir.glob("*.json"):
            profiles.append(profile_path.stem)
            
        return sorted(profiles)
        
    def get_profile(self, profile_name):
        """Get a specific profile by name."""
        profile_path = self.profiles_dir / f"{profile_name}.json"
        
        if not profile_path.exists():
            logger.error(f"Profile {profile_name} not found")
            return None
            
        try:
            with open(profile_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load profile {profile_name}: {str(e)}")
            return None
            
    def create_profile(self, name, data):
        """Create a new device profile."""
        # Sanitize name to be filesystem-friendly
        name = re.sub(r'[^\w\-_]', '_', name).lower()
        
        profile_path = self.profiles_dir / f"{name}.json"
        
        # Don't overwrite existing profiles unless explicitly stated
        if profile_path.exists():
            logger.warning(f"Profile {name} already exists")
            return False
            
        # Generate build.prop if not provided
        if "build_prop" not in data or not data["build_prop"]:
            data["build_prop"] = self._generate_build_prop(data)
            
        try:
            with open(profile_path, "w") as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Created profile: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create profile {name}: {str(e)}")
            return False
            
    def update_profile(self, name, data):
        """Update an existing device profile."""
        profile_path = self.profiles_dir / f"{name}.json"
        
        if not profile_path.exists():
            logger.error(f"Profile {name} not found")
            return False
            
        # Generate build.prop if not provided
        if "build_prop" not in data or not data["build_prop"]:
            data["build_prop"] = self._generate_build_prop(data)
            
        try:
            with open(profile_path, "w") as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Updated profile: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update profile {name}: {str(e)}")
            return False
            
    def delete_profile(self, name):
        """Delete a device profile."""
        profile_path = self.profiles_dir / f"{name}.json"
        
        if not profile_path.exists():
            logger.warning(f"Profile {name} not found")
            return False
            
        try:
            profile_path.unlink()
            logger.info(f"Deleted profile: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete profile {name}: {str(e)}")
            return False
            
    def get_random_profile(self):
        """Get a random profile from the available profiles."""
        profiles = self.get_profile_names()
        
        if not profiles:
            logger.warning("No profiles available")
            return None
            
        random_profile_name = random.choice(profiles)
        return self.get_profile(random_profile_name)


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    
    db = DeviceProfileDatabase()
    print("Available profiles:", db.get_profile_names())
    
    # Get a random profile
    random_profile = db.get_random_profile()
    if random_profile:
        print(f"Random profile: {random_profile['manufacturer']} {random_profile['model']}")
        print(f"Android version: {random_profile['android_version']}")
        print(f"Build ID: {random_profile['build_id']}")
        
        # Print some build.prop entries
        print("\nBuild.prop entries:")
        for key, value in list(random_profile["build_prop"].items())[:10]:
            print(f"{key}={value}")