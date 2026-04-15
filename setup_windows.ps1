<#
.SYNOPSIS
    DroneDigitalTwin - One-Click Windows Setup Script

.DESCRIPTION
    Automated setup for the Drone Digital Twin (Project AirSim) development environment.
    This script will:
      1. Check and install required tools (Visual Studio 2022, CMake, Ninja, Python 3.9)
      2. Guide the user through Unreal Engine 5.7 installation (manual step)
      3. Create a Python virtual environment and install all dependencies
      4. Set the UE_ROOT environment variable
      5. Build the C++ simulation libraries and Unreal plugin (build.cmd all)

    NOTE: This script is designed for Windows only.
    Run this script from the repository root directory.

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
$REQUIREMENTS    = Join-Path $REPO_ROOT "client\python\projectairsim\requirements.txt"
$PYPROJECT_DIR   = Join-Path $REPO_ROOT "client\python\projectairsim"
$BUILD_CMD       = Join-Path $REPO_ROOT "build.cmd"
$BLOCKS_UPROJECT = Join-Path $REPO_ROOT "unreal\Blocks\Blocks.uproject"

# Unreal Engine expected install location
$UE_EXPECTED_ROOT = "C:\Program Files\Epic Games\UE_5.7"

# Visual Studio Installer workload IDs
$VS_WORKLOADS = @(
    "--add Microsoft.VisualStudio.Workload.NativeDesktop",
    "--add Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
    "--add Microsoft.VisualStudio.Component.Windows11SDK.22621"
)

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
    $vsPath = & $vsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
    if ($vsPath) {
        $vsInstalled = $true
        Write-OK "Visual Studio 2022 with C++ tools found at: $vsPath"
    }
}

if (-not $vsInstalled) {
    Write-Warn "Visual Studio 2022 with C++ Desktop Development workload NOT found."
    Write-Info ""
    Write-Info "Option A (Recommended): Install via winget (auto):"
    Write-Info "  winget install Microsoft.VisualStudio.2022.Community --override ""--wait --add Microsoft.VisualStudio.Workload.NativeDesktop"""
    Write-Info ""
    Write-Info "Option B: Download manually from:"
    Write-Info "  https://visualstudio.microsoft.com/downloads/"
    Write-Info "  Select 'Desktop development with C++' workload during install."
    Write-Info ""

    $choice = Read-Host "  Install via winget now? (y/n)"
    if ($choice -eq 'y' -or $choice -eq 'Y') {
        Write-Step "1a" "Installing Visual Studio 2022 Community via winget..."
        Write-Warn "This may take 10-30 minutes. Do NOT close this window."
        try {
            winget install Microsoft.VisualStudio.2022.Community --override "--wait --quiet --add Microsoft.VisualStudio.Workload.NativeDesktop --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.Component.MSBuild" --accept-source-agreements --accept-package-agreements
            Write-OK "Visual Studio 2022 installation completed."
        } catch {
            Write-Err "winget installation failed. Please install manually."
            Write-Info "Download: https://visualstudio.microsoft.com/downloads/"
            Pause-ForUser "Install Visual Studio 2022 manually, then press ENTER to continue..."
        }
    } else {
        Pause-ForUser "Install Visual Studio 2022 manually, then press ENTER to continue..."
    }
}

# ============================================================================
# STEP 2: Check / Install CMake & Ninja
# ============================================================================

Write-Banner "Step 2/6: CMake & Ninja (Build System)"

# --- CMake ---
if (Test-CommandExists "cmake") {
    $cmakeVer = (cmake --version | Select-Object -First 1)
    Write-OK "CMake found: $cmakeVer"
} else {
    Write-Warn "CMake not found. Installing via winget..."
    try {
        winget install Kitware.CMake --accept-source-agreements --accept-package-agreements
        Write-OK "CMake installed. You may need to restart your terminal for PATH to update."
    } catch {
        Write-Err "Failed to install CMake via winget."
        Write-Info "Download manually: https://cmake.org/download/"
        Pause-ForUser "Install CMake, then press ENTER..."
    }
}

# --- Ninja ---
if (Test-CommandExists "ninja") {
    $ninjaVer = (ninja --version 2>$null)
    Write-OK "Ninja found: v$ninjaVer"
} else {
    Write-Warn "Ninja not found. Installing via winget..."
    try {
        winget install Ninja-build.Ninja --accept-source-agreements --accept-package-agreements
        Write-OK "Ninja installed."
    } catch {
        Write-Err "Failed to install Ninja via winget."
        Write-Info "Download manually: https://github.com/ninja-build/ninja/releases"
        Pause-ForUser "Install Ninja, then press ENTER..."
    }
}

