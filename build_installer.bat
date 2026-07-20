@echo off
title AI Game Shorts - Complete Installer Builder
color 0B
setlocal enabledelayedexpansion

echo ===============================================
echo    AI Game Shorts - Installer Builder v1.0
echo    Poore software ka ek click mein build!
echo ===============================================
echo.

:: Check admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Admin rights nahi hai! Kuch features kaam nahi karenge.
    echo        Isko "Run as Administrator" se chalao.
    echo.
    choice /c CN /m "Continue ya Cancel? "
    if errorlevel 2 exit /b 1
)

set BUILD_DIR=%CD%
set VENV_DIR=%BUILD_DIR%\venv
set DIST_DIR=%BUILD_DIR%\dist
set INSTALLER_DIR=%BUILD_DIR%\installer_output

:: ===== STEP 1: Environment Setup =====
echo.
echo [STEP 1/5] Python aur virtual env check...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python nahi mila!
    echo         Download: https://www.python.org/downloads/
    echo         "Add Python to PATH" check karna mat bhoolna!
    pause
    exit /b 1
)
python --version
echo.

if not exist "%VENV_DIR%" (
    echo [INFO] Virtual env bana raha hoon...
    python -m venv "%VENV_DIR%"
)
echo.

:: ===== STEP 2: Install Requirements =====
echo [STEP 2/5] Dependencies install kar raha hoon...
call "%VENV_DIR%\Scripts\activate.bat"
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet
echo [DONE] Dependencies ready!
echo.

:: ===== STEP 3: Download FFmpeg =====
echo [STEP 3/5] FFmpeg download kar raha hoon...
if not exist "ffmpeg_bin\ffmpeg.exe" (
    if not exist "ffmpeg_bin" mkdir ffmpeg_bin
    echo Downloading FFmpeg from gyan.dev...
    powershell -Command "try { $url='https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'; $wc = New-Object System.Net.WebClient; Write-Host 'Downloading...'; $wc.DownloadFile($url, \"$env:TEMP\ffmpeg.zip\"); Write-Host 'Extracting...'; Expand-Archive \"$env:TEMP\ffmpeg.zip\" \"$env:TEMP\ffmpeg_extracted\" -Force; Get-ChildItem \"$env:TEMP\ffmpeg_extracted\" -Recurse -Include 'ffmpeg.exe','ffprobe.exe' | %%{ Copy-Item $_.FullName 'ffmpeg_bin\'.$_.Name -Force }; Write-Host 'FFmpeg ready!' } catch { Write-Host 'FFmpeg download failed - will use system FFmpeg' }"
) else (
    echo [OK] FFmpeg already downloaded.
)
echo.

:: ===== STEP 4: Build EXE with PyInstaller =====
echo [STEP 4/5] AI_Game_Shorts.exe build kar raha hoon...
echo         Ye 5-15 minute le sakta hai. Chai bana lo ☕
echo.

if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "build" rmdir /s /q "build"

pyinstaller ai_game_shorts.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build fail ho gaya!
    echo         Common fixes:
    echo          1. Visual C++ Redistributable install karo
    echo          2. torch DLL error ignore karo (whisper API use karega)
    pause
    exit /b 1
)
echo [DONE] EXE build complete!
echo.

:: ===== Check Inno Setup =====
set INNO_PATH=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe

if "%INNO_PATH%"=="" (
    :: Check for NSIS
    set NSIS_PATH=
    if exist "C:\Program Files (x86)\NSIS\makensis.exe" set NSIS_PATH=C:\Program Files (x86)\NSIS\makensis.exe
    if exist "C:\Program Files\NSIS\makensis.exe" set NSIS_PATH=C:\Program Files\NSIS\makensis.exe
    
    if not "!NSIS_PATH!"=="" (
        echo [STEP 5/5] NSIS installer bana raha hoon...
        "!NSIS_PATH!" installer.nsi
        echo [DONE] NSIS installer ready: installer_output\AI_Game_Shorts_Setup.exe
    ) else (
        echo [STEP 5/5] Inno Setup / NSIS nahi mila.
        echo.
        echo ===============================================
        echo   PORTABLE BUILD READY!
        echo ===============================================
        echo.
        echo Portable folder: %DIST_DIR%\AI_Game_Shorts\
        echo Run karo: %DIST_DIR%\AI_Game_Shorts\AI_Game_Shorts.exe
        echo.
        echo Proper .exe installer banane ke liye:
        echo   1. Download Inno Setup: https://jrsoftware.org/isdl.php
        echo   2. Install karo
        echo   3. Isko run karo dobara - automatic pick karega
        echo.
        echo YA installer.iss ko Inno Setup mein kholo aur Compile karo
    )
) else (
    echo [STEP 5/5] Inno Setup se installer bana raha hoon...
    "%INNO_PATH%" installer.iss
    echo [DONE] Installer ready!
)

echo.
echo ===============================================
echo   BUILD COMPLETED! Sab kuch ready hai!  🎉
echo ===============================================
echo.
echo Output files:
echo   - Portable: %DIST_DIR%\AI_Game_Shorts\
echo   - Installer: %INSTALLER_DIR%\AI_Game_Shorts_Setup_*.exe
echo.
pause
