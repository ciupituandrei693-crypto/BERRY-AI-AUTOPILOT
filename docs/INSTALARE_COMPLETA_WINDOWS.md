# BERRY — Instalare completa asistata Windows (etapele locale 1–11)

Acest instalator **nu a fost executat pe PC-ul utilizatorului**. Este un script cu confirmare la fiecare descarcare. Internetul este folosit pentru descarcarea componentelor gratuite; **nu** pentru inferenta cloud, server extern, OAuth, publicare sau plati.

## Pornire

1. Descarca ultima arhiva a repository-ului BERRY, dezarhiveaz-o.
2. Deschide `INSTALARE_TOATE_COMPONENTELE.cmd` (sau `INSTALARE_COMPONENTE_LOCALE.cmd`).
3. Accepta numai pachetele si licentele pe care doresti sa le instalezi. Descărcarile mari pot dura mult si pot ocupa zeci de GB.
4. La final, trimite raportul `%LOCALAPPDATA%\BERRY_AI_AUTOPILOT\reports\install_*.json`.
5. Ruleaza `TESTE_FINALE_PC.cmd` pentru validare. Daca doresti EXE, ruleaza `BUILD_WINDOWS_EXE.cmd` si apoi repeta testele.

## Componentele instalate de script, daca sunt acceptate

| Componenta | Ce face scriptul | Ce ramane de verificat |
|---|---|---|
| Blender | winget; scrie BERRY_BLENDER_PATH daca gaseste executabilul | Randare reala si compatibilitate versiune |
| Rhubarb | Descarca arhiva Windows oficiala v1.14.0; extrage rhubarb.exe | Calitate lipsync |
| FFmpeg | winget | Codare MP4 |
| Python/Git/7-Zip | winget daca lipsesc | PATH si drepturi Windows |
| PyInstaller | pip in .venv BERRY | Build Windows si test EXE |
| Piper | pip piper-tts; optional voci romanesti din rhasspy/piper-voices | Licenta vocii, ONNX, test TTS |
| faster-whisper | pip; optional model small Systran/faster-whisper-small | Test transcriere CPU |
| VoiceStudio | Descarca installerul oficial v0.5.7 x64 si il porneste cu confirmare | Modele vocale prin Model Manager, licente |
| ComfyUI | Portable oficial NVIDIA/AMD v0.44.0 (1.7–2.1 GB) | GPU/driver, model de imagini, workflow API |
| LivePortrait | Cloneaza sursa; optional weights HF; runtime Python separat la cerere | Python 3.10, PyTorch CUDA, inferenta |
| MuseTalk | Cloneaza sursa; optional weights HF; runtime Python separat la cerere | VAE, Whisper, DWPose, SyncNet, CUDA |
| LatentSync | Cloneaza sursa; **nu** descarca automat 1.6 | 1.6 cere min. 18 GB VRAM; Windows manual |
| Hunyuan3D-2 | Cloneaza sursa; optional weights mini; runtime separat | PyTorch/extensii, mesh GLB, rigging |
| WanGP | Cloneaza sursa; poate porni installerul oficial scripts/install.bat | Modele si setari din UI, CUDA |
| ACE-Step | Cloneaza sursa; optional weights; runtime Python separat | Compatibilitate versiune API, GPU, licente |
| Chatterbox | Cloneaza resemble-ai/chatterbox si poate instala chatterbox-tts in Python 3.11 separat | Inferenta TTS, model, VRAM, licenta vocii; upstream nu mai ofera suport |
| HyperFrames | Instaleaza Node.js 22+ si hyperframes@0.9.33 local cu npm | Randare MP4 si FFmpeg; doar CLI local gratuit, nu Studio Pro |
| OpenClipper | Cloneaza sursa GrepCut/OpenClipper; ofera linkul oficial pentru installerul Windows | Instalare desktop manuala, modele locale si export; publicare dezactivata |
| Instagram Agent Skill | Cloneaza Jakeschincariol/instagram-agent-skill ca referinta | Analiza si adaptarea template-urilor in managerul BERRY, fara executie si fara postare |

**Semnificatia raportului:** `INSTALLED` = installerul/pip a reusit; `PRESENT` = fisierul/folderul detectat; `SOURCE_ONLY` = doar cod; `WEIGHTS_DOWNLOADED` = doar checkpoint; `DEPS_INSTALLED` = pachete Python instalate; `MANUAL` = interventie necesara; `SKIP` = omis; `FAILED` = eroare. **Niciunul nu garanteaza inferenta AI functionala.**

