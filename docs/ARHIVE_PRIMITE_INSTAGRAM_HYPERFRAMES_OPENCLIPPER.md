# BERRY — cele 3 arhive primite, verificate și pregătite pentru integrare

**Arhive furnizate în conversație, verificate prin citirea efectivă a fișierelor ZIP.** Nu mai trebuie trimise încă o dată. Au fost inspectate structura, licențele, fișierele executabile relevante și integritatea arhivelor. **Nu am rulat cod terț, nu am instalat aplicații pe PC-ul utilizatorului, nu am conectat conturi sociale și nu am pornit cloud.**

## Inventar verificat

| Sursă | Arhivă | SHA256 | Fișiere ZIP | Dimensiune necomprimată | Licență |
|---|---|---|---:|---:|---|
| [Instagram Agent Skill](https://github.com/Jakeschincariol/instagram-agent-skill) | `instagram-agent-skill-main(2).zip` | `c4bd00ef53fd9c45b5c6e3f6390f3456cac290a6a84ecf1fd97177c692515518` | 45 | 183282 B | MIT |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | `hyperframes-main(2).zip` | `a216caa6a2c7260c5936adcb36895e7ddad2d80dafef3b4f439b52b816361db1` | 11603 | 333303558 B | Apache 2.0 |
| [OpenClipper](https://github.com/GrepCut/OpenClipper) | `OpenClipper-master.zip` | `f9fb461401d34d9f6a20a7dedfdc66f7c7424872776ec735b8b6b303f09585ce` | 901 | 191172204 B | MIT |

Verificările de arhivă au trecut. HyperFrames conține două **symlink-uri** către căi interne (`packages/cli/src/audio/scripts`, `packages/producer/tests/render-symlinked-assets/src/shared`). Importatorul nu le restaurează automat pentru a evita traversarea prin symlink; **un build complet din sursa importată poate necesita refacerea lor și verificare manuală**. Pentru CLI preferăm distribuția oficială npm, instalată separat, cu confirmare.

## Integrarea efectivă BERRY

### Instagram Agent Skill

Sursa include **13 skill-uri** (reel, viral, caption, carousel, story, profile, plan, human, comment, reply, DM, repurpose, audit), cu șase scripturi Python locale. În BERRY sunt conectate **trei verificări offline**, numai după importul sursei:
- `POST /api/seo/instagram/analyze` cu `kind=hook` → `hookscore.py`, evaluare orientativă a hook-ului;
- `kind=caption` → `caption.py`, verificare lungime, hashtaguri, CTA, primul rând;
- `kind=beats` → `beats.py`, împărțirea scenariului în secvențe și estimarea duratei.

Scripturile sunt apelate doar la cerere, după verificarea **SHA256 individuală**, cu `subprocess` fără shell și timeout. Nu se execută automat `SKILL.md`, nu se solicită tokenuri, nu se trimite nimic pe Instagram. **Heuristicile originale sunt în primul rând pentru engleză**, deci scorurile în română sunt doar orientative.

Celelalte zece skill-uri rămân **material de referință editorială**, nu automatizări active. `ig-dm` și `ig-comment` nu vor trimite mesaje/comentarii automat.

### HyperFrames

- Arhiva conține monorepo și pachetul CLI `@hyperframes/cli` versiunea **0.9.33**, cu cerință **Node.js >=22**; sursa folosește și **Bun** pentru buildul monorepo.
- CLI-ul local acceptă `hyperframes render -c ./composition.html -o output.mp4`, dar pentru randare reală sunt necesare instalarea npm, FFmpeg și browser/Chromium local.
- `publish`, `cloud render`, `events` și funcțiile Pro **nu se vor executa automat**. Unele skill-uri upstream sugerează evenimente de telemetrie; BERRY nu invocă acele instrucțiuni.
- În BERRY este pregătită detectarea sursei importate și a CLI-ului, dar **nu există încă dovada randării unui MP4 real** pe PC-ul utilizatorului.

### OpenClipper

- Arhiva este o aplicație **React/Vite + Tauri/Rust** pentru Windows, versiune `26.11.2` în `package.json`.
- Include modele ONNX pentru detecție/reîncadrare, dar transcrierea completă poate necesita descărcarea modelelor Whisper/Parakeet.
- Aplicația poate pregăti Shorts/Reels, subtitrări și export. Are și funcții de conectare/publicare către unele platforme; **BERRY nu le activează**.
- Importul sursei **nu echivalează cu instalarea aplicației desktop**. Pentru rulare se folosește instalatorul oficial Windows sau un build Tauri cu Rust/Windows SDK.
- Nu a fost confirmat un API local stabil OpenClipper pentru control automat de către JARVIS; până atunci, exportul este o operație supravegheată/manuală.

## Instalare din arhivele deja existente pe PC (fără re-descărcare)

1. Descarcă versiunea actualizată a repository-ului BERRY și dezarhiveaz-o.
2. Creează/folosește folderul `incoming` din rădăcina BERRY.
3. Copiază **arhivele ZIP originale, cu aceleași nume** în `incoming`:
   - `instagram-agent-skill-main(2).zip`
   - `hyperframes-main(2).zip`
   - `OpenClipper-master.zip`
4. Rulează `IMPORT_ARHIVE_PRIMITE.cmd` (necesită Python). Mai întâi verifică SHA256/CRC, apoi cere acordul pentru extragere.
5. Sursele ajung în `local_engines/InstagramAgentSkill`, `local_engines/HyperFramesSource` și `local_engines/OpenClipper`. Nu suprascrie foldere existente.
6. În BERRY, deschide **SEO Studio → Instagram Agent Skill — verificare locală** și testează un hook, o descriere sau un scenariu.
7. Rulează `TESTE_FINALE_PC.cmd` și trimite raportul de validare. Nu trimite parole/tokenuri.

Dacă numele ZIP diferă de cele de mai sus sau conținutul s-a schimbat, importatorul se oprește în mod intenționat. Nu îl forța fără o nouă verificare.

## Ce rămâne de finalizat

- Teste Windows cu **MP4 real HyperFrames**, FFmpeg, timpi și calitate.
- Instalare și verificare **OpenClipper desktop** și export vertical real.
- Teste end-to-end pentru AI imagini, image-to-video, voci, subtitrări și montaj.
- API JARVIS cu jobs persistente și control de acces validat.
- OAuth real YouTube/TikTok/Instagram și publicare supravegheată **numai după aprobarea explicită**, cu respectarea cerințelor platformelor.
- Build Windows EXE și test pe GPU-ul utilizatorului.

**Nicio conexiune live, plată, GPU cloud sau server extern nu a fost activată.**
