# Undetected Android Emulator

This project aims to create an Android phone emulator that is undetectable by LinkedIn and other applications while providing a fully functional visual GUI experience.

## Quick Setup Guide

### Prerequisites
- Python 3.8 or higher
- QEMU 6.0+ (see platform-specific instructions below)

### Simple Installation (All Platforms)

1. Run the Python setup script:
   ```bash
   # On all platforms
   python install_requirements.py
   ```

2. Activate the virtual environment:
   ```bash
   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. Run the emulator:
   ```bash
   python main.py
   ```

### Alternative Platform-Specific Installation

#### Windows
1. Download and install [QEMU for Windows](https://www.qemu.org/download/#windows)
2. Run the setup script:
   ```
   setup.bat
   ```

#### macOS
1. Install dependencies:
   ```bash
   # Using Homebrew
   brew install python qemu libmagic
   ```
2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

#### Linux (Ubuntu/Debian)
1. Install dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-venv qemu-system-x86 qemu-utils libmagic1
   ```
2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

### Command-line Options
```
python main.py --help
```

### Troubleshooting Common Issues

#### Image Download Errors
If you're experiencing timeouts or errors while downloading Android images:

1. **Use the 'Use Local File' Button**: The emulator now has a button to use a locally downloaded ISO file
2. **Manual Download Instructions**:
   - Go to the [Android-x86 Project Website](https://www.android-x86.org/download.html)
   - Download the appropriate ISO file (e.g., android-x86_64-9.0-r2.iso)
   - Recommended: Android-x86 9.0-r2 for x86_64 architecture
   - Once downloaded, click "Use Local File" in the emulator's Images tab
   - Navigate to your download location and select the ISO file

3. **Direct Download Links**:
   - [Android-x86 9.0-r2 (64-bit)](https://sourceforge.net/projects/android-x86/files/Release%209.0/android-x86_64-9.0-r2.iso/download)
   - [Android-x86 8.1-r6 (64-bit)](https://sourceforge.net/projects/android-x86/files/Release%208.1/android-x86_64-8.1-r6.iso/download)
   - [Android-x86 7.1-r5 (64-bit)](https://sourceforge.net/projects/android-x86/files/Release%207.1/android-x86_64-7.1-r5.iso/download)

4. **Advanced Manual Setup**: 
   You can directly place the downloaded ISO files in the emulator's images directory:
   - Windows: `C:\Users\YOUR_USERNAME\.config\undetected-emulator\images\`
   - Linux/macOS: `~/.config/undetected-emulator/images/`

#### QEMU Not Found Error
If you see "QEMU not found" errors:

1. **Install QEMU**:
   - Windows: Download from [QEMU for Windows](https://qemu.weilnetz.de/w64/)
   - macOS: `brew install qemu`
   - Linux: `sudo apt install qemu-system-x86`
   
2. **Add QEMU to PATH**: Ensure the QEMU installation directory is in your system PATH
   - Windows: Add `C:\Program Files\qemu` to your PATH in System Properties

3. **Specify QEMU path in the GUI**: 
   - In the emulator GUI, go to the Settings tab
   - Enter the full path to QEMU (e.g., `C:\Program Files\qemu\qemu-system-x86_64.exe`)
   - Click "Apply" to save the setting

4. **Git Bash Users on Windows**:
   - Git Bash may not see the system PATH correctly
   - Use the Settings tab to manually set the QEMU path
   - Or specify the full path: `python main.py --qemu-path="C:\Program Files\qemu\qemu-system-x86_64.exe"`
   - Alternatively, run the emulator using Command Prompt or PowerShell instead

#### GUI Display Issues
If you encounter problems with the GUI display:

1. **Qt dependencies**: Install required Qt libraries
   - Windows: `pip install PyQt5`
   - Linux: `sudo apt install python3-pyqt5`

2. **Font issues**: If text appears garbled, try changing the font settings in the interface

3. **Scaling problems**: On high DPI displays, try setting the environment variable: `QT_AUTO_SCREEN_SCALE_FACTOR=1`

#### Windows QEMU Window Not Appearing
If you're on Windows and the QEMU window (Android phone interface) doesn't appear:

1. **Use the Enhanced Windows Launcher**:
   ```
   enhanced_windows_launcher.bat
   ```
   This provides options for different launch methods and troubleshooting.

2. **Apply Windows-specific fixes**:
   ```
   python windows_gui_fix_fixed.py
   ```
   This applies several fixes specifically for Windows display issues.

3. **Use Direct Launcher** as a fallback:
   ```
   python direct_launch.py
   ```
   or
   ```
   run_qemu.bat
   ```
   These launchers use Windows-friendly settings to ensure the QEMU window appears.

4. **Check QEMU Installation**: Make sure QEMU is properly installed at one of these locations:
   - `C:\Program Files\qemu\qemu-system-x86_64.exe`
   - `C:\Program Files (x86)\qemu\qemu-system-x86_64.exe`

For detailed information, see the `WINDOWS_GUI_FIX.md` file.

## Project Goals

1. Create a fully functional Android emulator with a visual GUI
2. Implement anti-detection techniques to bypass LinkedIn's emulator detection
3. Provide an easy-to-use interface for users
4. Build on existing open-source technologies
5. Ensure the solution is maintainable and updatable

## Why This Exists

Many applications, including LinkedIn, implement emulator detection to prevent automated usage and testing. This project aims to create a research tool that can help understand these detection mechanisms and provide a platform for legitimate testing of mobile applications in a controlled environment.

## Architecture Overview

Our emulator will be built on a layered architecture:

1. **Base Virtualization Layer**: Modified QEMU-based system with hardware fingerprint spoofing
2. **Android Runtime Layer**: Customized Android-x86 implementation
3. **Anti-Detection Layer**: Specialized modules to bypass common detection techniques
4. **GUI Interface Layer**: User-friendly interface for controlling the emulator

## Technical Approach

### 1. Emulator Base
We'll leverage existing open-source Android emulators, primarily:
- **Android-x86 Project**: For the core Android implementation
- **QEMU**: As the virtualization engine
- **Anbox**: For containerization techniques

### 2. Anti-Detection Mechanisms

From our research, LinkedIn and similar apps use several methods to detect emulators:

#### Hardware Identifier Detection
- IMEI, Device ID, MAC addresses
- Build properties and serial numbers
- Sensor data (accelerometer, gyroscope, etc.)

#### Virtualization Detection
- CPU characteristics and performance
- Memory access patterns
- I/O timing analysis

#### Behavioral Detection
- Touch input patterns
- Network traffic patterns
- System API usage

Our approach will implement countermeasures for each:

1. **Hardware Spoofing**:
   - Customized Build.prop with realistic device identifiers
   - Machine learning-based sensor data generation that mimics real devices
   - Spoofed IMEI, Device ID, and MAC address

2. **Virtualization Masking**:
   - Modified QEMU with timing attack prevention
   - CPU features masking
   - Memory access pattern normalization

3. **Behavioral Emulation**:
   - TouchScreen input randomization
   - Network traffic pattern normalization
   - System API call interception and modification

### 3. Implementation Tools

We'll use several frameworks and tools:

- **Frida**: For runtime hooking and modification of system calls
- **Xposed Framework**: For deeper system modifications
- **Magisk**: For root hiding and system modification
- **Flutter**: For a cross-platform GUI

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
- Set up base Android-x86 system
- Configure QEMU with basic virtualization
- Implement basic GUI controls
- Create initial build system

### Phase 2: Anti-Detection Core (Week 3-4)
- Implement hardware identifier spoofing
- Add virtualization detection countermeasures
- Create sensor data simulation
- Develop system property modifications

### Phase 3: Advanced Countermeasures (Week 5-6)
- Add Frida scripts for runtime detection bypass
- Implement Xposed modules for system-level modifications
- Create behavior normalization tools
- Set up network traffic pattern controls

### Phase 4: GUI and User Experience (Week 7-8)
- Develop user-friendly GUI interface
- Add device profile selection and customization
- Implement performance optimization
- Create user documentation and guides

### Phase 5: Testing and Validation (Week 9-10)
- Implement automated detection bypass testing framework
- Create comprehensive test suite for detection methods
- Develop CI/CD pipeline for continuous testing
- Validate against popular apps with emulator detection

## Dependencies

- Android-x86 (latest stable version)
- QEMU 6.0+
- Frida toolkit
- Xposed Framework
- Flutter for GUI development
- Python 3.8+ for build scripts and tools

## Building and Running

Detailed build instructions will be added as development progresses. In general, the process will involve:

1. Setting up the development environment
2. Building the customized Android-x86 image
3. Configuring the QEMU virtualization environment
4. Installing and running the GUI interface

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This project is for research and educational purposes only. Users are responsible for ensuring they comply with all applicable terms of service and laws when using this software.

## License

This project is licensed under the MIT License - see the LICENSE file for details.