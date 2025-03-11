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
    from src.core.image_manager import ImageManager
    from src.core.android_customizer import AndroidCustomizer
    from src.anti_detection.hardware_spoof import HardwareSpoofer
    from src.anti_detection.sensor_simulator import SensorSimulator
    from src.anti_detection.frida_manager import FridaManager
    from src.anti_detection.device_profiles import DeviceProfileDatabase
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
    parser.add_argument("--data-image", help="Path to data image (for persistent storage)")
    parser.add_argument("--device-profile", help="Device profile to use")
    parser.add_argument("--memory", default="2048", help="Memory size in MB")
    parser.add_argument("--cores", default="4", help="Number of CPU cores")
    parser.add_argument("--auto-start", action="store_true", help="Start emulator automatically")
    parser.add_argument("--target-app", help="Target app package name (e.g., com.linkedin.android)")
    parser.add_argument("--frida-script", help="Path to custom Frida script to use")
    parser.add_argument("--linkedin-mode", action="store_true", help="Enable LinkedIn-specific detection bypass")
    parser.add_argument("--qemu-path", help="Full path to QEMU executable (e.g., C:\\Program Files\\qemu\\qemu-system-x86_64.exe)")
    
    return parser.parse_args()

def run_headless(args):
    """Run the emulator in headless mode (no GUI)."""
    logger.info("Starting in headless mode")
    
    # Initialize components
    qemu = QEMUWrapper()
    
    # Set QEMU path if provided
    if args.qemu_path:
        logger.info(f"Using QEMU path from command line: {args.qemu_path}")
        qemu.qemu_path = args.qemu_path
    
    image_manager = ImageManager()
    android_customizer = AndroidCustomizer()
    
    # Get device profile
    profile_db = DeviceProfileDatabase()
    device_profile = None
    
    if args.device_profile:
        device_profile = profile_db.get_profile(args.device_profile)
        if not device_profile:
            logger.error(f"Device profile '{args.device_profile}' not found")
            logger.info(f"Available profiles: {', '.join(profile_db.get_profile_names())}")
            return 1
    else:
        # Use a random profile
        device_profile = profile_db.get_random_profile()
        if not device_profile:
            logger.error("No device profiles available")
            return 1
            
    logger.info(f"Using device profile: {device_profile['manufacturer']} {device_profile['model']}")
    
    # Configure QEMU
    qemu.set_param("memory", args.memory)
    qemu.set_param("smp", args.cores)
    qemu.set_param("display", "none")  # Headless mode
    
    # Set up Android image
    if args.system_image:
        system_image = args.system_image
        if not os.path.exists(system_image):
            logger.error(f"System image not found: {system_image}")
            return 1
    else:
        # Try to find an image
        available_images = image_manager.get_available_images()
        if not available_images:
            logger.error("No system images available. Please specify --system-image or download one.")
            return 1
            
        # Use the first available image
        system_image = available_images[0]['path']
        logger.info(f"Using system image: {system_image}")
    
    qemu.set_param("cdrom", system_image)
    
    # Set up data image if provided
    if args.data_image:
        if not os.path.exists(args.data_image):
            logger.error(f"Data image not found: {args.data_image}")
            return 1
            
        qemu.set_param("hda", args.data_image)
    else:
        # Create a temporary data image
        temp_data = image_manager.create_empty_image("temp_data", size_gb=8)
        if temp_data:
            qemu.set_param("hda", temp_data)
            logger.info(f"Created temporary data image: {temp_data}")
        else:
            logger.warning("Failed to create temporary data image, proceeding without persistent storage")
    
    # Initialize sensor simulator with device profile
    sensor_simulator = SensorSimulator()
    if "sensors" in device_profile:
        sensor_profile = {
            "sensors": device_profile["sensors"],
            "device": {
                "manufacturer": device_profile["manufacturer"],
                "model": device_profile["model"]
            }
        }
        sensor_simulator.set_profile(sensor_profile)
        logger.info("Set up sensor simulation from device profile")
    
    # Initialize Frida manager
    frida_manager = FridaManager()
    
    # Set up Frida script
    if args.linkedin_mode:
        frida_script_path = os.path.join(os.path.dirname(__file__), 
                                        "src", "anti_detection", "frida_scripts", "linkedin_bypass.js")
        frida_manager.load_script(frida_script_path)
        logger.info("Loaded LinkedIn-specific Frida script")
    elif args.frida_script:
        if not os.path.exists(args.frida_script):
            logger.error(f"Frida script not found: {args.frida_script}")
            return 1
            
        frida_manager.load_script(args.frida_script)
        logger.info(f"Loaded custom Frida script: {args.frida_script}")
    else:
        # Load default script
        default_script = os.path.join(os.path.dirname(__file__), 
                                    "src", "anti_detection", "frida_scripts", "detection_bypass.js")
        frida_manager.load_script(default_script)
        logger.info("Loaded default Frida detection bypass script")
    
    # Set target app if specified
    if args.target_app:
        frida_manager.set_target_package(args.target_app)
        logger.info(f"Set target package: {args.target_app}")
    
    # Start the emulator
    if qemu.start():
        logger.info("Emulator started successfully")
        
        # Start sensor simulation
        if sensor_simulator.current_profile:
            if sensor_simulator.start_simulation():
                logger.info("Sensor simulation started")
        
        # Start Frida manager to inject scripts when target app launches
        frida_manager.start_monitoring()
        logger.info("Frida manager started")
                
        # Keep running until terminated
        try:
            while qemu.is_alive():
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            # Cleanup
            frida_manager.stop_monitoring()
            logger.info("Stopped Frida monitoring")
            
            if sensor_simulator.sensor_simulation_active:
                sensor_simulator.stop_simulation()
                logger.info("Stopped sensor simulation")
                
            qemu.stop()
            logger.info("Emulator stopped")
            
        return 0
    else:
        logger.error("Failed to start emulator")
        return 1

