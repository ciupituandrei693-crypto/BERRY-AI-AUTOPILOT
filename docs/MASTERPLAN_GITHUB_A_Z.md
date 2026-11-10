# BERRY AI AUTOPILOT — MASTERPLAN GITHUB A–Z

Data: 10 noiembrie 2026 · Proiect: BERRY AI FRUIT STUDIO · Mod: Semi-Autopilot

## Reguli ferme
- Dezvoltare și testare **locală pe Windows** mai întâi. Nicio conectare la server extern, GPU închiriat sau conturi sociale până la ultima etapă, cu aprobare explicită.
- Aplicație universală: dashboard web/PWA iOS, Android, Windows și browser; ulterior, doar dacă este justificat, clienți nativi Flutter. Un singur backend securizat.
- Nicio publicare, activare de publicitate sau cheltuială fără aprobarea utilizatorului. Kill Switch, jurnal de audit și reaprobare după modificări.
- Cele 5 canale: FRUIT MIND (MUREX), FRUIT WEALTH (BANAN), FRUIT BEATS (AFINA STAR/RUBY NOTE/GOLD PINE), FRUIT LAB (AFINA), FRUIT HEART (EMERA/CHERO). BERRY = manager.
- Luni–vineri: 5×90s, 5×15s Shorts, 15 imagini/zi. Povești YouTube 5–10 minute separat; frecvența exactă de aprobat.
- Bugete de planificare, nu costuri garantate: producție $250/lună; promovare $100/canal/lună ($500 total); orice plată separată necesită aprobare.
- Repozitoarele sunt candidate, NU componente deja integrate, auditate sau instalate. Licențele și modelele AI se verifică separat, în special pentru uz comercial.

## 0. Arhive deja trimise (cod-sursă, nu runtime complet)
- FastAPI — https://github.com/fastapi/fastapi
- Authlib — https://github.com/authlib/authlib
- FFmpeg — https://github.com/FFmpeg/FFmpeg
- WanGP / Wan2GP — https://github.com/deepbeepmeep/Wan2GP
- ComfyUI — https://github.com/Comfy-Org/ComfyUI
- Blender — https://github.com/blender/blender
- VoiceStudio — https://github.com/debpalash/VoiceStudio
- Chatterbox — https://github.com/resemble-ai/chatterbox
- faster-whisper — https://github.com/SYSTRAN/faster-whisper
- ACE-Step 1.5 — https://github.com/ace-step/ACE-Step-1.5
- Două arhive Chatterbox și două arhive Blender pot fi duplicate. Verificarea ZIP nu dovedește compatibilitate, licențiere comercială ori funcționare.

## 1. Nucleu, AI local, baze de date și joburi — PRIORITATE LOCALĂ
- FastAPI — https://github.com/fastapi/fastapi — backend și API.
- Uvicorn — https://github.com/encode/uvicorn — server local.
- KoboldCpp — https://github.com/LostRuins/koboldcpp — inferență LLM GGUF locală pentru scenarii, SEO și idei.
- llama.cpp — https://github.com/ggml-org/llama.cpp — alternativă backend LLM.
- SQLAlchemy — https://github.com/sqlalchemy/sqlalchemy — ORM; SQLite local.
- Alembic — https://github.com/sqlalchemy/alembic — migrații de baze de date.
- APScheduler — https://github.com/agronholm/apscheduler — programarea lucrărilor locale.
- Dramatiq — https://github.com/Bogdanp/dramatiq — coadă de joburi, opțional când devine necesară.
- LangGraph — https://github.com/langchain-ai/langgraph — orchestrare AI opțională; nu obligatorie în MVP.

## 2. Voce, subtitrări, muzică — PRIORITATE LOCALĂ
- VoiceStudio — https://github.com/debpalash/VoiceStudio — studio audio și integrare voce.
- Chatterbox — https://github.com/resemble-ai/chatterbox — TTS expresiv, compatibilitate de verificat.
- faster-whisper — https://github.com/SYSTRAN/faster-whisper — transcriere și subtitrări.
- Piper — https://github.com/OHF-Voice/piper1-gpl — TTS de rezervă CPU, verificare licență.
- ACE-Step 1.5 — https://github.com/ace-step/ACE-Step-1.5 — muzică originală; cerințe hardware/model.
- Ultimate RVC — arhivă transmisă în altă conversație; sursa exactă și licența trebuie reverificate înainte de includere.
- Nu clonați voci fără drepturi/consimțământ; fiecare fruct are profil vocal original.

