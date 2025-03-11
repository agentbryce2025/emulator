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

# Import ML sensor generator if available
try:
    from .ml_sensor_generator import MLSensorGenerator
    ML_GENERATOR_AVAILABLE = True
except ImportError:
    ML_GENERATOR_AVAILABLE = False
    logging.warning("ML sensor generator not available. Using basic sensor simulation.")

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
        
        # Initialize ML generator if available
        self.ml_generator = None
        self.use_ml_generation = False
        if ML_GENERATOR_AVAILABLE:
            try:
                self.ml_generator = MLSensorGenerator()
                # Try to train models if they don't exist
                if not any(info["trained"] for _, info in self.ml_generator.get_model_info().items()):
                    logger.info("Training ML models for sensor simulation...")
                    self.ml_generator.train_models()
                self.use_ml_generation = True
                logger.info("ML sensor generation enabled")
            except Exception as e:
                logger.error(f"Error initializing ML sensor generator: {e}")
                self.use_ml_generation = False
        
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
            
    def create_device_profile(self, device_type, activity_type="stationary", position="flat", use_ml=True):
        """
        Create a new sensor profile based on device type and activity.
        
        Args:
            device_type: Type of device ('smartphone', 'tablet', 'smartwatch')
            activity_type: Activity being performed ('stationary', 'walking', 'running', 'driving')
            position: Device position ('flat', 'tilted', 'vertical', 'upside_down')
            use_ml: Whether to use ML-generated sensor patterns if available
        """
        # Device types: smartphone, tablet, smartwatch
        # Activity types: stationary, walking, running, driving
        # Positions: flat, tilted, vertical, upside_down
        
        profile = {
            "device_type": device_type,
            "activity_type": activity_type,
            "position": position,
            "sensors": {},
            "simulation_parameters": {
                "noise_factor": self.noise_factor,
                "update_frequency": 50,  # Hz
                "drift_enabled": True,
                "drift_factor": 0.001,
                "use_ml": use_ml and self.use_ml_generation
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
        self._adjust_for_activity(profile, activity_type, position)
        
        self.current_profile = profile
        return profile
    
    def _adjust_for_activity(self, profile, activity_type, position="flat"):
        """
        Adjust sensor parameters based on activity type and position.
        
        Args:
            profile: The sensor profile to adjust
            activity_type: Activity being performed ('stationary', 'walking', 'running', 'driving')
            position: Device position ('flat', 'tilted', 'vertical', 'upside_down')
        """
        # Check if ML should be used for pattern generation
        use_ml = profile["simulation_parameters"].get("use_ml", False) and self.use_ml_generation
        
        if use_ml:
            # Use ML for pattern generation
            profile["simulation_parameters"]["patterns"] = {
                "accelerometer": {
                    "type": "ml_generated",
                    "activity": activity_type,
                    "position": position
                },
                "gyroscope": {
                    "type": "ml_generated",
                    "activity": activity_type,
                    "position": position
                },
                "magnetometer": {
                    "type": "ml_generated",
                    "activity": activity_type,
                    "position": position
                }
            }
            
            # Log that we're using ML-based pattern generation
            logger.info(f"Using ML-based sensor pattern generation for {activity_type} activity in {position} position")
        else:
            # Use rule-based pattern generation (original approach)
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
            
            # Adjust based on position
            if position != "flat":
                # Modify the patterns based on device position
                if "patterns" in profile["simulation_parameters"] and "accelerometer" in profile["simulation_parameters"]["patterns"]:
                    # Adjust pattern phases and amplitudes based on position
                    if position == "tilted":
                        # Tilted position (e.g., ~45 degrees)
                        if profile["simulation_parameters"]["patterns"]["accelerometer"]["type"] == "sine":
                            # Modify sine wave pattern for tilted position
                            profile["simulation_parameters"]["patterns"]["accelerometer"]["amplitude"]["x"] *= 1.5
                            profile["simulation_parameters"]["patterns"]["accelerometer"]["amplitude"]["y"] *= 0.8
                    elif position == "vertical":
                        # Vertical position (upright)
                        if profile["simulation_parameters"]["patterns"]["accelerometer"]["type"] == "sine":
                            # For vertical position, most movement is in X and Y, less in Z
                            profile["simulation_parameters"]["patterns"]["accelerometer"]["amplitude"]["z"] *= 0.5
                            profile["simulation_parameters"]["patterns"]["accelerometer"]["amplitude"]["x"] *= 1.2
                            profile["simulation_parameters"]["patterns"]["accelerometer"]["amplitude"]["y"] *= 1.2
                    elif position == "upside_down":
                        # Upside down (inverted)
                        if profile["simulation_parameters"]["patterns"]["accelerometer"]["type"] == "sine":
                            # Invert Z axis for upside down
                            profile["simulation_parameters"]["patterns"]["accelerometer"]["amplitude"]["z"] *= -1
    
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
        
        # Initialize drift values with defensive code for profiles that might not have baseline defined
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
                    drift_values[sensor] = {"value": 0.0}
        
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
                    
                # Handle profiles that might not have baseline and variance fields
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
        # Use ML generator if available and enabled
        if self.use_ml_generation and self.ml_generator is not None and sensor_name in ["accelerometer", "gyroscope", "magnetometer"]:
            try:
                # Get activity and position from profile
                activity_type = self.current_profile.get("activity_type", "stationary")
                position = self.current_profile.get("position", "flat")
                
                # Generate a single pattern value at the current time using ML
                pattern_values = self.ml_generator.generate_sensor_patterns(
                    sensor_name, 
                    activity_type, 
                    position, 
                    duration=0.1,  # Just need a single value
                    frequency=10   # Low frequency since we only need one value
                )
                
                if pattern_values and len(pattern_values) > 0:
                    # Extract values from the first sample
                    result = {
                        "x": pattern_values[0]["x"],
                        "y": pattern_values[0]["y"],
                        "z": pattern_values[0]["z"]
                    }
                    return result
            except Exception as e:
                logger.warning(f"Error using ML sensor generator: {e}. Falling back to rule-based generation.")
        
        # Fall back to rule-based patterns if ML is not available
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
            
        elif pattern_type == "ml_generated":
            # Use ML generator directly from pattern config
            if self.use_ml_generation and self.ml_generator is not None:
                try:
                    activity_type = pattern_config.get("activity", "stationary")
                    position = pattern_config.get("position", "flat")
                    
                    pattern_values = self.ml_generator.generate_sensor_patterns(
                        sensor_name, 
                        activity_type, 
                        position, 
                        duration=0.1,
                        frequency=10
                    )
                    
                    if pattern_values and len(pattern_values) > 0:
                        # Extract values from the first sample
                        result = {
                            "x": pattern_values[0]["x"],
                            "y": pattern_values[0]["y"],
                            "z": pattern_values[0]["z"]
                        }
                        return result
                except Exception as e:
                    logger.warning(f"Error using ML pattern generation: {e}")
                    
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
        
    def contribute_sensor_data(self, sensor_type, activity_type, position, data_points):
        """
        Contribute user-collected sensor data to improve ML models.
        
        Args:
            sensor_type: Type of sensor ('accelerometer', 'gyroscope', 'magnetometer')
            activity_type: Activity being performed ('stationary', 'walking', 'running', 'driving')
            position: Device position ('flat', 'tilted', 'vertical', 'upside_down')
            data_points: List of sensor reading dictionaries with 'x', 'y', 'z' values
            
        Returns:
            True if successful, False otherwise
        """
        if not self.use_ml_generation or not self.ml_generator:
            logger.warning("ML sensor generation is not available. Cannot contribute data.")
            return False
            
        if sensor_type not in ["accelerometer", "gyroscope", "magnetometer"]:
            logger.error(f"Invalid sensor type: {sensor_type}")
            return False
            
        try:
            # Activities and positions for feature encoding
            activities = ["stationary", "walking", "running", "driving"]
            positions = ["flat", "tilted", "vertical", "upside_down"]
            
            # Check if the requested activity and position are known
            if activity_type not in activities:
                logger.warning(f"Unknown activity: {activity_type}. Using 'stationary'.")
                activity_type = "stationary"
                
            if position not in positions:
                logger.warning(f"Unknown position: {position}. Using 'flat'.")
                position = "flat"
            
            # Normalized activity and position IDs
            activity_id = activities.index(activity_type) / len(activities)
            position_id = positions.index(position) / len(positions)
            
            # Process the data points to create features and targets
            features = []
            targets = []
            
            prev_values = [0, 0, 0]  # Initialize previous values
            
            for i, point in enumerate(data_points):
                # Normalized time (0-1 over the sequence)
                normalized_time = i / max(1, len(data_points) - 1)
                
                # Create feature vector: [time, activity, position, prev_x, prev_y, prev_z]
                feature = [
                    normalized_time,
                    activity_id,
                    position_id,
                    prev_values[0],
                    prev_values[1],
                    prev_values[2]
                ]
                
                # Target is the current x, y, z values
                target = [point["x"], point["y"], point["z"]]
                
                features.append(feature)
                targets.append(target)
                
                # Update previous values for next point
                prev_values = target
                
            # Add the data to the ML model
            success = self.ml_generator.add_training_data(sensor_type, features, targets)
            
            if success:
                # Retrain the model with the new data
                self.ml_generator.train_models()
                logger.info(f"Successfully added {len(data_points)} points of {sensor_type} data for {activity_type} activity")
            
            return success
        except Exception as e:
            logger.error(f"Error contributing sensor data: {e}")
            return False
            
    def get_ml_model_info(self):
        """Get information about the ML models used for sensor simulation."""
        if not self.use_ml_generation or not self.ml_generator:
            return {
                "available": False,
                "reason": "ML sensor generation is not enabled or available"
            }
            
        try:
            # Get model info from ML generator
            model_info = self.ml_generator.get_model_info()
            
            # Add some additional information
            return {
                "available": True,
                "models": model_info,
                "enabled": self.use_ml_generation,
                "can_contribute": True
            }
        except Exception as e:
            logger.error(f"Error getting ML model info: {e}")
            return {
                "available": True,
                "enabled": self.use_ml_generation,
                "error": str(e)
            }


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