def run_gui(args=None):
    """Run the emulator with GUI."""
    logger.info("Starting with GUI")
    
    app = QApplication(sys.argv)
    window = EmulatorGUI()
    
    # If QEMU path was specified via command line, set it in the GUI
    if args and args.qemu_path:
        qemu_path = args.qemu_path
        logger.info(f"Using QEMU path from command line: {qemu_path}")
        window.qemu.qemu_path = qemu_path
        
        # Also update the GUI textbox if it exists
        if hasattr(window, 'qemu_path_input'):
            window.qemu_path_input.setText(qemu_path)
            
        # Save the configuration for future use
        window.qemu.save_config()
        
    window.show()
    
    return app.exec_() if hasattr(app, 'exec_') else app.exec()

def main():
    """Main function."""
    args = parse_arguments()
    
    logger.info("Undetected Android Emulator starting")
    
    # Check for required tools
    import subprocess
    import os
    import platform
    
    def check_qemu_installed():
        """Check if QEMU is installed and accessible."""
        try:
            # Standard check for most systems
            result = subprocess.run(["qemu-system-x86_64", "--version"], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                shell=False)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            # Check common installation locations on Windows
            if platform.system() == "Windows":
                possible_paths = [
                    "C:\\Program Files\\qemu\\qemu-system-x86_64.exe",
                    "C:\\Program Files (x86)\\qemu\\qemu-system-x86_64.exe",
                    os.path.expanduser("~\\qemu\\qemu-system-x86_64.exe"),
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        logger.info(f"Found QEMU at: {path}")
                        # Store this path for later use
                        if not os.path.exists(os.path.expanduser("~/.config/undetected-emulator")):
                            os.makedirs(os.path.expanduser("~/.config/undetected-emulator"), exist_ok=True)
                        
                        # Save the path to a config file
                        try:
                            with open(os.path.expanduser("~/.config/undetected-emulator/qemu.conf"), "w") as f:
                                f.write(f"qemu_path={path}")
                        except Exception as e:
                            logger.warning(f"Could not save QEMU path to config: {e}")
                            
                        return True
            
            return False
                
    if not check_qemu_installed():
        logger.warning("QEMU not found. Please install QEMU to run the emulator.")
    
    try:
        # Set the QEMU path explicitly if provided as an argument
        if args.qemu_path:
            logger.info(f"Command-line QEMU path provided: {args.qemu_path}")
            
            # Ensure the config directory exists
            config_dir = os.path.expanduser("~/.config/undetected-emulator")
            os.makedirs(config_dir, exist_ok=True)
            
            # Save this to a config file for future use
            try:
                with open(os.path.join(config_dir, "qemu.conf"), "w") as f:
                    f.write(f"qemu_path={args.qemu_path}\n")
                logger.info("Saved QEMU path to configuration file")
            except Exception as e:
                logger.warning(f"Could not save QEMU path to config: {e}")
            
        if args.no_gui:
            return run_headless(args)
        else:
            return run_gui(args)
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())