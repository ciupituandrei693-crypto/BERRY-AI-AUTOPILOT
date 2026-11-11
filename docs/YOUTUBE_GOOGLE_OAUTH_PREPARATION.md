# BERRY AI FRUIT STUDIO — Google OAuth / YouTube (PREGĂTIT, DEZACTIVAT)

**Stare: `PREPARED_OFFLINE`.** Nicio autentificare Google, niciun token, niciun upload, niciun API YouTube și nicio conexiune externă nu sunt activate. Butonul „Conectează Google” este blocat. Acesta este un modul de pregătire, **nu o integrare OAuth funcțională**.

## Ce există în cod

- `berry/youtube_oauth.py`: scope read-only, generare locală a unui URL OAuth 2.0 cu state + PKCE S256 (fără deschidere), parser offline pentru `channels.list?mine=true`, indicatori de configurare fără expunerea secretelor.
- `berry/db.py`: tabelul `youtube_channel_plans` pentru asocierea **neconfirmată** a celor cinci branduri BERRY cu nume și ID-uri YouTube introduse manual. Nu stochează tokenuri.
- `berry/app.py`: `GET /api/integrations/youtube/plan`, `POST /api/integrations/youtube/channel-plan`, `DELETE /api/integrations/youtube/channel-plan/{fruit_channel_id}`. Endpointurile `connect`, `callback` și `upload` răspund cu **HTTP 423 Locked**.
- `static/index.html` și `static/app.js`: status, cinci canale, formular local și buton Google dezactivat.
- `tests/test_youtube_oauth.py`: teste offline pentru scope, PKCE, validarea ID, unicitate, protecție Origin, lipsa conectării/publicării.

## Fluxul viitor, doar după aprobare explicită

1. Utilizatorul apasă „Conectează cu Google” în browserul Windows.
2. Backendul generează un `state` aleator, PKCE verifier/challenge, sesiune expirabilă, apoi validează callbackul.
3. Google solicită acord pentru `https://www.googleapis.com/auth/youtube.readonly` (**fără upload**).
4. Backendul schimbă codul în tokenuri prin HTTPS și apelează `channels.list?part=snippet&mine=true`.
5. Utilizatorul confirmă asocierea canalului Google verificat cu unul dintre cele cinci branduri BERRY.
6. Tokenurile vor fi stocate **criptat** într-un spațiu privat, cu reconectare, expirare și revocare.
7. Publicarea va fi un modul separat, cu `youtube.upload` și aprobare explicită.

**Pașii 2–7 nu sunt implementați în această versiune.** Funcțiile pure pentru URL și parser nu fac cereri și nu sunt expuse ca autorizare live.

## Configurare Google Cloud pentru un test viitor

1. Deschide [Google Cloud Console](https://console.cloud.google.com/) și creează/selectează proiectul tău.
2. Activează **YouTube Data API v3**.
3. Configurează **Google Auth Platform**: Branding, Audience, Data Access. Pentru Testing, adaugă utilizatorii de test; anumite scope-uri și aplicații publice pot necesita verificare Google.
4. Creează **OAuth Client ID** de tip **Web application**.
5. În Authorized redirect URIs, pentru un viitor test Windows strict local, adaugă exact:

   `http://localhost:8765/api/integrations/youtube/callback`

   Callbackul actual răspunde intenționat HTTP 423. **Nu încerca încă autentificarea.**
6. Păstrează fișierul `client_secret.json` într-un folder privat în afara repository-ului. Nu îl trimite în chat și nu îl urca pe GitHub.
7. Numai când aprobi testul, poți pregăti în `.env.local`:

   `BERRY_GOOGLE_OAUTH_CLIENT_ID=...apps.googleusercontent.com`

   `BERRY_GOOGLE_OAUTH_CLIENT_SECRET_FILE=C:\Users\...\AppData\Local\BERRY_AI_AUTOPILOT\private\google_oauth_client.json`

   Acestea sunt doar **indicatori de pregătire**; nu activează OAuth.

## Limitări și securitate

- Un link public către un profil YouTube **nu autorizează** accesul. Pentru `mine=true` este necesar Google OAuth 2.0.
- Asocierea manuală BERRY nu dovedește proprietatea canalului. Un cont Google poate administra mai multe canale sau Brand Accounts; fiecare identitate returnată trebuie confirmată.
- `localhost` pe iPhone ar indica telefonul, nu PC-ul Windows. Testul local se face pe PC. Accesul mobil ulterior necesită backend HTTPS și redirect URI distinct, doar în etapa finală aprobată.
- Nu există încă callback funcțional, token exchange, refresh/revocare, upload, YouTube Analytics sau publicare automată.
- Google API are politici, limite și eventuale cerințe de verificare care trebuie respectate înainte de activare.

## Teste

```bash
python -m pytest -q tests/test_youtube_oauth.py
python -m pytest -q
```

În BERRY deschide **Integrări → YouTube — pregătire OAuth Google**. Poți salva doar planuri locale, fără deschiderea paginii Google.

Documentație oficială: [Google OAuth Web](https://developers.google.com/identity/protocols/oauth2/web-server), [YouTube authorization](https://developers.google.com/youtube/data/guides/authentication), [channels.list](https://developers.google.com/youtube/v3/docs/channels/list), [scopes](https://developers.google.com/identity/protocols/oauth2/scopes).
