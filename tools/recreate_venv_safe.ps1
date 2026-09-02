param(
    [string]$VenvName = ".venv",
    [switch]$DeleteBackup,
    [switch]$SkipInstall,
    [switch]$ValidateSpec,
    [switch]$WhatIfOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-PythonLauncher {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }

    throw "Python launcher not found (py or python)."
}

function New-VenvSafe {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Launcher,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if ($Launcher.Length -eq 2) {
        & $Launcher[0] $Launcher[1] -m venv $Name
    }
    else {
        & $Launcher[0] -m venv $Name
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment: $Name"
    }
}

$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot

try {
    $venvPath = Join-Path $projectRoot $VenvName
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = ""
    $markerFiles = @("requirements.txt", "pyproject.toml", "Pipfile", "poetry.lock")
    $foundMarkers = @($markerFiles | Where-Object { Test-Path (Join-Path $projectRoot $_) })

    Write-Host "Project root: $projectRoot"
    Write-Host "Target venv:  $venvPath"

    if (Test-Path $venvPath) {
        $backupPath = Join-Path $projectRoot ("{0}.bak.{1}" -f $VenvName, $timestamp)
        Write-Host "Renaming existing venv to backup: $backupPath"
        if (-not $WhatIfOnly) {
            Rename-Item -Path $venvPath -NewName (Split-Path -Leaf $backupPath)
        }
    }
    else {
        Write-Host "No existing venv found. A new one will be created."
    }

    $py = Get-PythonLauncher
    Write-Host "Creating new venv..."
    if (-not $WhatIfOnly) {
        New-VenvSafe -Launcher $py -Name $VenvName
    }

    $pythonExe = Join-Path $venvPath "Scripts\python.exe"
    if (-not $WhatIfOnly -and -not (Test-Path $pythonExe)) {
        throw "New virtual environment was not created correctly: $pythonExe not found."
    }

    $installStatus = "skipped"
    if (-not $WhatIfOnly) {
        Write-Host "Validating new venv..."
        & $pythonExe "--version"
        & $pythonExe "-m" "pip" "--version"

        Write-Host "Upgrading pip..."
        & $pythonExe "-m" "pip" "install" "--upgrade" "pip"

        if (-not $SkipInstall) {
            $requirementsFile = Join-Path $projectRoot "requirements.txt"
            if (Test-Path $requirementsFile) {
                Write-Host "Installing dependencies from requirements.txt..."
                & $pythonExe "-m" "pip" "install" "-r" $requirementsFile
                if ($LASTEXITCODE -ne 0) {
                    throw "Dependency installation failed from requirements.txt"
                }
                $installStatus = "installed from requirements.txt"
            }
            elseif (Test-Path (Join-Path $projectRoot "pyproject.toml")) {
                Write-Host "pyproject.toml found. Install dependencies manually according to the project toolchain."
                $installStatus = "pyproject.toml found (manual install required)"
            }
            else {
                Write-Host "No dependency manifest found in project root."
                $installStatus = "no manifest found"
            }
        }

        if ($ValidateSpec) {
            $specFiles = Get-ChildItem -Path $projectRoot -Recurse -File -Filter "*.spec" -ErrorAction SilentlyContinue
            if (@($specFiles).Count -gt 0) {
                Write-Host "Spec files found: $(@($specFiles).Count)"
                Write-Host "Checking PyInstaller in new venv..."
                & $pythonExe "-m" "pip" "show" "pyinstaller" | Out-Host
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "PyInstaller not installed in the new venv. .spec build validation was skipped."
                }
                else {
                    & $pythonExe "-m" "PyInstaller" "--version" | Out-Host
                }
            }
            else {
                Write-Host "No .spec files found in this project."
            }
        }
    }

    if ($DeleteBackup -and -not [string]::IsNullOrWhiteSpace($backupPath)) {
        Write-Host "Deleting backup venv: $backupPath"
        if (-not $WhatIfOnly) {
            Remove-Item -Path $backupPath -Recurse -Force
        }
    }
    elseif (-not [string]::IsNullOrWhiteSpace($backupPath)) {
        Write-Host "Backup preserved for analysis: $backupPath"
    }

    $result = [PSCustomObject]@{
        ProjectRoot = $projectRoot
        NewVenv = $venvPath
        BackupVenv = $(if ([string]::IsNullOrWhiteSpace($backupPath)) { "none" } else { $backupPath })
        Markers = $(if ($foundMarkers.Count -eq 0) { "none" } else { $foundMarkers -join ", " })
        InstallStatus = $installStatus
        BackupDeleted = $DeleteBackup.IsPresent
        DryRun = $WhatIfOnly.IsPresent
    }

    Write-Host ""
    Write-Host "Summary:"
    $result | Format-List
}
catch {
    Write-Error $_
    throw
}
finally {
    Pop-Location
}
