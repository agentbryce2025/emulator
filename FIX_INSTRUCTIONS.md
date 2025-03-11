# Fix Instructions for Undetected Android Emulator

## Issue Description

The emulator is failing with the following error:
```
AttributeError: 'SensorSimulator' object has no attribute 'set_profile'. Did you mean: 'save_profile'?
```

This is happening because the code in `emulator_gui.py` is trying to call a method `set_profile()` on the `SensorSimulator` class, but this method doesn't exist. The `SensorSimulator` class has methods like `load_profile`, `save_profile`, and `create_device_profile`, but no `set_profile`.

## How to Fix

### Option 1: Manual Fix (Recommended)

1. Open the file `src/gui/emulator_gui.py` in your favorite text editor
2. Find line 722 (or search for `set_profile`)
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
                        }
                    }
                    logger.info("Configured sensor simulation from device profile")
```

4. Save the file
5. Run the emulator again with `python main.py`

### Option 2: Using the Patch File

If you have Git installed:

1. Copy the `fix_sensor_simulator.patch` file to your emulator directory
2. Open a command prompt in the emulator directory
3. Run: `git apply fix_sensor_simulator.patch`
4. Run the emulator again with `python main.py`

## What This Fix Does

This fix replaces the call to the non-existent `set_profile()` method with appropriate code that:

1. Creates a default device profile with `create_device_profile()`
2. Manually sets the `current_profile` property with the sensor data from the selected device profile

The emulator should now work correctly!