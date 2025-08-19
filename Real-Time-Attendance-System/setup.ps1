$ErrorActionPreference = 'Stop'

python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

# Install a local dlib wheel if present
$wheel = Get-ChildItem -Path 'wheels\*.whl' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($wheel) {
  Write-Host "Installing wheel: $($wheel.FullName)"
  python -m pip install "$($wheel.FullName)"
} else {
  Write-Host 'No local wheel found in wheels/ — skipping'
}

# Install the rest of requirements
if (Test-Path -Path 'requirements-py38.txt') {
  python -m pip install -r 'requirements-py38.txt'
} else {
  python -m pip install -r 'requirements.txt'
}

Write-Host 'Setup complete. Activate later with: .\.venv\Scripts\Activate.ps1'
