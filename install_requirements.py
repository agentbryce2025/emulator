#!/usr/bin/env python3
"""
Cross-platform setup script for Undetected Android Emulator.
This script works on Windows, macOS, and Linux.
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Check for Python 3.8 or higher."""
    print("Checking Python version...")
    
    if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 8):
        print(f"Error: Python 3.8+ is required. Found Python {sys.version_info.major}.{sys.version_info.minor}")
        print("Please install Python 3.8 or higher and try again.")
        sys.exit(1)
    
    print(f"Found Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def create_virtual_env():
    """Create a Python virtual environment."""
    print("Creating Python virtual environment...")
    
    try:
        if os.path.exists("venv"):
            print("Virtual environment already exists, skipping creation.")
            return
        
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)

def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    
    # Determine the path to pip in the virtual environment
    if platform.system() == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
    
    try:
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_path, "install", "-e", "."], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def check_qemu():
    """Check if QEMU is installed."""
    print("Checking for QEMU...")
    
    try:
        # Try to run QEMU, capturing output to avoid printing to console
        subprocess.run(
            ["qemu-system-x86_64", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            check=True
        )
        print("QEMU is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        system = platform.system()
        print("QEMU not found or not in PATH.")
        
        if system == "Windows":
            print("Please download and install QEMU for Windows: https://www.qemu.org/download/#windows")
        elif system == "Darwin":  # macOS
            print("Please install QEMU via Homebrew: brew install qemu")
        elif system == "Linux":
            print("Please install QEMU using your distribution's package manager:")
            print("  Ubuntu/Debian: sudo apt-get install qemu-system-x86")
            print("  Fedora: sudo dnf install qemu-system-x86")
            print("  Arch Linux: sudo pacman -S qemu")
        
        print("Note: The emulator requires QEMU to run, but setup can continue without it.")

def print_activation_instructions():
    """Print instructions for activating the virtual environment."""
    print("\nSetup completed!")
    print("\nTo run the emulator:")
    
    system = platform.system()
    if system == "Windows":
        print("1. Activate the virtual environment:")
        print("   venv\\Scripts\\activate")
    else:  # Unix-like systems (macOS, Linux)
        print("1. Activate the virtual environment:")
        print("   source venv/bin/activate")
    
    print("\n2. Run the emulator with GUI:")
    print("   python main.py")
    
    print("\n3. Or run in headless mode:")
    print("   python main.py --no-gui")
    
    print("\nSee 'python main.py --help' for more options.")

def main():
    """Main function."""
    print("Setting up Undetected Android Emulator...")
    
    check_python_version()
    create_virtual_env()
    install_dependencies()
    check_qemu()
    print_activation_instructions()

if __name__ == "__main__":
    main()