# ============================================================================
# STEP 3: Check / Install Python 3.9
# ============================================================================

Write-Banner "Step 3/6: Python 3.9"

$pythonCmd = $null
$pythonOK = $false

# Check for python command
foreach ($cmd in @("python", "python3", "py")) {
    if (Test-CommandExists $cmd) {
        $ver = & $cmd --version 2>&1
        if ($ver -match "3\.\d+") {
            $pythonCmd = $cmd
            $pythonOK = $true
            Write-OK "Python found: $ver (command: $cmd)"
            break
        }
    }
}

if (-not $pythonOK) {
    Write-Warn "Python 3.9+ not found."
    Write-Info "Installing Python 3.9 via winget..."
    try {
        winget install Python.Python.3.9 --accept-source-agreements --accept-package-agreements
        Write-OK "Python 3.9 installed. You may need to restart your terminal."
        $pythonCmd = "python"
    } catch {
        Write-Err "Failed to install Python via winget."
        Write-Info "Download manually: https://www.python.org/downloads/release/python-3913/"
        Write-Info "IMPORTANT: Check 'Add Python to PATH' during installation!"
        Pause-ForUser "Install Python 3.9, then press ENTER..."
        $pythonCmd = "python"
    }
}

# ============================================================================
# STEP 4: Unreal Engine 5.7
# ============================================================================

Write-Banner "Step 4/6: Unreal Engine 5.7"

$ueInstalled = $false

if (Test-Path $UE_EXPECTED_ROOT) {
    Write-OK "Unreal Engine 5.7 found at: $UE_EXPECTED_ROOT"
    $ueInstalled = $true
} else {
    # Also check common alternate paths
    $altPaths = @(
        "C:\Program Files\Epic Games\UE_5.7",
        "D:\Program Files\Epic Games\UE_5.7",
        "D:\Epic Games\UE_5.7",
        "E:\Epic Games\UE_5.7"
    )
    foreach ($p in $altPaths) {
        if (Test-Path $p) {
            $UE_EXPECTED_ROOT = $p
            $ueInstalled = $true
            Write-OK "Unreal Engine 5.7 found at: $p"
            break
        }
    }
}

if (-not $ueInstalled) {
    Write-Warn "Unreal Engine 5.7 NOT found."
    Write-Info ""
    Write-Info "This step CANNOT be fully automated. Please follow these steps:"
    Write-Info ""
    Write-Info "  1. Go to: https://www.unrealengine.com/en-US/download"
    Write-Info "  2. Download and install the Epic Games Launcher."
    Write-Info "  3. Sign in (or create an Epic Games account)."
    Write-Info "  4. In the Launcher, go to 'Unreal Engine' tab -> 'Library'."
    Write-Info "  5. Click the '+' button and select version 5.7."
    Write-Info "  6. Click 'Install'."
    Write-Info ""
    Write-Info "  Default install path: C:\Program Files\Epic Games\UE_5.7"
    Write-Info ""

    # Try to open the download page automatically
    Start-Process "https://www.unrealengine.com/en-US/download"

    Pause-ForUser "After installing UE 5.7, press ENTER to continue..."

    # Ask for custom path if not at default location
    if (-not (Test-Path $UE_EXPECTED_ROOT)) {
        Write-Info "UE 5.7 not found at default path: $UE_EXPECTED_ROOT"
        $customPath = Read-Host "  Enter the UE 5.7 install path (or press ENTER to skip)"
        if ($customPath -and (Test-Path $customPath)) {
            $UE_EXPECTED_ROOT = $customPath
            $ueInstalled = $true
        } else {
            Write-Warn "Skipping UE_ROOT setup. You can set it manually later:"
            Write-Warn '  [System.Environment]::SetEnvironmentVariable("UE_ROOT", "C:\Program Files\Epic Games\UE_5.7", "User")'
        }
    } else {
        $ueInstalled = $true
    }
}

# Set UE_ROOT environment variable
if ($ueInstalled) {
    Write-Step "4a" "Setting UE_ROOT environment variable..."
    [System.Environment]::SetEnvironmentVariable("UE_ROOT", $UE_EXPECTED_ROOT, "User")
    $env:UE_ROOT = $UE_EXPECTED_ROOT
    Write-OK "UE_ROOT set to: $UE_EXPECTED_ROOT"
}

