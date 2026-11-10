# Securitate — BERRY AI AUTOPILOT

Acest repository este un **prototip local**. Nu este configurat pentru Internet sau accesul mai multor utilizatori.

- Folosește numai `127.0.0.1:8765` pe PC-ul local; nu modifica bind-ul la `0.0.0.0`.
- Opțional, setează `BERRY_ACCESS_KEY` printr-o variabilă de mediu; cheia din antet nu înlocuiește autentificarea completă pentru acces remote.
- Nu comite `.env`, parole, tokenuri OAuth, baze de date SQLite, fișiere de utilizator sau modele AI mari.
- Nu conecta TikTok, YouTube, Instagram, GPU cloud sau server extern înainte de etapa finală și aprobare.
- Înainte de acces iPhone/Internet: autentificare robustă, TLS, protecție CSRF, limitare cereri, gestionarea secretelor, backup, teste de securitate și permisiuni.
- Nu accepta fișiere sau pluginuri externe fără verificarea provenienței, licenței și codului.

Pentru probleme de securitate, nu publica date sensibile în issues publice; folosește un canal privat stabilit de proprietarul repository-ului.
