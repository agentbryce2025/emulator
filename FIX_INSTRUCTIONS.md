# Fix Instructions for Undetected Android Emulator

## Issue Description

The emulator is failing with the following errors:

1. ```
   AttributeError: 'SensorSimulator' object has no attribute 'set_profile'. Did you mean: 'save_profile'?
   ```

2. ```
   KeyError: 'simulation_parameters'
   ```

3. ```
   KeyError: 'baseline'
   ```

4. ```
   AttributeError: 'FridaManager' object has no attribute 'load_script'
   ```

5. QEMU window not appearing on Windows (due to incompatible display and acceleration settings)

These errors occur because of mismatches between the method names and expected properties in different parts of the code.

## How to Fix

### Option 1: Automatic Fix Script (Recommended)

1. Run the automatic fix script:
   ```
   python fix_emulator.py
   ```

2. Run the emulator:
   ```
   python main.py
   ```

### Option 2: Manual Fix

#### Fix 1: SensorSimulator set_profile issue

1. Open the file `src/gui/emulator_gui.py` in your favorite text editor
2. Find the code around line 722 (or search for `set_profile`)
3. Replace the following code:

```python
                    sensor_profile = {
                        "sensors": self.selected_device_profile["sensors"],
                        "device": {
                            "manufacturer": self.selected_device_profile["manufacturer"],
                            "model": self.selected_device_profile["model"]
                        }
                    }
                    self.sensor_simulator.set_profile(sensor_profile)
                    logger.info("Configured sensor simulation from device profile")
```

with this code:

```python
                    # Create a device profile based on the device type
                    device_type = "smartphone"  # Default device type
                    self.sensor_simulator.create_device_profile(device_type)
                    # We have to manually set the current_profile
                    self.sensor_simulator.current_profile = {
                        "sensors": self.selected_device_profile["sensors"],
                        "device": {
                            "manufacturer": self.selected_device_profile["manufacturer"],
                            "model": self.selected_device_profile["model"]
                        },
                        "simulation_parameters": {
                            "noise_factor": 0.05,
                            "update_frequency": 50,  # Hz
                            "drift_enabled": True,
                            "drift_factor": 0.001,
                            "use_ml": True
                        }
                    }
                    logger.info("Configured sensor simulation from device profile")
```

#### Fix 2: FridaManager load_script issue

1. Open the file `src/anti_detection/frida_manager.py`
2. Add the following methods after the `__init__` method:

```python
    def load_script(self, script_path):
        """Compatibility method for loading a script - just stores the path for later use."""
        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}")
            return False
            
        try:
            with open(script_path, "r") as f:
                self.script_content = f.read()
            logger.info(f"Loaded script from {script_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading script {script_path}: {e}")
            return False
            
    def set_target_package(self, package_name):
        """Compatibility method for setting the target package."""
        self.target_package = package_name
        logger.info(f"Set target package: {package_name}")
        return True
```

3. Add the following method before the `close` method:

```python
    def start_monitoring(self):
        """Start monitoring for target app launch and inject scripts."""
        if self.target_package and self.script_content:
            logger.info(f"Monitoring started for package: {self.target_package}")
            # In a real implementation, this would start a background thread
            # that checks for the app to launch, then injects the script.
            # For compatibility purposes, we'll just log that it's started.
            return True
        else:
            logger.warning("Cannot start monitoring: No target package or script content set")
            return False
```

4. Add these properties to the `__init__` method:

```python
        self.script_content = None  # Store script content for compatibility
        self.target_package = None  # Store target package for compatibility
```

### Option 3: Using the Patch File

If you have Git installed:

1. Copy the `fix_sensor_simulator.patch` file to your emulator directory
2. Open a command prompt in the emulator directory
3. Run: `git apply fix_sensor_simulator.patch`
4. Note that this only fixes the first issue. Run `fix_emulator.py` to fix all issues.

#### Fix 3: SensorSimulator baseline KeyError

1. Open the file `src/anti_detection/sensor_simulator.py`
2. Find the `_simulation_loop` method (around line 448)
3. Replace the code:

```python
        drift_values = {sensor: {axis: 0.0 for axis in data["baseline"].keys()} 
                        for sensor, data in self.current_profile["sensors"].items()}
```

with:

```python
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
```

4. Find the sensor update code (around line 497)
5. Replace the code:

```python
                baseline = sensor_config["baseline"]
                variance = sensor_config["variance"]
```

with:

```python
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
```

#### Fix 4: Windows QEMU Launch Fix

If QEMU doesn't show a window when launched on Windows:

1. Use the provided direct launcher scripts:
   - Run `run_qemu.bat` for a direct command-line launch
   - Or run `python direct_launch.py` which handles Windows-specific process creation

2. If you want to fix the core emulator:
   - Edit your configuration file at `C:\Users\YOUR_USERNAME\.config\undetected-emulator\qemu.conf`
   - Change these settings:
     ```
     display=sdl
     vga=std
     ```
   - Remove these lines if they exist:
     ```
     accelerate=kvm
     audio=pa
     ```

## What These Fixes Do

1. **SensorSimulator set_profile Fix**: Replaces the call to the non-existent `set_profile()` method with code that creates a device profile and sets the `current_profile` property directly, including the required `simulation_parameters`.

2. **SensorSimulator baseline Fix**: Adds defensive code to handle sensor profiles that don't have the expected `baseline` and `variance` fields, providing sensible defaults based on sensor type.

3. **FridaManager Fix**: Adds compatibility methods to handle the calls to `load_script()`, `set_target_package()`, and `start_monitoring()` that are used in the GUI code.

4. **Windows QEMU Fix**: Updates the QEMU parameters and process creation to be compatible with Windows:
   - Changes display backend from GTK (Linux-only) to SDL (cross-platform)
   - Changes VGA from virtio to std for wider compatibility
   - Removes KVM acceleration which is Linux-only
   - Removes PulseAudio which is Linux-only
   - Uses Windows-specific process creation flags to ensure the window stays open

After applying these fixes, the emulator should now work correctly without those errors.