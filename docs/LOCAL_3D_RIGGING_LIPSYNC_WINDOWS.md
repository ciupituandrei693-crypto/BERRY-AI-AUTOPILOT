# BERRY v1.2 — rigging 3D, lip-sync și verificare Windows

## Ce funcționează în cod

- `tools/blender_fruit_scene.py` generează **personaje-fruct originale 3D procedurale** pentru toate cele cinci canale: MUREX, BANAN, AFINA STAR, AFINA și EMERA (cu un companion cireașă). Nu recreează exact desenele 2D aprobate și nu este încă un pipeline de film 3D cu aceeași identitate vizuală în fiecare episod.
- Fiecare personaj are un **armature Blender** cu oase `Root`, `Body`, `Head`, `Arm.L`, `Arm.R`, `Leg.L`, `Leg.R`; corpul are modificator Armature și vertex group; fața și membrele sunt atașate oaselor; gura are **shape keys A–H și X**. Există animații de gestică și balans.
- Cu voce WAV/MP3, FFmpeg o convertește în WAV PCM. Dacă există **Rhubarb Lip Sync** instalat local, sunt citite cue-uri fonetice A–H; altfel animația gurii este **aproximată din energia sunetului**, NU lip-sync fonetic precis. Fără voce, nu pretindem că există lip-sync.
- Blender produce un proiect `.blend` editabil și un MP4 vertical. FFmpeg poate adăuga vocea, iar MP4-ul este introdus în fluxul existent Media Studio → QA → export. **Nu publică nimic**.
- Istoricul joburilor include durata de procesare și FPS efectiv. Asta devine un benchmark real **numai când rulează pe calculatorul utilizatorului**.

## Pregătire pe Windows

1. Descarcă și instalează **Blender** (versiune compatibilă 4.x), de la https://www.blender.org/download/.
2. Pentru sincronizare fonetică, opțional instalează **Rhubarb Lip Sync**, de la https://github.com/DanielSWolf/rhubarb-lip-sync/releases. Fără acesta, BERRY folosește doar mișcare aproximativă a gurii din amplitudine.
3. Deschide `.env.local` (copiat din `.env.example`) și setează `BERRY_BLENDER_PATH` către `blender.exe` și, dacă există, `BERRY_RHUBARB_PATH` către `rhubarb.exe`.
4. Pornește `LAUNCH_BERRY.cmd` și intră în **AI Local Engines → Diagnostic PC / Windows**. Diagnosticarea verifică prezența executabilelor, NU performanța AI.
5. Creează un material DRAFT de 15 secunde, importă o voce WAV/MP3, selectează **Blender — personaj 3D rigged + lipsync local** și apasă generare. Implicit BERRY randază **maximum 6 secunde**, 360 px lățime, 12 FPS, pentru test. Modifică numai după benchmark: `BERRY_3D_MAX_SECONDS`, `BERRY_3D_WIDTH`, `BERRY_3D_FPS`.
6. La final, în istoricul AI vei vedea timpul în secunde. Fișierul `.blend` se află în directorul local `outputs/rig3d_XXXXXX/`. Pentru montaj folosește Media Studio → FULL. Verifică manual sincronizarea, identitatea personajului, drepturile și calitatea.

## EXE Windows

1. Pe un PC Windows cu Python 3.11+, rulează `BUILD_WINDOWS_EXE.cmd`. Scriptul instalează PyInstaller în `.build-venv`, produce `dist/BERRY_AI_AUTOPILOT/BERRY_AI_AUTOPILOT.exe` și lansează automat `tools/TEST_WINDOWS_BUILD.cmd`.
2. Smoke testul execută `BERRY_AI_AUTOPILOT.exe --self-test`, verificând importurile, resursele UI și scriptul Blender inclus. Rezultatul este salvat în `dist/berry-windows-self-test.json`.
3. Păstrează întreg directorul `dist/BERRY_AI_AUTOPILOT/`. Executabilul nu include Blender, Rhubarb, modele GGUF, ComfyUI sau weights AI. `LAUNCH_BERRY.cmd` îl folosește automat dacă există.
4. **Nu am construit sau executat un EXE Windows în mediul de dezvoltare Linux.** Validarea finală pe Windows și pe placa ta video trebuie făcută local; un test mock nu este dovada funcționării reale.

## Limite de performanță și calitate

- Blender EEVEE poate necesita driver grafic și resurse incompatibile cu unele sisteme. Testează întâi 6 secunde; nu presupune 5×90 secunde zilnic pe RX 580 8GB.
- Modelele ComfyUI, ACE-Step, WanGP, VoiceStudio și faster-whisper **nu sunt incluse** în arhivă. Prezența codului sau a adaptorului nu înseamnă că un model a fost testat. Fiecare motor poate fi testat explicit din AI Local Engines după configurare; timpul este înregistrat per job.
- **Animația 3D este procedurală**, nu model generativ video AI și nu înlocuiește retargeting facial complet ori rigging-ul de studio. Rhubarb oferă cue-uri aproximative, nu sincronizare perfectă a vorbirii în toate limbile.
- Server extern, GPU cloud, API-uri sociale, OAuth și publicarea automată rămân **DEZACTIVATE** până la etapa finală și aprobare separată.
