@echo off
chcp 65001 > nul
title Koemoji Installer
setlocal enabledelayedexpansion

rem Change working directory to the script location
cd /d "%~dp0"

echo ===================================================
echo      Koemoji - Installation Setup
echo ===================================================
echo.

rem Create logs folder
if not exist "logs" mkdir logs
set "log_file=logs\install_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "log_file=%log_file: =0%"

echo Installation log: %log_file%
echo.

rem Check if Python exists
echo Checking Python...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. >> "%log_file%"
    echo Python is not installed.
    echo.
    echo You need to install Python 3.8 or later.
    echo Please download and install Python from:
    echo https://www.python.org/downloads/
    echo.
    echo Note: Make sure to check "Add Python to PATH" during installation.
    echo.
    echo Run this setup again after installing Python.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%a in ('python --version 2^>^&1') do set pyver=%%a
    echo [INFO] Python version %pyver% found. >> "%log_file%"
    echo Python version %pyver% found.
    echo.
)

rem Install required libraries
echo Installing required libraries...
echo [INFO] Installing libraries with pip... >> "%log_file%"

python -m pip install --upgrade pip >> "%log_file%" 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Failed to upgrade pip. Continuing... >> "%log_file%"
    echo Warning: Failed to upgrade pip, but continuing.
)

echo Installing libraries...
python -m pip install -r requirements.txt >> "%log_file%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install libraries. >> "%log_file%"
    echo Error: Failed to install required libraries.
    echo Please check the log file: %log_file%
    pause
    exit /b 1
) else (
    echo [INFO] Required libraries installed successfully. >> "%log_file%"
    echo Required libraries installed successfully.
    echo.
)

rem Create desktop shortcut
echo Creating desktop shortcut...
echo [INFO] Creating desktop shortcut... >> "%log_file%"

rem Use environment variable for Desktop path instead of hardcoded path
set "shortcut=%USERPROFILE%\Desktop\Koemoji.lnk"
set "app_path=%~dp0start_koemoji.bat"
set "icon_path=%~dp0resources\koemoji-logo256x256.ico"

if not exist "%icon_path%" (
    echo [WARNING] Icon file not found: %icon_path% >> "%log_file%"
    echo Warning: Icon file not found. Using default icon.
    set "icon_path=%~dp0start_koemoji.bat"
)

rem Create shortcut using VBScript
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%shortcut%" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%app_path%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%~dp0" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Koemoji - Audio/Video Transcription Application" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "%icon_path%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript /nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

if exist "%shortcut%" (
    echo [INFO] Desktop shortcut created successfully: %shortcut% >> "%log_file%"
    echo Desktop shortcut created successfully.
) else (
    echo [WARNING] Failed to create shortcut. >> "%log_file%"
    echo Warning: Failed to create shortcut.
)

echo.
echo ===================================================
echo      Installation Complete!
echo ===================================================
echo.
echo Click the "Koemoji" icon on your desktop
echo to launch the application.
echo.
echo On first launch, the Whisper model will be downloaded.
echo This may take some time depending on the size.
echo.
echo Would you like to start the application now?
choice /c YN /m "Press Y to launch now or N to exit"

if %errorlevel% equ 1 (
    echo.
    echo Starting Koemoji...
    call "%~dp0start_koemoji.bat"
) else (
    echo.
    echo Installation complete. You can launch from the "Koemoji" icon on your desktop.
)

echo.
pause
exit /b 0
