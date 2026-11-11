# BERRY - optional local media add-ons from user-provided component table.
# Chatterbox, HyperFrames, OpenClipper, Instagram Agent Skill.
# NO cloud, social login, posting, payments, or auto-execution of third-party skills.
param([string]$ProjectRoot = '')
$ErrorActionPreference = 'Stop'
if (-not $ProjectRoot) { $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
Set-Location $ProjectRoot
$Engines = Join-Path $ProjectRoot 'local_engines'
$Reports = Join-Path $env:LOCALAPPDATA 'BERRY_AI_AUTOPILOT\reports'
New-Item -ItemType Directory -Force -Path $Engines, $Reports | Out-Null
$Results = New-Object 'System.Collections.Generic.List[object]'
function Ask([string]$Question) {
  $answer = Read-Host ($Question + ' [d/N]')
  return ($answer -match '^(d|da|y|yes)$')
}
function Mark([string]$Name, [string]$Status, [string]$Detail) {
  $Results.Add([ordered]@{name=$Name;status=$Status;detail=$Detail}) | Out-Null
  Write-Host ('[' + $Status + '] ' + $Name + ' - ' + $Detail)
}
function Cmd([string]$Name) { return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
              [Environment]::GetEnvironmentVariable('Path','User')
}
function Add-Env([string]$Key, [string]$Value) {
  if (-not $Value -or $Value.Contains([char]10) -or $Value.Contains([char]13)) { return }
  $file = Join-Path $ProjectRoot '.env.local'
  $lines = @()
  if (Test-Path $file) { $lines = @(Get-Content $file -Encoding UTF8) }
  $pattern = '^\s*' + [regex]::Escape($Key) + '='
  $lines = @($lines | Where-Object { $_ -notmatch $pattern })
  $lines += ($Key + '=' + $Value.Replace('\','/'))
  [IO.File]::WriteAllLines($file, [string[]]$lines, ([System.Text.UTF8Encoding]::new($false)))
}
function Clone-Repo([string]$Name, [string]$Url) {
  $dest = Join-Path $Engines $Name
  if (Test-Path (Join-Path $dest '.git')) {
    Mark $Name 'SOURCE_PRESENT' 'Codul exista; nu modific versiunea fara aprobare.'
    return $dest
  }
  if (Test-Path $dest) {
    Mark $Name 'MANUAL' 'Folder existent dar incomplet; nu suprascriu.'
    return $null
  }
  if (-not (Cmd 'git')) {
    Mark $Name 'MANUAL' 'Git lipseste.'
    return $null
  }
  if (-not (Ask ('Descarc sursa publica ' + $Name + '?'))) {
    Mark $Name 'SKIP' 'Nu descarc sursa.'
    return $null
  }
  & git clone --depth 1 $Url $dest
  if ($LASTEXITCODE -ne 0) {
    Mark $Name 'FAILED' 'Git clone esuat.'
    return $null
  }
  Mark $Name 'SOURCE_ONLY' 'Sursa descarcata, nu inseamna instalare functionala.'
  return $dest
}
function Get-Python311 {
  $exe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
  if (Test-Path $exe) {
    $version = & $exe -c 'import sys; print("%d.%d" % sys.version_info[:2])'
    if ($version -eq '3.11') { return $exe }
  }
  if (Cmd 'py') {
    & py -3.11 --version 2>$null
    if ($LASTEXITCODE -eq 0) { return 'py' }
  }
  return $null
}
Write-Host ''
Write-Host 'BERRY - EXTRA MEDIA ADDONS - LOCAL ONLY' -ForegroundColor Cyan
Write-Host 'Chatterbox / HyperFrames / OpenClipper / Instagram Agent Skill'
Write-Host 'No cloud, no Instagram login, no publishing, no paid subscriptions.'
if (-not (Ask 'Continui instalarea optionala?')) {
  Mark 'BERRY extras' 'CANCELLED' 'Utilizatorul a refuzat.'
} else {
  # HyperFrames: local deterministic HTML/CSS video renderer, Node 22+.
  $nodeOK = $false
  if (Cmd 'node') {
    try { $nodeOK = ([int](& node -p 'process.versions.node.split(".")[0]') -ge 22) } catch {}
  }
  if (-not $nodeOK -and (Cmd 'winget') -and (Ask 'Instalez Node.js LTS (versiune 22+) pentru HyperFrames?')) {
    & winget install --id OpenJS.NodeJS.LTS --exact --source winget --accept-package-agreements --accept-source-agreements
    Refresh-Path
    if (Cmd 'node') {
      try { $nodeOK = ([int](& node -p 'process.versions.node.split(".")[0]') -ge 22) } catch {}
    }
  }
  if (-not $nodeOK) {
    Mark 'HyperFrames' 'MANUAL' 'Node.js 22+ lipseste; nu rulez npm.'
  } else {
    $hf = Join-Path $Engines 'HyperFrames'
    $bin = Join-Path $hf 'node_modules\.bin\hyperframes.cmd'
    if (Test-Path $bin) {
      Add-Env 'BERRY_HYPERFRAMES_BIN' $bin
      Mark 'HyperFrames' 'PACKAGE_PRESENT' 'CLI instalat; randarea MP4 nu este testata.'
    } elseif (Ask 'Instalez pachetul oficial npm hyperframes@0.9.33 local (nu Studio Pro)?') {
      New-Item -ItemType Directory -Force -Path $hf | Out-Null
      & npm install --prefix $hf 'hyperframes@0.9.33' --no-audit --no-fund
      if ($LASTEXITCODE -eq 0 -and (Test-Path $bin)) {
        Add-Env 'BERRY_HYPERFRAMES_BIN' $bin
        Mark 'HyperFrames' 'PACKAGE_INSTALLED' 'CLI local prezent; verifica render si FFmpeg.'
      } else {
        Mark 'HyperFrames' 'FAILED' 'npm/CLI nu a reusit; consulta logul.'
      }
    } else { Mark 'HyperFrames' 'SKIP' 'Pachet npm amanat.' }
  }

  # Chatterbox: separate Python environment; no automatic voice cloning.
  $cb = Clone-Repo 'Chatterbox' 'https://github.com/resemble-ai/chatterbox.git'
  if ($cb) {
    Add-Env 'BERRY_CHATTERBOX_ROOT' $cb
    $py = Get-Python311
    if (-not $py) {
      Mark 'Chatterbox runtime' 'MANUAL' 'Necesita Python 3.11. Nu instalez in mediul principal BERRY.'
    } elseif (Ask 'Instalez chatterbox-tts in venv Python 3.11 SEPARAT? Poate necesita GPU si modele mari') {
      $venv = Join-Path $cb '.venv'
      $exe = Join-Path $venv 'Scripts\python.exe'
      if (-not (Test-Path $exe)) {
        if ($py -eq 'py') { & py -3.11 -m venv $venv }
        else { & $py -m venv $venv }
      }
      if (-not (Test-Path $exe)) {
        Mark 'Chatterbox runtime' 'FAILED' 'Nu s-a creat venv.'
      } else {
        & $exe -m pip install chatterbox-tts
        if ($LASTEXITCODE -eq 0) {
          Add-Env 'BERRY_CHATTERBOX_PYTHON' $exe
          Mark 'Chatterbox runtime' 'DEPS_INSTALLED' 'Pachet instalat; inferenta si licenta vocii nu sunt validate.'
        } else { Mark 'Chatterbox runtime' 'PARTIAL' 'pip a esuat; verifica dependentele Windows.' }
      }
    } else { Mark 'Chatterbox runtime' 'SKIP' 'Pachet TTS amanat.' }
  }

  # OpenClipper: GitHub source only. Official Windows installer is distributed separately.
  $oc = Clone-Repo 'OpenClipper' 'https://github.com/GrepCut/OpenClipper.git'
  if ($oc) {
    Add-Env 'BERRY_OPENCLIPPER_ROOT' $oc
    Mark 'OpenClipper installer' 'MANUAL' 'Instalator Windows: https://grepcut.com/en/open-clipper ; fara login sau publish.'
  }

  # Instagram Agent Skill: content-writing templates only; NEVER execute or publish.
  $ig = Clone-Repo 'InstagramAgentSkill' 'https://github.com/Jakeschincariol/instagram-agent-skill.git'
  if ($ig) {
    Add-Env 'BERRY_INSTAGRAM_SKILL_ROOT' $ig
    Mark 'Instagram Agent Skill' 'REFERENCE_ONLY' 'Template-uri pentru hook/caption/planificare; niciun script executat.'
  }
}
$report = [ordered]@{
  product = 'BERRY AI AUTOPILOT'
  category = 'local_media_addons'
  timestamp_utc = [DateTime]::UtcNow.ToString('o')
  local_only = $true
  social_accounts_connected = $false
  publishing_enabled = $false
  paid_services_enabled = $false
  functional_inference_validated = $false
  steps = @($Results.ToArray())
}
$path = Join-Path $Reports ('media_addons_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.json')
$report | ConvertTo-Json -Depth 6 | Set-Content -Path $path -Encoding UTF8
Write-Host ('Raport: ' + $path)
Write-Host 'Pachetele instalate nu inseamna ca fluxul BERRY de productie este integrat si testat.'
