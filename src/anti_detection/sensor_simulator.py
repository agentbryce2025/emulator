#!/usr/bin/env python3
"""
Sensor simulation module for the undetected Android emulator.
This module handles simulating realistic sensor data to avoid detection.
"""

import time
import random
import math
import logging
import json
import os
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

class SensorSimulator:
    """Simulates realistic sensor data for Android device emulation."""
    
    def __init__(self, profile_path=None):
        """Initialize sensor simulator with optional profile path."""
        self.profile_path = profile_path or os.path.join(
            os.path.expanduser("~"), ".config", "undetected-emulator", "sensor_profiles"
        )
        self.current_profile = None
        self.available_profiles = []
        self.simulation_active = False
        self.simulation_thread = None
        self.sensor_values = {}
        self.noise_factor = 0.05  # Base noise factor
        
        # Ensure profile directory exists
        os.makedirs(self.profile_path, exist_ok=True)
        
        # Load available profiles
        self._load_available_profiles()
        
        # Initialize sensor data
        self._init_sensor_data()
        
    def _init_sensor_data(self):
        """Initialize default sensor data."""
        self.sensor_values = {
            "accelerometer": {"x": 0.0, "y": 0.0, "z": 9.81},  # Default to gravity on z-axis
            "gyroscope": {"x": 0.0, "y": 0.0, "z": 0.0},
            "magnetometer": {"x": 25.0, "y": 10.0, "z": 40.0},  # Approximate magnetic field values
            "proximity": {"distance": 100.0},  # Far distance (no object close)
            "light": {"lux": 500.0},  # Medium indoor lighting
            "pressure": {"hPa": 1013.25},  # Standard atmospheric pressure
            "temperature": {"celsius": 22.0},  # Room temperature
            "humidity": {"percent": 50.0},  # Medium humidity
        }
        
    def _load_available_profiles(self):
        """Load all available sensor profiles."""
        self.available_profiles = []
        
        try:
            for file in os.listdir(self.profile_path):
                if file.endswith(".json"):
                    self.available_profiles.append(file[:-5])  # Remove .json extension
            logger.info(f"Loaded {len(self.available_profiles)} sensor profiles")
        except Exception as e:
            logger.error(f"Error loading sensor profiles: {str(e)}")
            
    def load_profile(self, profile_name):
        """Load a specific sensor profile."""
        profile_file = os.path.join(self.profile_path, f"{profile_name}.json")
        
        if not os.path.exists(profile_file):
            logger.error(f"Profile {profile_name} not found")
            return False
            
        try:
            with open(profile_file, "r") as f:
                self.current_profile = json.load(f)
            logger.info(f"Loaded sensor profile {profile_name}")
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
            logger.info(f"Saved sensor profile {profile_name}")
            
            # Update available profiles
            if profile_name not in self.available_profiles:
                self.available_profiles.append(profile_name)
                
            return True
        except Exception as e:
            logger.error(f"Error saving profile {profile_name}: {str(e)}")
            return False
            
    def create_device_profile(self, device_type, activity_type="stationary"):
        """Create a new sensor profile based on device type and activity."""
        # Device types: smartphone, tablet, smartwatch
        # Activity types: stationary, walking, running, driving
        
        profile = {
            "device_type": device_type,
            "activity_type": activity_type,
            "sensors": {},
            "simulation_parameters": {
                "noise_factor": self.noise_factor,
                "update_frequency": 50,  # Hz
                "drift_enabled": True,
                "drift_factor": 0.001,
            }
        }
        
        # Configure sensors based on device type
        if device_type == "smartphone":
            profile["sensors"] = {
                "accelerometer": {
                    "enabled": True,
                    "baseline": {"x": 0.0, "y": 0.0, "z": 9.81},
                    "variance": {"x": 0.1, "y": 0.1, "z": 0.1},
                },
                "gyroscope": {
                    "enabled": True,
                    "baseline": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "variance": {"x": 0.02, "y": 0.02, "z": 0.02},
                },
                "magnetometer": {
                    "enabled": True,
                    "baseline": {"x": 25.0, "y": 10.0, "z": 40.0},
                    "variance": {"x": 2.0, "y": 2.0, "z": 2.0},
                },
                "proximity": {
                    "enabled": True,
                    "baseline": {"distance": 100.0},
                    "variance": {"distance": 0.0},  # Binary sensor, no variance
                },
                "light": {
                    "enabled": True,
                    "baseline": {"lux": 500.0},
                    "variance": {"lux": 50.0},
                },
                "pressure": {
                    "enabled": True,
                    "baseline": {"hPa": 1013.25},
                    "variance": {"hPa": 0.5},
                },
                "temperature": {
                    "enabled": device_type != "smartwatch",  # Not all smartphones have this
                    "baseline": {"celsius": 22.0},
                    "variance": {"celsius": 0.5},
                },
                "humidity": {
                    "enabled": False,  # Most smartphones don't have this
                    "baseline": {"percent": 50.0},
                    "variance": {"percent": 1.0},
                },
            }
        elif device_type == "tablet":
            # Similar to smartphone but with different baselines and variances
            profile["sensors"] = {
                "accelerometer": {
                    "enabled": True,
                    "baseline": {"x": 0.0, "y": 0.0, "z": 9.81},
                    "variance": {"x": 0.08, "y": 0.08, "z": 0.08},  # Less movement than phone
                },
                "gyroscope": {
                    "enabled": True,
                    "baseline": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "variance": {"x": 0.015, "y": 0.015, "z": 0.015},
                },
                "magnetometer": {
                    "enabled": True,
                    "baseline": {"x": 25.0, "y": 10.0, "z": 40.0},
                    "variance": {"x": 2.0, "y": 2.0, "z": 2.0},
                },
                "proximity": {
                    "enabled": False,  # Many tablets don't have this
                    "baseline": {"distance": 100.0},
                    "variance": {"distance": 0.0},
                },
                "light": {
                    "enabled": True,
                    "baseline": {"lux": 500.0},
                    "variance": {"lux": 50.0},
                },
                "pressure": {
                    "enabled": False,  # Many tablets don't have this
                    "baseline": {"hPa": 1013.25},
                    "variance": {"hPa": 0.5},
                },
                "temperature": {
                    "enabled": False,
                    "baseline": {"celsius": 22.0},
                    "variance": {"celsius": 0.5},
                },
                "humidity": {
                    "enabled": False,
                    "baseline": {"percent": 50.0},
                    "variance": {"percent": 1.0},
                },
            }
        elif device_type == "smartwatch":
            profile["sensors"] = {
                "accelerometer": {
                    "enabled": True,
                    "baseline": {"x": 0.0, "y": 0.0, "z": 9.81},
                    "variance": {"x": 0.15, "y": 0.15, "z": 0.15},  # More movement on wrist
                },
                "gyroscope": {
                    "enabled": True,
                    "baseline": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "variance": {"x": 0.03, "y": 0.03, "z": 0.03},
                },
                "magnetometer": {
                    "enabled": True,
                    "baseline": {"x": 25.0, "y": 10.0, "z": 40.0},
                    "variance": {"x": 3.0, "y": 3.0, "z": 3.0},
                },
                "proximity": {
                    "enabled": True,
                    "baseline": {"distance": 100.0},
                    "variance": {"distance": 0.0},
                },
                "light": {
                    "enabled": True,
                    "baseline": {"lux": 500.0},
                    "variance": {"lux": 50.0},
                },
                "pressure": {
                    "enabled": False,
                    "baseline": {"hPa": 1013.25},
                    "variance": {"hPa": 0.5},
                },
                "temperature": {
                    "enabled": True,  # Many smartwatches have temperature sensors
                    "baseline": {"celsius": 32.0},  # Higher due to body contact
                    "variance": {"celsius": 0.3},
                },
                "humidity": {
                    "enabled": False,
                    "baseline": {"percent": 50.0},
                    "variance": {"percent": 1.0},
                },
            }
            
        # Adjust for activity type
        self._adjust_for_activity(profile, activity_type)
        
        self.current_profile = profile
        return profile
    
    def _adjust_for_activity(self, profile, activity_type):
        """Adjust sensor parameters based on activity type."""
        if activity_type == "stationary":
            # Already the default
            pass
        elif activity_type == "walking":
            # Increase accelerometer and gyroscope variance
            if "accelerometer" in profile["sensors"]:
                for axis in ["x", "y", "z"]:
                    profile["sensors"]["accelerometer"]["variance"][axis] *= 3
            if "gyroscope" in profile["sensors"]:
                for axis in ["x", "y", "z"]:
                    profile["sensors"]["gyroscope"]["variance"][axis] *= 2.5
                    
            # Add walking pattern
            profile["simulation_parameters"]["patterns"] = {
                "accelerometer": {
                    "type": "sine",
                    "amplitude": {"x": 0.8, "y": 1.2, "z": 1.5},
                    "frequency": {"x": 1.8, "y": 1.8, "z": 1.8},
                    "phase": {"x": 0, "y": math.pi/2, "z": math.pi/4},
                }
            }
        elif activity_type == "running":
            # Significantly increase accelerometer and gyroscope variance
            if "accelerometer" in profile["sensors"]:
                for axis in ["x", "y", "z"]:
                    profile["sensors"]["accelerometer"]["variance"][axis] *= 6
            if "gyroscope" in profile["sensors"]:
                for axis in ["x", "y", "z"]:
                    profile["sensors"]["gyroscope"]["variance"][axis] *= 5
                    
            # Add running pattern (faster than walking)
            profile["simulation_parameters"]["patterns"] = {
                "accelerometer": {
                    "type": "sine",
                    "amplitude": {"x": 1.5, "y": 2.5, "z": 3.0},
                    "frequency": {"x": 3.0, "y": 3.0, "z": 3.0},
                    "phase": {"x": 0, "y": math.pi/2, "z": math.pi/4},
                }
            }
        elif activity_type == "driving":
            # Moderate increase in variance with occasional larger movements
            if "accelerometer" in profile["sensors"]:
                for axis in ["x", "y", "z"]:
                    profile["sensors"]["accelerometer"]["variance"][axis] *= 2
            if "gyroscope" in profile["sensors"]:
                for axis in ["x", "y", "z"]:
                    profile["sensors"]["gyroscope"]["variance"][axis] *= 1.5
            
            # Add driving pattern (mix of smooth and occasional jolts)
            profile["simulation_parameters"]["patterns"] = {
                "accelerometer": {
                    "type": "mixed",
                    "smooth": {
                        "amplitude": {"x": 0.3, "y": 0.3, "z": 0.2},
                        "frequency": {"x": 0.5, "y": 0.5, "z": 0.5},
                    },
                    "jolt_probability": 0.01,  # 1% chance of jolt per update
                    "jolt_magnitude": {"x": 3.0, "y": 3.0, "z": 2.0},
                }
            }
    
    def start_simulation(self):
        """Start the sensor data simulation."""
        if self.simulation_active:
            logger.warning("Simulation is already running")
            return False
            
        if not self.current_profile:
            logger.error("No sensor profile loaded")
            return False
            
        self.simulation_active = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
        logger.info("Sensor simulation started")
        return True
        
    def stop_simulation(self):
        """Stop the sensor data simulation."""
        if not self.simulation_active:
            logger.warning("Simulation is not running")
            return False
            
        self.simulation_active = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2)
            
        logger.info("Sensor simulation stopped")
        return True
        
    def _simulation_loop(self):
        """Main simulation loop that updates sensor values."""
        update_interval = 1.0 / self.current_profile["simulation_parameters"].get("update_frequency", 50)
        
        drift_values = {sensor: {axis: 0.0 for axis in data["baseline"].keys()} 
                        for sensor, data in self.current_profile["sensors"].items()}
        
        pattern_time = 0.0
        last_significant_change = time.time()
        environment_state = self._generate_environment_state()
        
        while self.simulation_active:
            start_time = time.time()
            
            # Occasionally change environment state for more realistic sensor patterns
            if time.time() - last_significant_change > random.uniform(5, 30):
                environment_state = self._generate_environment_state()
                last_significant_change = time.time()
                
            # Update each sensor
            for sensor_name, sensor_config in self.current_profile["sensors"].items():
                if not sensor_config.get("enabled", False):
                    continue
                    
                baseline = sensor_config["baseline"]
                variance = sensor_config["variance"]
                
                # Apply pattern if defined
                pattern_values = self._calculate_pattern_values(sensor_name, pattern_time)
                
                # Apply environmental factors
                environmental_values = self._apply_environment_factors(sensor_name, environment_state)
                
                # Apply drift
                if self.current_profile["simulation_parameters"].get("drift_enabled", False):
                    drift_factor = self.current_profile["simulation_parameters"].get("drift_factor", 0.001)
                    for axis in baseline.keys():
                        drift_values[sensor_name][axis] += random.uniform(-drift_factor, drift_factor)
                        # Limit drift to reasonable values
                        drift_values[sensor_name][axis] = max(min(drift_values[sensor_name][axis], 0.5), -0.5)
                
                # Calculate and apply noise for each axis
                for axis, base_value in baseline.items():
                    noise = random.gauss(0, variance[axis] * self.noise_factor)
                    pattern_value = pattern_values.get(axis, 0.0) if pattern_values else 0.0
                    drift_value = drift_values[sensor_name].get(axis, 0.0)
                    
                    # Combine baseline, noise, pattern, and drift
                    new_value = base_value + noise + pattern_value + drift_value
                    
                    # Update the sensor value
                    if sensor_name not in self.sensor_values:
                        self.sensor_values[sensor_name] = {}
                    self.sensor_values[sensor_name][axis] = new_value
            
            # Increment pattern time
            pattern_time += update_interval
            
            # Sleep for the remainder of the update interval
            elapsed = time.time() - start_time
            if elapsed < update_interval:
                time.sleep(update_interval - elapsed)
    
    def _generate_environment_state(self):
        """Generate a random environmental state for realistic sensor changes."""
        return {
            "lighting": random.choice(["dark", "dim", "normal", "bright", "very_bright"]),
            "movement": random.choice(["none", "slight", "moderate", "significant"]),
            "position": random.choice(["flat", "tilted", "vertical", "upside_down"]),
            "temperature": random.uniform(15, 35),  # Celsius
            "pressure": random.uniform(980, 1030),  # hPa
            "humidity": random.uniform(20, 80),     # %
            "magnetic_interference": random.uniform(0, 1),  # Normalized interference level
        }
        
    def _apply_environment_factors(self, sensor_name, environment):
        """Apply environmental factors to sensor values."""
        result = {}
        
        if sensor_name == "accelerometer":
            # Adjust accelerometer based on position
            if environment["position"] == "flat":
                result = {"x": random.uniform(-0.1, 0.1), "y": random.uniform(-0.1, 0.1), "z": 9.81}
            elif environment["position"] == "tilted":
                tilt_angle = random.uniform(0, 45) * (math.pi / 180)  # Convert to radians
                tilt_direction = random.uniform(0, 2 * math.pi)
                result = {
                    "x": 9.81 * math.sin(tilt_angle) * math.cos(tilt_direction),
                    "y": 9.81 * math.sin(tilt_angle) * math.sin(tilt_direction),
                    "z": 9.81 * math.cos(tilt_angle)
                }
            elif environment["position"] == "vertical":
                vertical_angle = random.uniform(80, 100) * (math.pi / 180)
                direction = random.uniform(0, 2 * math.pi)
                result = {
                    "x": 9.81 * math.sin(vertical_angle) * math.cos(direction),
                    "y": 9.81 * math.sin(vertical_angle) * math.sin(direction),
                    "z": 9.81 * math.cos(vertical_angle)
                }
            elif environment["position"] == "upside_down":
                result = {"x": random.uniform(-0.1, 0.1), "y": random.uniform(-0.1, 0.1), "z": -9.81}
            
            # Add movement effects
            if environment["movement"] == "slight":
                for axis in ["x", "y", "z"]:
                    result[axis] = result.get(axis, 0) + random.uniform(-0.2, 0.2)
            elif environment["movement"] == "moderate":
                for axis in ["x", "y", "z"]:
                    result[axis] = result.get(axis, 0) + random.uniform(-0.5, 0.5)
            elif environment["movement"] == "significant":
                for axis in ["x", "y", "z"]:
                    result[axis] = result.get(axis, 0) + random.uniform(-1.0, 1.0)
                    
        elif sensor_name == "gyroscope":
            # Base values based on movement
            if environment["movement"] == "none":
                result = {"x": 0, "y": 0, "z": 0}
            elif environment["movement"] == "slight":
                result = {
                    "x": random.uniform(-0.1, 0.1),
                    "y": random.uniform(-0.1, 0.1),
                    "z": random.uniform(-0.1, 0.1)
                }
            elif environment["movement"] == "moderate":
                result = {
                    "x": random.uniform(-0.3, 0.3),
                    "y": random.uniform(-0.3, 0.3),
                    "z": random.uniform(-0.3, 0.3)
                }
            elif environment["movement"] == "significant":
                result = {
                    "x": random.uniform(-0.8, 0.8),
                    "y": random.uniform(-0.8, 0.8),
                    "z": random.uniform(-0.8, 0.8)
                }
                
        elif sensor_name == "magnetometer":
            # Base magnetic field (approximate Earth's field)
            base_mag = {"x": 25.0, "y": 10.0, "z": 40.0}
            
            # Apply magnetic interference
            interference = environment["magnetic_interference"]
            result = {
                "x": base_mag["x"] + interference * random.uniform(-10, 10),
                "y": base_mag["y"] + interference * random.uniform(-10, 10),
                "z": base_mag["z"] + interference * random.uniform(-10, 10)
            }
            
        elif sensor_name == "light":
            # Light values based on lighting condition
            if environment["lighting"] == "dark":
                result = {"lux": random.uniform(0, 10)}
            elif environment["lighting"] == "dim":
                result = {"lux": random.uniform(10, 100)}
            elif environment["lighting"] == "normal":
                result = {"lux": random.uniform(100, 500)}
            elif environment["lighting"] == "bright":
                result = {"lux": random.uniform(500, 2000)}
            elif environment["lighting"] == "very_bright":
                result = {"lux": random.uniform(2000, 10000)}
                
        elif sensor_name == "proximity":
            # Proximity mostly binary: far or near
            if environment["movement"] == "none" and random.random() > 0.9:
                # Sometimes while stationary, something might be close (like user's face)
                result = {"distance": random.uniform(0, 5)}
            else:
                result = {"distance": 100.0}  # Far
                
        elif sensor_name == "pressure":
            result = {"hPa": environment["pressure"]}
            
        elif sensor_name == "temperature":
            result = {"celsius": environment["temperature"]}
            
        elif sensor_name == "humidity":
            result = {"percent": environment["humidity"]}
            
        return result
    
    def _calculate_pattern_values(self, sensor_name, time_value):
        """Calculate pattern-based values for sensors."""
        patterns = self.current_profile["simulation_parameters"].get("patterns", {})
        
        if sensor_name not in patterns:
            return None
            
        pattern_config = patterns[sensor_name]
        pattern_type = pattern_config.get("type", "sine")
        
        if pattern_type == "sine":
            # Simple sine wave pattern
            result = {}
            for axis in ["x", "y", "z"]:
                if axis in pattern_config.get("amplitude", {}) and axis in pattern_config.get("frequency", {}):
                    amplitude = pattern_config["amplitude"][axis]
                    frequency = pattern_config["frequency"][axis]
                    phase = pattern_config.get("phase", {}).get(axis, 0)
                    
                    result[axis] = amplitude * math.sin(2 * math.pi * frequency * time_value + phase)
            return result
            
        elif pattern_type == "mixed":
            # Mixed pattern with smooth movement and occasional jolts
            smooth = pattern_config.get("smooth", {})
            result = {}
            
            # Smooth component
            for axis in ["x", "y", "z"]:
                if axis in smooth.get("amplitude", {}) and axis in smooth.get("frequency", {}):
                    amplitude = smooth["amplitude"][axis]
                    frequency = smooth["frequency"][axis]
                    
                    result[axis] = amplitude * math.sin(2 * math.pi * frequency * time_value)
            
            # Add jolts with some probability
            jolt_probability = pattern_config.get("jolt_probability", 0)
            if random.random() < jolt_probability:
                jolt_magnitude = pattern_config.get("jolt_magnitude", {})
                for axis in ["x", "y", "z"]:
                    if axis in jolt_magnitude:
                        result[axis] = result.get(axis, 0) + random.uniform(-jolt_magnitude[axis], jolt_magnitude[axis])
                        
            return result
        
        elif pattern_type == "realistic":
            # Realistic walking/running pattern
            step_frequency = pattern_config.get("step_frequency", 1.8)  # Steps per second
            step_intensity = pattern_config.get("step_intensity", 1.0)
            
            # Each step has impact and recovery phases
            step_phase = (time_value * step_frequency) % 1.0
            
            # Simplified step impact model
            if step_phase < 0.2:  # Impact phase
                impact = math.sin(step_phase * math.pi / 0.2) * step_intensity
                result = {
                    "x": random.uniform(-0.2, 0.2) * impact,
                    "y": random.uniform(-0.2, 0.2) * impact,
                    "z": 9.81 + impact * 2.0  # Higher Z during impact
                }
            else:  # Recovery and flight phase
                recovery = math.sin((step_phase - 0.2) * math.pi / 0.8) * 0.5 * step_intensity
                result = {
                    "x": random.uniform(-0.1, 0.1) * recovery,
                    "y": random.uniform(-0.1, 0.1) * recovery,
                    "z": 9.81 - recovery  # Lower Z during flight
                }
                
            return result
            
        return None
        
    def get_current_values(self):
        """Get the current simulated sensor values."""
        return self.sensor_values
        
    def inject_to_system(self, system_path):
        """Inject sensor simulation into a system."""
        if not self.current_profile:
            logger.error("No sensor profile loaded")
            return False
            
        logger.info(f"Injecting sensor simulation to system at {system_path}")
        
        # This is a placeholder for actual implementation
        # In a real system, this would:
        # 1. Modify Android sensor HAL or inject a custom sensor service
        # 2. Set up communication channels between this simulator and the Android system
        # 3. Configure the system to use our simulated values
        
        return True


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    simulator = SensorSimulator()
    profile = simulator.create_device_profile("smartphone", "walking")
    print(json.dumps(profile, indent=2))
    
    simulator.start_simulation()
    
    try:
        for i in range(10):
            time.sleep(0.5)
            values = simulator.get_current_values()
            print(f"Current accelerometer values: {values.get('accelerometer', {})}")
            print(f"Current gyroscope values: {values.get('gyroscope', {})}")
    finally:
        simulator.stop_simulation()