# BERRY AI AUTOPILOT — Stadiul etapelor 1–6, actualizare v1.4 RC

**Data:** 11 noiembrie 2026. **Politică:** Windows/local întâi; niciun cont social, GPU cloud sau server extern activat automat. BERRY este un departament tehnic al JARVIS ONE ULTIMATE, fără asistent/avatar conversațional propriu.

## Etapele implementate în cod și dovezile necesare

| Etapă | Cod disponibil | Test efectiv confirmat |
|---|---|---|
| 1. HyperFrames + OpenClipper | **Da**: HyperFrames CLI -> HTML local/GSAP -> MP4; OpenClipper MCP HTTP numai pentru `list_projects`/`list_exports` | **NU** pentru aceste modificări; cere test MP4 și MCP pe Windows |
| 2. Producție AI locală | **Parțial**: adaptoare ComfyUI, WanGP, Blender, voice, faster-whisper, ACE-Step, FFmpeg, motion graphics și import media | **NU** pentru fiecare model/greutate; modelele nu sunt incluse |
| 3. JARVIS ONE | **Da**: API local securizat, pachete, idempotency, render, QA, evenimente, cerere review; aprobarea și publicarea blocate prin JARVIS | **NU** pe PC după modificări; teste incluse |
| 4. Conturi YouTube/TikTok/Instagram | **Da, opțional pentru autentificare doar citire**: OAuth state unic, PKCE pentru YouTube/TikTok, tokenuri criptate, deconectare locală | **NU** cu conturi reale; necesită aplicații de dezvoltator, credențiale, redirecturi și aprobare |
| 5. Calendar, SEO, publicare, analytics | **Parțial**: SEO, QA drepturi, aprobare umană, calendar local, pachete ZIP pentru publicare manuală, CSV analytics, YouTube channel stats opțional | **NU** pentru upload/publicare live; nu există scope de upload/posting |
| 6. Windows EXE + verificare | **Da**: `START_BERRY_PORTABLE.cmd`, `BUILD_WINDOWS_EXE.cmd`, `TESTE_FINALE_PC.cmd` și CI Windows | **DA în GitHub Actions Windows**: 80 teste trecute, 1 omis; executabil PyInstaller construit și `--self-test` trecut. **NU încă pe PC-ul utilizatorului** |

**Nu reprezenta tabelul ca „6/6 complet funcționale”.** Codul este livrat, dar o parte din motoare, autentificările și publicarea necesită verificări și permisiuni externe.

## Componentele noi

### HyperFrames

- `berry/hyperframes_bridge.py`: HTML generat și escapare anti-injecție, imagine locală, GSAP local obligatoriu, compoziție seekable, job persistent, randare MP4 la cerere, descărcare din dashboard.
- `BERRY_HYPERFRAMES_BIN`: CLI local, de exemplu `...\node_modules\.bin\hyperframes.cmd`.
- `BERRY_HYPERFRAMES_GSAP_PATH`: fișierul `gsap.min.js` local, dacă CLI nu îl are în `dist/vendor/npm/gsap@3.14.2/dist`. **Nu se folosește CDN.**
- MP4-ul creat este **video-concept motion graphics**, nu video AI 3D. Dacă există, poate fi reutilizat în randarea FULL BERRY.

### OpenClipper

- `berry/openclipper_bridge.py`: client MCP Streamable HTTP numai pe `127.0.0.1:12742/mcp` (port configurabil).
- Sunt permise doar `list_projects` și `list_exports`. Nu sunt apelate `patch_ai_clips`, `patch_export_social_metadata` sau funcțiile de publicare.
- Este necesar ca aplicația desktop OpenClipper să ruleze. Arhiva ZIP este sursă, nu executabil instalat.

### JARVIS ONE ULTIMATE

- `berry/jarvis_api.py` + `tests/test_jarvis_api.py`
- Configurare locală: `BERRY_JARVIS_API_KEY` (minimum 32 caractere, distinctă de `BERRY_ACCESS_KEY`).
- `GET /api/v1/jarvis/capabilities`
- `POST /api/v1/jarvis/packages` — `request_id` unic pentru idempotency, canal, format și subiect.
- `GET /api/v1/jarvis/packages`, `GET /api/v1/jarvis/packages/{id}`, `GET /api/v1/jarvis/packages/{id}/events`
- `POST /api/v1/jarvis/packages/{id}/render-local` și `GET /api/v1/jarvis/packages/{id}/qa`
- `POST /api/v1/jarvis/packages/{id}/review-request` — solicită verificare, **nu aprobă**.
- `/approve`, `/publish`, `/cloud/activate` — HTTP **423 Locked**.
- API doar local, `X-JARVIS-KEY` separat, comparație constant-time, SQLite + audit.

### OAuth social (opt-in)

