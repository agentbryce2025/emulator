#!/usr/bin/env python3
"""
Main script for the undetected Android emulator.
This script sets up and launches the emulator with anti-detection features.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("emulator.log")
    ]
)

logger = logging.getLogger(__name__)

# Check if running from the correct directory
if not os.path.exists(os.path.join(os.path.dirname(__file__), "src")):
    logger.error("Please run this script from the project root directory")
    sys.exit(1)

# Import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from src.core.qemu_wrapper import QEMUWrapper
    from src.anti_detection.hardware_spoof import HardwareSpoofer
    from src.anti_detection.sensor_simulator import SensorSimulator
    from src.anti_detection.frida_manager import FridaManager
    from src.gui.emulator_gui import EmulatorGUI, QApplication
except ImportError as e:
    logger.error(f"Error importing modules: {str(e)}")
    logger.error("Make sure you have installed all dependencies (run 'pip install -e .')")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Undetected Android Emulator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("--no-gui", action="store_true", help="Run in headless mode (no GUI)")
    parser.add_argument("--system-image", help="Path to Android system image")
    parser.add_argument("--hardware-profile", help="Hardware profile to use")
    parser.add_argument("--sensor-profile", help="Sensor profile to use")
    parser.add_argument("--memory", default="2048", help="Memory size in MB")
    parser.add_argument("--cores", default="4", help="Number of CPU cores")
    parser.add_argument("--auto-start", action="store_true", help="Start emulator automatically")
    
    return parser.parse_args()

def run_headless(args):
    """Run the emulator in headless mode (no GUI)."""
    logger.info("Starting in headless mode")
    
    # Initialize components
    qemu = QEMUWrapper()
    hardware_spoofer = HardwareSpoofer()
    sensor_simulator = SensorSimulator()
    
    # Configure QEMU
    qemu.set_param("memory", args.memory)
    qemu.set_param("smp", args.cores)
    qemu.set_param("display", "none")  # Headless mode
    
    if args.system_image:
        qemu.set_param("hda", args.system_image)
    else:
        logger.error("No system image specified. Use --system-image to provide one.")
        return 1
        
    # Load hardware profile if specified
    if args.hardware_profile:
        if hardware_spoofer.load_profile(args.hardware_profile):
            logger.info(f"Loaded hardware profile: {args.hardware_profile}")
        else:
            logger.error(f"Failed to load hardware profile: {args.hardware_profile}")
            return 1
    else:
        # Create a default profile
        hardware_spoofer.create_new_profile("Samsung", "Galaxy S21", "12.0")
        logger.info("Created default hardware profile")
        
    # Load sensor profile if specified
    if args.sensor_profile:
        if sensor_simulator.load_profile(args.sensor_profile):
            logger.info(f"Loaded sensor profile: {args.sensor_profile}")
        else:
            logger.error(f"Failed to load sensor profile: {args.sensor_profile}")
            return 1
            
    # Start the emulator
    if qemu.start():
        logger.info("Emulator started successfully")
        
        # Start sensor simulation
        if sensor_simulator.current_profile:
            if sensor_simulator.start_simulation():
                logger.info("Sensor simulation started")
                
        # Keep running until terminated
        try:
            while qemu.is_alive():
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            # Cleanup
            if sensor_simulator.sensor_simulation_active:
                sensor_simulator.stop_simulation()
                
            qemu.stop()
            logger.info("Emulator stopped")
            
        return 0
    else:
        logger.error("Failed to start emulator")
        return 1

def run_gui():
    """Run the emulator with GUI."""
    logger.info("Starting with GUI")
    
    app = QApplication(sys.argv)
    window = EmulatorGUI()
    window.show()
    
    return app.exec_() if hasattr(app, 'exec_') else app.exec()

def main():
    """Main function."""
    args = parse_arguments()
    
    logger.info("Undetected Android Emulator starting")
    
    try:
        if args.no_gui:
            return run_headless(args)
        else:
            return run_gui()
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())