# Cum încarci BERRY în GitHub

**Recomandat: repository PRIVATE** până la verificarea licențelor, imaginilor și a securității.

## Varianta Git CLI (recomandată)

1. Creează pe GitHub un repository **gol**, de exemplu `berry-ai-autopilot`, cu vizibilitate **Private**. Nu bifa „Add README”, „Add .gitignore” sau „Choose a license” — sunt deja tratate în pachet sau încă necesită o decizie.
2. Dezarhivează pachetul și deschide un terminal în folderul `berry-ai-autopilot`.
3. Rulează:

```powershell
git init
git branch -M main
git add .
git status
git commit -m "Initial BERRY AI local v0.1"
git remote add origin https://github.com/UTILIZATOR/berry-ai-autopilot.git
git push -u origin main
```

Înlocuiește `UTILIZATOR` cu numele contului tău. GitHub poate cere autentificare prin browser sau credential manager.

## Fără Git CLI

Creează repository privat pe GitHub și folosește **Add file → Upload files** pentru **conținutul dezarhivat** al folderului `berry-ai-autopilot` (nu încărca ZIP-ul ca un singur fișier). Pentru foldere multe, Git CLI este mai fiabil.

## Nu încărca

- Arhivele ZIP ale repository-urilor externe.
- `.env`, baze de date, tokenuri, parole, chei API, voci personale, videoclipuri de referință sau modele AI mari.
- Folderele `data`, `models`, `outputs`, `.venv`, `node_modules`.

Nu este configurată nicio GitHub Action automată: încărcarea în GitHub nu va porni servicii externe, GPU sau publicare socială.
