param(
    [switch]$Noconsole,
    [switch]$FreshExcel
)

# Build PyInstaller bundle for Digital Library Server
# Usage examples:
#   ./build_exe.ps1             # console window (shows logs)
#   ./build_exe.ps1 -Noconsole  # no console window
#   ./build_exe.ps1 -FreshExcel # do not bundle existing Excel file

$ErrorActionPreference = 'Stop'

# Ensure running from script directory
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Resolve venv python if present, else fallback to python on PATH
$venvPython = Join-Path -Path (Join-Path -Path (Get-Location) -ChildPath 'venv') -ChildPath 'Scripts/python.exe'
if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = 'python'
}

# Remove existing PyInstaller to avoid version conflicts
try {
    & $python -m pip uninstall -y pyinstaller | Out-Host
} catch {}

# Install dependencies (pin PyInstaller to avoid Py3.10 bytecode scan bug)
& $python -m pip install --upgrade pip | Out-Host
& $python -m pip install -r requirements.txt | Out-Host
& $python -m pip install --upgrade --force-reinstall "pyinstaller==6.17.0" | Out-Host

# Build arguments
$addData = @(
    'templates;templates'
)
if (-not $FreshExcel) {
    if (Test-Path 'library_data.xlsx') {
        $addData += 'library_data.xlsx;.'
    }
}

$pyiArgs = @('--clean', '--onefile', '--name', 'DigitalLibrary')
foreach ($item in $addData) {
    $pyiArgs += @('--add-data', $item)
}
if ($Noconsole) {
    $pyiArgs += '--noconsole'
}

Write-Host "Building EXE with: pyinstaller $($pyiArgs -join ' ')" -ForegroundColor Cyan

# Clean old artifacts to avoid stale state
Remove-Item -ErrorAction SilentlyContinue -Recurse -Force build, dist, DigitalLibrary.spec

& $python -m PyInstaller @pyiArgs 'server.py'

Write-Host "Build complete. EXE should be at dist/DigitalLibrary.exe" -ForegroundColor Green
