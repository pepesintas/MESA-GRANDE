// netlify/functions/redsys-notify.js
// Notificación servidor-a-servidor de Redsys (DS_MERCHANT_MERCHANTURL).
// Redsys hace POST (application/x-www-form-urlencoded) con:
//   Ds_SignatureVersion, Ds_MerchantParameters (base64url), Ds_Signature (base64url)
// Verificamos la firma HMAC y comprobamos Ds_Response (0000-0099 = autorizado).
//
// Aquí es donde debes marcar el pedido como pagado en tu base de datos
// (Supabase). Se deja el punto de integración señalado más abajo.
import crypto from 'node:crypto'

const TEST_KEY = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
const KEY = () => Netlify.env.get('REDSYS_SECRET_KEY') || TEST_KEY

const b64urlToBuf = (s) => Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64')
const bufToB64url = (b) => b.toString('base64').replace(/\+/g, '-').replace(/\//g, '_')

function deriveKey(order, secretKeyB64) {
  const key = Buffer.from(secretKeyB64, 'base64')
  const iv = Buffer.alloc(8, 0)
  const cipher = crypto.createCipheriv('des-ede3-cbc', key, iv)
  cipher.setAutoPadding(false)
  const data = Buffer.from(order, 'utf8')
  const pad = (8 - (data.length % 8)) % 8
  const padded = Buffer.concat([data, Buffer.alloc(pad, 0)])
  return Buffer.concat([cipher.update(padded), cipher.final()])
}

// La firma de la respuesta usa base64url sobre la cadena Ds_MerchantParameters recibida.
function signResponse(paramsB64url, order, secretKeyB64) {
  const mac = crypto.createHmac('sha256', deriveKey(order, secretKeyB64)).update(paramsB64url).digest()
  return bufToB64url(mac)
}

export default async function (req) {
  try {
    if (req.method !== 'POST') return new Response('OK', { status: 200 })

    const form = new URLSearchParams(await req.text())
    const paramsB64 = form.get('Ds_MerchantParameters') || ''
    const recvSig = form.get('Ds_Signature') || ''
    if (!paramsB64) return new Response('Bad Request', { status: 400 })

    const params = JSON.parse(b64urlToBuf(paramsB64).toString('utf8'))
    const order = params.Ds_Order || params.DS_ORDER || ''
    const response = parseInt(params.Ds_Response ?? params.DS_RESPONSE ?? '9999', 10)

    // verificación de firma (constante en tiempo)
    const expected = signResponse(paramsB64, order, KEY())
    const a = Buffer.from(expected)
    const b = Buffer.from(recvSig)
    const valid = a.length === b.length && crypto.timingSafeEqual(a, b)

    if (!valid) {
      console.warn('[redsys-notify] firma inválida', { order })
      return new Response('Signature mismatch', { status: 403 })
    }

    const authorized = response >= 0 && response <= 99
    console.log('[redsys-notify]', { order, response, authorized, amount: params.Ds_Amount })

    // ── PUNTO DE INTEGRACIÓN ─────────────────────────────────────────
    // if (authorized) { await marcarPedidoPagado(order, params) }
    // p.ej. insertar en la tabla `caja`/`cobros` de Supabase usando
    // SUPABASE_URL + SUPABASE_SERVICE_ROLE como variables de entorno.
    // ─────────────────────────────────────────────────────────────────

    // Redsys solo necesita un 200 para dar por entregada la notificación.
    return new Response('OK', { status: 200 })
  } catch (e) {
    console.error('[redsys-notify] error', e)
    return new Response('Error', { status: 500 })
  }
}
