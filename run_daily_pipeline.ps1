param(
    [switch]$Loop,
    [double]$IntervalHours = 8
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogsDir = Join-Path $ProjectRoot "logs"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$PythonCommand = if (Test-Path $VenvPython) { "`"$VenvPython`"" } else { "python" }

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

function Run-Full-Pipeline {
    Write-Log "Pipeline data demarre."

    Run-Step `
        -Label "Scraping Maroc Annonces (BeautifulSoup)" `
        -WorkingDirectory (Join-Path $ProjectRoot "data_engine\scraping\BeautifulSoup") `
        -Command "$PythonCommand anonce-maroc.py"

    Run-Step `
        -Label "Scraping Rekrute" `
        -WorkingDirectory (Join-Path $ProjectRoot "data_engine\scraping") `
        -Command "$PythonCommand scraping_Rekrute.py"

    Run-Step `
        -Label "Preprocessing complet" `
        -WorkingDirectory $ProjectRoot `
        -Command "$PythonCommand -m data_engine.run_pipeline"

    Run-Step `
        -Label "Import nouvelles offres Django" `
        -WorkingDirectory (Join-Path $ProjectRoot "backend") `
        -Command "$PythonCommand import_offers.py"

    Run-Step `
        -Label "Synchronisation clusters Django" `
        -WorkingDirectory (Join-Path $ProjectRoot "backend") `
        -Command "$PythonCommand sync_job_offers.py"

    Write-Log "Pipeline data terminee avec succes."
}

do {
    Run-Full-Pipeline

    if ($Loop) {
        $nextRun = (Get-Date).AddHours($IntervalHours)
        Write-Log ("Prochaine execution prevue: {0}" -f $nextRun.ToString("yyyy-MM-dd HH:mm:ss"))
        Start-Sleep -Seconds ([int]($IntervalHours * 3600))
    }
} while ($Loop)
