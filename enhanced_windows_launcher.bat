@echo off
REM Enhanced Windows Launcher for the Undetected Android Emulator
ECHO Undetected Android Emulator - Enhanced Windows Launcher
ECHO ----------------------------------------
ECHO.

REM Check Python installation
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python not found. Please install Python 3.7 or higher.
    ECHO You can download it from https://www.python.org/downloads/
    PAUSE
    EXIT /B 1
)

ECHO Checking and creating environment...
IF NOT EXIST venv (
    ECHO Creating Python virtual environment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        ECHO Error creating virtual environment. Please install venv with:
        ECHO python -m pip install virtualenv
        PAUSE
        EXIT /B 1
    )
)

ECHO Activating virtual environment...
CALL venv\Scripts\activate
IF %ERRORLEVEL% NEQ 0 (
    ECHO Error activating virtual environment.
    PAUSE
    EXIT /B 1
)

ECHO Installing required packages...
pip install -e . >nul 2>&1

:Start
ECHO.
ECHO Choose launch option:
ECHO 1 - Launch with standard GUI (Recommended first try)
ECHO 2 - Launch with direct QEMU (For QEMU window issues)
ECHO 3 - Troubleshoot and fix common issues
ECHO 4 - Exit
ECHO.

SET /P OPTION="Enter option (1-4): "

IF "%OPTION%"=="1" (
    ECHO.
    ECHO Launching emulator with standard GUI...
    python main.py
    GOTO End
)

IF "%OPTION%"=="2" (
    ECHO.
    ECHO Launching emulator with direct QEMU...
    ECHO Note: You should have run the GUI at least once to set up images.
    python direct_launch.py
    GOTO End
)

IF "%OPTION%"=="3" (
    ECHO.
    ECHO Running troubleshooter...
    ECHO 1. Fixing issues in emulator core...
    python fix_emulator.py
    ECHO.
    ECHO 2. Applying Windows-specific GUI fixes...
    python windows_gui_fix_fixed.py
    ECHO.
    ECHO Done! Try launching the emulator again with option 1.
    PAUSE
    GOTO Start
)

IF "%OPTION%"=="4" (
    ECHO Exiting...
    GOTO End
)

ECHO Invalid option selected.

:End
ECHO.
ECHO Thank you for using the Undetected Android Emulator.
PAUSE
