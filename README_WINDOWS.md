# Windows Setup Guide for Undetected Android Emulator

This guide provides step-by-step instructions for setting up and running the undetected Android emulator on Windows.

## Requirements

1. **Windows 10 or 11** (64-bit)
2. **Python 3.8 or newer** installed
3. **QEMU** installed on your system

## Installation

### Step 1: Install QEMU

1. Download QEMU from [https://qemu.weilnetz.de/w64/](https://qemu.weilnetz.de/w64/) (choose the latest version)
2. Run the installer and follow the instructions
3. Make sure to check "Add to PATH" during installation

### Step 2: Set up the emulator

1. Clone this repository or extract the zip file
2. Open Command Prompt or PowerShell as administrator
3. Navigate to the emulator directory:
   ```
   cd path\to\emulator
   ```
4. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -e .
   ```

## Running the Emulator

### Method 1: Using the batch file (recommended)

1. Double-click `run_emulator.bat` in the emulator directory
2. The batch file will set up everything and launch the emulator

### Method 2: Running manually

1. Open Command Prompt or PowerShell
2. Navigate to the emulator directory
3. Activate the virtual environment:
   ```
   venv\Scripts\activate
   ```
4. Run the emulator with specific Windows settings:
   ```
   python improved_windows_launcher.py
   ```

## Troubleshooting

### UI display issues

If you encounter issues with the emulator UI not displaying:

1. Make sure QEMU is correctly installed and in your PATH
2. Try running the emulator with different display options:
   ```
   python main.py --qemu-path "C:\Program Files\qemu\qemu-system-x86_64.exe"
   ```
3. Check the logs in `emulator.log` for error messages

### Error: QEMU not found

If you see "QEMU not found" errors:

1. Manually locate your QEMU executable (usually in `C:\Program Files\qemu\`)
2. Edit the `.config\undetected-emulator\qemu.conf` file in your home directory:
   ```
   qemu_path=C:\Program Files\qemu\qemu-system-x86_64.exe
   display=sdl
   vga=virtio
   ```

### Emulator starts but Android doesn't load

1. Ensure you have enough disk space (at least 10GB free)
2. Try using the "Quick Setup" button in the GUI
3. Make sure your Android system image is not corrupted

## Additional Notes

- The first time you start the emulator, it will download and set up an Android system image, which may take some time
- VirtualBox or VMware may conflict with QEMU; try disabling them if you experience issues
- For best performance, ensure your CPU supports hardware virtualization and it's enabled in BIOS

If you continue to experience issues, check the troubleshooting section in the main README or open an issue on GitHub.