/* Construir & Reformar — Service Worker
   Objetivo único: deixar o app instalável (PWA) e abrível offline depois da
   primeira visita. A vitrine não grava dados, então não há nada para sincronizar aqui —
   isto só cuida do "shell" do aplicativo (HTML/JS/ícones).

   Sempre que os arquivos do app forem republicados, suba o número da versão
   abaixo — isso invalida o cache antigo automaticamente. */
const VERSAO = 'cr-v2';
const ARQUIVOS_DO_SHELL = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './dados.js',
  './config.js',
  './privacidade.html',
  './fonts/fonts.css',
  './fonts/outfit-latin-wght-normal.woff2',
  './fonts/plus-jakarta-sans-latin-wght-normal.woff2',
  './fonts/plus-jakarta-sans-latin-wght-italic.woff2',
  './fonts/space-grotesk-latin-wght-normal.woff2',
];

self.addEventListener('install', (evento) => {
  evento.waitUntil(
    caches.open(VERSAO).then((cache) => cache.addAll(ARQUIVOS_DO_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches.keys().then((chaves) =>
      Promise.all(chaves.filter((c) => c !== VERSAO).map((c) => caches.delete(c)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (evento) => {
  const { request } = evento;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  if (url.origin === self.location.origin) {
    // Arquivos do próprio app: cache primeiro, com atualização em segundo plano
    // (stale-while-revalidate) — abre instantâneo e ainda assim se mantém atual.
    evento.respondWith(
      caches.open(VERSAO).then((cache) =>
        cache.match(request).then((resposta) => {
          const buscaRede = fetch(request)
            .then((resp) => { cache.put(request, resp.clone()); return resp; })
            .catch(() => resposta);
          return resposta || buscaRede;
        })
      )
    );
  } else {
    // Outras origens (ex.: lista de prestadores do servidor): tenta a rede primeiro; sem rede, usa o
    // que já estiver em cache (a última lista que chegou).
    evento.respondWith(
      fetch(request)
        .then((resp) => {
          const copia = resp.clone();
          caches.open(VERSAO).then((cache) => cache.put(request, copia));
          return resp;
        })
        .catch(() => caches.match(request))
    );
  }
});
