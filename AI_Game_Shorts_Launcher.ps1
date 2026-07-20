<#
.SYNOPSIS
    AI Game Shorts - One Click Launcher (PowerShell)
.DESCRIPTION
    Auto-setup + Menu-driven launcher for AI Game Shorts pipeline
#>

Write-Host @"
===============================================
   AI Game Shorts - One Click Launcher 🎮
===============================================

"@ -ForegroundColor Cyan

# --- Functions ---
function Check-Command($cmd) {
    try { Get-Command $cmd -ErrorAction Stop | Out-Null; return $true }
    catch { return $false }
}

function Install-FFmpeg {
    Write-Host "[DOWNLOAD] FFmpeg download kar raha hoon..." -ForegroundColor Yellow
    $ffmpegDir = Join-Path $env:USERPROFILE "ffmpeg"
    $zipPath = Join-Path $env:TEMP "ffmpeg.zip"
    
    if (-not (Test-Path $ffmpegDir)) {
        New-Item -ItemType Directory -Path $ffmpegDir -Force | Out-Null
        
        # Download FFmpeg
        $url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        Write-Host "[DOWNLOAD] $url" -ForegroundColor Gray
        Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
        
        # Extract
        Write-Host "[EXTRACT] Extracting..." -ForegroundColor Yellow
        Expand-Archive -Path $zipPath -DestinationPath $ffmpegDir -Force
        
        # Find ffmpeg.exe
        $ffmpegExe = Get-ChildItem -Path $ffmpegDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
        if ($ffmpegExe) {
            $binDir = $ffmpegExe.Directory.FullName
            # Add to PATH
            [Environment]::SetEnvironmentVariable("Path", $env:Path + ";" + $binDir, "User")
            $env:Path += ";" + $binDir
            Write-Host "[DONE] FFmpeg install ho gaya! PATH mein add kar diya." -ForegroundColor Green
        }
    }
}

function Show-Menu {
    Clear-Host
    Write-Host @"
╔══════════════════════════════════════════════════╗
║         AI Game Shorts - Main Menu              ║
╠══════════════════════════════════════════════════╣
║  1) 🎬  Short Banao (manual)                    ║
║  2) 📦  Batch Process (sab videos)              ║
║  3) 📊  Analytics Dekho                         ║
║  4) 🧠  Learning System Chalao                  ║
║  5) ⚙️   Setup Wizard                           ║
║  6) 🔑  .env file edit karo                     ║
║  7) ❌  Exit                                    ║
╚══════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan
    return Read-Host "Choose [1-7]"
}

# --- Main ---
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $rootDir

# 1. Check Python
if (-not (Check-Command "python")) {
    Write-Host "[ERROR] Python installed nahi hai!" -ForegroundColor Red
    Write-Host "        Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "        'Add Python to PATH' check karna mat bhoolna!"
    Read-Host "Enter dabao exit karne ke liye"
    exit 1
}
$pyVer = python --version
Write-Host "[OK] Python: $pyVer" -ForegroundColor Green

# 2. Check/Install FFmpeg
if (-not (Check-Command "ffmpeg")) {
    Write-Host "[WARN] FFmpeg nahi mila. Auto-install karun?" -ForegroundColor Yellow
    $choice = Read-Host "Install FFmpeg? (Y/N, default=Y)"
    if ($choice -eq "" -or $choice -eq "Y" -or $choice -eq "y") {
        Install-FFmpeg
    } else {
        Write-Host "[WARN] FFmpeg ke bina audio/caption kaam nahi karega." -ForegroundColor Red
    }
} else {
    Write-Host "[OK] FFmpeg: $(ffmpeg -version | Select-Object -First 1)" -ForegroundColor Green
}

# 3. Setup .env
if (-not (Test-Path ".env")) {
    Write-Host "[INFO] .env file nahi mila. .env.example se bana raha hoon..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env" -Force
    Write-Host "[WARN] .env file create ho gaya! Abhi API keys daal do:" -ForegroundColor Yellow
    Write-Host "        - AI_GAME_SHORTS_OPENAI_KEY=sk-your-key" -ForegroundColor White
    Write-Host "        - AI_GAME_SHORTS_GEMINI_KEY=your-key" -ForegroundColor White
    Start-Process notepad.exe -ArgumentList ".env"
    Read-Host "Enter dabao jab keys daal do"
}

# 4. Create & activate venv
if (-not (Test-Path "venv")) {
    Write-Host "[INFO] Virtual environment bana raha hoon..." -ForegroundColor Yellow
    python -m venv venv
}
$venvActivate = Join-Path $rootDir "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
    Write-Host "[OK] Virtual env activated!" -ForegroundColor Green
} else {
    & "venv\Scripts\activate.bat"
}

# 5. Install dependencies
Write-Host "[INFO] Dependencies install kar raha hoon..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "[DONE] Sab dependencies install ho gaye!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Dependencies install mein problem!" -ForegroundColor Red
    Read-Host "Enter dabao"
    exit 1
}

# 6. Check sample videos
$videos = Get-ChildItem "sample_data\*.mp4" -ErrorAction SilentlyContinue
if ($videos.Count -eq 0) {
    Write-Host "[WARN] sample_data mein koi video nahi hai!" -ForegroundColor Yellow
    Write-Host "      Wahan apni gameplay video daalo." -ForegroundColor Yellow
    Start-Process "sample_data"
    Read-Host "Video daal do, phir Enter dabao"
}

# 7. Menu loop
do {
    $choice = Show-Menu
    switch ($choice) {
        "1" {
            $videos = Get-ChildItem "sample_data\*.mp4" -ErrorAction SilentlyContinue
            if ($videos.Count -gt 0) {
                Write-Host "`nSample videos:" -ForegroundColor Cyan
                for ($i = 0; $i -lt $videos.Count; $i++) {
                    Write-Host "  $i) $($videos[$i].Name)"
                }
                $idx = Read-Host "`nVideo number daalo"
                if ($idx -match '^\d+$' -and [int]$idx -lt $videos.Count) {
                    python scripts\run_pipeline.py create --video $videos[$idx].FullName
                }
            } else {
                Write-Host "[ERROR] sample_data mein koi video nahi!" -ForegroundColor Red
            }
            Read-Host "`nEnter dabao..."
        }
        "2" { python scripts\run_pipeline.py batch; Read-Host "Enter dabao..." }
        "3" { python scripts\run_pipeline.py analytics; Read-Host "Enter dabao..." }
        "4" { python scripts\run_pipeline.py learn; Read-Host "Enter dabao..." }
        "5" { python scripts\run_pipeline.py setup; Read-Host "Enter dabao..." }
        "6" { Start-Process notepad.exe -ArgumentList ".env"; Read-Host "Enter dabao..." }
    }
} until ($choice -eq "7")

Write-Host "`nBye! 👋" -ForegroundColor Cyan
