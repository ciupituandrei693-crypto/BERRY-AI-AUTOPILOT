# BERRY AI AUTOPILOT - instalare interactiva Windows, local
param([switch]$SkipPackages)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host 'BERRY: instalare gratuita locala; fara cloud, plati sau publicare.' -ForegroundColor Cyan
function Confirm-Step([string]$message) { $a = Read-Host ($message + ' [d/N]'); return ($a -match '^(d|da|y|yes)$') }
function Has-Exe([string]$name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }
function Install-Package([string]$id, [string]$name) {
  if (-not (Has-Exe 'winget')) { Write-Warning 'winget lipseste: instaleaza App Installer din Microsoft Store.'; return }
  if (Confirm-Step ('Instalez ' + $name + ' cu winget? Necesita internet')) {
    & winget install --id $id --exact --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { Write-Warning ('Instalarea a esuat: ' + $name) }
  }
}
if (-not $SkipPackages) {
  if (-not (Has-Exe 'py') -and -not (Has-Exe 'python')) { Install-Package 'Python.Python.3.11' 'Python 3.11' }
  if (-not (Has-Exe 'git')) { Install-Package 'Git.Git' 'Git' }
  if (-not (Has-Exe 'ffmpeg')) { Install-Package 'Gyan.FFmpeg' 'FFmpeg' }
  $blender = Get-Command blender -ErrorAction SilentlyContinue
  $blenderFolder = Join-Path $env:ProgramFiles 'Blender Foundation'
  if (-not $blender -and (Test-Path $blenderFolder)) { $blender = Get-ChildItem $blenderFolder -Filter blender.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 }
  if (-not $blender) { Install-Package 'BlenderFoundation.Blender' 'Blender 3D' }
}
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
if (-not (Test-Path '.venv\Scripts\python.exe')) {
  if (Confirm-Step 'Creez mediul Python local .venv?') {
    if (Has-Exe 'py') { & py -3.11 -m venv .venv }
    elseif (Has-Exe 'python') { & python -m venv .venv }
    else { Write-Warning 'Python indisponibil. Reporneste terminalul dupa instalare.' }
  }
}
if (Test-Path '.venv\Scripts\python.exe') {
  if (Confirm-Step 'Instalez dependentele gratuite BERRY si pytest?') {
    & .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    if ($LASTEXITCODE -eq 0) { Set-Content '.venv\berry-ready-v12.flag' 'ready' }
    else { Write-Warning 'Dependente Python incomplete.' }
  }
}
$repos = @(
  @{name='LivePortrait';url='https://github.com/KwaiVGI/LivePortrait.git'},
  @{name='MuseTalk';url='https://github.com/TMElyralab/MuseTalk.git'},
  @{name='LatentSync';url='https://github.com/bytedance/LatentSync.git'},
  @{name='Hunyuan3D-2';url='https://github.com/Tencent/Hunyuan3D-2.git'},
  @{name='Rhubarb-Lip-Sync';url='https://github.com/DanielSWolf/rhubarb-lip-sync.git'}
)
if (Confirm-Step 'Descarc sursele open-source in local_engines? NU include modelele weights') {
  if (-not (Has-Exe 'git')) { Write-Warning 'Git lipseste. Reporneste terminalul.' }
  else {
    $base = Join-Path $PSScriptRoot 'local_engines'
    New-Item -ItemType Directory -Force -Path $base | Out-Null
    foreach ($repo in $repos) {
      $target = Join-Path $base $repo.name
      if (Test-Path $target) { Write-Host ('Exista: ' + $repo.name); continue }
      if (Confirm-Step ('Clonez ' + $repo.name + '?')) {
        & git clone --depth 1 $repo.url $target
        if ($LASTEXITCODE -ne 0) { Write-Warning ('Clonare esuata: ' + $repo.name) }
      }
    }
  }
}
Write-Host 'IMPORTANT: sursele NU includ weights/checkpoints, drivere sau mediile Python specifice.' -ForegroundColor Yellow
Write-Host 'Rhubarb din GitHub este sursa, nu executabilul Windows gata de utilizare.'
Write-Host 'Configureaza modelele conform docs\LOCAL_FINAL_STAGES_1_TO_11.md.'
Write-Host 'Ruleaza TESTE_FINALE_PC.cmd pentru raportul real de validare.'
Write-Host 'Nu s-au activat cloud, GPU inchiriat, conturi sociale sau plati.'
