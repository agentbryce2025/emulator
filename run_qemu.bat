@echo off
REM Direct QEMU launcher script for Windows
ECHO Starting Android Emulator with QEMU
ECHO ------------------------------
ECHO.

REM Get the path to the ISO file
SET IMG_DIR=%USERPROFILE%\.config\undetected-emulator\images
SET ISO_FILE=%IMG_DIR%\android-x86_64-9.0-r2.iso
SET DISK_FILE=%IMG_DIR%\auto_data.img

REM Check if files exist
IF NOT EXIST "%ISO_FILE%" (
    ECHO Error: ISO file not found at %ISO_FILE%
    ECHO Please run the emulator first to download/import an ISO.
    EXIT /B 1
)

IF NOT EXIST "%DISK_FILE%" (
    ECHO Warning: Disk image not found, trying to use a different one.
    FOR %%F IN (%IMG_DIR%\*.img) DO (
        SET DISK_FILE=%%F
        GOTO FOUND_DISK
    )
    ECHO Error: No disk image found. Run the emulator first to create one.
    EXIT /B 1
)

:FOUND_DISK
ECHO Using:
ECHO - ISO: %ISO_FILE%
ECHO - Disk: %DISK_FILE%
ECHO.

REM Run QEMU with appropriate parameters for Windows
"C:\Program Files\qemu\qemu-system-x86_64.exe" ^
    -memory 2048 ^
    -smp 4 ^
    -hda "%DISK_FILE%" ^
    -cpu host ^
    -vga std ^
    -display sdl ^
    -net user ^
    -usb ^
    -usbdevice tablet ^
    -cdrom "%ISO_FILE%"

ECHO.
ECHO QEMU has exited. Press any key to close this window.
PAUSE > NUL