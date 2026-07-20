@echo off
title AI Game Shorts - One Click Setup & Run
color 0A
setlocal enabledelayedexpansion

echo ===============================================
echo    AI Game Shorts - One Click Launcher
echo ===============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python installed nahi hai!
    echo         Download karo: https://www.python.org/downloads/
    echo         "Add to PATH" check karna mat bhoolna!
    pause
    exit /b 1
)
python --version
echo.

:: Check FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] FFmpeg nahi mila. Download kar raha hoon...
    echo.
    :: Download FFmpeg automatically
    curl -L -o "%TEMP%\ffmpeg-release-full.7z" "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z"
    if exist "%TEMP%\ffmpeg-release-full.7z" (
        echo [INFO] FFmpeg download ho gaya. Extract kar raha hoon...
        :: Try to use tar (built into Windows 10+)
        tar -xf "%TEMP%\ffmpeg-release-full.7z" -C "%TEMP%\ffmpeg_build" >nul 2>&1
        if %errorlevel% neq 0 (
            echo [INFO] 7-Zip se extract kar raha hoon...
            powershell -Command "Expand-Archive -Path '%TEMP%\ffmpeg-release-full.7z' -DestinationPath '%TEMP%\ffmpeg_build' -Force" >nul 2>&1
        )
    )
    echo [WARN] FFmpeg manual install karo ya 'setup_and_run.ps1' use karo
    echo        Download: https://ffmpeg.org/download.html
    pause
    exit /b 1
)
ffmpeg -version | findstr "ffmpeg"
echo.

:: Create .env if missing
if not exist ".env" (
    echo [INFO] .env file nahi mila. .env.example se bana raha hoon...
    copy ".env.example" ".env" >nul
    echo [WARN] .env file create ho gaya hai!
    echo        Isme apni API keys daalni hain:
    echo        - OpenAI key: AI_GAME_SHORTS_OPENAI_KEY=sk-your-key
    echo        - Gemini key: AI_GAME_SHORTS_GEMINI_KEY=your-key
    echo.
    notepad ".env"
    echo.
    pause
)

:: Create virtual environment
if not exist "venv" (
    echo [INFO] Virtual environment bana raha hoon...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Virtual environment create nahi ho paya!
        pause
        exit /b 1
    )
    echo [DONE] Virtual environment ready!
) else (
    echo [OK] Virtual environment already exists.
)
echo.

:: Activate venv and install dependencies
echo [INFO] Dependencies install kar raha hoon...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Virtual environment activate nahi ho paya!
    pause
    exit /b 1
)
pip install -r requirements.txt --quiet
echo [DONE] Dependencies installed!
echo.

:: Check for sample videos
dir sample_data\*.mp4 >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] sample_data mein koi video nahi hai!
    echo        Wahan apni gameplay video daalo aur dobara run karo.
    echo.
    explorer sample_data\
    echo.
    echo 1 minute ruko, video daal do, phir koi bhi key press karo...
    pause >nul
)

:: Menu
:menu
cls
echo ===============================================
echo    AI Game Shorts - Kya karna chahte ho?
echo ===============================================
echo.
echo  1) Short Banao (manual - ek video select karo)
echo  2) Batch Process (sab videos process karo)
echo  3) Analytics Dekho
echo  4) Learning System Chalao
echo  5) Setup Wizard
echo  6) .env file edit karo
echo  7) Exit
echo.
set /p choice="Choose [1-7]: "

if "%choice%"=="1" (
    echo.
    echo Sample videos:
    dir sample_data\*.mp4 /b 2>nul
    if exist "sample_data\*.mp4" (
        echo.
        set /p video="Video ka naam daalo (sample_data se): "
        python scripts\run_pipeline.py create --video "sample_data\!video!"
    ) else (
        echo [ERROR] sample_data mein koi video nahi!
    )
    pause
    goto menu
)
if "%choice%"=="2" (
    python scripts\run_pipeline.py batch
    pause
    goto menu
)
if "%choice%"=="3" (
    python scripts\run_pipeline.py analytics
    pause
    goto menu
)
if "%choice%"=="4" (
    python scripts\run_pipeline.py learn
    pause
    goto menu
)
if "%choice%"=="5" (
    python scripts\run_pipeline.py setup
    pause
    goto menu
)
if "%choice%"=="6" (
    notepad .env
    goto menu
)
if "%choice%"=="7" (
    exit /b 0
)
goto menu
