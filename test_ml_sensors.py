#!/usr/bin/env python3
"""
Test script to demonstrate machine learning-based sensor pattern generation.
"""

import os
import sys
import time
import json
import logging
import argparse
import matplotlib.pyplot as plt
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from src.anti_detection.sensor_simulator import SensorSimulator
from src.anti_detection.ml_sensor_generator import MLSensorGenerator

def plot_sensor_data(data, title, output_file=None):
    """Plot sensor data for visualization."""
    timestamps = [point["timestamp"] for point in data]
    x_values = [point["x"] for point in data]
    y_values = [point["y"] for point in data]
    z_values = [point["z"] for point in data]
    
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, x_values, 'r-', label='X')
    plt.plot(timestamps, y_values, 'g-', label='Y')
    plt.plot(timestamps, z_values, 'b-', label='Z')
    plt.grid(True)
    plt.xlabel('Time (seconds)')
    plt.ylabel('Sensor Value')
    plt.title(title)
    plt.legend()
    
    if output_file:
        plt.savefig(output_file)
        print(f"Plot saved to {output_file}")
    else:
        plt.show()

def test_ml_sensor_generation():
    """Test machine learning-based sensor pattern generation."""
    print("Testing ML-based sensor pattern generation...")
    
    # Initialize ML generator
    ml_generator = MLSensorGenerator()
    
    # Ensure models are trained
    ml_generator.train_models()
    
    # Get model info
    model_info = ml_generator.get_model_info()
    print("\nML Model Information:")
    for sensor, info in model_info.items():
        print(f"  {sensor}: {'Trained' if info['trained'] else 'Not trained'}")
        if info['trained'] and 'training_samples' in info:
            print(f"    - Training samples: {info['training_samples']}")
        if info['trained'] and 'feature_importance' in info and info['feature_importance']:
            print(f"    - Feature importance:")
            for feature, importance in info['feature_importance'].items():
                print(f"      - {feature}: {importance:.4f}")
    
    # Generate sensor patterns for different activities and positions
    activities = ["stationary", "walking", "running", "driving"]
    positions = ["flat", "tilted", "vertical", "upside_down"]
    
    # Choose one sensor type, activity, and position to plot
    sensor_type = "accelerometer"
    activity = "walking"
    position = "tilted"
    
    print(f"\nGenerating {sensor_type} data for {activity} activity in {position} position...")
    data = ml_generator.generate_sensor_patterns(
        sensor_type, activity, position, duration=5.0, frequency=50
    )
    
    # Plot the data
    title = f"{sensor_type.capitalize()} - {activity.capitalize()} in {position.capitalize()} position"
    output_file = f"ml_{sensor_type}_{activity}_{position}.png"
    
    try:
        plot_sensor_data(data, title, output_file)
    except Exception as e:
        print(f"Error plotting data: {e}")
        print("Plotting requires a display. Printing sample data instead.")
        for i in range(min(5, len(data))):
            print(f"  t={data[i]['timestamp']:.2f}s: x={data[i]['x']:.2f}, y={data[i]['y']:.2f}, z={data[i]['z']:.2f}")
    
    # Compare data from different activities
    print("\nComparing different activities (accelerometer data):")
    for activity in activities:
        data = ml_generator.generate_sensor_patterns(
            "accelerometer", activity, "flat", duration=0.5, frequency=10
        )
        print(f"  {activity.capitalize()} (5 samples):")
        for i in range(min(5, len(data))):
            print(f"    t={data[i]['timestamp']:.2f}s: x={data[i]['x']:.2f}, y={data[i]['y']:.2f}, z={data[i]['z']:.2f}")
    
    return ml_generator

def test_sensor_simulator_integration():
    """Test the integration of ML generator with the sensor simulator."""
    print("\nTesting SensorSimulator integration with ML sensor generation...")
    
    # Initialize sensor simulator
    simulator = SensorSimulator()
    
    # Create a profile with ML-based sensor generation
    profile = simulator.create_device_profile(
        device_type="smartphone",
        activity_type="walking",
        position="tilted",
        use_ml=True
    )
    
    # Print ML status
    ml_info = simulator.get_ml_model_info()
    print(f"ML generation available: {ml_info.get('available', False)}")
    print(f"ML generation enabled: {ml_info.get('enabled', False)}")
    
    if ml_info.get('available', False):
        print("\nML Models:")
        for sensor, sensor_info in ml_info.get('models', {}).items():
            print(f"  {sensor}: {'Trained' if sensor_info.get('trained', False) else 'Not trained'}")
    
    # Start simulation
    if simulator.start_simulation():
        print("Sensor simulation started")
        
        # Collect some simulated values
        print("\nCollecting simulated sensor values...")
        values = []
        
        try:
            for i in range(10):
                current_values = simulator.get_current_values()
                values.append(current_values)
                print(f"Sample {i+1}:")
                for sensor, data in current_values.items():
                    if sensor in ["accelerometer", "gyroscope", "magnetometer"]:
                        print(f"  {sensor}: x={data.get('x', 0):.2f}, y={data.get('y', 0):.2f}, z={data.get('z', 0):.2f}")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Sampling interrupted")
        finally:
            simulator.stop_simulation()
            print("Sensor simulation stopped")
    else:
        print("Failed to start sensor simulation")
    
    return simulator

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test ML-based sensor generation")
    parser.add_argument("--simulator-only", action="store_true", help="Only test simulator integration")
    parser.add_argument("--ml-only", action="store_true", help="Only test ML generator")
    args = parser.parse_args()
    
    if args.simulator_only:
        test_sensor_simulator_integration()
    elif args.ml_only:
        test_ml_sensor_generation()
    else:
        # Test both
        ml_generator = test_ml_sensor_generation()
        simulator = test_sensor_simulator_integration()
        
        # Test community contribution feature
        print("\nTesting community contribution of sensor data...")
        
        # Generate some synthetic data to contribute
        print("Generating synthetic 'user-collected' data...")
        synthetic_data = []
        for i in range(50):
            synthetic_data.append({
                "x": np.sin(i/10) * 0.5 + np.random.normal(0, 0.1),
                "y": np.cos(i/10) * 0.3 + np.random.normal(0, 0.1),
                "z": 9.81 + np.random.normal(0, 0.05)
            })
        
        # Contribute the data
        success = simulator.contribute_sensor_data(
            "accelerometer", "walking", "flat", synthetic_data
        )
        
        if success:
            print("Successfully contributed sensor data to ML model")
        else:
            print("Failed to contribute sensor data")
    
    print("\nML sensor generation testing complete!")

if __name__ == "__main__":
    main()