## 3. Personaje, imagini, animație, lip-sync și montaj — PRIORITATE LOCALĂ CU TESTE HARDWARE
- Blender — https://github.com/blender/blender — rigging, scene 3D, shape keys/viseme pentru fructe.
- ComfyUI — https://github.com/Comfy-Org/ComfyUI — workflow-uri de imagini AI; modele și dependențe separate.
- WanGP / Wan2GP — https://github.com/deepbeepmeep/Wan2GP — video AI; cerințe GPU ridicate.
- Hunyuan3D-2 — https://github.com/Tencent-Hunyuan/Hunyuan3D-2 — generare asset-uri 3D, opțional și posibil cloud la final.
- LivePortrait — https://github.com/KwaiVGI/LivePortrait — expresii, test pe fețe antropomorfe.
- MuseTalk — https://github.com/TMElyralab/MuseTalk — lip-sync alternativ, test pe fețe antropomorfe.
- LatentSync — https://github.com/bytedance/LatentSync — lip-sync alternativ, test pe fețe antropomorfe.
- FFmpeg — https://github.com/FFmpeg/FFmpeg — export MP4, mixaj, normalizare, subtitrări, Shorts.
- Remotion — https://github.com/remotion-dev/remotion — montaj și grafice programabile, verificare licență.
- HyperFrames — https://github.com/heygen-com/hyperframes — motion graphics, candidat opțional.
- PySceneDetect — https://github.com/Breakthrough/PySceneDetect — control și segmentare scene, opțional.
- Pentru fructe 3D: preferă rigging și forme de gură în Blender înainte de lip-sync antrenat pe fețe umane.

## 4. SEO, cercetare, automatizări și aprobări — PRIORITATE LOCALĂ
- n8n — https://github.com/n8n-io/n8n — orchestrare opțională; licență fair-code, de verificat.
- Agent Reach — https://github.com/Panniantong/Agent-Reach — colectare surse publice, candidat.
- Playwright — https://github.com/microsoft/playwright — teste browser și cercetare permisă.
- Instagram Agent Skill — https://github.com/Jakeschincariol/instagram-agent-skill — candidat pentru sugestii SEO.
- Vyral Content Skills — https://github.com/vyralcontent/content-skills — hook-uri și idei, candidat.
- YouTube Agent Pro — https://github.com/ahmedsakri/youtube-agent-pro — SEO YouTube, candidat.
- YouTube Marketing Skills — https://github.com/adityaarsharma/youtube-marketing-skills — analitice YouTube, ulterior OAuth.
- Stări obligatorii: DRAFT -> RENDERED -> QA_PASSED -> AWAITING_APPROVAL -> APPROVED -> SCHEDULED -> PUBLISHED/FAILED. Editarea după aprobare revocă aprobarea.

## 5. Aplicație universală și pachet Windows — LOCAL, FĂRĂ EXPUNERE INTERNET
- React — https://github.com/facebook/react — interfață dashboard.
- Vite — https://github.com/vitejs/vite — build frontend.
- vite-plugin-pwa — https://github.com/vite-pwa/vite-plugin-pwa — PWA, instalare din browser pe iPhone.
- Tauri — https://github.com/tauri-apps/tauri — înveliș desktop Windows, opțional.
- PyInstaller — https://github.com/pyinstaller/pyinstaller — împachetare executabil Windows, testare.
- Flutter — https://github.com/flutter/flutter — client nativ iOS/Android/Windows, opțional DUPĂ PWA; iOS nativ necesită mediu macOS pentru compilare/distribuire.
- Authlib — https://github.com/authlib/authlib — OAuth pentru conectarea viitoare a conturilor.
- cryptography — https://github.com/pyca/cryptography — criptare și gestionare chei, cu implementare corectă.
- Acces iPhone: pregătim UI local, dar activăm accesul din afara PC-ului doar după HTTPS, autentificare, audit și teste.