# ============================================================================
# STEP 5: Python Virtual Environment & Dependencies
# ============================================================================

Write-Banner "Step 5/6: Python Virtual Environment & Dependencies"

# Create venv
if (Test-Path $VENV_DIR) {
    Write-OK "Virtual environment already exists at: $VENV_DIR"
} else {
    Write-Step "5a" "Creating virtual environment..."
    & $pythonCmd -m venv $VENV_DIR
    Write-OK "Virtual environment created at: $VENV_DIR"
}

# Activate venv
Write-Step "5b" "Activating virtual environment..."
$activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-OK "Virtual environment activated."
} else {
    Write-Err "Could not find venv activation script at: $activateScript"
    exit 1
}

# Upgrade pip
Write-Step "5c" "Upgrading pip..."
& python -m pip install --upgrade pip --quiet
Write-OK "pip upgraded."

# Install core requirements
Write-Step "5d" "Installing core Python dependencies..."
if (Test-Path $REQUIREMENTS) {
    & pip install -r $REQUIREMENTS --quiet
    Write-OK "Core dependencies installed from requirements.txt"
} else {
    Write-Warn "requirements.txt not found at $REQUIREMENTS, installing package directly..."
}

# Install projectairsim in editable mode
Write-Step "5e" "Installing projectairsim package (editable mode)..."
& pip install -e $PYPROJECT_DIR --quiet
Write-OK "projectairsim installed in editable mode."

# Install additional tools for examples
Write-Step "5f" "Installing additional tools (keyboard)..."
& pip install keyboard --quiet
Write-OK "Additional tools installed."

# ============================================================================
# STEP 6: Build C++ Simulation Libraries & Unreal Plugin
# ============================================================================

Write-Banner "Step 6/6: Build Simulation Libraries (build.cmd all)"

if (-not $ueInstalled) {
    Write-Warn "UE_ROOT is not set. The build will proceed without Unreal integration."
    Write-Warn "Sim libs will still be built, but the Unreal plugin build will be skipped."
}

Write-Step "6a" "Starting build process..."
Write-Info "This step may take 15-30 minutes on first run."
Write-Info "It downloads and compiles: NNG, Assimp, Eigen, ONNX Runtime, etc."
Write-Info ""

$choice = Read-Host "  Start the build now? (y/n)"
if ($choice -eq 'y' -or $choice -eq 'Y') {
    Push-Location $REPO_ROOT
    try {
        & cmd.exe /c $BUILD_CMD all
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Build completed successfully!"
        } else {
            Write-Err "Build failed with exit code: $LASTEXITCODE"
            Write-Info "Try running from 'x64 Native Tools Command Prompt for VS 2022':"
            Write-Info "  cd $REPO_ROOT"
            Write-Info "  build.cmd all"
        }
    } catch {
        Write-Err "Build process encountered an error: $_"
    }
    Pop-Location
} else {
    Write-Warn "Build skipped. You can run it later with:"
    Write-Info "  cd $REPO_ROOT"
    Write-Info "  build.cmd all"
}

# ============================================================================
# Summary
# ============================================================================

Write-Banner "Setup Complete!"

Write-Host "  Environment Summary:" -ForegroundColor White
Write-Host "  -----------------------------------------------"
Write-Info "Repository:   $REPO_ROOT"
Write-Info "Python venv:  $VENV_DIR"
if ($ueInstalled) {
    Write-Info "UE_ROOT:      $UE_EXPECTED_ROOT"
} else {
    Write-Warn "UE_ROOT:      NOT SET (install UE 5.7 and set manually)"
}
Write-Host ""

Write-Host "  Quick Start Guide:" -ForegroundColor White
Write-Host "  -----------------------------------------------"
Write-Host "  1. Activate the virtual environment:" -ForegroundColor Gray
Write-Host "       .\venv\Scripts\activate" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Open the Unreal project:" -ForegroundColor Gray
Write-Host "       Start-Process unreal\Blocks\Blocks.uproject" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. In Unreal: Set GameMode Override -> ProjectAirSimGameMode" -ForegroundColor Gray
Write-Host "     Then press Play (green triangle)." -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Run a test script:" -ForegroundColor Gray
Write-Host "       cd client\python\example_user_scripts" -ForegroundColor Yellow
Write-Host "       python hello_drone.py" -ForegroundColor Yellow
Write-Host ""

Write-Host "  For full documentation, see: !note.md" -ForegroundColor DarkCyan
Write-Host ""
