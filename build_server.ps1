# Baut den PDF-Werkstatt-Server (PyInstaller).
# Ortunabhängig: liegt im Projektordner, nutzt $PSScriptRoot.
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$root = $PSScriptRoot
if (-not $root) { $root = Split-Path -Parent $MyInvocation.MyCommand.Path }
$venv = Join-Path $root "venv\Scripts"

if (-not (Test-Path (Join-Path $root "venv\Scripts\python.exe"))) {
    Write-Host "venv fehlt - lege an (py -3.14):"
    py -3.14 -m venv (Join-Path $root "venv")
}

Write-Host "=== pyinstaller sicherstellen ==="
& "$venv\python.exe" -m pip install --quiet --disable-pip-version-check pyinstaller pymupdf fastapi "uvicorn[standard]" python-multipart pillow
Write-Host "pip exit: $LASTEXITCODE"

$mp = & "$venv\python.exe" -c "import importlib.util; print('multipart' if importlib.util.find_spec('multipart') else ('python_multipart' if importlib.util.find_spec('python_multipart') else 'none'))"
Write-Host "multipart-Modul: $mp"

Set-Location (Join-Path $root "app")
$pargs = @("--noconfirm","--clean","--onedir","--name","PdfWerkstattServer",
           "--icon",(Join-Path $root "wrapper\pdfwerkstatt_icon.ico"),
           "--add-data","static;static",
           "--collect-all","pymupdf","--collect-all","uvicorn","--collect-all","fastapi",
           "--collect-all","cryptography")
if ($mp -eq "multipart") { $pargs += @("--collect-all","multipart") }
if ($mp -eq "python_multipart") { $pargs += @("--collect-all","python_multipart") }

Write-Host "=== PyInstaller-Build ==="
& "$venv\pyinstaller.exe" @pargs server.py 2>&1 | Select-Object -Last 3
Write-Host "pyinstaller exit: $LASTEXITCODE"

$dist = Join-Path $root "app\dist\PdfWerkstattServer\PdfWerkstattServer.exe"
if (Test-Path $dist) {
    $size = [math]::Round((Get-ChildItem (Split-Path $dist) -Recurse | Measure-Object Length -Sum).Sum/1MB,1)
    Write-Host "SERVER-EXE OK: $dist ($size MB)"
} else {
    Write-Host "SERVER-EXE FEHLT!"
}
