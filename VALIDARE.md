# Validare BERRY v1.1 RC

- 28/28 teste pytest trecute în mediul Linux de asamblare.
- FastAPI + SQLite, SEO, planificare, aprobare, QA, calendar, export ZIP și backup: testate.
- FFmpeg: preview MP4, motion graphics și import/mix audio-video testate local.
- ComfyUI, ACE-Step 1.5, VoiceStudio: contractele API testate cu răspunsuri simulate. **Nu** s-au executat modele reale.
- WanGP și faster-whisper: adaptoare locale și verificări de configurare; runtime-ul/modelul real nu au fost testate.
- Analytics CSV: import și duplicate testate.
- Fără acces extern, fără OAuth, fără postări, fără plăți.
- Windows, EXE și VRAM: **netestate** în acest mediu; trebuie verificate pe PC.

Comenzi: `python -m pip install -r requirements.txt -r requirements-dev.txt`, `python -m pytest -q`.
