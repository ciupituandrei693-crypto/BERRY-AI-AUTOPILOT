# Optional Windows AI runtimes. Each engine gets its own Python 3.10 venv.
# Do not run on AMD/Intel unless upstream instructions explicitly support it.
param([string]$ProjectRoot = '')
$ErrorActionPreference = 'Stop'
if (-not $ProjectRoot) { $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
Set-Location $ProjectRoot
$engines = Join-Path $ProjectRoot 'local_engines'
$reports = Join-Path $env:LOCALAPPDATA 'BERRY_AI_AUTOPILOT\reports'
New-Item -ItemType Directory -Force -Path $reports | Out-Null
$results = New-Object 'System.Collections.Generic.List[object]'
function Ask([string]$q) { return ((Read-Host ($q + ' [d/N]')) -match '^(d|da|y|yes)$') }
function Mark([string]$name, [string]$status, [string]$detail) {
  $results.Add([ordered]@{name=$name;status=$status;detail=$detail}) | Out-Null
  Write-Host ('[' + $status + '] ' + $name + ' - ' + $detail)
}
$gpu = ''
try { $gpu = ((Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }) -join ' / ') } catch {}
Write-Host ('GPU: ' + $gpu)
if ($gpu -notmatch 'NVIDIA') {
  Write-Warning 'GPU NVIDIA nedetectat. Runtimes CUDA nu vor fi instalate automat.'
  Mark 'AI CUDA' 'SKIP' 'Necesita verificare GPU/drivere si instructiuni upstream.'
} else {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if (-not $py) {
    Mark 'Python 3.10' 'MANUAL' 'Python Launcher py.exe lipseste.'
  } else {
    & py -3.10 --version
    if ($LASTEXITCODE -ne 0) {
      Write-Warning 'Python 3.10 lipseste. LivePortrait/MuseTalk/ACE-Step pot necesita aceasta versiune.'
      if ((Get-Command winget -ErrorAction SilentlyContinue) -and (Ask 'Instalez Python 3.10 prin winget?')) {
        & winget install --id Python.Python.3.10 --exact --source winget --accept-package-agreements --accept-source-agreements
      }
    }
    & py -3.10 --version
    if ($LASTEXITCODE -ne 0) {
      Mark 'Python 3.10' 'MANUAL' 'Reporneste terminalul dupa instalare sau instaleaza Python 3.10.'
    } else {
      $plans = @(
        @{name='LivePortrait';install=@('-r','requirements.txt')},
        @{name='MuseTalk';install=@('-r','requirements.txt')},
        @{name='Hunyuan3D-2';install=@('-r','requirements.txt')},
        @{name='ACE-Step';install=@('-e','.')}
      )
      foreach ($plan in $plans) {
        $name = $plan.name
        $dir = Join-Path $engines $name
        if (-not (Test-Path $dir)) { Mark $name 'MANUAL' 'Sursa nu este descarcata.'; continue }
        if (-not (Ask ('Pregatesc mediul Python separat pentru ' + $name + '? Poate descarca GB si poate esua pe Windows'))) {
          Mark $name 'SKIP' 'Mediul nu a fost instalat.'
          continue
        }
        $venv = Join-Path $dir '.venv'
        $exe = Join-Path $venv 'Scripts\python.exe'
        if (-not (Test-Path $exe)) {
          & py -3.10 -m venv $venv
        }
        if (-not (Test-Path $exe)) { Mark $name 'FAILED' 'Nu s-a creat venv.'; continue }
        & $exe -m pip install --upgrade pip
        Push-Location $dir
        try {
          & $exe -m pip install @($plan.install)
          if ($LASTEXITCODE -eq 0) {
            Mark $name 'DEPS_INSTALLED' 'Dependentele pip instalate; CUDA, checkpoints si inferenta NU sunt validate.'
          } else {
            Mark $name 'PARTIAL' 'Unele dependente pip nu au putut fi instalate; consulta logul terminalului.'
          }
        } catch {
          Mark $name 'FAILED' ('Eroare: ' + $_.Exception.GetType().Name)
        } finally { Pop-Location }
      }
    }
  }
  $wangp = Join-Path $engines 'WanGP\scripts\install.bat'
  if (Test-Path $wangp) {
    if (Ask 'Pornesc instalatorul OFICIAL WanGP pentru Windows? Va cere configurare GPU') {
      & cmd.exe /c $wangp
      if ($LASTEXITCODE -eq 0) { Mark 'WanGP' 'INSTALLER_RAN' 'Verifica env, checkpoints si inferenta.' }
      else { Mark 'WanGP' 'PARTIAL' 'Instalatorul a raportat eroare.' }
    }
  } else { Mark 'WanGP' 'MANUAL' 'Nu exista scripts\install.bat.' }
  Mark 'LatentSync' 'MANUAL' 'Upstream setup_env.sh este pentru Linux; nu se ruleaza automat pe Windows.'
}
$path = Join-Path $reports ('ai_runtimes_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.json')
[ordered]@{local_only=$true;gpu=$gpu;steps=@($results.ToArray());inference_validated=$false} |
  ConvertTo-Json -Depth 5 | Set-Content -Path $path -Encoding UTF8
Write-Host ('Raport: ' + $path)
Write-Host 'Nu a fost activat niciun server extern sau serviciu platit.'
