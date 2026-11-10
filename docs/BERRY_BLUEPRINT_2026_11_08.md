# BERRY AI AUTOPILOT — Blueprint de construcție (8 noiembrie 2026)

## Obiectiv confirmat

- **Mod activ în specificație:** Semi-Autopilot, nu funcționalitate implementată.
- **Cinci canale:** FRUIT MIND (MUREX, strugure mov noir), FRUIT WEALTH (BANAN, banană în costum), FRUIT BEATS (AFINA STAR / Ruby Note / Gold Pine; un singur fruct solist per videoclip, piese originale), FRUIT LAB (AFINA, afină albastră cu ochelari de protecție, halat și eprubetă), FRUIT HEART (EMERA, măr verde, și CHERO, cireașă roșie).
- **Program luni–vineri:** 5× video principal de 90 s/zi, 15 fotografii/zi, 5× Short 15 s/zi. Cross-post TikTok, Instagram și YouTube după aprobare.
- **YouTube povești 5–10 minute:** planificare separată; 1 poveste/canal/săptămână este o ipoteză inițială, nu frecvență aprobată.
- **Buget-țintă producție:** $250/lună, nedemonstrat încă la calitatea cerută; **promovare:** până la $100/lună/canal, $500/lună total; buget-țintă agregat $750/lună. Nicio cheltuială efectivă fără aprobare explicită separată.

## Analiza referințelor video

1. `Lets%20reflect%20on...mp4` — **94,0 s**, vertical **512×910**, performanță cu pisică mov antropomorfă în costum, ochelari, decor grandios, gesturi și texte/subtitrări în ritmul interpretării; pentru FRUIT BEATS, melodii și personaje proprii, look cinematografic cu sincronizare labială.
2. `VIDEO-2026-09-15-09-58-36.mp4` — **60,3 s**, vertical **512×910**, măr verde cu coroană, costum, gesturi autoritare, birouri luxoase, cadre dramatice și efecte aurii; model vizual pentru scene FRUIT MIND / FRUIT WEALTH.
3. `VIDEO-2026-09-15-09-58-36(1).mp4` — **60,37 s**, vertical **512×910**, măr roșu și banană în decor cu lumini albastre, discurs/întâlnire, prim-planuri și imagini simbolice (creier holografic); model de scenarizare și editare pentru dialog și educație.
4. `VIDEO-2026-09-15-09-58-36(2).mp4` — **60,37 s**, pare aceeași secvență video ca (1), dar fișierul este diferit; nu se tratează ca episod creativ independent.

Important: preluăm stilul și tehnicile, nu copiem modele, voci, melodii ori alte elemente protejate din videoclipuri.

## Github — blocuri de construcție

| Prioritate | Modul | Proiect | Repo | Loc de execuție |
| --- | --- | --- | --- | --- |
| P0 | Personaje și rigging 3D | Blender | https://github.com/blender/blender | PC pentru scene moderate, cloud pentru randări dificile |
| P0 | Imagini / referințe / fluxuri | ComfyUI | https://github.com/Comfy-Org/ComfyUI | Local unde este compatibil; GPU cloud pentru modele mari |
| P0 | Animații AI image-to-video | WanGP / Wan2GP | https://github.com/deepbeepmeep/Wan2GP | Preferabil RTX cloud |
| P0 | Compoziție și motion graphics | HyperFrames | https://github.com/heygen-com/hyperframes | PC local |
| P0 | Montaj și export | FFmpeg | https://github.com/FFmpeg/FFmpeg | PC local |
| P0 | Dublaj, narare, voci | VoiceStudio | https://github.com/debpalash/VoiceStudio | PC local CPU / test AMD |
| P0 | Subtitrări | faster-whisper | https://github.com/SYSTRAN/faster-whisper | PC local CPU |
| P1 | Muzică originală | ACE-Step 1.5 | https://github.com/ace-step/ACE-Step-1.5 | PC doar dacă suportat sau GPU cloud |
| P1 | Sincronizare buze | LatentSync | https://github.com/bytedance/LatentSync | GPU cloud compatibil; test separat pe fețe de fructe |
| P1 | Construire asset-uri 3D din imagini | Hunyuan3D-2 | https://github.com/Tencent-Hunyuan/Hunyuan3D-2 | GPU cloud; verificare licență și cerințe VRAM |
| P0 | Marketing Instagram | Instagram Agent Skill | https://github.com/Jakeschincariol/instagram-agent-skill | Agent local; nu publică singur |
| P0 | Hook-uri pentru TikTok/Reels/Shorts | Vyral Content Skills | https://github.com/vyralcontent/content-skills | Agent local |
| P0 | SEO YouTube, povești, thumbnails | YouTube Agent Pro | https://github.com/ahmedsakri/youtube-agent-pro | Agent local; nu publică singur |
| P1 | Analiză date canal YouTube OAuth | YouTube Marketing Skills | https://github.com/adityaarsharma/youtube-marketing-skills | Agent local; necesită acces autorizat |
| P1 | Programare și publicare | TryPost | https://github.com/trypostit/trypost | Self-host / VPS; platformele necesită acces API |

