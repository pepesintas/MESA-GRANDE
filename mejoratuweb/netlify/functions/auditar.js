/**
 * GET /api/auditar?url=https://ejemplo.com
 *
 * Descarga el HTML de una web y lo devuelve para que el auditor lo analice
 * en el navegador. Existe porque el navegador NO deja que una web descargue
 * otra web distinta (CORS): esa petición la tiene que hacer un servidor.
 *
 * Netlify Functions. Para Vercel es el mismo código cambiando la firma
 * (ver nota al final del archivo).
 *
 * OJO — esto es un endpoint público que descarga la URL que le pidas.
 * Sin las comprobaciones de abajo, cualquiera podría usarlo para leer
 * servicios internos de tu servidor o como proxy anónimo. No las quites.
 */

import dns from 'node:dns/promises';
import net from 'node:net';

const TIMEOUT_MS = 8000;
const MAX_BYTES = 2 * 1024 * 1024; // 2 MB: de sobra para cualquier HTML

/** Rangos que no debe poder alcanzar un endpoint público. */
function esIpPrivada(ip) {
  if (net.isIPv4(ip)) {
    const [a, b] = ip.split('.').map(Number);
    return (
      a === 0 ||
      a === 10 ||
      a === 127 ||
      (a === 169 && b === 254) ||          // link-local / metadatos cloud
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 168) ||
      (a === 100 && b >= 64 && b <= 127) ||
      a >= 224                              // multicast y reservados
    );
  }
  if (net.isIPv6(ip)) {
    const x = ip.toLowerCase();
    return (
      x === '::' || x === '::1' ||
      x.startsWith('fc') || x.startsWith('fd') ||  // únicas locales
      x.startsWith('fe80') ||                       // link-local
      x.startsWith('::ffff:')                       // IPv4 mapeada
    );
  }
  return true;
}

function error(mensaje, status = 400) {
  return new Response(JSON.stringify({ error: mensaje }), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

export default async (req) => {
  const entrada = (new URL(req.url).searchParams.get('url') || '').trim();
  if (!entrada) return error('Falta el parámetro url.');

  // Si escriben "misitio.com" a secas, damos por hecho https.
  let destino;
  try {
    destino = new URL(/^https?:\/\//i.test(entrada) ? entrada : 'https://' + entrada);
  } catch {
    return error('Esa dirección no es válida. Revisa que esté bien escrita.');
  }

  if (destino.protocol !== 'http:' && destino.protocol !== 'https:') {
    return error('Solo se pueden analizar direcciones http y https.');
  }

  // Resolvemos el dominio y comprobamos que no apunte a una red interna.
  let ips;
  try {
    ips = await dns.lookup(destino.hostname, { all: true });
  } catch {
    return error('No existe ese dominio, o no se puede resolver.');
  }
  if (ips.some((r) => esIpPrivada(r.address))) {
    return error('Esa dirección no se puede analizar.', 403);
  }

  const corte = AbortSignal.timeout(TIMEOUT_MS);

  let res;
  try {
    res = await fetch(destino.href, {
      signal: corte,
      redirect: 'follow',
      headers: {
        // Identificarse es de buena educación y evita bloqueos.
        'user-agent': 'AuditorVisibilidad/1.0 (+https://mejoratuweb.world/auditor)',
        'accept': 'text/html,application/xhtml+xml',
        'accept-language': 'es-ES,es;q=0.9',
      },
    });
  } catch (e) {
    return error(
      e.name === 'TimeoutError'
        ? 'La web ha tardado demasiado en responder. Vuelve a intentarlo.'
        : 'No se ha podido conectar con esa web.',
      502
    );
  }

  if (!res.ok) {
    return error('La web ha respondido con un error ' + res.status + '.', 502);
  }

  const tipo = res.headers.get('content-type') || '';
  if (!/text\/html|application\/xhtml/i.test(tipo)) {
    return error('Esa dirección no devuelve una página web.');
  }

  // Leemos con tope de tamaño: no queremos tragarnos un archivo enorme.
  const lector = res.body.getReader();
  const trozos = [];
  let total = 0;
  while (true) {
    const { done, value } = await lector.read();
    if (done) break;
    if (total + value.length > MAX_BYTES) {
      trozos.push(value.subarray(0, MAX_BYTES - total));
      total = MAX_BYTES;
      await lector.cancel();
      break;
    }
    trozos.push(value);
    total += value.length;
  }

  const buffer = new Uint8Array(total);
  let pos = 0;
  for (const t of trozos) { buffer.set(t, pos); pos += t.length; }
  const html = new TextDecoder('utf-8').decode(buffer);

  // Además de la página, miramos tres archivos del dominio que dicen mucho:
  // robots.txt (si bloquea a Google o a los rastreadores de IA), el sitemap,
  // y llms.txt (el archivo que empieza a usarse para guiar a las IAs).
  const raiz = new URL(destino.href).origin;

  async function auxiliar(ruta, soloExiste = false) {
    try {
      const r = await fetch(raiz + ruta, {
        signal: AbortSignal.timeout(4000),
        method: soloExiste ? 'HEAD' : 'GET',
        headers: { 'user-agent': 'AuditorVisibilidad/1.0' },
      });
      if (!r.ok) return soloExiste ? false : null;
      if (soloExiste) return true;
      return (await r.text()).slice(0, 20000);
    } catch {
      return soloExiste ? false : null;
    }
  }

  const [robots, sitemap, llms] = await Promise.all([
    auxiliar('/robots.txt'),
    auxiliar('/sitemap.xml', true),
    auxiliar('/llms.txt'),
  ]);

  return new Response(
    JSON.stringify({ url: res.url, html, robots, sitemap, llms }),
    {
      status: 200,
      headers: {
        'content-type': 'application/json; charset=utf-8',
        // Solo 60 segundos. Diez minutos parecía razonable para no repetir
        // descargas, pero rompe el uso normal: arreglas algo en tu web,
        // vuelves a analizar y sigues viendo el resultado viejo.
        'cache-control': 'public, max-age=60',
      },
    }
  );
};

export const config = { path: '/api/auditar' };

/*
 * ── PARA VERCEL ──────────────────────────────────────────────
 * Guarda este archivo en  /api/auditar.js  y cambia solo esto:
 *
 *   export default async (req) => { ... }        ← se queda igual
 *   export const config = { path: '/api/auditar' };   ← se borra
 *
 * Vercel ya enruta por la ruta del archivo.
 * ─────────────────────────────────────────────────────────────
 */
