// netlify/functions/redsys-create.js
// Crea una petición de pago firmada para el TPV Virtual de Redsys.
// Devuelve el endpoint y los 3 campos que el navegador debe enviar por POST
// (Ds_SignatureVersion, Ds_MerchantParameters, Ds_Signature).
//
// Credenciales por variables de entorno en Netlify (con fallback al entorno
// de PRUEBAS oficial de Redsys, para que funcione sin configurar nada):
//   REDSYS_ENV            -> 'test' (por defecto) | 'live'
//   REDSYS_MERCHANT_CODE  -> FUC del comercio        (test: 999008881)
//   REDSYS_TERMINAL       -> nº de terminal          (test: 001)
//   REDSYS_SECRET_KEY     -> clave secreta base64    (test: sq7Hjr...)
//   REDSYS_MERCHANT_NAME  -> nombre del comercio
//   SITE_URL              -> fuerza el dominio para las URLs de retorno/notif.
import crypto from 'node:crypto'

const TEST_KEY = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7' // clave pública de pruebas Redsys

const cfg = () => {
  const env = (Netlify.env.get('REDSYS_ENV') || 'test').toLowerCase()
  return {
    env,
    endpoint: env === 'live'
      ? 'https://sis.redsys.es/sis/realizarPago'
      : 'https://sis-t.redsys.es:25443/sis/realizarPago',
    fuc: Netlify.env.get('REDSYS_MERCHANT_CODE') || '999008881',
    terminal: (Netlify.env.get('REDSYS_TERMINAL') || '001').padStart(3, '0'),
    key: Netlify.env.get('REDSYS_SECRET_KEY') || TEST_KEY,
    name: Netlify.env.get('REDSYS_MERCHANT_NAME') || 'MESAGRANDE',
  }
}

// 3DES-CBC (IV de ceros, sin padding automático) del nº de pedido con la clave del comercio.
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

// HMAC-SHA256 de los parámetros (base64) con la clave derivada.
function sign(paramsB64, order, secretKeyB64) {
  return crypto.createHmac('sha256', deriveKey(order, secretKeyB64))
    .update(paramsB64).digest('base64')
}

const json = (obj, status = 200) => new Response(JSON.stringify(obj), {
  status,
  headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
})

export default async function (req) {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
      },
    })
  }
  if (req.method !== 'POST') return json({ error: 'Método no permitido' }, 405)

  try {
    const c = cfg()
    const body = await req.json().catch(() => ({}))

    // importe en euros -> céntimos (entero)
    const euros = parseFloat(body.amount)
    if (!Number.isFinite(euros) || euros <= 0) return json({ error: 'Importe inválido' }, 400)
    const cents = Math.round(euros * 100)

    // nº de pedido: 4-12 chars, los 4 primeros numéricos. Único por transacción.
    const order = String(body.order || Date.now()).replace(/\D/g, '').slice(-10).padStart(4, '0').slice(0, 12)
    const concept = String(body.concept || 'Pago MESAGRANDE').slice(0, 125)

    // dominio para URLs de retorno/notificación
    const origin = Netlify.env.get('SITE_URL') || new URL(req.url).origin

    const params = {
      DS_MERCHANT_AMOUNT: String(cents),
      DS_MERCHANT_ORDER: order,
      DS_MERCHANT_MERCHANTCODE: c.fuc,
      DS_MERCHANT_CURRENCY: '978',                 // EUR
      DS_MERCHANT_TRANSACTIONTYPE: '0',            // autorización
      DS_MERCHANT_TERMINAL: c.terminal,
      DS_MERCHANT_MERCHANTNAME: c.name,
      DS_MERCHANT_PRODUCTDESCRIPTION: concept,
      DS_MERCHANT_MERCHANTURL: `${origin}/.netlify/functions/redsys-notify`,
      DS_MERCHANT_URLOK: `${origin}/pago-ok.html?order=${order}`,
      DS_MERCHANT_URLKO: `${origin}/pago-ko.html?order=${order}`,
    }

    const merchantParameters = Buffer.from(JSON.stringify(params)).toString('base64')
    const signature = sign(merchantParameters, order, c.key)

    return json({
      env: c.env,
      endpoint: c.endpoint,
      order,
      amount: euros.toFixed(2),
      Ds_SignatureVersion: 'HMAC_SHA256_V1',
      Ds_MerchantParameters: merchantParameters,
      Ds_Signature: signature,
    })
  } catch (e) {
    return json({ error: e.message }, 500)
  }
}
