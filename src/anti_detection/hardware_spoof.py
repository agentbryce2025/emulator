#!/usr/bin/env python3
"""
Hardware spoofing module for the undetected Android emulator.
This module handles spoofing hardware identifiers to avoid detection.
"""

import os
import random
import string
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class HardwareSpoofer:
    """Handles hardware identifier spoofing."""
    
    def __init__(self, profile_path=None):
        """Initialize hardware spoofer with optional profile path."""
        self.profile_path = profile_path or os.path.join(
            os.path.expanduser("~"), ".config", "undetected-emulator", "device_profiles"
        )
        self.current_profile = None
        self.available_profiles = []
        
        # Ensure profile directory exists
        os.makedirs(self.profile_path, exist_ok=True)
        
        # Load available profiles
        self._load_available_profiles()
        
    def _load_available_profiles(self):
        """Load all available device profiles."""
        self.available_profiles = []
        
        try:
            for file in os.listdir(self.profile_path):
                if file.endswith(".json"):
                    self.available_profiles.append(file[:-5])  # Remove .json extension
            logger.info(f"Loaded {len(self.available_profiles)} device profiles")
        except Exception as e:
            logger.error(f"Error loading device profiles: {str(e)}")
            
    def apply_profile(self, profile):
        """Apply a device profile dictionary directly."""
        if not profile:
            logger.error("No profile provided")
            return False
            
        logger.info(f"Applying hardware profile: {profile.get('manufacturer', 'Unknown')} {profile.get('model', 'Unknown')}")
        self.current_profile = profile
        return True
    
    def load_profile(self, profile_name):
        """Load a specific device profile."""
        profile_file = os.path.join(self.profile_path, f"{profile_name}.json")
        
        if not os.path.exists(profile_file):
            logger.error(f"Profile {profile_name} not found")
            return False
            
        try:
            with open(profile_file, "r") as f:
                self.current_profile = json.load(f)
            logger.info(f"Loaded profile {profile_name}")
            return True
        except Exception as e:
            logger.error(f"Error loading profile {profile_name}: {str(e)}")
            return False
            
    def save_profile(self, profile_name):
        """Save current profile to file."""
        if not self.current_profile:
            logger.error("No profile to save")
            return False
            
        profile_file = os.path.join(self.profile_path, f"{profile_name}.json")
        
        try:
            with open(profile_file, "w") as f:
                json.dump(self.current_profile, f, indent=2)
            logger.info(f"Saved profile {profile_name}")
            
            # Update available profiles
            if profile_name not in self.available_profiles:
                self.available_profiles.append(profile_name)
                
            return True
        except Exception as e:
            logger.error(f"Error saving profile {profile_name}: {str(e)}")
            return False
            
    def create_new_profile(self, manufacturer, model, android_version):
        """Create a new device profile with randomized identifiers."""
        # Generate random identifiers
        imei = self._generate_imei()
        serial = self._generate_serial()
        mac_addr = self._generate_mac_address()
        android_id = self._generate_android_id()
        
        self.current_profile = {
            "manufacturer": manufacturer,
            "model": model,
            "android_version": android_version,
            "sdk_version": self._get_sdk_version(android_version),
            "identifiers": {
                "imei": imei,
                "serial": serial,
                "mac_address": mac_addr,
                "android_id": android_id,
                "build_fingerprint": f"{manufacturer}/{model}/{model}:{android_version}/release-keys",
                "build_tags": "release-keys",
                "build_type": "user",
            },
            "build_prop": {
                "ro.product.manufacturer": manufacturer,
                "ro.product.model": model,
                "ro.product.name": model.lower().replace(" ", "_"),
                "ro.product.device": model.lower().replace(" ", "_"),
                "ro.build.id": self._generate_build_id(),
                "ro.build.display.id": f"{android_version}.{random.randint(0, 5)}.{random.randint(1, 9)}",
                "ro.build.version.release": android_version,
                "ro.build.version.sdk": str(self._get_sdk_version(android_version)),
                "ro.build.date": self._generate_build_date(),
                "ro.build.date.utc": str(int(random.random() * 1600000000)),
                "ro.build.type": "user",
                "ro.build.tags": "release-keys",
                "ro.build.fingerprint": f"{manufacturer}/{model}/{model}:{android_version}/release-keys",
                "ro.serialno": serial,
                "ro.boot.serialno": serial,
                "net.hostname": f"{model.lower().replace(' ', '-')}-{random.randint(1000, 9999)}",
            },
            "sensors": {
                "accelerometer": True,
                "gyroscope": True,
                "magnetometer": True,
                "proximity": True,
                "light": True,
                "pressure": random.choice([True, False]),
                "temperature": random.choice([True, False]),
                "humidity": random.choice([True, False]),
            }
        }
        
        return self.current_profile
            
    def _generate_imei(self):
        """Generate a valid IMEI number."""
        # IMEI format: AA-BBBBBB-CCCCCC-D
        # AA: Type Allocation Code (TAC)
        # BBBBBB: Serial Number
        # CCCCCC: Usually zeros
        # D: Check digit
        
        # Simplified implementation for demo
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
        # Typical format: [A-Z]{3}[A-Z0-9]{5,12}
        prefix = ''.join(random.choices(string.ascii_uppercase, k=3))
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(5, 12)))
        return prefix + suffix
        
    def _generate_mac_address(self):
        """Generate a random MAC address."""
        # Format: XX:XX:XX:XX:XX:XX
        return ':'.join(['%02x' % random.randint(0, 255) for _ in range(6)])
        
    def _generate_android_id(self):
        """Generate a random Android ID."""
        # Format: 16 hexadecimal characters
        return ''.join(random.choices('0123456789abcdef', k=16))
        
    def _generate_build_id(self):
        """Generate a random build ID."""
        # Format: Usually 3 letters followed by numbers, e.g., "QP1A.190711.020"
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=1))
        date = f"{random.randint(190001, 230012)}.{random.randint(1, 999):03d}"
        return f"{letters}{numbers}A.{date}"
        
    def _generate_build_date(self):
        """Generate a random build date."""
        # Format: "day month year hour:minute:second timezone"
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        day = random.randint(1, 28)
        month = random.choice(months)
        year = random.randint(2020, 2023)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        return f"{day} {month} {year} {hour:02d}:{minute:02d}:{second:02d}"
        
    def _get_sdk_version(self, android_version):
        """Map Android version to SDK version."""
        version_map = {
            "8.0": 26,
            "8.1": 27,
            "9.0": 28,
            "10.0": 29,
            "11.0": 30,
            "12.0": 31,
            "13.0": 33,
            "14.0": 34,
        }
        
        return version_map.get(android_version, 29)  # Default to Android 10 SDK
        
    def generate_build_prop(self):
        """Generate a build.prop file content based on current profile."""
        if not self.current_profile:
            logger.error("No profile loaded")
            return None
            
        build_prop_content = ""
        
        for key, value in self.current_profile["build_prop"].items():
            build_prop_content += f"{key}={value}\n"
            
        return build_prop_content
        
    def apply_to_system(self, system_path):
        """Apply hardware spoofing to a system image."""
        if not self.current_profile:
            logger.error("No profile loaded")
            return False
            
        # This would need to be implemented based on the specific method
        # used to modify the system image
        logger.info(f"Applying hardware spoofing to system at {system_path}")
        
        # Placeholder for actual implementation
        # This would involve:
        # 1. Mounting the system image
        # 2. Modifying build.prop
        # 3. Possibly modifying other system files
        # 4. Unmounting the system image
        
        return True


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    spoofer = HardwareSpoofer()
    profile = spoofer.create_new_profile("Samsung", "Galaxy S21", "12.0")
    print(json.dumps(profile, indent=2))
    print("\nBuild.prop content:")
    print(spoofer.generate_build_prop())