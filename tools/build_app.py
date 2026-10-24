import os, shutil, sys
import pathlib; ROOT=pathlib.Path(__file__).resolve().parent.parent
SRC=str(ROOT/'tools/fold-viewer.html')
OUT=str(ROOT)
LIB=sys.argv[1]
os.makedirs(OUT+'/lib', exist_ok=True)
shutil.copy(LIB+'/pdfjs/build/pdf.min.js', OUT+'/lib/pdf.min.js')
shutil.copy(LIB+'/pdfjs/build/pdf.worker.min.js', OUT+'/lib/pdf.worker.min.js')
shutil.copy(LIB+'/jszip/dist/jszip.min.js', OUT+'/lib/jszip.min.js')
s=open(SRC).read()
s=s.replace('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js','lib/pdf.min.js')
s=s.replace('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js','lib/pdf.worker.min.js')
s=s.replace('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js','lib/jszip.min.js')
# installed app is same-origin, so pdf.js can use a real background worker
old='    await loadScript(PDFJS_WORKER); // runs the worker on the page itself; separate worker files are blocked here\n    await loadScript(PDFJS);\n'
assert old in s
s=s.replace(old,'    await loadScript(PDFJS);\n    window.pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS_WORKER;\n')
head='''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1f7a6d">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="icon-192.png">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);box-sizing:border-box;height:100%}*,*::before,*::after{box-sizing:border-box}body{margin:0}img{max-width:100%}</style>
'''
a=s.index('<div id="app">')
tail='''
<script>
// pick up new versions right away: skip the browser's HTTP cache for sw.js and reload once the new version takes over
if ("serviceWorker" in navigator) {
  const hadController = !!navigator.serviceWorker.controller;
  let reloaded = false;
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (!hadController || reloaded) return;
    reloaded = true;
    try { sessionStorage.setItem("fv.updated", "1"); } catch {}
    location.reload();
  });
  addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js", { updateViaCache: "none" }).then((r) => r.update()).catch(() => {});
    try { if (sessionStorage.getItem("fv.updated")) { sessionStorage.removeItem("fv.updated"); setTimeout(() => { const t = document.getElementById("toast"); if (t) { t.textContent = "새 버전으로 업데이트했어요"; t.hidden = false; setTimeout(() => (t.hidden = true), 2600); } }, 600); } } catch {}
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") navigator.serviceWorker.getRegistration().then((r) => r && r.update()).catch(() => {});
  });
}
</script>
</body>
</html>
'''
s=head+s[:a]+'</head>\n<body>\n'+s[a:]+tail
open(OUT+'/index.html','w').write(s)
open(OUT+'/manifest.webmanifest','w').write('''{
  "name": "펼침 뷰어",
  "short_name": "펼침뷰어",
  "description": "폴드를 펼치면 두 쪽, 접으면 한 쪽으로 보는 만화·문서 뷰어",
  "lang": "ko",
  "start_url": "./",
  "scope": "./",
  "display": "fullscreen",
  "display_override": ["fullscreen", "standalone"],
  "orientation": "any",
  "background_color": "#111316",
  "theme_color": "#1f7a6d",
  "icons": [
    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
''')
open(OUT+'/sw.js','w').write('''// 펼침 뷰어: works offline after the first visit
const CACHE = "fold-viewer-__HASH__";
const SHELL = ["index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png",
  "lib/pdf.min.js", "lib/pdf.worker.min.js", "lib/jszip.min.js"];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL.map((u) => new Request(u, { cache: "reload" })))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.protocol === "blob:" || url.protocol === "data:") return;
  // the page itself: network first so updates arrive, cache when offline
  if (e.request.mode === "navigate") {
    e.respondWith(fetch(e.request, { cache: "no-store" }).then((r) => { const c = r.clone(); caches.open(CACHE).then((k) => k.put("index.html", c)); return r; })
      .catch(() => caches.match("index.html")));
    return;
  }
  // everything else (libraries, fonts): cache first
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request).then((r) => {
    if (r.ok || r.type === "opaque") { const c = r.clone(); caches.open(CACHE).then((k) => k.put(e.request, c)); }
    return r;
  })));
});
''')
import hashlib
sw=open(OUT+'/sw.js').read().replace('__HASH__', hashlib.sha1(open(OUT+'/index.html','rb').read()).hexdigest()[:8])
open(OUT+'/sw.js','w').write(sw)
# icons: an open book over a fold hinge
from PIL import Image, ImageDraw
def icon(size, pad):
    im=Image.new('RGB',(size,size),'#1f7a6d'); d=ImageDraw.Draw(im)
    s=size; m=int(s*pad); cx=s//2
    top=int(s*0.28)+m//3; bot=int(s*0.74)-m//3; w=int(s*0.30)-m//2
    d.polygon([(cx,top+int(s*.03)),(cx-w,top),(cx-w,bot),(cx,bot+int(s*.03))],fill='#fbfbf9')
    d.polygon([(cx,top+int(s*.03)),(cx+w,top),(cx+w,bot),(cx,bot+int(s*.03))],fill='#e9ece9')
    d.line([(cx,top+int(s*.03)),(cx,bot+int(s*.03))],fill='#1b1e22',width=max(2,s//64))
    for i in range(4):
        y=top+int((bot-top)*(0.2+0.17*i)); 
        d.line([(cx-w+int(s*.05),y),(cx-int(s*.05),y)],fill='#9aa2ad',width=max(2,s//80))
        d.line([(cx+int(s*.05),y),(cx+w-int(s*.05),y)],fill='#9aa2ad',width=max(2,s//80))
    return im
icon(192,0).save(OUT+'/icon-192.png'); icon(512,0).save(OUT+'/icon-512.png'); icon(512,0.12).save(OUT+'/icon-maskable-512.png')
print('ok')
