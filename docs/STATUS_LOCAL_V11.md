# BERRY v1.1 RC — status de asamblare

| Componentă | Status verificat | Limitare |
|---|---|---|
| FastAPI + SQLite + PWA + 5 canale | Cod + teste locale | Test final Windows necesar |
| Un singur `LAUNCH_BERRY.cmd` | Script pregătit | Python necesar prima dată dacă nu există EXE compilat |
| FFmpeg motion graphics | Testat local | Nu este animație 3D AI |
| ComfyUI API image | Contract testat cu mock | Necesită workflow + checkpoint + motor pornit |
| ACE-Step 1.5 API music | Contract testat cu mock | Necesită server + weights; originalitate de verificat |
| VoiceStudio API TTS | Contract testat cu mock | Necesită model vocal instalat; licență AGPL |
| WanGP Python API | Adaptor pregătit, fără test de model | Necesită runtime + model + setări exportate + verificare licență |
| faster-whisper | Worker local pregătit, fără model real testat | Necesită Python separat și model local |
| Piper/SAPI | Integrare/fallback existente | Voce depinde de instalare și sistem |
| Import MP4/WAV/MP3/imagini | Testat prin API | Drepturi și QA uman obligatorii |
| Voice + music mix | FFmpeg integrat | În video importat, audio furnizat înlocuiește pista originală |
| SEO, QA, aprobări, calendar, export ZIP | Cod + teste locale | Publicare manuală |
| Analytics CSV offline | Testat | Nu reprezintă date live |
| LivePortrait / MuseTalk / LatentSync | Import video posibil | Fără invocare nativă automată |
| Hunyuan3D / Blender / Chatterbox | Inventariate | Modele/rigging/licențe/hardware nevalidate |
| Server extern / GPU cloud / API sociale | DEZACTIVATE | Ultima etapă, aprobare separată |

**Nu confunda adaptoarele software cu modele AI instalate.** Un ZIP de repository nu înseamnă un model gata de inferență. Nicio generare AI media reală nu a fost probată în mediul de dezvoltare fără modelele utilizatorului.