## Compatibilitate PC

- Daca PC-ul are **Radeon RX 580 8 GB**, majoritatea pipeline-urilor CUDA NVIDIA (MuseTalk, LatentSync, WanGP) nu vor rula direct. Nu descarca weights foarte mari inainte de a decide alternativa compatibila.
- Daca PC-ul are **RTX 2060 12 GB**, unele modele pot rula cu rezolutie mica/offloading, dar **LatentSync 1.6 cere cel putin 18 GB VRAM** conform proiectului oficial; nu il instalăm automat.
- Hunyuan3D-2 cere aproximativ 6 GB VRAM pentru generarea geometriei, iar texturarea completa aproximativ 16 GB. Varianta mini poate fi mai usoara.
- MuseTalk a documentat un test Windows cu RTX 3050 Ti 4 GB VRAM, dar timpul de procesare poate fi mare.
- Nu promitem productie zilnica de 5 videoclipuri de 90 secunde pana nu masuram timpii reali pe PC.

## Securitate, licente, spatiu

- Executabilele Rhubarb, VoiceStudio si ComfyUI provin din release-urile oficiale GitHub, dar scriptul nu verifica semnaturi criptografice independente. Verifica sursa si protectia Windows inainte de executie.
- Model weights se descarca prin `tools/install_weights_local.py` din repository-uri Hugging Face listate explicit. Scriptul nu foloseste tokenuri, nu executa weights si nu accepta surse arbitrare.
- Checkpoint-urile au licente proprii, distincte de cod. Inainte de monetizare, verifica drepturile de utilizare comerciala, voce, imagine si muzica.
- Pentru ComfyUI, WanGP si VoiceStudio, modelele se aleg separat in functie de GPU si licenta. **Nu exista un singur set universal de weights.**
- Scriptul nu instaleaza drivere NVIDIA/AMD, CUDA Toolkit, Conda sau extensii native in mod nesupravegheat.
- Datele si fisierele sunt locale. Nu activeaza publicare, cloud, reclame sau server extern.

## Daca apar erori

Trimite raportul JSON `install_*.json` si, daca exista, `ai_runtimes_*.json`. Nu trimite chei API, tokenuri sau date personale. Vom repara fiecare motor in ordinea dependintelor, apoi rulam `TESTE_FINALE_PC.cmd`.

## Completari din tabelul BERRY — AI FRUIT STUDIO

Cele patru resurse suplimentare se instaleaza optional prin `tools/INSTALL_BERRY_MEDIA_ADDONS_WINDOWS.ps1` sau din `INSTALARE_TOATE_COMPONENTELE.cmd` (se solicita confirmare). Se genereaza un raport separat `media_addons_*.json`.

- **[Chatterbox](https://github.com/resemble-ai/chatterbox)**: TTS alternativ in mediu Python separat. Repository-ul original este disponibil ca arhiva fara suport; nu se cloneaza voci reale fara permisiune.
- **[HyperFrames](https://github.com/heygen-com/hyperframes)**: generare video determinista din HTML/CSS, animatii, titluri, subtitrari si elemente grafice; Node.js 22+ si FFmpeg. Folosim doar CLI local gratuit; functiile Pro/hosted sunt excluse.
- **[OpenClipper](https://github.com/GrepCut/OpenClipper)**: aplicație Windows pentru selectie si reformatare Shorts/Reels; sursa este clonata, iar instalatorul desktop se obtine manual de la [pagina oficiala](https://grepcut.com/en/open-clipper). Are functionalitati de conectare si publicare, dar BERRY nu le activeaza.
- **[Instagram Agent Skill](https://github.com/Jakeschincariol/instagram-agent-skill)**: 13 skill-uri pentru hook-uri, scenarii, descrieri, profil, calendar, analiza si reutilizarea continutului. Sursa este doar referinta pentru managerul BERRY; **nu ruleaza automat scripturi si nu publica**.

**Important:** instalarea surselor nu echivaleaza cu integrarea lor functionala in pipeline-ul BERRY. Testele de randare, TTS si export Shorts se fac separat pe PC-ul Windows, dupa instalare. Niciun cont social, token, API extern sau serviciu platit nu este conectat.