## Documentație obligatorie pentru conectarea conturilor

- TikTok Content Posting API: https://developers.tiktok.com/products/content-posting-api ; postările publice prin Direct Post necesită auditul integrării, iar utilizatorul trebuie să autorizeze aplicația.
- YouTube Videos API: https://developers.google.com/youtube/v3/docs/videos/insert ; programare: https://developers.google.com/youtube/v3/docs/videos#status.publishAt .
- Meta Instagram Graph API: verificați documentația oficială și permisiunile actuale pentru tipurile de conturi și publicațiile acceptate înainte de conectare.
- Politica de monetizare YouTube: https://support.google.com/youtube/answer/1311392 — episoadele trebuie să fie substanțial diferite, originale și utile, nu conținut produs în masă fără variație.

## Arhitectură propusă

`BERRY Orchestrator -> Research + Script -> Character Bible / Storyboard -> ComfyUI/Blender -> WanGP -> VoiceStudio/ACE-Step -> LipSync (opțional) -> HyperFrames/FFmpeg -> Subtitle / thumbnail / QA -> SEO Skills -> Approval Batch -> TryPost sau API oficial -> Analytics`.

**Semi-Autopilot:** statusuri `DRAFT` -> `RENDERED` -> `QA_PASSED` -> `AWAITING_APPROVAL` -> `APPROVED` -> `SCHEDULED` -> `PUBLISHED` / `FAILED`. Modificările după aprobare readuc materialul în `AWAITING_APPROVAL`. Kill Switch oprește postările planificate; plățile pentru GPU și reclame au aprobări separate, fără debite automate.

## Criterii minime pentru pilot

1. Două modele de personaje stabile din cele 5 canale, cu aceleași trăsături la cel puțin trei unghiuri și zece expresii.
2. Un video pilot de **90s**, 3 imagini promo și Short de **15s**, cu cadre narative, subtitrări și audio legal.
3. Un video musical cu solist fruct și **melodie originală** cu buze sincronizate cât permite modelul, fără deformări grave.
4. Pachet SEO separat pe platformă, cu titlu, hook, descriere, CTA, hashtaguri și thumbnail.
5. Previzualizare și aprobare de către utilizator; fără publicare automată la primul test.
6. Log de timp și cost GPU pe fiecare scenă; refuz automat al depășirii plafonului fără aprobarea utilizatorului.
7. Păstrarea surselor, licențelor, modelelor și a fișierelor folosite pentru a reface ulterior episodul.

## Stadiu real

Acesta este un **plan tehnic de integrare** și un inventar de proiecte publice, nu o aplicație construită, conectată la conturi sau instalată. Fiecare repository și fiecare model trebuie testate, iar licențele comerciale verificate înainte de monetizare.
