# BERRY AI AUTOPILOT — predare locală către JARVIS ONE ULTIMATE

Data: 11.11.2026. Serverul extern 24/7 și GPU-ul cloud sunt administrate separat de titular. **Acest document NU configurează, nu pornește și nu autorizează servere externe, GPU sau publicarea socială.**

## Livrabilul local

- Cod: [BERRY AI AUTOPILOT](https://github.com/ciupituandrei693-crypto/BERRY-AI-AUTOPILOT)
- Windows portable: după succesul workflow-ului [BERRY Local QA + Windows EXE](../.github/workflows/berry-local-qa-windows.yml), descarcă artefactul `BERRY_AI_AUTOPILOT_WINDOWS_PORTABLE` din fila **Actions**.
- În interiorul ZIP-ului: folderul complet `BERRY_AI_AUTOPILOT` cu executabil, `START_BERRY_PORTABLE.cmd`, README și `.env.example`. Nu extrage doar EXE-ul.
- Pornire: `START_BERRY_PORTABLE.cmd` sau direct `BERRY_AI_AUTOPILOT.exe`; browser local la `http://127.0.0.1:8765`.
- Stocare: `%LOCALAPPDATA%\BERRY_AI_AUTOPILOT\` (SQLite, outputs, assets, scripts și cheia OAuth locală). Fă backup criptat separat înainte de mutarea PC-ului.
- În modul sursă: `LAUNCH_BERRY.cmd` necesită Python și instalarea dependențelor. În modul EXE portabil **nu** este necesară instalarea separată a Python. Motoarele externe precum Blender, HyperFrames, ComfyUI și modelele lor **nu** sunt incluse în EXE.

## API local pentru JARVIS

Configurează în `.env.local`, lângă executabil, o valoare aleatoare de minimum 32 de caractere pentru `BERRY_JARVIS_API_KEY`. Nu pune cheia în GitHub, chat sau capturi de ecran.

- `GET /api/v1/jarvis/capabilities` — capacități și starea motoarelor.
- `POST /api/v1/jarvis/packages` — pachet nou cu `request_id` unic, `channel_id` (`mind|wealth|beats|lab|heart`), `content_type` (`short15|main90|image|longform`) și `topic`.
- `GET /api/v1/jarvis/packages`, `GET /api/v1/jarvis/packages/{id}` — inspectare.
- `GET /api/v1/jarvis/packages/{id}/events` — audit.
- `POST /api/v1/jarvis/packages/{id}/render-local` — randare explicită locală.
- `GET /api/v1/jarvis/packages/{id}/qa` — verificări drepturi, conținut și format.
- `POST /api/v1/jarvis/packages/{id}/review-request` — solicită revizuire umană.

Header obligatoriu: `X-JARVIS-KEY`. Acest API acceptă doar conexiuni loopback. Nu poate aproba, publica, cheltui sau porni cloud. **Nu îl expune direct pe Internet** și nu elimina restricțiile loopback pentru integrarea cu serverul. Viitoarea integrare externă necesită un canal securizat proiectat și testat separat, cu autorizare explicită.

## Verificări de acceptanță

1. Workflow-ul GitHub Actions are **ambele joburi verzi** și a încărcat arhiva Windows.
2. Executabilul trece `--self-test` pe Windows și pornește dashboardul.
3. `TESTE_FINALE_PC.cmd` este rulat pe PC-ul țintă. **SKIP nu este PASS**.
4. Se verifică separat motoarele AI instalate și un videoclip 3D real; testul AFINA CI de 15 secunde este **motion graphics**, nu animație 3D AI.
5. Se conectează conturile YouTube/TikTok/Instagram numai după înregistrarea aplicațiilor de dezvoltator și consimțământul titularului. OAuth-ul disponibil este **read-only**; nu există publicare automată live.
6. Se revizuiesc manual drepturile asupra muzicii, vocii, imaginilor, afirmațiilor și etichetarea AI înainte de export sau publicare.

## Ce rămâne exclus din această predare

Server extern, GPU cloud, costuri, aprobare conturi sociale, publicare automată și garantarea performanței modelelor AI 3D pe PC-ul utilizatorului. Niciunul nu a fost activat.
