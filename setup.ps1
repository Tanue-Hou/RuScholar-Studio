param(
    [string]$PythonBin = "python",
    [string]$VenvDir = (Join-Path $env:LOCALAPPDATA "PHD-Scholar\venvs\ruscholar"),
    [switch]$DownloadModel
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

& $PythonBin -c "import sys; sys.exit('Python 3.10 or newer is required (the mcp package needs it).') if sys.version_info < (3, 10) else None"

if (-not (Test-Path $VenvDir)) {
    & $PythonBin -m venv $VenvDir
}

& "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip
& "$VenvDir\Scripts\pip.exe" install -r requirements-dev.txt
& "$VenvDir\Scripts\pip.exe" install --no-deps -e .
& "$VenvDir\Scripts\python.exe" -m spacy download ru_core_news_sm

if (Get-Command npm -ErrorAction SilentlyContinue) {
    $FrontendStage = Join-Path ([IO.Path]::GetTempPath()) ("ruscholar-frontend-" + [Guid]::NewGuid())
    New-Item -ItemType Directory -Path $FrontendStage | Out-Null
    try {
        Get-ChildItem (Join-Path $RootDir "frontend") -Force |
            Where-Object { $_.Name -notin @("node_modules", "dist", ".DS_Store") } |
            Copy-Item -Destination $FrontendStage -Recurse -Force
        Push-Location $FrontendStage
        try {
            npm ci
            if ($LASTEXITCODE -ne 0) { throw "npm ci failed" }
            npm run build
            if ($LASTEXITCODE -ne 0) { throw "frontend build failed" }
        } finally { Pop-Location }
        $Dist = Join-Path $RootDir "frontend\dist"
        if (Test-Path $Dist) { Remove-Item $Dist -Recurse -Force }
        Copy-Item (Join-Path $FrontendStage "dist") -Destination $Dist -Recurse
    } finally { Remove-Item $FrontendStage -Recurse -Force }
} else {
    Write-Host "npm was not found. Install Node.js 20+ and run: cd frontend; npm install; npm run build"
}

if ($DownloadModel) {
    & "$VenvDir\Scripts\python.exe" -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
}

Write-Host "Setup complete. Start Web UI with: & '$VenvDir\Scripts\ruscholar-web.exe'"
Write-Host "MCP server (stdio): & '$VenvDir\Scripts\ruscholar-mcp.exe'"
