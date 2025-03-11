#!/usr/bin/env python3
"""
Machine Learning Sensor Pattern Generator for undetected Android emulator.
This module uses machine learning to generate realistic sensor data patterns.
"""

import os
import logging
import json
import random
import math
import numpy as np
from pathlib import Path
from datetime import datetime

try:
    # Optional ML libraries - will use simpler models if not available
    import sklearn
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import MinMaxScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("scikit-learn not available. Using simplified model generation.")

logger = logging.getLogger(__name__)

class MLSensorGenerator:
    """Machine learning-based sensor data pattern generator."""
    
    def __init__(self, data_path=None):
        """Initialize the ML sensor pattern generator."""
        if data_path:
            self.data_path = Path(data_path)
        else:
            # Default to ~/.config/undetected-emulator/ml_data
            self.data_path = Path.home() / ".config" / "undetected-emulator" / "ml_data"
            
        # Create data directory if it doesn't exist
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize models dictionary
        self.models = {
            "accelerometer": None,
            "gyroscope": None,
            "magnetometer": None
        }
        
        # Initialize scalers
        self.scalers = {
            "accelerometer": None,
            "gyroscope": None,
            "magnetometer": None
        }
        
        # Try to load pre-trained models
        self._load_models()
        
        # Initialize training data
        self.training_data = self._initialize_training_data()
        
    def _initialize_training_data(self):
        """Initialize or load training data for the models."""
        training_data = {
            "accelerometer": {
                "X": [],  # Features: time, activity, position, previous values, etc.
                "y": []   # Target: sensor values x, y, z
            },
            "gyroscope": {
                "X": [],
                "y": []
            },
            "magnetometer": {
                "X": [],
                "y": []
            }
        }
        
        # Try to load existing training data
        training_data_file = self.data_path / "training_data.json"
        if training_data_file.exists():
            try:
                with open(training_data_file, "r") as f:
                    loaded_data = json.load(f)
                    
                # Convert loaded data to numpy arrays
                for sensor in training_data.keys():
                    if sensor in loaded_data:
                        training_data[sensor]["X"] = np.array(loaded_data[sensor]["X"])
                        training_data[sensor]["y"] = np.array(loaded_data[sensor]["y"])
                        
                logger.info(f"Loaded training data from {training_data_file}")
            except Exception as e:
                logger.error(f"Error loading training data: {e}")
                
        # If no data was loaded, we'll generate synthetic data
        if all(len(training_data[sensor]["X"]) == 0 for sensor in training_data.keys()):
            logger.info("No training data found. Generating synthetic data.")
            training_data = self._generate_synthetic_data()
                
        return training_data
        
    def _generate_synthetic_data(self):
        """Generate synthetic training data for initial model training."""
        training_data = {
            "accelerometer": {
                "X": [],
                "y": []
            },
            "gyroscope": {
                "X": [],
                "y": []
            },
            "magnetometer": {
                "X": [],
                "y": []
            }
        }
        
        # Activities to generate data for
        activities = ["stationary", "walking", "running", "driving"]
        positions = ["flat", "tilted", "vertical", "upside_down"]
        
        # Generate sequence for each activity and position
        for activity in activities:
            for position in positions:
                # Activity ID and position ID (one-hot encoded features)
                activity_id = activities.index(activity)
                position_id = positions.index(position)
                
                # Generate a 60-second sequence (at 50Hz = 3000 samples)
                sequence_length = 3000
                
                # Time feature (normalized to 0-1 over the sequence)
                time_feature = np.linspace(0, 1, sequence_length)
                
                # Previous values (start with zeros)
                prev_accel = np.zeros((3,))
                prev_gyro = np.zeros((3,))
                prev_mag = np.zeros((3,))
                
                for i in range(sequence_length):
                    time = time_feature[i]
                    
                    # Generate features
                    accel_features = np.array([
                        time,
                        activity_id / len(activities),  # Normalized activity ID
                        position_id / len(positions),   # Normalized position ID
                        prev_accel[0], prev_accel[1], prev_accel[2]
                    ])
                    
                    gyro_features = np.array([
                        time,
                        activity_id / len(activities),
                        position_id / len(positions),
                        prev_gyro[0], prev_gyro[1], prev_gyro[2]
                    ])
                    
                    mag_features = np.array([
                        time,
                        activity_id / len(activities),
                        position_id / len(positions),
                        prev_mag[0], prev_mag[1], prev_mag[2]
                    ])
                    
                    # Generate synthetic sensor values based on activity and position
                    accel_values = self._generate_synthetic_accelerometer(time, activity, position)
                    gyro_values = self._generate_synthetic_gyroscope(time, activity, position)
                    mag_values = self._generate_synthetic_magnetometer(time, activity, position)
                    
                    # Add noise for realism
                    accel_values += np.random.normal(0, 0.05, size=(3,))
                    gyro_values += np.random.normal(0, 0.02, size=(3,))
                    mag_values += np.random.normal(0, 0.5, size=(3,))
                    
                    # Add to training data
                    training_data["accelerometer"]["X"].append(accel_features)
                    training_data["accelerometer"]["y"].append(accel_values)
                    
                    training_data["gyroscope"]["X"].append(gyro_features)
                    training_data["gyroscope"]["y"].append(gyro_values)
                    
                    training_data["magnetometer"]["X"].append(mag_features)
                    training_data["magnetometer"]["y"].append(mag_values)
                    
                    # Update previous values for next iteration
                    prev_accel = accel_values
                    prev_gyro = gyro_values
                    prev_mag = mag_values
        
        # Convert lists to numpy arrays
        for sensor in training_data.keys():
            training_data[sensor]["X"] = np.array(training_data[sensor]["X"])
            training_data[sensor]["y"] = np.array(training_data[sensor]["y"])
            
        # Save generated data
        self._save_training_data(training_data)
            
        return training_data
        
    def _generate_synthetic_accelerometer(self, time, activity, position):
        """Generate synthetic accelerometer data for a given activity and position."""
        base_values = np.array([0.0, 0.0, 9.81])  # Default (flat, stationary)
        
        # Adjust for position
        if position == "flat":
            pass  # Default
        elif position == "tilted":
            tilt_angle = (math.sin(time * 2 * math.pi) * 0.2 + 0.3) * math.pi / 4  # Varying tilt 0-45 degrees
            tilt_direction = time * 2 * math.pi  # Rotating direction
            base_values = np.array([
                9.81 * math.sin(tilt_angle) * math.cos(tilt_direction),
                9.81 * math.sin(tilt_angle) * math.sin(tilt_direction),
                9.81 * math.cos(tilt_angle)
            ])
        elif position == "vertical":
            vertical_angle = math.pi / 2  # 90 degrees
            base_values = np.array([
                9.81 * math.cos(time * 2 * math.pi),
                9.81 * math.sin(time * 2 * math.pi),
                0.0
            ])
        elif position == "upside_down":
            base_values = np.array([0.0, 0.0, -9.81])
            
        # Add activity patterns
        if activity == "stationary":
            pass  # Just add minor noise in the final step
        elif activity == "walking":
            step_freq = 2.0  # Hz
            base_values[0] += math.sin(time * step_freq * 2 * math.pi) * 0.8
            base_values[1] += math.cos(time * step_freq * 2 * math.pi) * 0.5
            base_values[2] += math.sin(time * step_freq * 4 * math.pi) * 1.2
        elif activity == "running":
            step_freq = 3.0  # Hz
            base_values[0] += math.sin(time * step_freq * 2 * math.pi) * 1.5
            base_values[1] += math.cos(time * step_freq * 2 * math.pi) * 1.0
            base_values[2] += math.sin(time * step_freq * 4 * math.pi) * 2.5
        elif activity == "driving":
            # Simulate road vibration and occasional turns/bumps
            road_vibration = 0.3 * math.sin(time * 20 * math.pi)
            turn = 0.0
            if 0.2 < time < 0.3 or 0.6 < time < 0.7:  # Simulate turns
                turn = math.sin((time - 0.25) * 20 * math.pi) * 1.5
                
            bump = 0.0
            if abs(time - 0.5) < 0.05:  # Simulate bump
                bump = 2.0 * math.exp(-100 * (time - 0.5)**2)
                
            base_values[0] += turn + road_vibration
            base_values[1] += road_vibration
            base_values[2] += bump + road_vibration
            
        return base_values
        
    def _generate_synthetic_gyroscope(self, time, activity, position):
        """Generate synthetic gyroscope data for a given activity and position."""
        base_values = np.array([0.0, 0.0, 0.0])  # Default (stationary)
        
        # Add activity patterns
        if activity == "stationary":
            pass  # Near zero values with just minor noise
        elif activity == "walking":
            step_freq = 2.0  # Hz
            base_values[0] += math.cos(time * step_freq * 2 * math.pi) * 0.3
            base_values[1] += math.sin(time * step_freq * 2 * math.pi) * 0.2
            base_values[2] += math.sin(time * step_freq * 2 * math.pi + math.pi/4) * 0.1
        elif activity == "running":
            step_freq = 3.0  # Hz
            base_values[0] += math.cos(time * step_freq * 2 * math.pi) * 0.6
            base_values[1] += math.sin(time * step_freq * 2 * math.pi) * 0.5
            base_values[2] += math.sin(time * step_freq * 2 * math.pi + math.pi/4) * 0.3
        elif activity == "driving":
            # Simulate turns and road vibration
            if 0.2 < time < 0.3:  # Right turn
                base_values[2] += math.sin((time - 0.25) * 20) * 0.5
            elif 0.6 < time < 0.7:  # Left turn
                base_values[2] -= math.sin((time - 0.65) * 20) * 0.5
                
            # Road vibration
            base_values[0] += math.sin(time * 30 * math.pi) * 0.1
            base_values[1] += math.cos(time * 30 * math.pi) * 0.1
            
        return base_values
        
    def _generate_synthetic_magnetometer(self, time, activity, position):
        """Generate synthetic magnetometer data for a given activity and position."""
        # Earth's magnetic field baseline (approximate)
        base_values = np.array([25.0, 10.0, 40.0])
        
        # Adjust for position similar to accelerometer
        if position == "flat":
            pass  # Default orientation
        elif position == "tilted":
            tilt_angle = (math.sin(time * 2 * math.pi) * 0.2 + 0.3) * math.pi / 4
            tilt_direction = time * 2 * math.pi
            
            # Rotate the magnetic field vector
            rotated = np.array([
                base_values[0] * math.cos(tilt_direction) - base_values[1] * math.sin(tilt_direction),
                base_values[0] * math.sin(tilt_direction) + base_values[1] * math.cos(tilt_direction),
                base_values[2]
            ])
            
            # Then tilt it
            base_values = np.array([
                rotated[0] * math.cos(tilt_angle) + rotated[2] * math.sin(tilt_angle),
                rotated[1],
                -rotated[0] * math.sin(tilt_angle) + rotated[2] * math.cos(tilt_angle)
            ])
        elif position == "vertical":
            # 90-degree rotation around Y axis
            base_values = np.array([
                base_values[2],
                base_values[1],
                -base_values[0]
            ])
        elif position == "upside_down":
            # 180-degree rotation
            base_values = np.array([
                -base_values[0],
                -base_values[1],
                -base_values[2]
            ])
            
        # Add small variations based on activity
        if activity != "stationary":
            # Motion causes small fluctuations in readings
            freq = 2.0 if activity == "walking" else 3.0 if activity == "running" else 1.0
            base_values[0] += math.sin(time * freq * 2 * math.pi) * 2.0
            base_values[1] += math.cos(time * freq * 2 * math.pi) * 2.0
            base_values[2] += math.sin(time * freq * 2 * math.pi + math.pi/3) * 1.0
            
        # Add interference in certain regions (simulating electrical devices, etc.)
        if 0.4 < time < 0.6:
            interference = math.exp(-50 * (time - 0.5)**2) * 15
            base_values += np.random.normal(0, interference, size=(3,))
            
        return base_values
        
    def _save_training_data(self, training_data):
        """Save training data to disk."""
        try:
            # Convert numpy arrays to lists for JSON serialization
            json_data = {}
            for sensor in training_data.keys():
                json_data[sensor] = {
                    "X": training_data[sensor]["X"].tolist() if isinstance(training_data[sensor]["X"], np.ndarray) else training_data[sensor]["X"],
                    "y": training_data[sensor]["y"].tolist() if isinstance(training_data[sensor]["y"], np.ndarray) else training_data[sensor]["y"]
                }
                
            # Save to file
            with open(self.data_path / "training_data.json", "w") as f:
                json.dump(json_data, f)
                
            logger.info(f"Saved training data to {self.data_path / 'training_data.json'}")
            return True
        except Exception as e:
            logger.error(f"Error saving training data: {e}")
            return False
            
    def _load_models(self):
        """Load pre-trained models if available."""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available. Cannot load models.")
            return False
            
        success = False
        
        # Attempt to load models for each sensor type
        for sensor in self.models.keys():
            model_path = self.data_path / f"{sensor}_model.pkl"
            scaler_path = self.data_path / f"{sensor}_scaler.pkl"
            
            if model_path.exists() and scaler_path.exists():
                try:
                    import joblib
                    self.models[sensor] = joblib.load(model_path)
                    self.scalers[sensor] = joblib.load(scaler_path)
                    logger.info(f"Loaded model for {sensor}")
                    success = True
                except Exception as e:
                    logger.error(f"Error loading model for {sensor}: {e}")
            else:
                logger.info(f"No pre-trained model found for {sensor}")
                
        return success
        
    def _save_models(self):
        """Save trained models to disk."""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available. Cannot save models.")
            return False
            
        success = True
        
        # Save each model if it exists
        for sensor in self.models.keys():
            if self.models[sensor] is not None and self.scalers[sensor] is not None:
                try:
                    import joblib
                    joblib.dump(self.models[sensor], self.data_path / f"{sensor}_model.pkl")
                    joblib.dump(self.scalers[sensor], self.data_path / f"{sensor}_scaler.pkl")
                    logger.info(f"Saved model for {sensor}")
                except Exception as e:
                    logger.error(f"Error saving model for {sensor}: {e}")
                    success = False
                    
        return success
        
    def train_models(self):
        """Train the ML models on the available data."""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available. Cannot train models.")
            return False
            
        success = True
        
        # Train a model for each sensor
        for sensor in self.models.keys():
            if len(self.training_data[sensor]["X"]) > 0:
                try:
                    # Create and fit the scaler
                    self.scalers[sensor] = MinMaxScaler()
                    X_scaled = self.scalers[sensor].fit_transform(self.training_data[sensor]["X"])
                    
                    # Create and train the model
                    self.models[sensor] = RandomForestRegressor(
                        n_estimators=100, 
                        max_depth=10,
                        n_jobs=-1  # Use all available cores
                    )
                    
                    self.models[sensor].fit(X_scaled, self.training_data[sensor]["y"])
                    logger.info(f"Trained model for {sensor} on {len(self.training_data[sensor]['X'])} samples")
                except Exception as e:
                    logger.error(f"Error training model for {sensor}: {e}")
                    success = False
            else:
                logger.warning(f"No training data available for {sensor}")
                success = False
                
        # Save the trained models
        if success:
            self._save_models()
            
        return success
        
    def generate_sensor_patterns(self, sensor_type, activity_type, position, duration=10.0, frequency=50):
        """
        Generate realistic sensor patterns using ML models.
        
        Args:
            sensor_type: Type of sensor ('accelerometer', 'gyroscope', 'magnetometer')
            activity_type: Activity being performed ('stationary', 'walking', 'running', 'driving')
            position: Device position ('flat', 'tilted', 'vertical', 'upside_down')
            duration: Duration of the pattern in seconds
            frequency: Sampling frequency in Hz
            
        Returns:
            A list of sensor values as dictionaries with timestamps
        """
        # Check if we have a model for this sensor
        if ML_AVAILABLE and self.models[sensor_type] is not None and self.scalers[sensor_type] is not None:
            return self._generate_patterns_with_ml(sensor_type, activity_type, position, duration, frequency)
        else:
            # Fall back to rule-based generation
            return self._generate_patterns_without_ml(sensor_type, activity_type, position, duration, frequency)
            
    def _generate_patterns_with_ml(self, sensor_type, activity_type, position, duration, frequency):
        """Generate patterns using the trained ML models."""
        # Activities and positions for feature encoding
        activities = ["stationary", "walking", "running", "driving"]
        positions = ["flat", "tilted", "vertical", "upside_down"]
        
        # Check if the requested activity and position are known
        if activity_type not in activities:
            logger.warning(f"Unknown activity: {activity_type}. Falling back to 'stationary'.")
            activity_type = "stationary"
            
        if position not in positions:
            logger.warning(f"Unknown position: {position}. Falling back to 'flat'.")
            position = "flat"
        
        # Generate a sequence of timestamps
        num_samples = int(duration * frequency)
        if num_samples <= 0:
            num_samples = 1  # Ensure at least one sample
            
        timestamps = np.linspace(0, duration, num_samples)
        
        # Normalized activity and position IDs
        activity_id = activities.index(activity_type) / max(1, len(activities))
        position_id = positions.index(position) / max(1, len(positions))
        
        # Results container
        results = []
        
        # Previous values (start with zeros)
        prev_values = np.zeros((3,))
        
        # Generate each sample
        for i, timestamp in enumerate(timestamps):
            # Normalized time (0-1 over the full duration)
            normalized_time = i / max(1, (num_samples - 1))  # Prevent division by zero
            
            # Prepare features
            features = np.array([
                normalized_time,
                activity_id,
                position_id,
                prev_values[0], prev_values[1], prev_values[2]
            ]).reshape(1, -1)
            
            # Scale the features
            try:
                scaled_features = self.scalers[sensor_type].transform(features)
                
                # Predict values
                predicted_values = self.models[sensor_type].predict(scaled_features)[0]
            except Exception as e:
                # Fall back to synthetic data generation if scaling or prediction fails
                logger.warning(f"ML prediction failed: {e}. Using synthetic data generation.")
                
                if sensor_type == "accelerometer":
                    predicted_values = self._generate_synthetic_accelerometer(normalized_time, activity_type, position)
                elif sensor_type == "gyroscope":
                    predicted_values = self._generate_synthetic_gyroscope(normalized_time, activity_type, position)
                elif sensor_type == "magnetometer":
                    predicted_values = self._generate_synthetic_magnetometer(normalized_time, activity_type, position)
                else:
                    # Default to zeros if unknown sensor type
                    predicted_values = np.zeros((3,))
            
            # Add small random noise for realism
            noise_level = 0.02 if sensor_type == "gyroscope" else 0.05 if sensor_type == "accelerometer" else 0.5
            predicted_values += np.random.normal(0, noise_level, size=(3,))
            
            # Format result
            if sensor_type == "accelerometer":
                result = {
                    "timestamp": timestamp,
                    "x": predicted_values[0],
                    "y": predicted_values[1],
                    "z": predicted_values[2]
                }
            elif sensor_type == "gyroscope":
                result = {
                    "timestamp": timestamp,
                    "x": predicted_values[0],
                    "y": predicted_values[1],
                    "z": predicted_values[2]
                }
            elif sensor_type == "magnetometer":
                result = {
                    "timestamp": timestamp,
                    "x": predicted_values[0],
                    "y": predicted_values[1],
                    "z": predicted_values[2]
                }
            
            results.append(result)
            
            # Update previous values for next iteration
            prev_values = predicted_values
            
        return results
        
    def _generate_patterns_without_ml(self, sensor_type, activity_type, position, duration, frequency):
        """Generate patterns using rule-based methods when ML is not available."""
        # Generate a sequence of timestamps
        num_samples = int(duration * frequency)
        timestamps = np.linspace(0, duration, num_samples)
        
        # Results container
        results = []
        
        # Generate each sample
        for i, timestamp in enumerate(timestamps):
            # Normalized time (0-1 for pattern generation)
            normalized_time = (timestamp % 5) / 5  # Repeat pattern every 5 seconds
            
            # Generate values based on sensor type, activity and position
            if sensor_type == "accelerometer":
                values = self._generate_synthetic_accelerometer(normalized_time, activity_type, position)
                result = {
                    "timestamp": timestamp,
                    "x": values[0],
                    "y": values[1],
                    "z": values[2]
                }
            elif sensor_type == "gyroscope":
                values = self._generate_synthetic_gyroscope(normalized_time, activity_type, position)
                result = {
                    "timestamp": timestamp,
                    "x": values[0],
                    "y": values[1],
                    "z": values[2]
                }
            elif sensor_type == "magnetometer":
                values = self._generate_synthetic_magnetometer(normalized_time, activity_type, position)
                result = {
                    "timestamp": timestamp,
                    "x": values[0],
                    "y": values[1],
                    "z": values[2]
                }
            
            results.append(result)
            
        return results
        
    def add_training_data(self, sensor_type, features, values):
        """
        Add new training data for a sensor model.
        
        Args:
            sensor_type: Type of sensor ('accelerometer', 'gyroscope', 'magnetometer')
            features: Features array or list
            values: Target values array or list
        
        Returns:
            True if successful, False otherwise
        """
        if sensor_type not in self.training_data:
            logger.error(f"Unknown sensor type: {sensor_type}")
            return False
            
        try:
            # Convert to numpy arrays if they aren't already
            features_arr = np.array(features)
            values_arr = np.array(values)
            
            # Add to existing training data
            if len(self.training_data[sensor_type]["X"]) == 0:
                self.training_data[sensor_type]["X"] = features_arr
                self.training_data[sensor_type]["y"] = values_arr
            else:
                self.training_data[sensor_type]["X"] = np.vstack([
                    self.training_data[sensor_type]["X"], features_arr
                ])
                self.training_data[sensor_type]["y"] = np.vstack([
                    self.training_data[sensor_type]["y"], values_arr
                ])
                
            logger.info(f"Added {len(features)} samples to {sensor_type} training data")
            
            # Save the updated training data
            self._save_training_data(self.training_data)
            
            return True
        except Exception as e:
            logger.error(f"Error adding training data: {e}")
            return False
            
    def get_model_info(self):
        """Get information about the trained models."""
        info = {}
        
        for sensor in self.models.keys():
            if ML_AVAILABLE and self.models[sensor] is not None:
                # Get feature importances if available
                if hasattr(self.models[sensor], 'feature_importances_'):
                    feature_names = ['time', 'activity', 'position', 'prev_x', 'prev_y', 'prev_z']
                    importances = self.models[sensor].feature_importances_
                    feature_importance = dict(zip(feature_names, importances))
                else:
                    feature_importance = None
                    
                info[sensor] = {
                    "trained": True,
                    "training_samples": len(self.training_data[sensor]["X"]) if len(self.training_data[sensor]["X"]) > 0 else 0,
                    "feature_importance": feature_importance,
                    "model_type": type(self.models[sensor]).__name__
                }
            else:
                info[sensor] = {
                    "trained": False,
                    "training_samples": len(self.training_data[sensor]["X"]) if isinstance(self.training_data[sensor]["X"], np.ndarray) else 0,
                    "model_type": "None" if not ML_AVAILABLE else "Not trained"
                }
                
        return info


