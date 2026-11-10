# BERRY AI AUTOPILOT - instalare asistata Windows, exclusiv LOCAL
# Lansare: INSTALARE_COMPONENTE_LOCALE.cmd
# NU porneste GPU cloud, server extern, OAuth, publicare sau servicii platite.
# Descarcarile gratuite necesita internet si spatiu liber; cere confirmare.
param([switch]$SkipPackages)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Set-Location $PSScriptRoot
$Root = $PSScriptRoot
$Engines = Join-Path $Root 'local_engines'
$Models = Join-Path $Root 'local_models'
$Downloads = Join-Path $Engines '_downloads'
$ReportDir = Join-Path $env:LOCALAPPDATA 'BERRY_AI_AUTOPILOT\reports'
foreach ($dir in @($Engines, $Models, $Downloads, $ReportDir)) {
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
}
$Results = New-Object 'System.Collections.Generic.List[object]'
function Record([string]$Name, [string]$Status, [string]$Detail) {
  $Results.Add([ordered]@{name=$Name;status=$Status;detail=$Detail}) | Out-Null
  Write-Host ('[' + $Status + '] ' + $Name + ' - ' + $Detail)
}
function Ask([string]$Question) {
  $answer = Read-Host ($Question + ' [d/N]')
  return ($answer -match '^(d|da|y|yes)$')
}
function Command-Exists([string]$Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
              [Environment]::GetEnvironmentVariable('Path','User')
}
function Install-Winget([string]$Id, [string]$Name) {
  if (-not (Command-Exists 'winget')) {
    Record $Name 'MANUAL' 'winget/App Installer nu este disponibil.'
    return
  }
  if (-not (Ask ('Instalez ' + $Name + ' prin winget?'))) {
    Record $Name 'SKIP' 'Refuzat sau amanat.'
    return
  }
  & winget install --id $Id --exact --source winget --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -eq 0) { Record $Name 'INSTALLED' 'Comanda winget a reusit; verifica executabilul.' }
  else { Record $Name 'FAILED' ('winget exit=' + $LASTEXITCODE) }
}
function Add-Env([string]$Key, [string]$Value) {
  if (-not $Value -or $Value.Contains([char]10) -or $Value.Contains([char]13)) { return }
  $file = Join-Path $Root '.env.local'
  $lines = @()
  if (Test-Path $file) { $lines = @(Get-Content $file -Encoding UTF8) }
  $pattern = '^\s*' + [regex]::Escape($Key) + '='
  $lines = @($lines | Where-Object { $_ -notmatch $pattern })
  $lines += ($Key + '=' + $Value.Replace('\','/'))
  [IO.File]::WriteAllLines($file, [string[]]$lines, ([System.Text.UTF8Encoding]::new($false)))
}
function Download-File([string]$Url, [string]$Path) {
  if (Test-Path $Path) {
    if ((Get-Item $Path).Length -gt 10000) { return $true }
    Remove-Item $Path -Force
  }
  try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $Url -OutFile $Path -UseBasicParsing -MaximumRedirection 8
    if ((Get-Item $Path).Length -le 10000) { throw 'Fisier incomplet.' }
    return $true
  } catch {
    Remove-Item $Path -Force -ErrorAction SilentlyContinue
    Write-Warning ('Download esuat: ' + $_.Exception.Message)
    return $false
  }
}
function Free-GiB {
  try {
    $drive = (Get-Item $Root).PSDrive
    return [math]::Round($drive.Free / 1GB, 1)
  } catch { return 0 }
}
function Clone-Source([string]$Name, [string]$Url) {
  $dest = Join-Path $Engines $Name
  if (Test-Path (Join-Path $dest '.git')) {
    Record $Name 'PRESENT' 'Sursa Git exista; nu este suprascrisa.'
    return
  }
  if (Test-Path $dest) {
    Record $Name 'MANUAL' 'Folder partial existent; verifica si repara inainte de clonare.'
    return
  }
  if (-not (Command-Exists 'git')) {
    Record $Name 'MANUAL' 'Git lipseste; reia dupa instalare.'
    return
  }
  if (-not (Ask ('Descarc sursa ' + $Name + ' de pe GitHub?'))) {
    Record $Name 'SKIP' 'Sursa nu a fost descarcata.'
    return
  }
  & git clone --depth 1 $Url $dest
  if ($LASTEXITCODE -eq 0) { Record $Name 'SOURCE_ONLY' 'Cod descarcat; weights si dependentele pot lipsi.' }
  else { Record $Name 'FAILED' 'Clonare Git esuata.' }
}
function Find-Python {
  $exe = Join-Path $Root '.venv\Scripts\python.exe'
  if (Test-Path $exe) { return $exe }
  if (Command-Exists 'py') {
    & py -3.11 -m venv (Join-Path $Root '.venv')
  } elseif (Command-Exists 'python') {
    & python -m venv (Join-Path $Root '.venv')
  }
  if (Test-Path $exe) { return $exe }
  return $null
}
function Install-Pip([string]$Python, [string]$Name, [string[]]$PipArgs) {
  if (-not $Python -or -not (Test-Path $Python)) {
    Record $Name 'MANUAL' 'Mediul Python nu este disponibil.'
    return $false
  }
  if (-not (Ask ('Instalez ' + $Name + ' in mediul local Python?'))) {
    Record $Name 'SKIP' 'Instalare amanata.'
    return $false
  }
  & $Python -m pip install @PipArgs
  if ($LASTEXITCODE -eq 0) {
    Record $Name 'INSTALLED' 'Pachete instalate; testul functional urmeaza.'
    return $true
  }
  Record $Name 'FAILED' 'pip a esuat; verifica dependentele si compatibilitatea.'
  return $false
}
function Download-Weights([string]$Python, [string]$Name, [string]$Folder, [string]$Warning) {
  if (-not $Python -or -not (Test-Path $Python)) { Record $Name 'MANUAL' 'Python lipseste.'; return $false }
  if ((Free-GiB) -lt 12) { Record $Name 'SKIP' 'Sub 12 GiB liberi; nu descarc weights.'; return $false }
  if (-not (Ask ('Descarc weights ' + $Name + ' in ' + $Folder + '? ' + $Warning))) {
    Record $Name 'SKIP' 'Weights amanate.'
    return $false
  }
  & $Python (Join-Path $Root 'tools\install_weights_local.py') $Name --dest $Folder
  if ($LASTEXITCODE -eq 0) {
    Record $Name 'WEIGHTS_DOWNLOADED' 'Doar fisiere locale; inferenta NU a fost verificata.'
    return $true
  }
  Record $Name 'FAILED' 'Download HF esuat, licenta/retea/spatiu/versiune; verifica mesajul.'
  return $false
}
Write-Host ''
Write-Host 'BERRY - INSTALARE COMPONENTE LOCALE, FARA CLOUD' -ForegroundColor Cyan
Write-Host 'Scriptul nu este executat de ChatGPT pe calculatorul tau.'
Write-Host 'Internetul este folosit doar pentru instalarea pachetelor si modelelor gratuite.'
Write-Host 'Nu se instaleaza drivere GPU, nu se foloseste GPU cloud si nu se fac plati.'
Write-Host ('Spatiu liber in folderul BERRY: ' + (Free-GiB) + ' GiB')
$gpuNames = @()
try { $gpuNames = @(Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }) } catch {}
$gpu = ($gpuNames -join ' / ')
Write-Host ('GPU detectat: ' + $gpu)
$Nvidia = ($gpu -match 'NVIDIA')
$Amd = ($gpu -match 'AMD|Radeon')
if (-not $Nvidia) {
  Write-Warning 'Nu s-a detectat NVIDIA CUDA. MuseTalk, LatentSync, WanGP si unele modele 3D pot fi incompatibile sau foarte lente.'
}
if ((Free-GiB) -lt 25) { Write-Warning 'Sub 25 GiB liberi: instalarea tuturor modelelor nu este recomandata.' }
if (-not (Ask 'Continui cu instalarea locala?')) {
  Record 'Instalare' 'CANCELLED' 'Utilizatorul a oprit procedura.'
} else {
  if (-not $SkipPackages) {
    if (-not (Command-Exists 'py') -and -not (Command-Exists 'python')) {
      Install-Winget 'Python.Python.3.11' 'Python 3.11'
    } else { Record 'Python' 'PRESENT' 'Interpretor detectat.' }
    if (-not (Command-Exists 'git')) { Install-Winget 'Git.Git' 'Git' }
    else { Record 'Git' 'PRESENT' 'Git detectat.' }
    if (-not (Command-Exists 'ffmpeg')) { Install-Winget 'Gyan.FFmpeg' 'FFmpeg' }
    else { Record 'FFmpeg' 'PRESENT' 'FFmpeg detectat.' }
    $blender = Get-Command blender -ErrorAction SilentlyContinue
    $blenderFolder = Join-Path $env:ProgramFiles 'Blender Foundation'
    if (-not $blender -and (Test-Path $blenderFolder)) {
      $blender = Get-ChildItem $blenderFolder -Filter blender.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    }
    if (-not $blender) { Install-Winget 'BlenderFoundation.Blender' 'Blender 3D' }
    else { Record 'Blender 3D' 'PRESENT' 'Executabil gasit.' }
    if (-not (Test-Path (Join-Path $env:ProgramFiles '7-Zip\7z.exe'))) {
      Install-Winget '7zip.7zip' '7-Zip (pentru ComfyUI)'
    }
  }
  Refresh-Path
  $blenderFolder = Join-Path $env:ProgramFiles 'Blender Foundation'
  if (Test-Path $blenderFolder) {
    $found = Get-ChildItem $blenderFolder -Filter blender.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { Add-Env 'BERRY_BLENDER_PATH' $found.FullName }
  }
  $ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
  if ($ff) { Add-Env 'BERRY_FFMPEG_PATH' $ff.Source }
  $python = Find-Python
  if ($python) {
    Record 'BERRY Python .venv' 'PRESENT' 'Mediu virtual disponibil.'
    $ok = Install-Pip $python 'BERRY + teste + PyInstaller + Piper + faster-whisper + Hugging Face' @('-r','requirements-dev.txt','pyinstaller','piper-tts','faster-whisper','huggingface_hub')
    if ($ok) {
      Set-Content (Join-Path $Root '.venv\berry-ready-v12.flag') 'ready'
      Add-Env 'BERRY_WHISPER_PYTHON' $python
      $piper = Join-Path $Root '.venv\Scripts\piper.exe'
      if (Test-Path $piper) { Add-Env 'BERRY_PIPER_PATH' $piper }
      $whisperPath = Join-Path $Models 'faster-whisper-small'
      if (Download-Weights $python 'whisper_small' $whisperPath 'Model local pentru subtitrari; cateva sute de MB.') {
        Add-Env 'BERRY_WHISPER_MODEL' $whisperPath
      }
      $piperPath = Join-Path $Models 'piper-voices'
      if (Download-Weights $python 'piper_ro' $piperPath 'Voci romanesti; verifica licenta modelului ales.') {
        $voice = Get-ChildItem $piperPath -Filter '*.onnx' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($voice) { Add-Env 'BERRY_PIPER_MODEL' $voice.FullName }
        else { Record 'Piper voice' 'MANUAL' 'Nu a fost gasit un model .onnx romanesc.' }
      }
    }
  } else { Record 'BERRY Python .venv' 'FAILED' 'Python 3.11 nu este disponibil; reia instalarea.' }
  # Rhubarb: use the OFFICIAL prebuilt Windows release, not source ZIP.
  $rhubarbDir = Join-Path $Engines 'Rhubarb'
  $rhubarb = Get-ChildItem $rhubarbDir -Filter rhubarb.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $rhubarb) {
    if (Ask 'Descarc Rhubarb 1.14.0 Windows ZIP oficial (~87 MB)?') {
      $archive = Join-Path $Downloads 'Rhubarb-Lip-Sync-1.14.0-Windows.zip'
      $url = 'https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Windows.zip'
      if (Download-File $url $archive) {
        New-Item -ItemType Directory -Force -Path $rhubarbDir | Out-Null
        try {
          Expand-Archive -LiteralPath $archive -DestinationPath $rhubarbDir -Force
          $rhubarb = Get-ChildItem $rhubarbDir -Filter rhubarb.exe -Recurse | Select-Object -First 1
        } catch { Record 'Rhubarb' 'FAILED' 'Dezarhivarea a esuat.' }
      }
    }
  }
  if ($rhubarb) {
    Add-Env 'BERRY_RHUBARB_PATH' $rhubarb.FullName
    Record 'Rhubarb Lip Sync' 'INSTALLED' 'Executabil Windows detectat; testul fonetic urmeaza.'
  } else { Record 'Rhubarb Lip Sync' 'MANUAL' 'Executabil Windows inca nedetectat.' }
  # VoiceStudio official Windows installer, not a remote PowerShell script.
  $voiceSetup = Join-Path $Downloads 'VoiceStudio-0.5.7-win-x64.exe'
  if (Ask 'Descarc si pornesc instalatorul oficial VoiceStudio v0.5.7 x64 (~222 MB)?') {
    $url = 'https://github.com/debpalash/VoiceStudio/releases/download/v0.5.7/VoiceStudio-0.5.7-win-x64.exe'
    if (Download-File $url $voiceSetup) {
      if (Ask 'Execut instalatorul VoiceStudio descarcat de pe GitHub?') {
        try {
          $process = Start-Process -FilePath $voiceSetup -Wait -PassThru
          Record 'VoiceStudio' 'INSTALLER_RAN' ('Instalator terminat cu cod ' + $process.ExitCode + '; modelele vocale se aleg in aplicatie.')
        } catch { Record 'VoiceStudio' 'FAILED' 'Instalatorul nu a putut porni.' }
      }
    }
  } else { Record 'VoiceStudio' 'SKIP' 'Instalare amanata.' }
  # ComfyUI official GPU-specific portable bundle; requires 7-Zip and significant disk.
  $comfy = Join-Path $Engines 'ComfyUI'
  $comfyLaunch = @(Get-ChildItem $comfy -Filter 'run_*gpu*.bat' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($comfyLaunch.Count -gt 0) {
    Record 'ComfyUI' 'PRESENT' 'Launcher portabil detectat; verifica motorul si checkpoint-urile.'
  } elseif (Test-Path $comfy) {
    Record 'ComfyUI' 'MANUAL' 'Folder incomplet; muta-l sau repara-l inainte de instalare.'
  } elseif ((Free-GiB) -lt 18) {
    Record 'ComfyUI' 'SKIP' 'Sub 18 GiB liberi.'
  } elseif (-not $Nvidia -and -not $Amd) {
    Record 'ComfyUI' 'MANUAL' 'GPU necunoscut/Intel: selecteaza pachetul portabil compatibil.'
  } else {
    $variant = if ($Nvidia) { 'nvidia' } else { 'amd' }
    if ($Amd) { Write-Warning 'ComfyUI AMD necesita GPU si driver compatibil; RX 580 poate fi incompatibil cu ROCm modern.' }
    $url = 'https://github.com/Comfy-Org/ComfyUI/releases/download/v0.44.0/ComfyUI_windows_portable_' + $variant + '.7z'
    if (Ask ('Descarc ComfyUI portable ' + $variant + ' (~1.7-2.1 GB)? GPU-ul poate necesita driver/compatibilitate specifica')) {
      $archive = Join-Path $Downloads ('ComfyUI_windows_portable_' + $variant + '.7z')
      $sevenZip = Join-Path $env:ProgramFiles '7-Zip\7z.exe'
      if (-not (Test-Path $sevenZip)) { Record 'ComfyUI' 'MANUAL' '7z.exe nu a fost gasit.' }
      elseif (Download-File $url $archive) {
        New-Item -ItemType Directory -Force -Path $comfy | Out-Null
        & $sevenZip x $archive ('-o' + $comfy) -y
        if ($LASTEXITCODE -eq 0) {
          Record 'ComfyUI' 'INSTALLED' 'Portable extras; modelul de imagine si workflow-ul API raman de configurat.'
          Add-Env 'BERRY_COMFYUI_URL' 'http://127.0.0.1:8188'
        } else { Record 'ComfyUI' 'FAILED' '7-Zip nu a putut extrage arhiva.' }
      }
    } else { Record 'ComfyUI' 'SKIP' 'Descarcare amanata.' }
  }
  # All sources are downloaded separately, to avoid incompatible shared environments.
  $repos = @(
    @{name='LivePortrait';url='https://github.com/KlingAIResearch/LivePortrait.git'},
    @{name='MuseTalk';url='https://github.com/TMElyralab/MuseTalk.git'},
    @{name='LatentSync';url='https://github.com/bytedance/LatentSync.git'},
    @{name='Hunyuan3D-2';url='https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git'},
    @{name='WanGP';url='https://github.com/deepbeepmeep/WanGP.git'},
    @{name='ACE-Step';url='https://github.com/ace-step/ACE-Step.git'},
    @{name='VoiceStudio-source';url='https://github.com/debpalash/VoiceStudio.git'}
  )
  foreach ($repo in $repos) { Clone-Source $repo.name $repo.url }
  # Heavy models: opt-in only, no automatic CUDA/PyTorch/driver installation.
  if ($python -and (Test-Path $python)) {
    $heavy = @(
      @{name='liveportrait';dir='LivePortrait';folder='pretrained_weights';warn='GPU NVIDIA recomandat; model mare.'},
      @{name='musetalk';dir='MuseTalk';folder='models';warn='Necesita si dependente auxiliare (VAE, Whisper, DWPose, SyncNet).'},
      @{name='hunyuan3d_mini';dir='Hunyuan3D-2';folder='weights_mini';warn='Model mini de geometrie; nu produce rig automat.'},
      @{name='ace_step';dir='ACE-Step';folder='checkpoints';warn='Model muzical mare; poate necesita mult spatiu si GPU.'}
    )
    foreach ($model in $heavy) {
      $source = Join-Path $Engines $model.dir
      if (-not (Test-Path $source)) {
        Record $model.name 'MANUAL' 'Sursa motorului nu este prezenta.'
        continue
      }
      if (-not $Nvidia) {
        Record $model.name 'SKIP' 'GPU NVIDIA nedetectat; nu descarc model greu inutil.'
        continue
      }
      if ((Free-GiB) -lt 30) {
        Record $model.name 'SKIP' 'Sub 30 GiB liberi pentru model greu.'
        continue
      }
      $folder = Join-Path $source $model.folder
      $null = Download-Weights $python $model.name $folder $model.warn
    }
    if ($Nvidia -and (Free-GiB) -ge 30) {
      Record 'LatentSync 1.6' 'MANUAL' 'Necesita minimum 18 GB VRAM la inferenta; nu descarc automat pe GPU necunoscut.'
    } else {
      Record 'LatentSync 1.6' 'SKIP' 'Cerintele GPU sunt prea mari sau insuficient verificate.'
    }
  }
  # Optional upstream-specific environments are always isolated from BERRY.
  if ($Nvidia -and (Ask 'Pregatesc si mediile Python separate pentru LivePortrait/MuseTalk/Hunyuan3D/ACE-Step si WanGP?')) {
    & (Join-Path $Root 'tools/INSTALL_AI_RUNTIMES_WINDOWS.ps1') -ProjectRoot $Root
    Record 'AI runtimes separate' 'INSTALLER_RAN' 'Verifica raportul ai_runtimes_*.json; nu inseamna inferenta validata.'
  }
  # These projects require their own CUDA/PyTorch/Conda environments.
  # Never blindly pip-install all of them into the BERRY environment.
  Record 'LivePortrait runtime' 'MANUAL' 'Python 3.10 + PyTorch/requirements conform README; configureaza weights si bridge.'
  Record 'MuseTalk runtime' 'MANUAL' 'Conda Python 3.10, CUDA si dependentele auxiliare conform README.'
  Record 'LatentSync runtime' 'MANUAL' 'Upstream setup_env.sh este Linux; configurare Windows separata.'
  Record 'Hunyuan3D runtime' 'MANUAL' 'Necesita PyTorch si extensii native; testeaza versiunea Windows.'
  Record 'WanGP runtime' 'MANUAL' 'Ruleaza local_engines\WanGP\scripts\install.bat, daca exista, pentru configurare GPU.'
  Record 'ACE-Step runtime' 'MANUAL' 'Python 3.10 + PyTorch compatibil; verifica README upstream.'
  Record 'ComfyUI model/workflow' 'MANUAL' 'Alege checkpoint cu licenta potrivita si exporta un workflow API JSON.'
  Record 'VoiceStudio voice model' 'MANUAL' 'Instaleaza un model vocal prin managerul intern si verifica licenta.'
  Record 'PyInstaller EXE' 'MANUAL' 'Ruleaza BUILD_WINDOWS_EXE.cmd pe Windows, apoi TESTE_FINALE_PC.cmd.'
}
$report = [ordered]@{
  product = 'BERRY AI AUTOPILOT'
  timestamp_utc = [DateTime]::UtcNow.ToString('o')
  machine = $env:COMPUTERNAME
  gpu_detected = $gpu
  free_gib_at_end = Free-GiB
  local_only = $true
  cloud_gpu_used = $false
  social_accounts_connected = $false
  publishing_enabled = $false
  paid_services_enabled = $false
  steps = @($Results.ToArray())
}
$filename = 'install_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.json'
$path = Join-Path $ReportDir $filename
$report | ConvertTo-Json -Depth 7 | Set-Content -Path $path -Encoding UTF8
Write-Host ''
Write-Host ('Raport instalare: ' + $path) -ForegroundColor Cyan
Write-Host 'INSTALLED/PRESENT nu inseamna ca modelele au trecut teste de inferenta.'
Write-Host 'SOURCE_ONLY si WEIGHTS_DOWNLOADED nu inseamna runtime functional.'
Write-Host 'Pentru validare finala: TESTE_FINALE_PC.cmd'
Write-Host 'Etapa 12 (server, GPU cloud, OAuth, postare, plati) ramane DEZACTIVATA.'
