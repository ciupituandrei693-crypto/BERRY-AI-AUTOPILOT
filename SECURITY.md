# BERRY — Local Security Boundary

- Runs on `127.0.0.1:8765` only. Do not bind to `0.0.0.0` or forward the port.
- `TrustedHostMiddleware` restricts Host; unsafe API methods reject foreign Origin.
- Set a strong `BERRY_ACCESS_KEY` if untrusted local users/processes may access the browser.
- This is **not** production-grade remote authentication. Before phone/network access, implement session auth, TLS, CSRF tokens, rate limits, role permissions and secrets management.
- No real social API, OAuth, remote server, paid promotion or cloud GPU code is active.
- User-uploaded art/audio and custom scripts stay in `data/`, ignored by Git; limits and format checks apply, but imported content must be reviewed for rights and safety.
- The repository is public; do not commit database files, generated outputs, API keys, personal content, ZIPs or model weights.
- Bundled artwork is conceptual; distribution rights must be confirmed before commercial/public redistribution.
- GitHub ZIP source dependencies are **not** auto-executed; inspect licenses, hashes, dependency trees and models before installing.
- The local ZIP export is for **manual** posting and cannot bypass human QA + approval.
