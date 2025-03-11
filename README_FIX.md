# Undetected Android Emulator Bug Fix

## Issue Description

The emulator is failing with the following error:
```
AttributeError: 'SensorSimulator' object has no attribute 'set_profile'. Did you mean: 'save_profile'?
```

This happens when you try to start the emulator after selecting a device profile and system image.

## How to Fix the Issue

There are three ways to fix this issue:

### Option 1: Run the Fix Script (Easiest)

1. Run this command in your emulator directory:
   ```
   python fix_emulator.py
   ```
2. Run the emulator:
   ```
   python main.py
   ```

### Option 2: Apply the Patch File (If you have Git)

1. Apply the patch:
   ```
   git apply fix_sensor_simulator.patch
   ```
2. Run the emulator:
   ```
   python main.py
   ```

### Option 3: Manual Fix

Please follow the detailed instructions in `FIX_INSTRUCTIONS.md`.

## What This Fix Does

The fix replaces the call to a non-existent method `set_profile()` in the `SensorSimulator` class with the correct method call. The fix uses `create_device_profile()` and then directly sets the `current_profile` property.

## Files Included in This Fix

- `fix_emulator.py` - Python script to automatically apply the fix
- `fix_sensor_simulator.patch` - Git patch file
- `FIX_INSTRUCTIONS.md` - Manual fix instructions
- `README_FIX.md` - This file

## After Applying the Fix

After applying the fix, the emulator should start correctly when you click the "Start Emulator" button. The error `'SensorSimulator' object has no attribute 'set_profile'` should no longer appear.

If you encounter any other issues, please refer to the project's main README.md file for troubleshooting guidance.