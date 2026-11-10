# BERRY 1.0 RC — ce s-a integrat și ce a rămas blocat

Data: 2026-11-10. Fără conectare la servicii externe, fără costuri.

## Module implementate și testate

- FastAPI + SQLite, 5 canale / 9 personaje, fișe DRAFT și plan zilnic, SEO local, loturi și aprobare umană, buget propus, audit și Kill Switch.
- Media Studio cu editare scenariu, import imagine PNG/JPEG/WEBP (max 8 MB) și audio WAV/MP3 (max 25 MB), FFmpeg auto-disponibil prin `imageio-ffmpeg`, opțional Piper și Windows SAPI, fișiere de producție, montaj motion graphics FULL 15/90/300 sec, PNG, SRT, manifest.
- QA cu drepturi și verificări umane, calendar local cu dată ISO și fus orar, verificare a amprentei QA, pachete ZIP pentru publicare **manuală**, backup SQLite.
- PWA responsive, origine/host limitate, local-only, launcher Windows și script de build PyInstaller.
- Teste automate (20/20) pe Linux, inclusiv randare FFmpeg 15 sec, QA, aprobare, programare, ZIP și backup. Buildul Windows nu a fost rulat aici.

## Limitări tehnice și licențe

- **3D AI cinematic**: codul Blender, Hunyuan3D, ComfyUI și WanGP din arhive este sursă, nu un motor instalat/configurat. Fără modele, rig-uri de personaje, dependențe GPU și teste hardware, nu se poate certifica generarea AI 3D.
- **Vocile naturale**: Piper necesită fișier .onnx și configurare locală; Chatterbox/VoiceStudio necesită integrare și modele. Windows SAPI este o alternativă offline, nu voce de studio.
- **Muzică AI originală**: ACE-Step necesită instalare și modele; nu e activ. FRUIT BEATS acceptă importul unei piese originale cu drepturi confirmate.
- **Publicare și social analytics**: niciun OAuth/API activ. Calendarul este local și ZIP-ul trebuie postat manual; nicio publicare automată.
- **iPhone remote**: doar după autentificare, HTTPS și tunel privat, în faza finală cu acord separat.
- **Licențe externe**: nu au fost importate automat repository-uri terțe. Înainte de distribuire/comercializare trebuie revizuite licențele componentelor și drepturile asupra imaginilor incluse în `static/img`.
- **Windows build**: scriptul `BUILD_WINDOWS_EXE.cmd` trebuie rulat pe Windows; `.exe` nu este livrat în acest ZIP.

## Pași de verificare pe Windows

1. Deschide `LAUNCH_BERRY.cmd` și verifică localhost:8765.
2. Creează un material FRUIT LAB 15s, salvează scriptul, randează FULL și descarcă MP4.
3. Bifează manual QA numai după verificarea reală a drepturilor și afirmațiilor; aprobă lotul.
4. Adaugă data și platforma în calendar, descarcă ZIP și verifică MP4/SEO/SRT.
5. Descarcă backup, verifică existența arhivei, testează Kill Switch.
6. Dacă dorești pachet fără Python la destinație, rulează `BUILD_WINDOWS_EXE.cmd` și testează întreg folderul `dist/BERRY_AI_AUTOPILOT`.

**Atenție:** randarea FULL 90s/300s poate dura semnificativ pe CPU, în funcție de hardware. Nu confunda motion graphics cu generare AI video 3D.
