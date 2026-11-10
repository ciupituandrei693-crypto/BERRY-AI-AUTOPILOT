// Offline app shell only; NEVER cache API responses, account data or published content.
const CACHE='berry-shell-v1';const ASSETS=['/static/style.css','/static/app.js','/static/manifest.json','/static/icon-192.png'];
self.addEventListener('install',ev=>{ev.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',ev=>{ev.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',ev=>{const u=new URL(ev.request.url);if(ev.request.method!=='GET'||u.pathname.startsWith('/api/')||u.origin!==location.origin)return;if(!u.pathname.startsWith('/static/'))return;ev.respondWith(caches.match(ev.request).then(c=>c||fetch(ev.request)))});
