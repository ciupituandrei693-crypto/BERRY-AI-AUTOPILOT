# 🍓 BERRY AI AUTOPILOT — v1.0 RC (LOCAL)

**Status real:** aplicație locală de planificare, SEO, generare de pachete media, montaj motion graphics, verificare QA, aprobare, calendar, export manual și randare locală în lot, plus producție secvențială locală în lot (maximum 30 de fișe). **Nu** este încă o platformă de animație 3D AI completă și **nu** publică automat pe TikTok, Instagram sau YouTube.

## Un singur buton de lansare

Pe Windows, dezarhivează pachetul și dă dublu-click pe **`LAUNCH_BERRY.cmd`**. Dacă ai compilat aplicația, butonul pornește `dist/BERRY_AI_AUTOPILOT/BERRY_AI_AUTOPILOT.exe`. Altfel pornește versiunea Python, creând automat `.venv` și instalând bibliotecile gratuite la prima utilizare. Pentru prima lansare din sursă trebuie să ai **Python 3.11+** instalat și acces la internet pentru pachetele pip. Ulterior motorul aplicației rulează local la **http://127.0.0.1:8765**.

**Pentru un executabil fără Python la utilizator:** rulează **`BUILD_WINDOWS_EXE.cmd` o singură dată pe un PC Windows cu Python**, apoi distribuie întreg folderul `dist/BERRY_AI_AUTOPILOT`. Acest build Windows este **pregătit, dar nu a putut fi verificat în mediul Linux**. Nu promitem un `.exe` autonom testat înainte de rularea scriptului pe Windows.

## Fluxul complet disponibil local

1. **Content Planner:** planifică 25 de fișe/zi lucrătoare (5×90s, 5×15s, 15 imagini) pentru cele cinci canale; fișe suplimentare YouTube 5–10 min se pot crea separat.
2. **SEO Studio:** titluri, hook, descrieri TikTok/Instagram/YouTube, hashtaguri și prompturi. Șabloane locale; KoboldCpp poate genera text dacă un model GGUF este instalat și pornit separat.
3. **Media Studio:** alege DRAFT, editează scenariul, încarcă imaginea și/sau audio proprii, apasă **FULL** pentru un MP4 cu patru scene și mișcare de cameră, imagine PNG, subtitrări SRT și manifest. `preview` produce doar un clip static scurt. Pentru video este necesar FFmpeg; `imageio-ffmpeg` îl aduce automat ca dependență gratuită la prima instalare. Pe Windows, dacă nu ai Piper configurat, poate folosi vocea offline SAPI (calitatea depinde de vocile Windows).
4. **Quality & Rights QA:** confirmă manual verificarea faptelor, drepturile asupra imaginilor, vocii, muzicii și cerințele platformei. Randarea FULL și toate confirmările sunt obligatorii înainte de programare.
5. **Approval Center:** trimite fișele DRAFT într-un lot și aprobă-le manual. Aprobarea **nu** înseamnă publicare.
6. **Calendar & Export:** programează local materialele aprobate cu QA valid, apoi descarcă un ZIP cu video, imagine, subtitrări, scenariu, SEO și raport QA pentru **publicare manuală**.
7. **Backup:** descarcă baza SQLite într-o arhivă ZIP. Fișierul este privat și nu trebuie pus pe GitHub.

## Ce NU este finalizat / nu poate fi activat fără modele sau permisiuni

- Animație 3D AI cinematică cu rigging și lipsync real pentru fructe: **NU**. Motion graphics cu patru scene este o alternativă locală funcțională, nu echivalentul ei.
- Generare de imagini AI cu ComfyUI, video AI cu WanGP, voce Chatterbox, muzică ACE-Step și lip sync MuseTalk/LatentSync: **NU sunt integrate ca motoare executabile**. Arhivele sursă nu includ automat modelele/weights și dependențele necesare.
- Piese originale cântate de un fruct: nu sunt generate automat. Pentru FRUIT BEATS, importă o piesă originală proprie; QA blochează exportul fără ea. Lip sync pentru personaj nu este implementat.
- Publicare automată, autentificare TikTok/Instagram/YouTube, analitice reale, promovare plătită: **NU**. Acestea sunt rezervate ultimei etape, cu aprobare separată.
- Server extern, GPU cloud, acces iPhone din afara PC-ului: **NU**. PWA este responsive, dar `127.0.0.1` este accesibil doar de pe PC-ul local.

## Siguranță și costuri

Backendul ascultă exclusiv pe `127.0.0.1`. API-ul verifică origin/host, folosește antete de securitate, nu execută shell cu textul utilizatorului, limitează importurile și nu stochează tokenuri sociale. Pentru protecție suplimentară poți configura `BERRY_ACCESS_KEY` ca variabilă de mediu. **Nu expune portul 8765 pe Internet**. Kill Switch începe ACTIV și nicio publicare nu este posibilă în această versiune. Bugetele de 250 USD producție + 500 USD promovare sunt estimări de plan, nu cheltuieli efectuate.

## Testare și dezvoltare

`python -m pip install -r requirements.txt -r requirements-dev.txt` apoi `python -m pytest -q`. Testele rulează cu baze SQLite temporare și fără servicii cloud. Versiunea v1.0 RC a trecut 21 teste automate în mediul Linux de asamblare; **testul final pe Windows este necesar**.

Proiectul nu include ZIP-urile externe, weights, tokenuri, date locale sau fișierele importate de utilizator. Consultă `docs/FINALIZARE_SI_LIMITARI.md`, `SECURITY.md` și `LINKURI_GITHUB.md`.
