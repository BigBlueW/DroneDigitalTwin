<#
.SYNOPSIS
    DroneDigitalTwin - One-Click Windows Setup Script (Optimized)

.DESCRIPTION
    Automated setup for the Drone Digital Twin (Project AirSim) development environment.
    This version includes robust detection to avoid redundant installations and fixes
    pathing issues for team collaborations.

.NOTES
    Usage:  Right-click this file -> "Run with PowerShell"
            OR from an elevated PowerShell terminal:
                Set-ExecutionPolicy Bypass -Scope Process -Force
                .\setup_windows.ps1
#>

# ============================================================================
# Configuration
# ============================================================================
$ErrorActionPreference = "Stop"

$REPO_ROOT       = $PSScriptRoot
$VENV_DIR        = Join-Path $REPO_ROOT "venv"
$PYPROJECT_DIR   = Join-Path $REPO_ROOT "client\python\projectairsim"
$REQUIREMENTS    = Join-Path $PYPROJECT_DIR "requirements.txt"
$BUILD_CMD       = Join-Path $REPO_ROOT "build.cmd"
$BLOCKS_UPROJECT = Join-Path $REPO_ROOT "unreal\Blocks\Blocks.uproject"
$PACKAGES_DIR    = Join-Path $REPO_ROOT "packages"

# Unreal Engine expected install location
$UE_EXPECTED_ROOT = "C:\Program Files\Epic Games\UE_5.7"

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Banner {
    param([string]$Message)
    $line = "=" * 70
    Write-Host ""
    Write-Host $line -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host $line -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$StepNum, [string]$Message)
    Write-Host "[$StepNum] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message -ForegroundColor White
}

function Write-OK {
    param([string]$Message)
    Write-Host "  [OK] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Hint {
    param([string]$Message)
    Write-Host "  [SKIP] " -ForegroundColor DarkGreen -NoNewline
    Write-Host $Message -ForegroundColor DarkGreen
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [!!] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "  [FAIL] " -ForegroundColor Red -NoNewline
    Write-Host $Message -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [i] " -ForegroundColor DarkCyan -NoNewline
    Write-Host $Message
}

