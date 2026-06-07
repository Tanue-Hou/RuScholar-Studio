param(
    [string]$PythonBin = "python",
    [string]$VenvDir = ".venv",
    [switch]$DownloadModel
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

& $PythonBin -c "import sys; sys.exit('Python 3.9 or newer is required.') if sys.version_info < (3, 9) else None"

if (-not (Test-Path $VenvDir)) {
    & $PythonBin -m venv $VenvDir
}

& "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip
& "$VenvDir\Scripts\pip.exe" install -r requirements.txt
& "$VenvDir\Scripts\python.exe" -m spacy download ru_core_news_sm

if (Get-Command npm -ErrorAction SilentlyContinue) {
    Push-Location frontend
    npm install
    npm run build
    Pop-Location
} else {
    Write-Host "npm was not found. Install Node.js 20+ and run: cd frontend; npm install; npm run build"
}

if ($DownloadModel) {
    & "$VenvDir\Scripts\python.exe" -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
}

Write-Host "Setup complete. Start Web UI with: .\.venv\Scripts\python.exe backend\main.py"
