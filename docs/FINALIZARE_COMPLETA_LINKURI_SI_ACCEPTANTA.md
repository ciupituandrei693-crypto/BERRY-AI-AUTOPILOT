# BERRY AI AUTOPILOT — plan de finalizare verificabil

**Stare reală:** repo-ul conține dashboard, flux editorial local, adaptoare de motoare și pregătirea OAuth YouTube **dezactivată**. Nu există încă integrare OAuth live pentru YouTube/TikTok/Instagram, publicare reală, pipeline cinematic validat cap-coadă sau un API JARVIS complet confirmat în ramura main. Nu confunda un mockup sau o arhivă anterioară cu o versiune testată.

## Repository-uri și documentație

| Sistem | Link | Scop | Criteriu de acceptare |
|---|---|---|---|
| Blender | https://github.com/blender/blender | Modelare/rig/render 3D | MP4 cu fruct animat randat pe Windows |
| ComfyUI | https://github.com/comfyanonymous/ComfyUI | Imagini AI | PNG valid generat local din prompt |
| WanGP | https://github.com/deepbeepmeep/Wan2GP | Video AI | clip scurt local, durată/VRAM măsurate |
| LivePortrait | https://github.com/KwaiVGI/LivePortrait | Portrete animate | output MP4 local cu față fictivă |
| MuseTalk | https://github.com/TMElyralab/MuseTalk | Lip-sync | sincronizare testată pe audio original |
| LatentSync | https://github.com/bytedance/LatentSync | Lip-sync alternativ | funcționează numai pe GPU compatibil |
| Hunyuan3D-2 | https://github.com/Tencent/Hunyuan3D-2 | Mesh 3D | export GLB și verificare geometrie |
| Rhubarb | https://github.com/DanielSWolf/rhubarb-lip-sync | Foneme pentru animație | JSON foneme pe audio local |
| VoiceStudio | https://github.com/debpalash/VoiceStudio | Studio vocal | audio generat și licență verificată |
| Piper | https://github.com/OHF-Voice/piper1-gpl | TTS local | WAV valid pentru limba selectată |
| Chatterbox | https://github.com/resemble-ai/chatterbox | TTS alternativ | WAV valid și consimțământ pentru voce |
| faster-whisper | https://github.com/SYSTRAN/faster-whisper | Transcriere | SRT cu timpi corecți |
| FFmpeg | https://github.com/FFmpeg/FFmpeg | Montaj/export | MP4 H.264/AAC 9:16 și 16:9 |
| HyperFrames | https://github.com/heygen-com/hyperframes | Titluri și animații programabile | randare locală fără Pro/Cloud |
| OpenClipper | https://github.com/GrepCut/OpenClipper | Shorts/Reels | clip vertical exportat |
| ACE-Step | https://github.com/ace-step/ACE-Step | Muzică originală | WAV original și drepturi comerciale |
| Instagram Agent Skill | https://github.com/Jakeschincariol/instagram-agent-skill | Idei, hook, descrieri | doar template-uri, fără execuție automată |

## Conectarea conturilor — numai API-uri oficiale

- **YouTube:** https://developers.google.com/youtube/v3 și https://developers.google.com/identity/protocols/oauth2/web-server — OAuth Google, selecție canal, scope read-only inițial; upload separat cu aprobare.
- **TikTok:** https://developers.tiktok.com/doc/login-kit-overview și https://developers.tiktok.com/doc/content-posting-api-get-started — Login Kit, Content Posting API; revizuirea aplicației și permisiuni pot fi necesare.
- **Instagram:** https://developers.facebook.com/docs/instagram-platform/ — autentificare oficială Meta/Instagram, numai conturi eligibile; respectă cerințele de verificare și limitele API.

**Nu se conectează conturi doar cu URL-ul profilului.** Utilizatorul autorizează OAuth; parolele nu intră în BERRY. Cheile și tokenurile nu se salvează în GitHub sau în fișiere de log. Conturile conectate se pot deconecta și revoca.

## Contract propus JARVIS ONE ULTIMATE → BERRY

Versiune API: `/api/v1/jarvis`; doar loopback Windows la început; autentificare prin cheie dedicată în header, comparare constant-time, rate limit, jurnal și idempotency key pentru comenzi. În viitor: identitate de serviciu/mTLS sau HTTPS securizat. **Acesta este un contract de implementat și testat, nu o afirmație că endpointurile există deja.**

| Metodă | Endpoint | Comportament |
|---|---|---|
| GET | `/health` | stare servicii, GPU, disk, versiuni |
| GET | `/channels` | cele cinci canale |
| POST | `/jobs` | creează pachet editorial, returnează job ID |
| GET | `/jobs/{id}` | progres, etape, erori, cost estimat |
| POST | `/jobs/{id}/render` | randare locală, numai motoare verificate |
| GET | `/jobs/{id}/artifacts` | manifest fișiere, hash, MIME, dimensiune |
| POST | `/jobs/{id}/review` | aprobare/respingere material |
| POST | `/jobs/{id}/prepare-publication` | pregătește, nu publică |
| GET | `/integrations` | status OAuth și drepturi |
| POST | `/jobs/{id}/cancel` | anulare și oprire operații |

**Politică:** niciun endpoint JARVIS nu poate declanșa cheltuieli, GPU cloud sau publicare reală fără aprobare umană explicită, verificată pe server. Estimările de cost nu sunt facturi. Fiecare etapă raportează `queued/running/blocked/failed/completed`, `progress_pct`, `artifacts`, `error`, `estimated_cost`.

## Ordine de implementare

1. Fixare versiuni, test suite, instalare Windows, inventar hardware real (GPU/VRAM, RAM, spațiu).
2. Motor imagini → imagine-to-video → voce → subtitrări → FFmpeg, cu teste pe fișiere reale și rapoarte de durată/consum.
3. Editor, bibliotecă media, 5 canale, formate 15s/90s/5–10 min; drepturi muzicale și verificare editorială.
4. API JARVIS cu autentificare, idempotency, jobs persistente, progres, fișiere, audit, kill switch.
5. OAuth Google, TikTok și Instagram: mai întâi mock/local, apoi aprobări platforme, autorizare live explicită.
6. Calendar și publicare supravegheată, retry sigur, statistici, revocare tokenuri.
7. Build EXE Windows și teste end-to-end pe PC-ul utilizatorului; apoi ZIP cu manifest și checksum.
8. Server extern și GPU cloud **numai la final și numai cu aprobare separată**.

## Ce NU este finalizat

Nu există dovada unui test real de producție cinematică de 90 secunde pe hardware-ul utilizatorului, a unei conectări live YouTube/TikTok/Instagram sau a publicării prin API. Pentru aceste etape sunt necesare rulare pe Windows, aprobări OAuth, acreditări de aplicație păstrate privat și eventual verificare de platformă.

## Primul pas pe Windows

1. Descarcă https://github.com/ciupituandrei693-crypto/BERRY-AI-AUTOPILOT/archive/refs/heads/main.zip
2. Rulează `INSTALARE_TOATE_COMPONENTELE.cmd`, apoi `TESTE_FINALE_PC.cmd`.
3. Trimite doar rapoartele de instalare/test (fără parole sau tokenuri). Pe baza lor se aleg motoarele care pot rula efectiv pe GPU-ul tău.