function Test-CommandExists {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Pause-ForUser {
    param([string]$Message = "Press ENTER to continue...")
    Write-Host ""
    Write-Host "  >> $Message" -ForegroundColor Magenta
    Read-Host
}

# ============================================================================
# Pre-flight: Must run from repo root
# ============================================================================

Write-Banner "DroneDigitalTwin - Automated Windows Setup"

if (-not (Test-Path (Join-Path $REPO_ROOT "CMakeLists.txt"))) {
    Write-Err "This script must be run from the DroneDigitalTwin repository root."
    Write-Err "Current directory: $REPO_ROOT"
    exit 1
}

Write-Info "Repository root: $REPO_ROOT"

# ============================================================================
# STEP 1: Check / Install Visual Studio 2022
# ============================================================================

Write-Banner "Step 1/6: Visual Studio 2022 (C++ Build Tools)"

$vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vsInstalled = $false

if (Test-Path $vsWhere) {
    # Specifically looking for 17.x (VS 2022) with C++ tools
    $vsPath = & $vsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
    if ($vsPath) {
        $vsInstalled = $true
        Write-Hint "Visual Studio 2022 with C++ tools already installed at: $vsPath"
    }
}

if (-not $vsInstalled) {
    Write-Step "1" "Installing Visual Studio 2022 Community via winget..."
    try {
        winget install Microsoft.VisualStudio.2022.Community --override "--wait --quiet --add Microsoft.VisualStudio.Workload.NativeDesktop --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.Component.MSBuild" --accept-source-agreements --accept-package-agreements
        Write-OK "Visual Studio 2022 installation completed."
    } catch {
        Write-Err "winget installation failed. Please install manually: https://visualstudio.microsoft.com/downloads/"
        Pause-ForUser "Install VS 2022 manually, then press ENTER..."
    }
}

# ============================================================================
# STEP 2: Check / Install CMake & Ninja
# ============================================================================

Write-Banner "Step 2/6: CMake & Ninja (Build System)"

# --- CMake ---
if (Test-CommandExists "cmake") {
    $cmakeVer = (cmake --version | Select-Object -First 1)
    Write-Hint "CMake already installed: $cmakeVer"
} else {
    Write-Step "2a" "Installing CMake via winget..."
    winget install Kitware.CMake --accept-source-agreements --accept-package-agreements
    Write-OK "CMake installed."
}

# --- Ninja ---
if (Test-CommandExists "ninja") {
    $ninjaVer = (ninja --version 2>$null)
    Write-Hint "Ninja build tool already installed: v$ninjaVer"
} else {
    Write-Step "2b" "Installing Ninja via winget..."
    winget install Ninja-build.Ninja --accept-source-agreements --accept-package-agreements
    Write-OK "Ninja installed."
}

# ============================================================================
# STEP 3: Check / Install Python 3.9 (Strict Versioning)
# ============================================================================

Write-Banner "Step 3/6: Python 3.9 (Required for compatibility)"

$python39Exe = $null

# Search for Python 3.9 in standard locations
$searchPaths = @(
    "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
    "$env:ProgramFiles\Python39\python.exe",
    "C:\Python39\python.exe"
)

foreach ($path in $searchPaths) {
    if (Test-Path $path) {
        $python39Exe = $path
        Write-Hint "Python 3.9 already found at: $path"
        break
    }
}

if ($null -eq $python39Exe) {
    # Check if a 'python' command exists and is 3.9
    if (Test-CommandExists "python") {
        $ver = python --version 2>&1
        if ($ver -match "3\.9\.") {
            $python39Exe = (Get-Command python).Source
            Write-Hint "System 'python' command is already version 3.9: $ver"
        }
    }
}

if ($null -eq $python39Exe) {
    Write-Step "3" "Installing Python 3.9 via winget..."
    try {
        winget install Python.Python.3.9 --accept-source-agreements --accept-package-agreements
        Write-OK "Python 3.9 installed."
        # Refresh executable path
        $python39Exe = "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe"
        if (-not (Test-Path $python39Exe)) {
            $python39Exe = "$env:ProgramFiles\Python39\python.exe"
        }
    } catch {
        Write-Err "Failed to install Python 3.9. Please install manually."
        Pause-ForUser "Install Python 3.9 manually, then press ENTER..."
        $python39Exe = "python" # Fallback
    }
}

# ============================================================================
# STEP 4: Unreal Engine 5.7 & UE_ROOT
# ============================================================================

Write-Banner "Step 4/6: Unreal Engine 5.7"

$ueRoot = [System.Environment]::GetEnvironmentVariable("UE_ROOT", "User")
if (-not $ueRoot) { $ueRoot = $env:UE_ROOT }

if ($ueRoot -and (Test-Path $ueRoot)) {
    Write-Hint "UE_ROOT already set to: $ueRoot"
} else {
    Write-Warn "UE_ROOT environment variable is missing or invalid."
    
    # Try finding it in default locations
    $ueSearch = @(
        "C:\Program Files\Epic Games\UE_5.7",
        "D:\Program Files\Epic Games\UE_5.7",
        "D:\Epic Games\UE_5.7"
    )
    foreach ($p in $ueSearch) {
        if (Test-Path $p) {
            $ueRoot = $p
            Write-OK "Found UE 5.7 automatically at: $p"
            break
        }
    }

    if (-not $ueRoot) {
        Write-Info "UE 5.7 not found. Opening download page..."
        Start-Process "https://www.unrealengine.com/en-US/download"
        Pause-ForUser "After installing UE 5.7, press ENTER..."
        $ueRoot = Read-Host "  Please paste the UE 5.7 install path (e.g., C:\Program Files\Epic Games\UE_5.7)"
    }

    if ($ueRoot -and (Test-Path $ueRoot)) {
        [System.Environment]::SetEnvironmentVariable("UE_ROOT", $ueRoot, "User")
        $env:UE_ROOT = $ueRoot
        Write-OK "UE_ROOT has been set successfully."
    }
}

# ============================================================================
# STEP 5: Python Virtual Environment & Dependencies
# ============================================================================

Write-Banner "Step 5/6: Python Virtual Environment"

if (Test-Path $VENV_DIR) {
    # Validate if venv is broken (often happens if folder is moved/renamed)
    $isBroken = $false
    $activateBat = Join-Path $VENV_DIR "Scripts\activate.bat"
    if (Test-Path $activateBat) {
        $batContent = Get-Content $activateBat
        # Check if the internal VIRTUAL_ENV path matches current location
        if ($batContent -match 'set "VIRTUAL_ENV=(.*)"') {
            $venvPathInBat = $Matches[1].Trim()
            # Resolve paths for comparison
            $actualPath = (Resolve-Path $VENV_DIR).Path
            if ($venvPathInBat -ne $actualPath) {
                Write-Warn "Detected broken virtual environment (moved from $venvPathInBat to $actualPath)."
                $isBroken = $true
            }
        }
    } else {
        $isBroken = $true
    }

    if ($isBroken) {
        Write-Step "5a" "Re-creating broken virtual environment..."
        Remove-Item -Recurse -Force $VENV_DIR
        & $python39Exe -m venv $VENV_DIR
        Write-OK "Virtual environment re-created."
    } else {
        Write-Hint "Virtual environment already exists and is healthy at: $VENV_DIR"
    }
} else {
    Write-Step "5a" "Creating virtual environment..."
    & $python39Exe -m venv $VENV_DIR
    Write-OK "Virtual environment created at: $VENV_DIR"
}

# Activation
Write-Step "5b" "Activating environment and installing dependencies..."
$activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
& $activateScript

# Fix Pathing: Change directory to the package folder so '-e .' resolves correctly
Push-Location $PYPROJECT_DIR
try {
    Write-Info "Installing dependencies from requirements.txt..."
    & python -m pip install --upgrade pip --quiet
    & pip install -r requirements.txt --quiet
    Write-OK "Dependencies installed successfully."
} catch {
    Write-Err "Dependency installation failed: $_"
}
Pop-Location

# ============================================================================
# STEP 6: Build C++ Simulation Libraries
# ============================================================================

Write-Banner "Step 6/6: Build Simulation Libraries"

$buildNeeded = $true
if (Test-Path $PACKAGES_DIR) {
    Write-Info "Existing 'packages' folder detected. Simulation libs might already be built."
    $buildNeeded = $false
}

$prompt = if ($buildNeeded) { "Start the C++ build now? (y/n)" } else { "Re-run the C++ build? (y/n) [Recommended: n]" }
$choice = Read-Host "  $prompt"

if ($choice -eq 'y' -or $choice -eq 'Y') {
    Push-Location $REPO_ROOT
    cmd.exe /c $BUILD_CMD all
    Pop-Location
} else {
    Write-Hint "Build skipped."
}

Write-Banner "Setup Complete! Happy Flying!"
Write-Info "Documentation: !note.md"
Write-Info "To start working, run: .\venv\Scripts\activate"
Write-Host ""