## 6. Teste, securitate, backup — LOCAL ÎNAINTE DE ORICE PUBLICARE
- pytest — https://github.com/pytest-dev/pytest — teste API și logică.
- Playwright — https://github.com/microsoft/playwright — teste UI desktop/mobil.
- Ruff — https://github.com/astral-sh/ruff — lint/format Python.
- pip-audit — https://github.com/pypa/pip-audit — vulnerabilități dependințe Python.
- Trivy — https://github.com/aquasecurity/trivy — audit imagini și dependențe.
- Restic — https://github.com/restic/restic — backup criptat.
- QA media: verificare rezoluție, durată, audio, subtitrări, cadre greșite, licențe, personaje coerente, aprobări și export.

## 7. ULTIMA ETAPĂ — conexiuni externe, GPU, social media, analitice
- Tailscale — https://github.com/tailscale/tailscale — acces privat la dashboard de pe iPhone, după securizare.
- Caddy — https://github.com/caddyserver/caddy — HTTPS/reverse proxy, dacă necesar.
- Docker Compose — https://github.com/docker/compose — servicii izolate pentru VPS, opțional.
- PostgreSQL — https://github.com/postgres/postgres — migrare de la SQLite doar dacă este justificată.
- Redis — https://github.com/redis/redis — cozi/cache la scalare, opțional.
- TryPost — https://github.com/trypostit/trypost — candidat scheduler self-hosted, de verificat.
- TikTok Content Posting API — https://developers.tiktok.com/products/content-posting-api
- YouTube Data API — https://developers.google.com/youtube/v3
- Instagram Platform API — https://developers.facebook.com/docs/instagram-platform/
- GPU cloud: furnizor de ales doar după măsurarea performanței locale, plafon de cost și aprobare explicită. Nu porniți GPU/VPS fără aprobare.
- Publicarea depinde de aprobarea conturilor, OAuth, permisiuni API, cote, audituri și politicile fiecărei platforme.

## Ordinea efectivă de construcție
1. Audit cod local v0.1 și arhive; inventar licențe, versiuni, dependențe și test Windows.
2. Refactor backend, SQLite, Character Bible, fișiere, job queue și jurnalizare.
3. KoboldCpp/Qwen3 pentru scenarii și SEO, fără cloud.
4. VoiceStudio + Chatterbox/Piper + faster-whisper; bibliotecă de voci.
5. Blender + ComfyUI + FFmpeg; pilot FRUIT LAB AFINA 90s + 3 imagini + Short 15s.
6. ACE-Step și test video musical original FRUIT BEATS; identitate vocală consistentă.
7. WanGP, lip-sync opțional, montaj Remotion/HyperFrames doar dacă aduc valoare.
8. SEO, calendar, aprobări, Kill Switch, audit, QC, analytics simulată.
9. PWA universală, lansator Windows, autentificare și teste securitate; testare pe iPhone doar prin acces privat securizat.
10. Numai după acceptanța locală: server extern, GPU cloud, conectare OAuth și publicare/analitice reale.

## Criterii de acceptanță finale
- Personaje 3D consecvente și voci distincte, originale, reutilizabile.
- Pipeline cap-coadă pentru un episod 90s, 3 imagini și Short 15s, apoi extindere la 5 canale.
- Muzică originală pentru FRUIT BEATS, fără copierea pieselor protejate.
- Pachet SEO separat pe YouTube/TikTok/Instagram, cu editare și aprobare.
- Calendar cu retry, audit, limite de cost, Kill Switch, fără publicare neaprobată.
- Acces securizat iOS/Android/Windows/web; date și tokenuri protejate.
- Teste locale, backup, procedură de recuperare, verificare drepturi comerciale.
- GPU/VPS și conturile sociale conectate numai la final și cu aprobare separată.

## Notă despre fezabilitate
Pe Ryzen 5 5600X, 16 GB RAM și AMD RX 580 8 GB, editarea, transcrierea CPU și generarea de texte sunt obiective locale rezonabile de testat; generarea a 5 videoclipuri cinematografice ×90s în fiecare zi poate depăși practic performanța GPU-ului local. Nu există garanție de viteză, cost sau monetizare. Nici ZIP-urile cod-sursă nu înlocuiesc modelele AI, driverele și runtime-urile.
