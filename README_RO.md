# 🍓 BERRY AI AUTOPILOT v1.1 RC — studio local Windows

**BERRY funcționează local** pentru cinci canale de personaje-fructe. Această versiune adaugă adaptoare reale pentru motoare AI locale, dar **nu conține weights, nu garantează randare AI 3D/video și nu publică online**. Conectarea la server extern și GPU cloud rămâne ultima etapă, numai cu aprobare.

## Un singur buton

1. Descarcă ZIP-ul și dezarhivează folderul BERRY.
2. Pe Windows, fă dublu-click pe **`LAUNCH_BERRY.cmd`**.
3. Dacă nu ai deja un executabil compilat, lansatorul folosește Python **3.11+** și creează automat `.venv`/instalează dependențele gratuite la prima pornire (necesită internet atunci). După instalare, aplicația rulează la **http://127.0.0.1:8765** și se deschide automat în browser.
4. Pentru o distribuție Windows fără Python, pe un PC Windows cu Python rulează **`BUILD_WINDOWS_EXE.cmd`** o singură dată; apoi păstrează întreg folderul `dist/BERRY_AI_AUTOPILOT`. Acest build nu a fost încă verificat pe Windows.

## Funcții locale integrate

- **Content Planner:** 25 fișe pe zi lucrătoare pentru 5 canale (5×90s, 5×15s, 15 imagini), plus fișe longform YouTube 5 minute.
- **SEO Studio:** hook, titluri, descrieri, hashtaguri, CTA și prompturi, șabloane offline sau KoboldCpp local dacă există un model GGUF pornit.
- **Media Studio:** scenarii editabile, subtitrări SRT, imagini concept, video MP4 cu 4 scene și motion graphics FFmpeg, import de imagine, voce, muzică și MP4. Vocea și muzica se pot mixa în același video. Importul unui MP4 înlocuiește montajul standard.
- **AI Local Engines:** ComfyUI (imagini), ACE-Step 1.5 (muzică), VoiceStudio (voce), WanGP (video), faster-whisper (SRT). Sunt adaptoare *opționale*; fiecare necesită model și runtime propriu, separat. Testele de contract cu simulatoare nu înlocuiesc un test cu model real.
- **Quality & Rights QA:** verificare obligatorie a faptelor, drepturilor asupra imaginilor, vocii, muzicii și regulilor platformelor; video importat cu durată greșită este blocat de QA.
- **Approval Center:** aprobare umană fără publicare automată.
- **Calendar & Export:** planificare locală și pachet ZIP cu MP4/PNG/SRT/SEO/QA pentru publicare manuală.
- **Producție în lot:** până la 30 fișe DRAFT procesate secvențial pe CPU; fără cheltuieli.
- **Analytics offline:** import CSV manual cu statistici istorice și sugestii SEO bazate pe datele importate.
- **Backup:** export SQLite local.

## AI local: configurare

Dacă dorești ComfyUI, ACE-Step, VoiceStudio, WanGP sau faster-whisper, consultă **[`docs/LOCAL_AI_ENGINES.md`](docs/LOCAL_AI_ENGINES.md)**. Copiază `.env.example` în `.env.local` și setează doar căile locale necesare. `.env.local` și `data/` sunt ignorate de Git. Nu încărca tokenuri, fișiere private sau weights în GitHub.

## Ce rămâne pentru validare și etapa finală

**Nu este finalizată** animația 3D AI cu rigging/lipsync automat și personaje perfect consistente, nici generarea AI video 5×90s pe zi verificată pe PC-ul țintă. LivePortrait/MuseTalk/LatentSync pot livra MP4 prin import local, dar nu sunt invocate nativ de BERRY. Blender, Hunyuan3D și Chatterbox nu au workflow-uri de producție validate. Licențele WanGP/VoiceStudio/Hunyuan3D și ale weights trebuie revizuite înainte de distribuție sau monetizare.

**ULTIMA ETAPĂ (dezactivată):** server extern, GPU închiriat, acces iPhone din afara PC-ului, OAuth, publicare automată, analytics live și promovare plătită. Nicio plată și nicio postare nu se poate executa din versiunea curentă.

## Testare

`python -m pip install -r requirements.txt -r requirements-dev.txt` apoi `python -m pytest -q`. La asamblarea v1.1 RC au trecut **28/28 teste locale** (inclusiv simulatoare pentru API-urile AI și test FFmpeg). Testele Windows, modelele AI și buildul `.exe` rămân de validat pe calculatorul tău. Vezi `docs/STATUS_LOCAL_V11.md` și `SECURITY.md`.

## Nou în v1.2 RC — animație 3D locală

- **Blender procedural 3D**: armature, mișcări de corp/brațe/cap, gură cu shape keys A–H/X și MP4 vertical + `.blend` editabil.
- **Lip-sync**: Rhubarb local opțional pentru cue-uri fonetice; fallback din energie audio este aproximativ, fără foneme.
- **Diagnostic PC / Windows** în AI Local Engines, timp de randare măsurat în istoricul joburilor.
- **Windows EXE**: scriptul de build verifică automat executabilul cu `--self-test` după compilare. Nu este un EXE deja compilat și testat pe PC-ul utilizatorului.
- **Modelele AI nu sunt incluse și nu au fost benchmarkate pe hardware-ul utilizatorului**. Vezi `docs/LOCAL_3D_RIGGING_LIPSYNC_WINDOWS.md`.
