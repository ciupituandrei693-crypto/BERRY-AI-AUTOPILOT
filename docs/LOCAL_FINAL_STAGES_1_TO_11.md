# BERRY AI AUTOPILOT — etapele 1–11, LOCAL, fără server extern

## Ce este implementat în cod
- 5 canale, 9 personaje, SEO, Content Planner, QA, aprobare umană, calendar offline, export ZIP, audit și backup.
- Blender procedural: rig cu oase, expresii și mouth shapes A–H/X; Rhubarb opțional pentru sincronizare fonetică (necesită executabil Windows, ZIP-ul sursă nu este suficient).
- Media Studio: montaj FFmpeg, imagini, audio, MP4, subtitrări și export.
- Adaptoare existente: ComfyUI, ACE-Step, VoiceStudio, WanGP, faster-whisper, Piper.
- **Nou:** bridge local opt-in pentru LivePortrait, MuseTalk, LatentSync și Hunyuan3D, bazat pe configurație explicită de executabil Python + argv + checkpoints. Nu rulează automat și nu descarcă weights.
- **Nou:** TESTE_FINALE_PC.cmd produce raport de diagnostic și benchmark FFmpeg/Blender pe Windows. Raportul este salvat local, nu trimis în cloud.

## Ce trebuie configurat pentru fiecare model
1. Instalează motorul și mediul Python separat, în directoare locale, folosind instrucțiunile versiunii de repository pe care o ai.
2. Instalează checkpoints/weights compatibile, după verificarea licenței (inclusiv pentru utilizare comercială).
3. Copiază tools/model_bridge.example.json într-un fișier personal model_bridge.local.json (ignorat de Git).
4. Modifică root, python, argv și weights. CLI-urile upstream se schimbă; exemplele sunt puncte de pornire, NU comenzi validate pe hardware.
5. Adaugă în .env.local: BERRY_MODEL_BRIDGE_CONFIG=C:/cale/absoluta/model_bridge.local.json.
6. Pornește LAUNCH_BERRY.cmd, verifică AI Local Engines. READY = fișiere/config detectate; nu înseamnă că inferența a reușit.
7. Pentru un material DRAFT: încarcă imaginea/vocea/video sursă, apoi pornește explicit modelul. LivePortrait cere imagine + video de mișcare; MuseTalk/LatentSync cer video + voce; Hunyuan3D cere imagine și un adaptor CLI compatibil, furnizat local.
8. Un model este confirmat funcțional numai dacă produce un fișier valid și dacă revizuiești manual rezultatul.

## Teste finale PC
1. Pe Windows, rulează LAUNCH_BERRY.cmd cel puțin o dată (instalează dependențele gratuite Python).
2. Instalează Blender și, opțional, Rhubarb (executabile, nu doar cod sursă).
3. Rulează TESTE_FINALE_PC.cmd. Va instala uneltele de testare gratuite dacă lipsesc, apoi va rula:
   - smoke test FastAPI + SQLite pe o bază temporară;
   - FFmpeg: randare locală MP4 2s la 360×640, 12 fps;
   - Blender: scenă AFINA rigged, 2s, 180px, 8 fps, cu proiect .blend;
   - PyInstaller EXE --self-test, dacă executabilul există;
   - teste automate pytest.
4. Citește raportul JSON din %LOCALAPPDATA%/BERRY_AI_AUTOPILOT/reports.
5. PASS = test efectuat cu succes; SKIP = nu a fost executat; FAIL = trebuie reparat. Nu confunda verificarea FFmpeg cu benchmark GPU de inferență AI.
6. Rulează BUILD_WINDOWS_EXE.cmd pentru a compila executabilul pe Windows, apoi rulează din nou TESTE_FINALE_PC.cmd.

## Limite reale
- Nu există încă weights AI incluse; codul-sursă ZIP nu este același lucru cu un model funcțional.
- **Hunyuan3D generează mesh**, nu un personaj gata riggat; rigging-ul procedural Blender este un pipeline separat. Transferul automat al scheletului pe mesh-uri Hunyuan nu este garantat.
- CLI-urile LivePortrait/MuseTalk/LatentSync trebuie adaptate versiunilor exacte ale arhivelor; bridge-ul oferă execuție locală și verificări, nu dovada compatibilității.
- Arhivele ZIP încărcate în conversație au fost primite, dar nu au putut fi inspectate byte-cu-byte în mediul curent. Integrarea se bazează pe API/CLI public documentat și trebuie verificată cu versiunile exacte ale arhivelor.
- Niciun benchmark de inferență AI pe PC-ul utilizatorului nu poate fi confirmat de aici.
- Windows .exe trebuie construit și testat pe Windows; GitHub conține surse, nu un EXE Windows verificat.
- Nu instala weights/licențe fără verificarea termenilor și a resurselor PC.

## Etapa 12 — ÎN AFARA ACESTEI LIVRĂRI
Server extern, GPU cloud, OAuth, conectarea conturilor sociale, publicare automată, analytics live și reclame cu plată: **dezactivate până la aprobare explicită**.
