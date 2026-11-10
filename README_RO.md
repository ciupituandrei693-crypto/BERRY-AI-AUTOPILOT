# 🍓 BERRY AI AUTOPILOT — LOCAL V0.1

**Aplicație reală de planificare, SEO și aprobare locală**, cu backend FastAPI, interfață web responsive/PWA și bază SQLite. Rulează pe Windows fără server extern, fără GPU cloud și fără abonament. Proiectul este un **nucleu funcțional**, NU încă motor complet de producție AI video sau programator de postări.

## Pornire pe Windows

1. Instalează **Python 3.11/3.12** dacă nu există, bifând `Add Python to PATH`.
2. Dezarhivează fișierul ZIP într-un folder simplu, ex. `C:\BERRY_AI`.
3. Dublu-click pe **`start_berry.bat`**. La prima pornire descarcă pachetele Python gratuite (`fastapi`, `uvicorn`, `pydantic`) folosind internetul. Ulterior rulează local.
4. Browserul se deschide la **http://127.0.0.1:8765**.
5. Lasă fereastra neagră deschisă cât timp folosești aplicația. Închizi cu `Ctrl+C`.

Alternativ: `python -m pip install -r requirements.txt` și `python -m uvicorn berry.app:app --host 127.0.0.1 --port 8765`.

### Cum folosești

1. **Canale & personaje**: verifică FRUIT MIND/MUREX, FRUIT WEALTH/BANAN, FRUIT BEATS/AFINA STAR, FRUIT LAB/AFINA (afină albastră cercetătoare) și FRUIT HEART/EMERA & CHERO.
2. **Content Planner**: poți crea **un pachet editorial pentru o zi (25 fișe DRAFT)** sau adaugă o fișă de episod 90s, Short 15s, imagine sau poveste YouTube 5–10 min. Primește automat un pachet SEO **pe bază de șabloane**.
3. **SEO Studio**: previzualizează descrieri personalizate pentru YouTube, TikTok, Instagram, hook, CTA, hashtaguri și prompturi.
4. **Content Planner → selectează DRAFT → creează lot**.
5. **Approval Center**: aprobă lotul ori respinge. Aprobarea = `APPROVED_NOT_PUBLISHED`. Nu se transmit postări.
6. **Bugete**: adaugă propuneri GPU sau reclamă **fără plată și fără autorizarea de cheltuire**.
7. **Integrări**: vezi Kill Switch, activ implicit, și conectorii marcați neconectați. Jurnalizează modificările.
8. Poți exporta catalogul de conținut în CSV.

### Ce funcționează efectiv acum

- 5 canale seed + 9 personaje; grafici de referință incluse;
- creare și stocare persistentă de fișe media în SQLite; generator de plan zilnic cu 25 fișe DRAFT în zilele lucrătoare;
- generare deterministă de **texte-propunere SEO** și prompturi vizuale;
- grupare în loturi, aprobare/respingere, audit;
- registru de propuneri de cost, control Kill Switch;
- interfață responsive/PWA și export CSV;
- două utilitare opționale locale pentru creare Short 15s și extragere 3 imagini dintr-un videoclip existent (necesită FFmpeg instalat separat).

### Ce NU funcționează încă

- Nu există generare imagine/video 3D sau melodii AI; grafica inclusă este doar concept de personaj.
- Nu există conectare de conturi Google/Meta/TikTok, nicio publicare API și niciun marketing plătit.
- Nu există model local GGUF instalat în aplicație. Dacă ai deja KoboldCpp pornit pe `http://127.0.0.1:5001`, butonul „Încearcă AI local” din SEO Studio poate genera text cu modelul tău (modelele și prompturile trebuie testate).
- Nu există actualizare automată a trendurilor și nici SEO bazat pe metrici reale.
- Nu există server extern, închiriere GPU sau acces remote iPhone configurat.
- Nu există plăți automate. `$250 + $500 = $750` reprezintă limitele de **planificare**, fără garanția că vor acoperi întreaga producție.

## iOS și aplicația universală

Frontendul este **responsive și are manifest PWA**, dar acum serverul ascultă **doar 127.0.0.1**, așa încât iPhone-ul nu poate intra încă direct. Am respectat cerința să lăsăm **serverul și conectivitatea externă la final**. După securizarea prin HTTPS, autentificare și conexiune privată (ex. Tailscale), va fi accesibil din Safari și poate fi adăugat pe ecranul principal. **Nu expune portul public pe Internet în această etapă.**

## Securitate

- Programul nu face apeluri externe automate în utilizare. Numai prima instalare `pip` necesită internet.
- API-ul e disponibil exclusiv pe localhost. Opțional poți seta variabila `BERRY_ACCESS_KEY` înainte de pornire; interfața va cere cheia. Nu salva parole sociale în fișierele proiectului.
- Kill Switch pornește ACTIV, iar publicarea reală este *inexistentă* chiar dacă îl dezactivezi.
- Auditul este salvat în `data/berry.sqlite3`. Nu include parole.
- Nu sincroniza folderul `data` cu servicii publice sau repository Git.
- Înainte de orice utilizare multi-device sau prin Internet trebuie adăugată autentificare reală, HTTPS, CSRF protection, rate limiting, backup și rotație de secrete.

## Formatul editorial aprobat

5 canale × [1 videoclip 90s + 3 imagini + 1 Short 15s] în fiecare zi lucrătoare; povești YouTube de 5–10 min pe calendar separat, câte una pe nișă/săptămână ca ipoteză de test. Piesa canalului FRUIT BEATS va fi **originală**, un singur solist-fruct pe episod. Promovare: 100 USD/canal/lună, total 500; producție: țintă 250 USD/lună (nevalidată).

## Roadmap: local până la final

**Faza 1 – inclusă în arhivă:** structură backend, bază de date, design responsive/PWA, character bible, planner, SEO template, aprobări, Kill Switch.

**Faza 2 – local:** generator efectiv de scenarii cu KoboldCpp/Qwen3; motor media FFmpeg/VoiceStudio; salvat fișiere în bibliotecă, test pe 5 episoade. Nu porni niciun serviciu cloud.

**Faza 3 – local:** integrare grafică Blender, șabloane video HyperFrames, versiune de producție cu jurnalizare, QA automat și testare licențe.

**Faza 4 – local:** autentificare întărită, teste de securitate, PWA pregătită pentru acces privat și gestionare sincronizată a proiectelor.

**Faza 5 – ULTIMA:** numai după aprobare explicită conectăm server extern, GPU închiriat și conturile TikTok/Instagram/YouTube prin API-uri oficiale. Nicio activare automată, nicio cheltuială implicită.

## Dezvoltare și teste

`python -m pip install pytest httpx` (doar pentru teste); apoi `python -m pytest -q`. Pentru arhitectură și integrări GitHub, vezi `LINKURI_GITHUB.md`.

### Structura fișierelor

- `berry/app.py` — API FastAPI
- `berry/db.py` — SQLite și date de bază
- `berry/seo.py` — șabloane SEO și adaptor opțional KoboldCpp
- `static/` — UI/PWA
- `data/` — baza locală (creată la prima pornire)
- `tools/` — FFmpeg local
- `tests/` — teste automate
- `start_berry.bat` — lansator Windows

**Licență:** codul nou din această arhivă este oferit pentru utilizarea ta în proiectul BERRY; nu include cod copiat din proiectele externe enumerate. Licențele proiectelor externe trebuie verificate separat înaintea integrării.
