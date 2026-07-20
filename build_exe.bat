@echo off
title AI Game Shorts - Building Installer
color 0A
echo ===============================================
echo   Building AI Game Shorts Standalone EXE
echo ===============================================
echo.

:: Activate venv
echo [1/5] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install PyInstaller
echo [2/5] Ensuring PyInstaller is installed...
pip install pyinstaller --quiet

:: Clean old builds
echo [3/5] Cleaning old build files...
if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "build" rmdir /s /q "build" >nul 2>&1

:: Copy FFmpeg to ffmpeg_bin
echo [4/5] FFmpeg - OK (%windir%\ffmpeg_bin\ exists)

:: Run PyInstaller
echo [5/5] Building AI_Game_Shorts.exe (this may take 5-15 minutes)...
pyinstaller ai_game_shorts.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed! Error code: %errorlevel%
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   BUILD COMPLETE! 
echo ===============================================
echo.
echo Standalone exe folder: dist\AI_Game_Shorts\
echo Run: dist\AI_Game_Shorts\AI_Game_Shorts.exe
echo.
echo To create a single-file installer:
echo   1. Download Inno Setup from https://jrsoftware.org/isdl.php
echo   2. Open installer.iss with Inno Setup
echo   3. Click Compile (or Build ^> Compile)
echo.
pause