- `berry/social_oauth.py` + `berry/social_routes.py`, criptare Fernet locală.
- `GET /api/social/status`, `POST /api/social/{provider}/start`, `GET /api/social/{provider}/callback`, `POST /api/social/{provider}/disconnect`.
- YouTube: `youtube.readonly` și citire la cerere a statisticilor agregate ale canalului prin `POST /api/social/youtube/channel-stats`.
- TikTok: `user.info.basic` — doar profil.
- Instagram: `instagram_business_basic` — doar profil profesional eligibil.
- **Fără** `youtube.upload`, `video.publish`, `instagram_business_content_publish`; nu există cod care să posteze.
- Implicit `BERRY_SOCIAL_OAUTH_ENABLED=false`. Conectarea reală necesită `BERRY_ACCESS_KEY` de minimum 16 caractere, ID-uri de aplicație, fișiere private de client secret, consimțământ explicit și permisiuni aprobate de platforme.
- Pentru Google OAuth local, redirect exact: `http://localhost:8765/api/social/youtube/callback`. Pentru TikTok/Instagram, redirectul HTTPS aprobat necesită infrastructură accesibilă public; **nu se pornește acum**. Endpointurile/scopurile trebuie reverificate cu documentația platformelor înainte de autorizarea reală.
- Tokenurile sunt criptate în SQLite cu o cheie locală în `%LOCALAPPDATA%\BERRY_AI_AUTOPILOT\private\social_fernet.key`. Nu partaja cheia sau baza de date. Deconectarea locală nu revocă automat tokenul la furnizor; revocă și în contul social.

## Procedură unică Windows

1. Descarcă ultima versiune BERRY din GitHub.
2. Păstrează `.env.local` privat și folderul `%LOCALAPPDATA%\BERRY_AI_AUTOPILOT` existent; nu șterge datele sau tokenurile la actualizare.
3. Rulează `LAUNCH_BERRY.cmd` pentru instalarea dependențelor actualizate și pornirea dashboardului.
4. În **Media Studio**, verifică HyperFrames și OpenClipper. Pentru HyperFrames configurează CLI + GSAP local; pentru OpenClipper pornește aplicația desktop.
5. În **Integrări**, configurează cheia JARVIS separat. OAuth rămâne dezactivat până la configurarea și aprobarea conturilor.
6. Rulează `TESTE_FINALE_PC.cmd`. Raportul JSON se salvează în `%LOCALAPPDATA%\BERRY_AI_AUTOPILOT\reports`.
7. **SKIP = NEVALIDAT, nu PASS.** Nu se poate declara finalizat un motor AI sau un cont social fără testul real corespunzător.

## Testul automat AFINA 15 secunde

`tools/smoke_afina.py` generează, într-o bază temporară separată, un material **FRUIT LAB / AFINA** de 15 secunde prin pipeline-ul local FFmpeg/motion graphics, verifică fișierul MP4 și manifestul, apoi șterge fișierele temporare. Nu atinge proiectele utilizatorului, nu publică și nu folosește cloud. **Nu generează automat o animație 3D AI** și nu înlocuiește testarea ComfyUI/WanGP/Blender/voice.

`TESTE_FINALE_PC.cmd` include acest smoke test în validarea completă. Raportul distinge `PASS`, `FAIL` și `SKIP`; dacă lipsește FFmpeg, testul este `SKIP`, nu `PASS`.

## Ce nu se poate finaliza doar din repository

- Model weights AI, compatibilitatea GPU/driverelor și randarea 3D de calitate fără teste hardware.
- Aprobare Google/TikTok/Meta Developer, configurarea OAuth și autentificarea conturilor de către titular.
- Publicarea automată live, fără scopes, verificări ale platformelor și aprobare explicită pentru acțiunea externă.
- Serverul extern 24/7, domeniul HTTPS și GPU cloud la cerere — fază separată, **neautorizată încă**.

## Stadiul verificării în acest mediu

Fișierele au fost confirmate în repository-ul GitHub. **GitHub Actions 43038564660 a trecut pe Windows și Linux**: 80 teste trecute și 1 omis pe fiecare sistem; testul AFINA de 15 secunde a produs un MP4 real **MOTION_GRAPHICS_LOCAL**, nepublicat, fără GPU cloud. Executabilul Windows PyInstaller a fost compilat, iar `--self-test` a trecut; arhiva portabilă include `START_BERRY_PORTABLE.cmd`. Nu există încă dovadă de funcționare pe PC-ul utilizatorului, OAuth real, publicare automată sau videoclip AI 3D complet. Testele HyperFrames și OpenClipper folosesc simulări/mocks, nu motoarele desktop instalate.

**Regulă de acceptanță:** fiecare etapă se declară finalizată funcțional doar după raportul de test real, fără erori și fără SKIP la componenta relevantă.
