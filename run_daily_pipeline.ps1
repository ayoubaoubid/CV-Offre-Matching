$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogsDir = Join-Path $ProjectRoot "logs"

if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}

$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$LogFile = Join-Path $LogsDir "daily_pipeline_$Timestamp.log"

function Write-Log {
    param(
        [string]$Message
    )

    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Run-Step {
    param(
        [string]$Label,
        [string]$WorkingDirectory,
        [string]$Command
    )

    Write-Log "START - $Label"
    Push-Location $WorkingDirectory
    try {
        Invoke-Expression $Command 2>&1 | Tee-Object -FilePath $LogFile -Append
        if ($LASTEXITCODE -ne 0) {
            throw "Le script '$Label' a retourne le code $LASTEXITCODE."
        }
        Write-Log "DONE  - $Label"
    }
    finally {
        Pop-Location
    }
}

Write-Log "Pipeline quotidien demarre."

Run-Step `
    -Label "Scraping Maroc Annonces (BeautifulSoup)" `
    -WorkingDirectory (Join-Path $ProjectRoot "data_engine\scraping\BeautifulSoup") `
    -Command "python anonce-maroc.py"

Run-Step `
    -Label "Scraping complet" `
    -WorkingDirectory (Join-Path $ProjectRoot "data_engine\scraping") `
    -Command "python scraping_Rekrute.py"

Run-Step `
    -Label "Preprocessing complet" `
    -WorkingDirectory $ProjectRoot `
    -Command "python -m data_engine.run_pipeline"

Write-Log "Pipeline quotidien termine avec succes."
