#!/bin/bash
# setup.sh - Setup script for Undetected Android Emulator
# Works on Mac and Linux systems

set -e  # Exit on error

echo "Setting up Undetected Android Emulator..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python 3.8+
if command_exists python3; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        echo "Error: Python 3.8+ is required. Found Python $PYTHON_VERSION"
        echo "Please install Python 3.8 or higher and try again."
        exit 1
    else
        echo "Found Python $PYTHON_VERSION"
    fi
else
    echo "Error: Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check for required system packages based on OS
SYSTEM_NAME=$(uname -s)
if [ "$SYSTEM_NAME" = "Linux" ]; then
    echo "Detected Linux system"
    
    # Check for package manager
    if command_exists apt-get; then
        echo "Installing required packages with apt..."
        sudo apt-get update
        sudo apt-get install -y python3-pip python3-venv qemu-system-x86 qemu-utils \
            libmagic1 python3-dev build-essential libffi-dev
    elif command_exists dnf; then
        echo "Installing required packages with dnf..."
        sudo dnf install -y python3-pip python3-virtualenv qemu-system-x86 qemu-img \
            file-libs python3-devel gcc gcc-c++ libffi-devel
    elif command_exists pacman; then
        echo "Installing required packages with pacman..."
        sudo pacman -Sy python-pip python-virtualenv qemu file python-devel base-devel libffi
    else
        echo "Warning: Unsupported Linux distribution. Please install the following packages manually:"
        echo "- Python 3.8+ with pip"
        echo "- QEMU (qemu-system-x86_64)"
        echo "- libmagic/file"
        echo "- Development tools for building Python extensions"
    fi
elif [ "$SYSTEM_NAME" = "Darwin" ]; then
    echo "Detected macOS system"
    
    # Check for Homebrew
    if command_exists brew; then
        echo "Installing required packages with Homebrew..."
        brew update
        brew install python qemu libmagic
    else
        echo "Homebrew not found. We recommend installing Homebrew (brew.sh) to manage dependencies."
        echo "Please install the following manually:"
        echo "- Python 3.8+"
        echo "- QEMU"
        echo "- libmagic"
    fi
else
    echo "Warning: Unsupported operating system. Please install required dependencies manually."
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -e .

echo
echo "Setup completed successfully!"
echo
echo "To run the emulator:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo
echo "2. Run the emulator with GUI:"
echo "   python main.py"
echo
echo "3. Or run in headless mode:"
echo "   python main.py --no-gui"
echo
echo "See 'python main.py --help' for more options."