# Simple test function
def test_ml_generator():
    """Test the ML sensor generator functionality."""
    logging.basicConfig(level=logging.INFO)
    
    generator = MLSensorGenerator()
    
    # Train models if ML is available
    if ML_AVAILABLE:
        generator.train_models()
    
    # Generate and print some sample data
    print("\nAccelerometer data (walking, tilted):")
    accel_data = generator.generate_sensor_patterns(
        "accelerometer", "walking", "tilted", duration=2.0, frequency=10
    )
    for sample in accel_data[:5]:  # First 5 samples
        print(f"t={sample['timestamp']:.2f}s: x={sample['x']:.2f}, y={sample['y']:.2f}, z={sample['z']:.2f}")
    
    print("\nGyroscope data (running, flat):")
    gyro_data = generator.generate_sensor_patterns(
        "gyroscope", "running", "flat", duration=2.0, frequency=10
    )
    for sample in gyro_data[:5]:  # First 5 samples
        print(f"t={sample['timestamp']:.2f}s: x={sample['x']:.2f}, y={sample['y']:.2f}, z={sample['z']:.2f}")
    
    # Print model info
    print("\nModel Information:")
    info = generator.get_model_info()
    for sensor, sensor_info in info.items():
        print(f"{sensor}: {'Trained' if sensor_info['trained'] else 'Not trained'}, {sensor_info['training_samples']} samples")
    
    return generator


if __name__ == "__main__":
    generator = test_ml_generator()