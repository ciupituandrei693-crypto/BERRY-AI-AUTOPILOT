# Opens BERRY only after the local server has started. No external calls.
$ErrorActionPreference = 'SilentlyContinue'
$url = 'http://127.0.0.1:8765/'
for ($i = 0; $i -lt 60; $i++) {
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) { Start-Process $url; exit 0 }
    } catch { }
    Start-Sleep -Seconds 1
}
exit 1
