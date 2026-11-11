# 🍓 BERRY AI AUTOPILOT v1.4 RC — studio local Windows

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

## Nou în v1.3 RC — integrare locală până la testele finale PC

- Bridge opt-in pentru **LivePortrait, MuseTalk, LatentSync și Hunyuan3D**. Necesită instalarea motoarelor și checkpoints compatibile, separat; configurare în `tools/model_bridge.example.json` copiat în fișier local privat. Nu există instalare automată a weights.
- **TESTE_FINALE_PC.cmd** rulează diagnostic FastAPI/SQLite, FFmpeg, Blender, verificare EXE dacă există și pytest; salvează raport JSON local cu PASS/FAIL/SKIP.
- Dashboardul afișează ultimul raport de testare PC. Statusul READY al unui model înseamnă doar că fișierele configurate există, nu că inferența a reușit.
- **Hunyuan3D nu produce rig automat**, doar mesh printr-un adaptor configurat separat. Animația procedurală Blender este independentă.
- Arhivele încărcate în conversație nu au putut fi inspectate integral în mediul actual. CLI-urile trebuie verificate cu versiunile ZIP.
- **Windows EXE, randarea reală și performanța GPU nu sunt încă validate pe PC-ul tău.** Instrucțiuni: `docs/LOCAL_FINAL_STAGES_1_TO_11.md`.
- **Etapa 12 (server, GPU cloud, conturi sociale, publicare și plăți) rămâne dezactivată.**

## Instalare completa asistata Windows

**Porneste `INSTALARE_TOATE_COMPONENTELE.cmd`** (sau `INSTALARE_COMPONENTE_LOCALE.cmd`). Instalatorul poate instala, cu confirmare, Python/Git/7-Zip/FFmpeg/Blender, Rhubarb Windows executabil, VoiceStudio Windows, ComfyUI portable pentru GPU, PyInstaller, Piper si faster-whisper. Poate descarca si modelele locale selectate (Hugging Face), sursele LivePortrait/MuseTalk/LatentSync/Hunyuan3D/WanGP/ACE-Step si poate pregati medii Python izolate pentru motoarele CUDA compatibile.

**Nu inseamna ca toate motoarele vor rula automat.** Modelele AI mari pot necesita alte checkpoints, CUDA, drivere, Conda, licente si configurari specifice. Pe placi AMD mai vechi sau NVIDIA cu VRAM insuficient, unele modele sunt omise in mod intentionat. LatentSync 1.6 cere cel putin 18 GB VRAM conform autorilor. Scriptul cere confirmare inaintea descarcarilor mari si salveaza un raport `install_*.json` in `%LOCALAPPDATA%\BERRY_AI_AUTOPILOT\reports`.

**Instalarea nu a fost executata pe PC-ul utilizatorului.** Pentru explicatii, limitari si verificare vezi [ghidul complet](docs/INSTALARE_COMPLETA_WINDOWS.md). Dupa instalare ruleaza `TESTE_FINALE_PC.cmd` si trimite raportul. Etapa 12 (cloud/server/OAuth/publicare/plati) ramane dezactivata.

## Componente noi din lista AI FRUIT STUDIO

Instalatorul asistat poate pregati suplimentar **Chatterbox** (TTS separat), **HyperFrames** (video HTML/CSS local), **OpenClipper** (sursa Windows si instalator desktop manual) si **Instagram Agent Skill** (biblioteca de idei, hook-uri, descrieri si planificare, fara postare automata). La final apare raportul `media_addons_*.json` in `%LOCALAPPDATA%\BERRY_AI_AUTOPILOT\reports`. Codul si pachetele instalate nu garanteaza functionarea motoarelor; sunt necesare teste reale Windows. Vezi [documentatia](docs/INSTALARE_COMPLETA_WINDOWS.md).

## Google OAuth / YouTube (PREGĂTIRE OFFLINE)

În pagina **Integrări**, BERRY afișează cinci sloturi YouTube și permite salvarea unui plan local cu nume/ID canal, fără verificarea identității. `youtube.readonly` este singurul scope pregătit; conectarea Google, callbackul și uploadul răspund cu HTTP 423 și nu stochează tokenuri. Butonul Google este dezactivat. Vezi [ghidul de pregătire](docs/YOUTUBE_GOOGLE_OAUTH_PREPARATION.md).

## Arhivele BERRY primite și analizate — nu retrimite

Au fost primite și verificate cele trei ZIP-uri: `instagram-agent-skill-main(2).zip` (MIT), `hyperframes-main(2).zip` (Apache 2.0), `OpenClipper-master.zip` (MIT). Hash-urile SHA256, inventarul și limitările sunt documentate în [analiza arhivelor](docs/ARHIVE_PRIMITE_INSTAGRAM_HYPERFRAMES_OPENCLIPPER.md).

**Import local fără re-descărcare:** copiază ZIP-urile originale în `incoming/` și execută `IMPORT_ARHIVE_PRIMITE.cmd`. Importatorul verifică SHA256, CRC, căi nesigure și symlink-uri, nu suprascrie surse existente și nu execută cod terț. În SEO Studio, instrumentele `hookscore.py`, `caption.py` și `beats.py` din arhiva Instagram pot fi apelate local după import, cu SHA256 individual verificat. Scorurile originale sunt predominant pentru engleză și orientative în română.

**HyperFrames și OpenClipper nu sunt încă randate/instalate funcțional pe PC-ul utilizatorului.** Pentru HyperFrames folosim CLI-ul oficial npm separat; OpenClipper necesită aplicația desktop Tauri sau build Windows. Conturile sociale și cloud rămân dezactivate.

## Actualizare v1.4 RC — JARVIS, HyperFrames, OpenClipper, OAuth opțional

[**Stadiul exact al celor 6 etape, cu teste și limitări**](docs/STATUS_IMPLEMENTARE_ETAPE_1_6_2026_11_11.md).

- **JARVIS ONE ULTIMATE**: API local `/api/v1/jarvis` cu cheie separată, creare draft, randare, QA și cereri de review; nu poate aproba sau publica.
- **HyperFrames**: adaptor CLI local cu GSAP local obligatoriu, generare HTML sigur, job MP4 și descărcare. Este un video-concept, nu animație AI 3D.
- **OpenClipper**: citire proiecte și exporturi prin MCP local `127.0.0.1:12742`, când aplicația desktop este pornită; fără modificare sau publicare.
- **OAuth YouTube/TikTok/Instagram**: cod opt-in pentru conectare cu permisiuni de citire/profil, state unic și tokenuri criptate local. Implicit este **dezactivat**; necesită aplicații de dezvoltator, chei și autorizarea ta. TikTok/Instagram necesită callback HTTPS aprobat.
- **YouTube statistici**: interogare agregată doar la cerere după conectare; analytics CSV și calendarul local rămân disponibile fără OAuth.
- **Windows**: `LAUNCH_BERRY.cmd`, `BUILD_WINDOWS_EXE.cmd` și `TESTE_FINALE_PC.cmd` actualizate; raportul testează inclusiv HyperFrames MP4 și OpenClipper MCP dacă sunt configurate. Testul complet include și un **AFINA 15 secunde** end-to-end local, într-o bază temporară.

**Nu declara aplicația finalizată operațional până când nu trec testele reale pe Windows.** Nu au fost activate conturi, publicare, server extern sau GPU cloud.
