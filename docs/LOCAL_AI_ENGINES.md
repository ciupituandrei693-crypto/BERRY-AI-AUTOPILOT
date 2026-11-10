# BERRY AI — motoare locale, fără server extern (v1.1 RC)

## Ce este deja conectat în cod

BERRY poate comunica **doar cu procese locale** (`127.0.0.1`, `localhost` sau `::1`) și numai după ce utilizatorul a instalat separat motorul și modelele. Nu există fallback cloud, descărcări de weights, costuri, autentificare socială sau postare automată. Butonul `LAUNCH_BERRY.cmd` pornește **BERRY**, nu toate motoarele AI grele simultan. Asta protejează PC-urile cu 16 GB RAM și GPU limitat.

1. **ComfyUI — generare imagine**: REST `/prompt` → `/history/{id}` → `/view`, rezultat `data/assets/item_ID.webp`. Cere ComfyUI pornit local și un workflow exportat în format **API**, care include `SaveImage`. Poți copia `templates/comfyui_api_workflow.json` și înlocui `REPLACE_WITH_YOUR_LOCAL_MODEL.safetensors` cu checkpoint-ul instalat. Șablonul este exemplu, nu include modelul.
2. **ACE-Step 1.5 — muzică originală**: REST `/release_task` → `/query_result` → `/v1/audio`, rezultat WAV/MP3 pentru canalul FRUIT BEATS. Necesită server local și weights. Generează un segment de 30 secunde (coloana muzicală poate fi repetată în video mai lung). Nu garantează originalitate juridică sau drepturi comerciale; QA uman rămâne obligatoriu.
3. **WanGP — video AI**: API Python `shared.api.init(...).submit_task(...)` în mediul Python propriu WanGP, cu setări exportate din interfața WanGP. BERRY copiază MP4 în `data/assets/item_ID_video.mp4`. Modelele și VRAM trebuie configurate separat. Verifică **WanGP Community License 2.0** și licența modelului ales înainte de monetizare. BERRY identifică WanGP în UI și documentație.
4. **VoiceStudio — TTS**: REST OpenAI-compatibil **local** `/v1/audio/speech`, generează WAV, stocat `item_ID_voice.wav`. Necesită VoiceStudio pornit și model vocal instalat. VoiceStudio este AGPL-3.0: verifică obligațiile licenței înainte de distribuire/operare ca serviciu.
5. **faster-whisper — subtitrări din voce**: proces Python local separat, model existent pe disc, `local_files_only=True`, CPU `int8`, SRT pentru vocea importată. Nu transcrie automat muzica și nu descarcă modele.
6. **Piper / Windows SAPI**: fallback TTS deja existent pentru randarea motion graphics; Piper cere `piper.exe` și un model `.onnx`, SAPI folosește vocile Windows.
7. **FFmpeg**: montaj MP4 cu patru scene, subtitrări SRT și **mix voce + muzică**. Import MP4 din LivePortrait, MuseTalk, LatentSync sau alte aplicații locale; BERRY îl verifică cu FFmpeg și îl folosește la randarea FULL.
8. **KoboldCpp**: generator local opțional de texte SEO și scenarii; necesită un model GGUF pornit separat.

## Instalare și configurare

1. Descarcă pachetul BERRY și dezarhivează-l într-un folder Windows.
2. Pornește **`LAUNCH_BERRY.cmd`**. La prima pornire este necesar Python 3.11+ și internet pentru bibliotecile gratuite. Dacă ai compilat `BUILD_WINDOWS_EXE.cmd` pe Windows, lansatorul folosește executabilul din `dist/` și nu mai cere Python pe PC-ul de destinație.
3. Pentru un motor AI, instalează-l **separat**, cu modelul și mediul Python cerute de proiectul său. Nu presupune că un ZIP de cod conține weights sau un executabil Windows.
4. Copiază `.env.example` în `.env.local` și completează doar valorile locale relevante, de exemplu:

```ini
BERRY_COMFYUI_URL=http://127.0.0.1:8188
BERRY_COMFYUI_WORKFLOW=C:\BERRY\workflows\fruit_image_api.json
BERRY_ACE_STEP_URL=http://127.0.0.1:8001
BERRY_VOICESTUDIO_URL=http://127.0.0.1:3900
BERRY_VOICESTUDIO_MODEL=tts-1
BERRY_VOICESTUDIO_VOICE=default
BERRY_WANGP_ROOT=C:\WanGP
BERRY_WANGP_PYTHON=C:\WanGP\.venv\Scripts\python.exe
BERRY_WANGP_SETTINGS=C:\BERRY\workflows\wan_settings.json
BERRY_WHISPER_MODEL=C:\BERRY\models\faster-whisper-small
BERRY_WHISPER_PYTHON=C:\BERRY\whisper-env\Scripts\python.exe
```

5. Repornește BERRY, intră în **AI Local Engines**, verifică `READY`, alege o fișă DRAFT și apasă **Generează cu motorul local**. Procesul rulează în fundal, câte un job AI la un moment dat. După succes, revino la Media Studio → FULL → QA → aprobare → calendar/export manual.

## Motoare pentru care integrarea directă rămâne condiționată

- **LivePortrait, MuseTalk, LatentSync**: importul MP4 rezultat este funcțional. Execuția lor nativă în BERRY nu este încă automatizată; necesită weights, fluxuri de intrare și validare GPU. Nu le prezentăm ca „gata”.
- **Hunyuan3D-2**: doar sursă de cercetare; licența Tencent Hunyuan 3D 2.0 Community și condițiile comerciale trebuie revizuite înainte de integrarea de producție.
- **Blender**: executabil detectabil dacă este instalat; generarea automată de rig-uri 3D cinematice consistente încă nu este implementată.
- **Chatterbox**: motor separat neintegrat nativ; poate fi investigat după verificarea modelului, licenței și hardware-ului. Nu presupunem că VoiceStudio îl expune automat.

## Calitate și hardware

Pe un PC cu **Ryzen 5 5600X, 16 GB RAM, RX 580 8 GB**, BERRY (FastAPI/SQLite/FFmpeg) poate funcționa local; modelele AI 3D/video mari pot să nu încapă sau să fie foarte lente. `READY` confirmă doar endpoint-ul/configurația, **nu** performanța, memoria, calitatea sau rezultatul unui model. Nu este garantat un volum de 5×90s AI video pe zi fără benchmark pe PC.

## Limite de securitate

- Endpoint-urile HTTP sunt restricționate la loopback; redirecturile sunt blocate.
- `BERRY_ACCESS_KEY` poate proteja API-ul local; `data/`, `.env.local`, tokenurile și modelele nu sunt puse pe GitHub.
- Nu activa port forwarding sau expunerea aplicației către internet.
- Toate ieșirile AI necesită verificarea faptelor, drepturilor și etichetării conținutului AI înainte de publicare.
- **Serverul extern, GPU cloud, OAuth și publicarea automată rămân ULTIMA ETAPĂ, cu aprobare explicită.**
