#!/usr/bin/env python3
"""
Real device profile database.
This module provides a database of real device profiles for emulator configuration.
"""

import os
import json
import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)

class DeviceProfileDB:
    """Database of real device profiles for emulator configuration."""
    
    def __init__(self, db_path=None):
        """Initialize the device profile database."""
        self.db_path = db_path or os.path.join(
            os.path.expanduser("~"), ".config", "undetected-emulator", "device_profiles_db"
        )
        self.profiles = {}
        self.manufacturers = []
        
        # Ensure database directory exists
        os.makedirs(self.db_path, exist_ok=True)
        
        # Load profiles
        self._load_profiles()
        
    def _load_profiles(self):
        """Load all available device profiles."""
        self.profiles = {}
        
        try:
            for file in os.listdir(self.db_path):
                if file.endswith(".json"):
                    manufacturer = file[:-5]  # Remove .json extension
                    self.manufacturers.append(manufacturer)
                    
                    with open(os.path.join(self.db_path, file), "r") as f:
                        self.profiles[manufacturer] = json.load(f)
                        
            logger.info(f"Loaded {len(self.profiles)} manufacturer profiles")
            
            # If no profiles exist, create default profiles
            if not self.profiles:
                self._create_default_profiles()
        except Exception as e:
            logger.error(f"Error loading device profiles: {str(e)}")
            
    def _create_default_profiles(self):
        """Create default device profiles if none exist."""
        # Samsung devices
        samsung_devices = {
            "Galaxy S21": {
                "model": "SM-G991B",
                "android_versions": ["11.0", "12.0"],
                "properties": {
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.model": "SM-G991B",
                    "ro.product.name": "sm-g991b",
                    "ro.product.device": "sm-g991b",
                    "ro.build.fingerprint": "samsung/SM-G991B/SM-G991B:12/SP1A.210812.016/G991BXXU3AUL3:user/release-keys",
                    "ro.build.id": "SP1A.210812.016",
                    "ro.build.display.id": "SP1A.210812.016.G991BXXU3AUL3",
                    "ro.build.type": "user",
                    "ro.build.tags": "release-keys",
                    "ro.build.date.utc": "1638360000",
                    "ro.hardware": "exynos2100",
                    "ro.board.platform": "exynos2100"
                },
                "sensors": ["accelerometer", "gyroscope", "magnetometer", "proximity", "light", "pressure", "temperature"]
            },
            "Galaxy S20": {
                "model": "SM-G980F",
                "android_versions": ["10.0", "11.0", "12.0"],
                "properties": {
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.model": "SM-G980F",
                    "ro.product.name": "sm-g980f",
                    "ro.product.device": "sm-g980f",
                    "ro.build.fingerprint": "samsung/SM-G980F/SM-G980F:12/SP1A.210812.016/G980FXXSCEUL9:user/release-keys",
                    "ro.build.id": "SP1A.210812.016",
                    "ro.build.display.id": "SP1A.210812.016.G980FXXSCEUL9",
                    "ro.build.type": "user",
                    "ro.build.tags": "release-keys",
                    "ro.build.date.utc": "1640700000",
                    "ro.hardware": "exynos990",
                    "ro.board.platform": "exynos990"
                },
                "sensors": ["accelerometer", "gyroscope", "magnetometer", "proximity", "light", "pressure", "temperature"]
            },
            "Galaxy A52": {
                "model": "SM-A525F",
                "android_versions": ["11.0", "12.0"],
                "properties": {
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.model": "SM-A525F",
                    "ro.product.name": "sm-a525f",
                    "ro.product.device": "sm-a525f",
                    "ro.build.fingerprint": "samsung/SM-A525F/SM-A525F:12/SP1A.210812.016/A525FXXU4BVA2:user/release-keys",
                    "ro.build.id": "SP1A.210812.016",
                    "ro.build.display.id": "SP1A.210812.016.A525FXXU4BVA2",
                    "ro.build.type": "user",
                    "ro.build.tags": "release-keys",
                    "ro.build.date.utc": "1642550000",
                    "ro.hardware": "qcom",
                    "ro.board.platform": "sm7125"
                },
                "sensors": ["accelerometer", "gyroscope", "magnetometer", "proximity", "light"]
            }
        }
        
        # Google Pixel devices
        pixel_devices = {
            "Pixel 6": {
                "model": "Pixel 6",
                "android_versions": ["12.0", "13.0"],
                "properties": {
                    "ro.product.manufacturer": "Google",
                    "ro.product.brand": "google",
                    "ro.product.model": "Pixel 6",
                    "ro.product.name": "raven",
                    "ro.product.device": "raven",
                    "ro.build.fingerprint": "google/raven/raven:13/TP1A.220624.021/8877034:user/release-keys",
                    "ro.build.id": "TP1A.220624.021",
                    "ro.build.display.id": "TP1A.220624.021",
                    "ro.build.type": "user",
                    "ro.build.tags": "release-keys",
                    "ro.build.date.utc": "1658880000",
                    "ro.hardware": "tensor",
                    "ro.board.platform": "gs101"
                },
                "sensors": ["accelerometer", "gyroscope", "magnetometer", "proximity", "light", "barometer", "temperature"]
            },
            "Pixel 5": {
                "model": "Pixel 5",
                "android_versions": ["11.0", "12.0", "13.0"],
                "properties": {
                    "ro.product.manufacturer": "Google",
                    "ro.product.brand": "google",
                    "ro.product.model": "Pixel 5",
                    "ro.product.name": "redfin",
                    "ro.product.device": "redfin",
                    "ro.build.fingerprint": "google/redfin/redfin:13/TP1A.220624.021/8877034:user/release-keys",
                    "ro.build.id": "TP1A.220624.021",
                    "ro.build.display.id": "TP1A.220624.021",
                    "ro.build.type": "user",
                    "ro.build.tags": "release-keys",
                    "ro.build.date.utc": "1658880000",
                    "ro.hardware": "qcom",
                    "ro.board.platform": "sm7250"
                },
                "sensors": ["accelerometer", "gyroscope", "magnetometer", "proximity", "light", "barometer"]
            }
        }
        
        # Xiaomi devices
        xiaomi_devices = {
            "Mi 11": {
                "model": "M2011K2G",
                "android_versions": ["11.0", "12.0"],
                "properties": {
                    "ro.product.manufacturer": "Xiaomi",
                    "ro.product.brand": "xiaomi",
                    "ro.product.model": "M2011K2G",
                    "ro.product.name": "venus",
                    "ro.product.device": "venus",
                    "ro.build.fingerprint": "Xiaomi/venus_global/venus:12/SKQ1.211006.001/V13.0.5.0.SKBMIXM:user/release-keys",
                    "ro.build.id": "SKQ1.211006.001",
                    "ro.build.display.id": "SKQ1.211006.001",
                    "ro.build.type": "user",
                    "ro.build.tags": "release-keys",
                    "ro.build.date.utc": "1645300000",
                    "ro.hardware": "qcom",
                    "ro.board.platform": "sm8350"
                },
                "sensors": ["accelerometer", "gyroscope", "magnetometer", "proximity", "light", "pressure"]
            },
            "Redmi Note 10": {
                "model": "M2101K7AG",
                "android_versions": ["11.0", "12.0"],
                "properties": {
                    "ro.product.manufacturer": "Xiaomi",
                    "ro.product.brand": "Redmi",
                    "ro.product.model": "M2101K7AG",
                    "ro.product.name": "angelica",
                    "ro.product.device": "angelica",
                    "ro.build.fingerprint": "Redmi/angelica_global/angelica:12/SKQ1.211019.001/V13.0.2.0.SKZMIXM:user/release-keys",
                    "ro.build.id": "SKQ1.211019.001",
                    "ro.build.display.id": "SKQ1.211019.001",
                    "ro.build.type": "user",
                    "ro.build.tags": "release-keys",
                    "ro.build.date.utc": "1646509000",
                    "ro.hardware": "mt6768",
                    "ro.board.platform": "mt6768"
                },
                "sensors": ["accelerometer", "gyroscope", "magnetometer", "proximity", "light"]
            }
        }
        
        # OnePlus devices
        oneplus_devices = {
            "OnePlus 9": {
                "model": "LE2113",
                "android_versions": ["11.0", "12.0"],
                "properties": {
                    "ro.product.manufacturer": "OnePlus",
                    "ro.product.brand": "OnePlus",
                    "ro.product.model": "LE2113",
                    "ro.product.name": "OnePlus9",
                    "ro.product.device": "OnePlus9",
                    "ro.build.fingerprint": "OnePlus/OnePlus9_EEA/OnePlus9:12/SKQ1.210216.001/R.202201181823:user/release-keys",
                    "ro.build.id": "SKQ1.210216.001",
                    "ro.build.display.id": "SKQ1.210216.001",
                    "ro.build.type": "user",
                    "ro.build.tags": "release-keys",
                    "ro.build.date.utc": "1642529000",
                    "ro.hardware": "qcom",
                    "ro.board.platform": "sm8350"
                },
                "sensors": ["accelerometer", "gyroscope", "magnetometer", "proximity", "light", "pressure"]
            }
        }
        
        # Save the profiles
        profiles = {
            "samsung": samsung_devices,
            "google": pixel_devices,
            "xiaomi": xiaomi_devices,
            "oneplus": oneplus_devices
        }
        
        for manufacturer, devices in profiles.items():
            self.profiles[manufacturer] = devices
            self.manufacturers.append(manufacturer)
            
            profile_path = os.path.join(self.db_path, f"{manufacturer}.json")
            with open(profile_path, "w") as f:
                json.dump(devices, f, indent=2)
                
        logger.info(f"Created default profiles for {len(profiles)} manufacturers")
        
    def get_manufacturers(self):
        """Get list of available manufacturers."""
        return self.manufacturers
        
    def get_devices(self, manufacturer):
        """Get list of available devices for a manufacturer."""
        if manufacturer not in self.profiles:
            return []
            
        return list(self.profiles[manufacturer].keys())
        
    def get_device_profile(self, manufacturer, device, android_version=None):
        """Get a specific device profile."""
        if manufacturer not in self.profiles or device not in self.profiles[manufacturer]:
            return None
            
        profile = self.profiles[manufacturer][device]
        
        # If no specific Android version is requested, use the highest available
        if android_version is None:
            android_version = profile["android_versions"][-1]
        
        # Check if the requested Android version is available
        if android_version not in profile["android_versions"]:
            logger.warning(f"Android version {android_version} not available for {manufacturer} {device}")
            android_version = profile["android_versions"][-1]
            logger.info(f"Using Android version {android_version} instead")
        
        # Deep copy and customize the profile for the specific Android version
        result = profile.copy()
        
        # Update the properties that depend on Android version
        if android_version == "11.0":
            result["properties"]["ro.build.version.release"] = "11"
            result["properties"]["ro.build.version.sdk"] = "30"
        elif android_version == "12.0":
            result["properties"]["ro.build.version.release"] = "12"
            result["properties"]["ro.build.version.sdk"] = "31"
        elif android_version == "13.0":
            result["properties"]["ro.build.version.release"] = "13"
            result["properties"]["ro.build.version.sdk"] = "33"
        elif android_version == "10.0":
            result["properties"]["ro.build.version.release"] = "10"
            result["properties"]["ro.build.version.sdk"] = "29"
        
        return result
        
    def get_random_profile(self, android_version=None):
        """Get a random device profile."""
        if not self.profiles:
            logger.error("No device profiles available")
            return None
            
        # Select random manufacturer and device
        manufacturer = random.choice(self.manufacturers)
        devices = self.get_devices(manufacturer)
        device = random.choice(devices)
        
        return self.get_device_profile(manufacturer, device, android_version)
        
    def add_device_profile(self, manufacturer, device, profile):
        """Add a new device profile."""
        if manufacturer not in self.profiles:
            self.profiles[manufacturer] = {}
            self.manufacturers.append(manufacturer)
            
        self.profiles[manufacturer][device] = profile
        
        # Save to file
        profile_path = os.path.join(self.db_path, f"{manufacturer}.json")
        
        try:
            with open(profile_path, "w") as f:
                json.dump(self.profiles[manufacturer], f, indent=2)
                
            logger.info(f"Added device profile: {manufacturer} {device}")
            return True
        except Exception as e:
            logger.error(f"Error saving device profile: {str(e)}")
            return False
            
    def delete_device_profile(self, manufacturer, device):
        """Delete a device profile."""
        if manufacturer not in self.profiles or device not in self.profiles[manufacturer]:
            logger.error(f"Device profile not found: {manufacturer} {device}")
            return False
            
        # Remove the device from the profiles
        del self.profiles[manufacturer][device]
        
        # If no more devices for this manufacturer, remove the manufacturer
        if not self.profiles[manufacturer]:
            del self.profiles[manufacturer]
            self.manufacturers.remove(manufacturer)
            
            # Remove the file
            profile_path = os.path.join(self.db_path, f"{manufacturer}.json")
            os.remove(profile_path)
        else:
            # Save the updated profiles
            profile_path = os.path.join(self.db_path, f"{manufacturer}.json")
            
            with open(profile_path, "w") as f:
                json.dump(self.profiles[manufacturer], f, indent=2)
                
        logger.info(f"Deleted device profile: {manufacturer} {device}")
        return True
        
    def generate_hardware_profile(self, manufacturer, device, android_version=None):
        """Generate a hardware profile for the specified device."""
        device_profile = self.get_device_profile(manufacturer, device, android_version)
        
        if not device_profile:
            logger.error(f"Device profile not found: {manufacturer} {device}")
            return None
            
        # Create hardware profile with the device's properties
        hardware_profile = {
            "manufacturer": manufacturer,
            "model": device,
            "android_version": android_version or device_profile["android_versions"][-1],
            "sdk_version": int(device_profile["properties"].get("ro.build.version.sdk", "31")),
            "identifiers": {
                "imei": self._generate_imei(),
                "serial": self._generate_serial(),
                "mac_address": self._generate_mac_address(),
                "android_id": self._generate_android_id(),
                "build_fingerprint": device_profile["properties"]["ro.build.fingerprint"],
                "build_tags": device_profile["properties"]["ro.build.tags"],
                "build_type": device_profile["properties"]["ro.build.type"],
            },
            "build_prop": device_profile["properties"],
            "sensors": {sensor: True for sensor in device_profile["sensors"]}
        }
        
        # Add some properties that might be missing
        if "ro.serialno" not in hardware_profile["build_prop"]:
            hardware_profile["build_prop"]["ro.serialno"] = hardware_profile["identifiers"]["serial"]
            
        if "ro.boot.serialno" not in hardware_profile["build_prop"]:
            hardware_profile["build_prop"]["ro.boot.serialno"] = hardware_profile["identifiers"]["serial"]
            
        if "net.hostname" not in hardware_profile["build_prop"]:
            hostname = f"{device_profile['properties']['ro.product.device']}-{random.randint(1000, 9999)}"
            hardware_profile["build_prop"]["net.hostname"] = hostname
            
        return hardware_profile
        
    def _generate_imei(self):
        """Generate a valid IMEI number."""
        # IMEI format: AA-BBBBBB-CCCCCC-D
        tac = random.choice(['01', '35', '86', '99'])
        serial = ''.join(random.choices('0123456789', k=6))
        remaining = ''.join(['0'] * 6)
        
        imei_without_check = tac + serial + remaining
        
        # Luhn algorithm for check digit
        sum = 0
        for i, digit in enumerate(imei_without_check):
            value = int(digit)
            if i % 2 == 1:  # Odd position (0-indexed)
                value *= 2
                if value > 9:
                    value -= 9
            sum += value
            
        check_digit = (10 - (sum % 10)) % 10
        
        return imei_without_check + str(check_digit)
        
    def _generate_serial(self):
        """Generate a random device serial number."""
        prefix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
        suffix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))
        return prefix + suffix
        
    def _generate_mac_address(self):
        """Generate a random MAC address."""
        return ':'.join(['%02x' % random.randint(0, 255) for _ in range(6)])
        
    def _generate_android_id(self):
        """Generate a random Android ID."""
        return ''.join(random.choices('0123456789abcdef', k=16))

if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    db = DeviceProfileDB()
    
    print("Available manufacturers:", db.get_manufacturers())
    
    manufacturer = "samsung"
    print(f"Available {manufacturer} devices:", db.get_devices(manufacturer))
    
    device = db.get_devices(manufacturer)[0]
    profile = db.get_device_profile(manufacturer, device)
    print(f"\nSample device profile for {manufacturer} {device}:")
    print(json.dumps(profile, indent=2))
    
    hardware_profile = db.generate_hardware_profile(manufacturer, device)
    print(f"\nGenerated hardware profile for {manufacturer} {device}:")
    print(json.dumps(hardware_profile, indent=2))