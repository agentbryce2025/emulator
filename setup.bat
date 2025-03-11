@echo off
REM setup.bat - Setup script for Undetected Android Emulator (Windows)

echo Setting up Undetected Android Emulator...

REM Check for Python 3.8+
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python not found. Please install Python 3.8 or higher.
    echo Visit: https://www.python.org/downloads/
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
echo Found Python %PYTHON_VERSION%

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
pip install --upgrade pip
pip install -e .

REM Note about QEMU
echo.
echo IMPORTANT: This project requires QEMU to run.
echo Please download and install QEMU for Windows if you haven't already:
echo https://www.qemu.org/download/#windows

echo.
echo Setup completed successfully!
echo.
echo To run the emulator:
echo 1. Activate the virtual environment:
echo    call venv\Scripts\activate.bat
echo.
echo 2. Run the emulator with GUI:
echo    python main.py
echo.
echo 3. Or run in headless mode:
echo    python main.py --no-gui
echo.
echo See 'python main.py --help' for more options.

pause