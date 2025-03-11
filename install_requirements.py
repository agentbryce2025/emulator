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
        # Check if venv module is available
        try:
            import venv
        except ImportError:
            print("Error: The 'venv' module is not available. Please install it first.")
            print("For Ubuntu/Debian: sudo apt-get install python3-venv")
            print("For Windows: Make sure you're using Python 3.3+ with the venv module included")
            sys.exit(1)
            
        if os.path.exists("venv"):
            print("Virtual environment directory already exists.")
            # Check if it's actually a valid venv
            is_valid_venv = False
            if platform.system() == "Windows":
                is_valid_venv = os.path.exists(os.path.join("venv", "Scripts", "python.exe"))
            else:
                is_valid_venv = os.path.exists(os.path.join("venv", "bin", "python"))
                
            if is_valid_venv:
                print("Existing virtual environment looks valid, skipping creation.")
                return
            else:
                print("Warning: Existing 'venv' directory doesn't appear to be a valid virtual environment.")
                print("Attempting to recreate it. If this fails, please delete the 'venv' directory manually.")
                
                # Try to remove the existing directory
                try:
                    if platform.system() == "Windows":
                        subprocess.run(["rmdir", "/S", "/Q", "venv"], shell=True, check=False)
                    else:
                        subprocess.run(["rm", "-rf", "venv"], check=False)
                except Exception as e:
                    print(f"Warning: Could not remove existing venv directory: {e}")
                    print("Please delete the 'venv' directory manually and run this script again.")
                    sys.exit(1)
        
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have permissions to write to the current directory")
        print("2. Try creating the virtual environment manually: python -m venv venv")
        print("3. If the above fails, try installing virtualenv: pip install virtualenv")
        print("   Then create the environment: virtualenv venv")
        sys.exit(1)

def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    
    # Determine the python and pip paths in the virtual environment
    if platform.system() == "Windows":
        python_path = os.path.join("venv", "Scripts", "python")
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        python_path = os.path.join("venv", "bin", "python")
        pip_path = os.path.join("venv", "bin", "pip")
    
    # Verify the paths exist
    if not os.path.exists(python_path + (".exe" if platform.system() == "Windows" else "")):
        print(f"Error: Python executable not found at {python_path}")
        print("The virtual environment may not have been created properly.")
        print("Try deleting the 'venv' directory and running this script again.")
        sys.exit(1)
    
    try:
        print("Upgrading pip...")
        # Upgrade pip using the recommended approach for each platform
        if platform.system() == "Windows":
            # On Windows, always use python -m pip to upgrade pip
            upgrade_result = subprocess.run(
                [python_path, "-m", "pip", "install", "--upgrade", "pip"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False  # Don't fail on non-zero exit
            )
            
            # Even if there's an error message, pip might still be updated
            if upgrade_result.returncode != 0:
                print("Note: Pip upgrade may have had issues, but we'll continue with installation.")
                print(f"Pip error details: {upgrade_result.stderr}")
        else:
            # On Unix systems, we can use pip directly
            subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
            
        print("Installing project dependencies...")
        # Install the project in development mode
        if platform.system() == "Windows":
            # On Windows, use python -m pip for installation too
            install_result = subprocess.run(
                [python_path, "-m", "pip", "install", "-e", "."],
                check=True
            )
        else:
            subprocess.run([pip_path, "install", "-e", "."], check=True)
            
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\nError installing dependencies: {e}")
        print("\nFallback installation: Try running these commands manually:")
        print("1. Activate the virtual environment:")
        if platform.system() == "Windows":
            print("   venv\\Scripts\\activate")
            print("\n2. Then run:")
            print("   python -m pip install --upgrade pip")
            print("   python -m pip install -e .")
        else:
            print("   source venv/bin/activate")
            print("\n2. Then run:")
            print("   pip install --upgrade pip")
            print("   pip install -e .")
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