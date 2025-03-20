@echo off
REM Improved Windows launcher for the undetected Android emulator
REM This script handles Windows-specific quirks to ensure the emulator UI displays correctly

echo Starting Undetected Android Emulator...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found at venv\Scripts\activate.bat
    echo Will attempt to use system Python
)

REM Run the improved Windows launcher script
python improved_windows_launcher.py

REM If an error occurred, keep the window open
if %ERRORLEVEL% NEQ 0 (
    echo Launcher exited with errors. See logs for details.
    pause
)

exit /b 0