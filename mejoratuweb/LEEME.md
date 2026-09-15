# Tu sitio, montado

Todo lo que hay aquí funciona tal cual. Lo único que falta son **tus datos**:
busca `[` en cualquier archivo y verás todos los huecos.

## Estructura

```
index.html                          portada
auditor.html                        herramienta 1
presupuesto.html                    herramienta 2
contacto.html                       formulario
aviso-legal.html                    \
politica-de-privacidad.html          }  obligatorias para AdSense
politica-de-cookies.html            /
estilo.css                          el diseño de todo el sitio
robots.txt                          permisos para buscadores
sitemap.xml                         mapa para Search Console
blog/
  precio-web-negocio-pequeno.html   ← el pilar (2.000 palabras)
  precio-web-restaurante.html       satélite
  precio-web-peluqueria.html        satélite
netlify/functions/
  auditar.js                        el servidor del auditor
```

## Antes de publicar: los tres cambios obligatorios

**1 · Tus datos.** Busca `[` y sustituye:
`Mejora tu web`, `[TU NOMBRE]`, `mejoratuweb.world`, `[TU ZONA]`, `[EMAIL]`,
`[NIF]`, `[DIRECCIÓN COMPLETA, CP y LOCALIDAD]`, `[TU NÚMERO]`,
`[TU USUARIO]`, `[MES]`, `[MM]`, `[DD]`, `[PROVEEDOR DE HOSTING]`,
`[PROVEEDOR DE EMAIL]`.

**2 · Tus precios.** Están en dos sitios y tienen que coincidir:
- `presupuesto.html` y `blog/precio-web-negocio-pequeno.html`: objeto `P`
  al final del archivo, comentado.
- Las tablas de precios dentro de los tres artículos.
- La lista «Qué hago» de `index.html`.

**3 · El auditor por URL.** Ahora mismo pide pegar el código fuente.
Sigue `auditor-url-cambios.md` para que pida la dirección. Necesita
la función de `netlify/functions/`.

## Publicar en Netlify

1. Entra en netlify.com y arrastra esta carpeta a la zona de despliegue.
2. En *Domain settings*, conecta tu dominio.
3. El HTTPS se activa solo en unos minutos.

Las funciones se detectan solas y el formulario de contacto empieza a
funcionar sin tocar nada: los mensajes llegan a *Forms* y a tu correo.

Crea también una página `gracias.html` sencilla, que es a donde va el
formulario después de enviarse.

## Después de publicar, por orden

1. **Search Console** → verificar el dominio con un registro TXT.
2. **Enviar `sitemap.xml`** desde Search Console → Sitemaps.
3. **Google Analytics 4** → con la misma cuenta que usarás para AdSense.
4. **Escribir hasta llegar a 15-20 artículos.** Uno cada una o dos semanas.
   Los dos siguientes ya están enlazados y sin escribir:
   `ficha-google-business` y `velocidad-web`.
5. **Crear la cuenta de AdSense** y configurar el CMP en
   *Privacidad y mensajes*. Sin eso no se sirven anuncios en la UE.
6. **Solicitar la revisión** cuando haya 15-20 artículos y algo de tráfico.
   Antes de eso, el rechazo es casi seguro.

## Los huecos de anuncios

Cada artículo lleva tres `<div class="ad">` marcados con un comentario.
Sustituye cada uno por tu bloque de AdSense cuando te aprueben.

**Ni el auditor ni la calculadora llevan anuncios, y es a propósito.**
Son las páginas que convierten en clientes; un anuncio ahí cambia dos
céntimos por la posibilidad de mil euros.
