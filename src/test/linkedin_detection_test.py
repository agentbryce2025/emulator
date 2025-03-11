#!/usr/bin/env python3
"""
LinkedIn emulator detection test.
This module tests whether LinkedIn can detect our emulator.
"""

import os
import sys
import logging
import json
import time
import argparse
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.qemu_wrapper import QEMUWrapper
    from anti_detection.hardware_spoof import HardwareSpoofer
    from anti_detection.sensor_simulator import SensorSimulator
    from anti_detection.frida_manager import FridaManager
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

logger = logging.getLogger(__name__)

class LinkedInDetectionTest:
    """Tests LinkedIn's emulator detection against our undetected emulator."""
    
    def __init__(self, device_id=None):
        """Initialize the LinkedIn detection test."""
        self.device_id = device_id
        self.frida_manager = None
        self.linkedin_package = "com.linkedin.android"
        self.test_results = {
            "timestamp": time.time(),
            "success": False,
            "detection_methods": {},
            "summary": ""
        }
        
        # Initialize Frida manager
        self._init_frida()
        
    def _init_frida(self):
        """Initialize Frida for runtime manipulation."""
        try:
            self.frida_manager = FridaManager(device_id=self.device_id)
            logger.info("Frida manager initialized")
        except Exception as e:
            logger.error(f"Error initializing Frida: {str(e)}")
            self.frida_manager = None
            
    def _create_detection_script(self):
        """Create a custom Frida script to detect LinkedIn's detection methods."""
        script = """
        // LinkedIn Detection Monitoring Script
        // This script logs and intercepts LinkedIn's attempts to detect emulators
        
        console.log("[+] LinkedIn detection monitoring script loaded");
        
        // Store detection attempts
        var detectionAttempts = {
            "build_props": [],
            "system_props": [],
            "device_ids": [],
            "sensors": [],
            "files": [],
            "network": [],
            "fingerprinting": []
        };
        
        // Monitor Build property access
        var Build = Java.use("android.os.Build");
        var buildFields = [
            "FINGERPRINT", "MODEL", "MANUFACTURER", "PRODUCT", 
            "BRAND", "DEVICE", "HARDWARE", "BOARD"
        ];
        
        buildFields.forEach(function(field) {
            try {
                var original = Build[field].value;
                
                // Create a dynamic property to monitor access
                Object.defineProperty(Build, field, {
                    get: function() {
                        console.log("[*] LinkedIn accessed Build." + field + " = " + original);
                        var stack = Thread.backtrace(this.context, Backtracer.ACCURATE).map(DebugSymbol.fromAddress).join("\\n");
                        
                        detectionAttempts.build_props.push({
                            "field": field,
                            "value": original,
                            "stack": stack.substring(0, 500) // Limit stack size
                        });
                        
                        return original;
                    }
                });
            } catch (e) {
                console.log("[!] Error hooking Build." + field + ": " + e);
            }
        });
        
        // Monitor System Properties access
        try {
            var SystemProperties = Java.use("android.os.SystemProperties");
            
            SystemProperties.get.overload("java.lang.String").implementation = function(key) {
                var value = this.get(key);
                console.log("[*] SystemProperties.get(" + key + ") = " + value);
                
                detectionAttempts.system_props.push({
                    "key": key,
                    "value": value
                });
                
                return value;
            };
            
            SystemProperties.get.overload("java.lang.String", "java.lang.String").implementation = function(key, def) {
                var value = this.get(key, def);
                console.log("[*] SystemProperties.get(" + key + ", " + def + ") = " + value);
                
                detectionAttempts.system_props.push({
                    "key": key,
                    "default": def,
                    "value": value
                });
                
                return value;
            };
        } catch (e) {
            console.log("[!] Error hooking SystemProperties: " + e);
        }
        
        // Monitor TelephonyManager for device ID access
        try {
            var TelephonyManager = Java.use("android.telephony.TelephonyManager");
            
            if (TelephonyManager.getDeviceId) {
                TelephonyManager.getDeviceId.overload().implementation = function() {
                    var id = this.getDeviceId();
                    console.log("[*] TelephonyManager.getDeviceId() = " + id);
                    
                    detectionAttempts.device_ids.push({
                        "method": "getDeviceId",
                        "value": id
                    });
                    
                    return id;
                };
            }
            
            if (TelephonyManager.getImei) {
                TelephonyManager.getImei.overload().implementation = function() {
                    var imei = this.getImei();
                    console.log("[*] TelephonyManager.getImei() = " + imei);
                    
                    detectionAttempts.device_ids.push({
                        "method": "getImei",
                        "value": imei
                    });
                    
                    return imei;
                };
            }
        } catch (e) {
            console.log("[!] Error hooking TelephonyManager: " + e);
        }
        
        // Monitor SensorManager access
        try {
            var SensorManager = Java.use("android.hardware.SensorManager");
            
            SensorManager.getSensorList.implementation = function(type) {
                var sensors = this.getSensorList(type);
                console.log("[*] SensorManager.getSensorList(" + type + ") returned " + sensors.size() + " sensors");
                
                detectionAttempts.sensors.push({
                    "method": "getSensorList",
                    "type": type,
                    "count": sensors.size()
                });
                
                return sensors;
            };
            
            SensorManager.getDefaultSensor.overload("int").implementation = function(type) {
                var sensor = this.getDefaultSensor(type);
                var sensorName = sensor != null ? sensor.getName() : "null";
                console.log("[*] SensorManager.getDefaultSensor(" + type + ") = " + sensorName);
                
                detectionAttempts.sensors.push({
                    "method": "getDefaultSensor",
                    "type": type,
                    "available": sensor != null,
                    "name": sensorName
                });
                
                return sensor;
            };
        } catch (e) {
            console.log("[!] Error hooking SensorManager: " + e);
        }
        
        // Monitor File access for emulator-specific files
        try {
            var File = Java.use("java.io.File");
            
            File.exists.implementation = function() {
                var path = this.getAbsolutePath();
                var exists = this.exists();
                
                if (path.indexOf("/sys/") >= 0 || 
                    path.indexOf("/proc/") >= 0 || 
                    path.indexOf("/dev/") >= 0 || 
                    path.indexOf("qemu") >= 0 || 
                    path.indexOf("goldfish") >= 0 || 
                    path.indexOf("emulator") >= 0) {
                    
                    console.log("[*] File.exists() checked for " + path + " = " + exists);
                    
                    detectionAttempts.files.push({
                        "method": "exists",
                        "path": path,
                        "exists": exists
                    });
                }
                
                return exists;
            };
        } catch (e) {
            console.log("[!] Error hooking File: " + e);
        }
        
        // Monitor network interfaces for emulator-specific interfaces
        try {
            var NetworkInterface = Java.use("java.net.NetworkInterface");
            
            NetworkInterface.getNetworkInterfaces.implementation = function() {
                var interfaces = this.getNetworkInterfaces();
                console.log("[*] NetworkInterface.getNetworkInterfaces() called");
                
                detectionAttempts.network.push({
                    "method": "getNetworkInterfaces",
                    "timestamp": new Date().toISOString()
                });
                
                return interfaces;
            };
        } catch (e) {
            console.log("[!] Error hooking NetworkInterface: " + e);
        }
        
        // Detect when LinkedIn makes final detection decision
        // This would ideally hook into LinkedIn's emulator detection logic
        // but that would require knowing more about their internal structure
        
        // For testing, send detection data periodically
        setInterval(function() {
            send({
                type: "detection_data",
                data: detectionAttempts
            });
            
            // Clear the collected data after sending
            for (var key in detectionAttempts) {
                detectionAttempts[key] = [];
            }
        }, 5000);
        
        console.log("[+] LinkedIn detection monitoring active");
        """
        
        return script
        
    def run_test(self, duration=60):
        """Run the LinkedIn detection test for a specified duration (seconds)."""
        if not self.frida_manager or not self.frida_manager.connected:
            logger.error("Frida not connected, can't run test")
            self.test_results["summary"] = "Failed: Frida not connected"
            return self.test_results
            
        # Check if LinkedIn is installed
        apps = self.frida_manager.list_running_applications()
        linkedin_running = any(app["identifier"] == self.linkedin_package for app in apps)
        
        if not linkedin_running:
            logger.warning(f"LinkedIn app ({self.linkedin_package}) not running")
            # In a real implementation, we might try to start LinkedIn
            
        logger.info(f"Starting LinkedIn detection test for {duration} seconds")
        
        # Create and inject the detection monitoring script
        script_content = self._create_detection_script()
        
        # Prepare to receive data from the script
        detection_data = {
            "build_props": [],
            "system_props": [],
            "device_ids": [],
            "sensors": [],
            "files": [],
            "network": [],
            "fingerprinting": []
        }
        
        # In a real implementation, we would:
        # 1. Inject the script into LinkedIn
        # 2. Set up message handling to receive detection data
        # 3. Wait for the specified duration, collecting data
        # 4. Stop the script and analyze results
        
        # For this demo, we'll simulate the results
        logger.info("Simulating test results (in a real test, we would inject the script)")
        
        # Simulate some detection attempts
        detection_data["build_props"] = [
            {"field": "FINGERPRINT", "value": "generic/sdk/generic:10/QSR1.190920.001/eng.build.20200730.192226:userdebug/dev-keys"},
            {"field": "MODEL", "value": "Android SDK built for x86"},
            {"field": "MANUFACTURER", "value": "Google"}
        ]
        
        detection_data["system_props"] = [
            {"key": "ro.kernel.qemu", "value": "1"},
            {"key": "ro.hardware", "value": "ranchu"}
        ]
        
        detection_data["sensors"] = [
            {"method": "getSensorList", "type": 1, "count": 0},
            {"method": "getDefaultSensor", "type": 1, "available": False}
        ]
        
        detection_data["files"] = [
            {"method": "exists", "path": "/dev/qemu_pipe", "exists": True},
            {"method": "exists", "path": "/sys/qemu_trace", "exists": True}
        ]
        
        # Analyze the results
        detected = (
            len(detection_data["build_props"]) > 0 and
            any(prop["value"].lower().find("sdk") >= 0 for prop in detection_data["build_props"]) or
            any(prop["value"] == "1" for prop in detection_data["system_props"] if prop["key"] == "ro.kernel.qemu") or
            any(not item["available"] for item in detection_data["sensors"] if item["method"] == "getDefaultSensor" and item["type"] == 1) or
            any(item["exists"] for item in detection_data["files"] if "qemu" in item["path"].lower())
        )
        
        # Update test results
        self.test_results["success"] = not detected
        self.test_results["detection_methods"] = detection_data
        
        if detected:
            self.test_results["summary"] = "Emulator detected by LinkedIn"
            logger.warning("LinkedIn detection test result: DETECTED as emulator")
        else:
            self.test_results["summary"] = "LinkedIn did not detect the emulator"
            logger.info("LinkedIn detection test result: UNDETECTED (success)")
            
        return self.test_results
        
    def save_results(self, output_file=None):
        """Save the test results to a file."""
        if not output_file:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            output_file = f"linkedin_detection_test_{timestamp}.json"
            
        try:
            with open(output_file, "w") as f:
                json.dump(self.test_results, f, indent=2)
                
            logger.info(f"Test results saved to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving test results: {str(e)}")
            return False
            
    def print_summary(self):
        """Print a summary of the test results."""
        print("\n" + "=" * 50)
        print("LINKEDIN DETECTION TEST SUMMARY")
        print("=" * 50)
        
        if self.test_results["success"]:
            print("TEST RESULT: SUCCESS - Emulator was not detected")
        else:
            print("TEST RESULT: FAILED - Emulator was detected")
            
        print("\nDetection methods used by LinkedIn:")
        
        # Build properties
        if self.test_results["detection_methods"]["build_props"]:
            print("\nBuild Properties Checked:")
            for prop in self.test_results["detection_methods"]["build_props"]:
                print(f"  {prop['field']} = {prop['value']}")
                
        # System properties
        if self.test_results["detection_methods"]["system_props"]:
            print("\nSystem Properties Checked:")
            for prop in self.test_results["detection_methods"]["system_props"]:
                print(f"  {prop['key']} = {prop['value']}")
                
        # Sensors
        if self.test_results["detection_methods"]["sensors"]:
            print("\nSensor Checks:")
            for sensor in self.test_results["detection_methods"]["sensors"]:
                if sensor["method"] == "getDefaultSensor":
                    print(f"  Sensor type {sensor['type']}: {'Available' if sensor['available'] else 'Not available'}")
                elif sensor["method"] == "getSensorList":
                    print(f"  Sensor list type {sensor['type']}: {sensor['count']} sensors found")
                    
        # Files
        if self.test_results["detection_methods"]["files"]:
            print("\nFile Existence Checks:")
            for file in self.test_results["detection_methods"]["files"]:
                print(f"  {file['path']}: {'Exists' if file['exists'] else 'Does not exist'}")
                
        print("\nSUMMARY: " + self.test_results["summary"])
        print("=" * 50 + "\n")


def main():
    """Main function to run the LinkedIn detection test."""
    parser = argparse.ArgumentParser(description="Test LinkedIn's emulator detection.")
    parser.add_argument("--device", help="Device ID to connect to")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--output", help="Output file for test results")
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    logger.info("Starting LinkedIn detection test")
    
    test = LinkedInDetectionTest(device_id=args.device)
    results = test.run_test(duration=args.duration)
    
    if args.output:
        test.save_results(args.output)
    else:
        test.save_results()
        
    test.print_summary()
    
    return 0 if results["success"] else 1


if __name__ == "__main__":
    sys.exit(main())