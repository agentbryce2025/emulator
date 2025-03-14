# Undetected Android Emulator Bug Fix

## Issue Description

The emulator is failing with multiple errors:

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

These errors happen when you try to start the emulator after selecting a device profile and system image.

## How to Fix the Issues

There are three ways to fix these issues:

### Option 1: Run the Fix Script (Recommended)

1. Run this command in your emulator directory:
   ```
   python fix_emulator.py
   ```
2. Run the emulator:
   ```
   python main.py
   ```

The script will automatically fix all three issues.

### Option 2: Apply the Patch File (Partial Fix)

1. Apply the patch:
   ```
   git apply fix_sensor_simulator.patch
   ```
2. Run the fix script to address the additional issues:
   ```
   python fix_emulator.py
   ```
3. Run the emulator:
   ```
   python main.py
   ```

### Option 3: Manual Fix

Please follow the detailed instructions in `FIX_INSTRUCTIONS.md`.

## What These Fixes Do

1. **SensorSimulator set_profile Fix**: Replaces the call to the non-existent `set_profile()` method with code that creates a device profile and sets the `current_profile` property directly. Also adds the required `simulation_parameters` to prevent the KeyError.

2. **SensorSimulator baseline Fix**: Adds defensive code to handle sensor profiles that don't have the expected `baseline` and `variance` fields, providing sensible defaults based on sensor type.

3. **FridaManager Fix**: Adds compatibility methods (`load_script()`, `set_target_package()` and `start_monitoring()`) to the FridaManager class to make it compatible with the GUI code.

4. **Windows QEMU Fix**: Updates the QEMU parameters and process creation to be compatible with Windows, including:
   - Changes display backend from GTK (Linux-only) to SDL (cross-platform)
   - Changes VGA from virtio to std for wider compatibility
   - Removes KVM acceleration which is Linux-only
   - Adds Windows-specific direct launcher scripts

## Files Included in This Fix

- `fix_emulator.py` - Python script to automatically apply all fixes
- `fix_sensor_simulator.patch` - Git patch file (partial fix)
- `FIX_INSTRUCTIONS.md` - Manual fix instructions
- `README_FIX.md` - This file
- `direct_launch.py` - Python script for directly launching QEMU with working settings
- `run_qemu.bat` - Batch script for directly launching QEMU on Windows

## After Applying the Fixes

After applying the fixes, the emulator should start correctly when you click the "Start Emulator" button. The errors related to `set_profile`, `simulation_parameters`, and `load_script` should no longer appear.

### Windows Users

If you don't see the QEMU window after clicking "Start Emulator" in the GUI:

1. Try the direct launcher:
   ```
   run_qemu.bat
   ```
   or
   ```
   python direct_launch.py
   ```

2. Look for a QEMU window that might be minimized or hidden behind other windows

Once the emulator is running, there might still be some expected errors related to Frida not finding a connected device, which is normal during the initial startup phase.

If you encounter any other issues, please refer to the project's main README.md file for troubleshooting guidance.