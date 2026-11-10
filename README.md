# 🍓 BERRY AI AUTOPILOT

**Versiune: 0.1 — nucleu local Windows / FastAPI + interfață web/PWA.**

> **Stadiu:** cod funcțional pentru planificare, propuneri SEO pe șabloane, aprobări, bugete propuse și Kill Switch. **Nu este aplicația finală:** generarea AI de imagini, videoclipuri, voci și muzică, publicarea pe rețelele sociale și accesul iPhone la distanță nu sunt încă integrate.

## Pornire locală pe Windows

1. Instalează Python **3.11 sau 3.12**.
2. Descarcă acest repository și extrage-l într-un folder (de exemplu `C:\BERRY_AI`).
3. Rulează `start_berry.bat`. Prima pornire instalează dependențele Python prin pip.
4. Deschide `http://127.0.0.1:8765`.

Alternativ, din terminal:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn berry.app:app --host 127.0.0.1 --port 8765
```

## Teste

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest -q
```

## Documentație

- [Ghid complet în română](README_RO.md)
- [Masterplan A–Z și linkuri GitHub](docs/MASTERPLAN_GITHUB_A_Z.md)
- [Biblioteca componentelor externe](docs/EXTERNAL_COMPONENTS.md)
- [Stadiu și pași de integrare](docs/STATUS_SI_ROADMAP.md)
- [Publicare în GitHub](docs/INCARCARE_GITHUB.md)
- [Securitate](SECURITY.md)
- [Licențiere și proveniență](docs/LICENTE_SI_ASSETS.md)

## Reguli de operare

- **Local-first:** fără server extern, GPU închiriat sau conexiuni la conturi sociale în acest stadiu.
- **Semi-Autopilot:** nicio publicare sau cheltuială fără aprobare explicită.
- **Kill Switch:** activ inițial; în această versiune nici dezactivarea lui nu permite publicare reală.
- Nu publica `.env`, baze de date, chei API, fișiere model, voci personale sau date ale conturilor.
- Nu expune serviciul local pe Internet; ascultă doar pe `127.0.0.1`.

## Notă privind licența

Codul BERRY și documentația sunt separate de repository-urile externe, care **nu sunt incluse** aici. Nu este acordată implicit o licență open-source pentru codul BERRY; alege licența înainte de a face repository-ul public. Verifică separat drepturile pentru imagini, personaje și orice componente integrate ulterior.


**One-click Windows launch:** double-click `LAUNCH_BERRY.cmd` (Python 3.11+ prerequisite). Local Media Studio creates storyboard assets and optional static FFmpeg previews, not final AI videos. See [README_RO.md](README_RO.md).
