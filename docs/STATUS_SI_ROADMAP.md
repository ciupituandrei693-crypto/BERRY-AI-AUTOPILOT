# Stadiu real și roadmap

## Funcțional în nucleul v0.1

- Backend FastAPI local și interfață responsive cu manifest PWA.
- 5 canale, personaje și bibliotecă de referință.
- Planner cu 25 fișe DRAFT/zi lucrătoare (5 video principale, 5 shorts, 15 imagini).
- SEO pe șabloane, loturi de aprobare/respingere, audit, propuneri de buget și Kill Switch.
- Export CSV; utilitare locale FFmpeg pentru media existentă (necesită instalare FFmpeg).
- Adaptor opțional către KoboldCpp **dacă** acesta rulează deja pe localhost; nu include model GGUF.

## Neimplementat / neverificat

- Generarea reală de imagini, video, muzică, voce, lip-sync și personaje 3D.
- Modele AI, runtime-uri și dependențe media.
- Publicare, OAuth și analytics pe platforme sociale.
- Acces remote securizat iPhone/Android și server extern.
- Execuție pe GPU cloud și estimare demonstrată de cost/viteză.

## Ordinea de dezvoltare

1. Audit licențe și compatibilitate pentru arhivele terțe.
2. Local: voce + transcriere, teste de performanță pe hardware-ul Windows.
3. Local: Blender + ComfyUI + generare media, pilot AFINA.
4. Local: muzică originală, lip-sync, montaj, QA și SEO automatizat.
5. Local: securitate, backup, aprobare, testare end-to-end și interfață PWA.
6. **Doar la final, cu aprobare explicită:** server extern, GPU închiriat, conectarea conturilor sociale și publicare.

Nicio instalare sau integrare a arhivelor externe nu este realizată prin simpla creare a acestei copii GitHub.
