# 🚀 Guía de Deployment - Operación Portal 27

## Opción 1: Cloudflare Pages (Recomendada) ⭐

### Ventajas:
- ✅ **Gratuito** para uso personal
- ✅ **Custom domain** incluido
- ✅ **SSL/HTTPS** automático
- ✅ **CDN global** automático
- ✅ **Analytics integrado**
- ✅ **Deploy automático** desde GitHub

### Pasos para deployar:

#### 1. Crear cuenta en Cloudflare
1. Ve a [Cloudflare](https://dash.cloudflare.com/sign-up)
2. Crea una cuenta gratuita

#### 2. Configurar Cloudflare Pages
1. En el dashboard de Cloudflare, ve a **"Workers & Pages"**
2. Haz clic en **"Create application"** → **"Pages"** → **"Connect to Git"**
3. Conecta tu cuenta de GitHub
4. Selecciona tu repositorio `cumpleona`

#### 3. Configurar el build
```
Framework preset: None
Build command: (dejar vacío)
Build output directory: _output
Root directory: (dejar vacío)
Branch: main
```

**Nota**: El script `build.sh` copia automáticamente los archivos de `web/` a `_output/` durante el deployment.

#### 4. Deploy
1. Haz clic en **"Save and Deploy"**
2. Espera a que se complete el deploy (~1-2 minutos)
3. ¡Tu sitio estará live! Te dará una URL como: `cumpleona.pages.dev`

#### 5. Añadir Custom Domain
1. En tu proyecto de Pages, ve a **"Custom domains"**
2. Haz clic en **"Set up a custom domain"**
3. Ingresa tu dominio (ej: `cumpleona.tudominio.com` o `www.tudominio.com`)
4. Sigue las instrucciones para:
   - Si tu dominio YA está en Cloudflare: Se configurará automáticamente ✨
   - Si tu dominio NO está en Cloudflare: Tendrás que añadir un registro CNAME

**Ejemplo de registro CNAME:**
```
Type: CNAME
Name: cumpleona (o www)
Target: cumpleona.pages.dev
Proxy status: Proxied (naranja)
```

#### 6. Configurar Web Analytics

##### Cloudflare Web Analytics (Gratis, sin cookies, privacy-friendly):
1. Ve a **"Analytics"** → **"Web Analytics"** en Cloudflare
2. Haz clic en **"Add a site"**
3. Ingresa tu dominio
4. Copia el **token** que te dan
5. En `web/index.html`, reemplaza `TU_TOKEN_AQUI` con tu token real (línea 13)
6. Haz commit y push

Verás en el dashboard:
- 📊 Visitantes únicos
- 📍 Países de origen
- 📱 Dispositivos (mobile/desktop)
- ⏱️ Tiempos de carga
- 🔗 Páginas más visitadas

---

## Opción 2: Vercel

### Ventajas:
- ✅ Gratuito
- ✅ Deploy muy rápido
- ✅ Custom domain incluido
- ✅ SSL automático

### Pasos:
1. Ve a [Vercel](https://vercel.com)
2. Conecta tu repositorio de GitHub
3. Configura:
   ```
   Root Directory: web
   Output Directory: (dejar vacío, usa web/)
   ```
4. Deploy automático

Para custom domain:
1. Ve a **"Settings"** → **"Domains"**
2. Añade tu dominio
3. Configura el registro DNS según te indiquen

---

## Opción 3: Netlify

### Ventajas:
- ✅ Gratuito
- ✅ Interfaz muy simple
- ✅ Custom domain incluido

### Pasos:
1. Ve a [Netlify](https://netlify.com)
2. Arrastra la carpeta `web/` a la interfaz
3. O conecta tu repositorio de GitHub

Para custom domain:
1. Ve a **"Domain settings"**
2. Añade tu dominio
3. Configura DNS según indicaciones

---

## 📊 Analytics Personalizado

El juego incluye un sistema de analytics propio que guarda eventos en localStorage del navegador.

### Datos que se trackean:
- ✅ Escenas visitadas
- ✅ Decisiones tomadas (choices)
- ✅ Finales alcanzados
- ✅ Tiempo en cada escena
- ✅ Puzzles completados
- ✅ Cambios de agente
- ✅ Uso del botón "Atrás"

### Ver analytics en la consola del navegador:

```javascript
// Ver todos los eventos
viewAnalytics()

// Exportar eventos a JSON
exportAnalytics()

// Limpiar eventos guardados
clearAnalytics()
```

### Conectar a un backend propio:

Si quieres enviar los datos a tu propio servidor, edita `web/js/analytics.js`:

1. Cambia `ANALYTICS_ENABLED` a `true` (ya está por defecto)
2. Cambia `ANALYTICS_ENDPOINT` a tu URL de API
3. Descomenta el código de `fetch` en el método `sendEvent` (líneas ~51-58)

Ejemplo con Cloudflare Workers (gratis):

```javascript
// En analytics.js
const ANALYTICS_ENDPOINT = 'https://tu-worker.workers.dev/analytics';
```

Crea un Worker en Cloudflare que guarde los eventos en D1 (SQL), KV, o envíe a Google Sheets.

---

## 🔒 Configurar dominio (Paso a Paso)

### Si tu dominio está en GoDaddy, Namecheap, etc:

#### Opción A: Transferir a Cloudflare (Recomendado)
1. Cambia los nameservers de tu dominio a los de Cloudflare
2. Espera 24-48h para la propagación
3. Todo se configurará automáticamente

#### Opción B: Solo usar DNS
1. En tu proveedor de dominio, añade un registro CNAME:
   ```
   Type: CNAME
   Name: cumpleona (o @ para root domain)
   Value: cumpleona.pages.dev
   ```
2. Espera 15-30 minutos para propagación

---

## 🚦 Verificar el deployment

Después de deployar, verifica:

1. ✅ El sitio carga correctamente
2. ✅ Las imágenes se ven bien
3. ✅ Los estilos CSS están aplicados
4. ✅ El JavaScript funciona
5. ✅ Analytics está activo (ver consola del navegador)
6. ✅ HTTPS está activo (candado en la URL)

---

## 📝 Comandos útiles

```bash
# Ver analytics en la consola del navegador (F12)
viewAnalytics()

# Exportar analytics a archivo JSON
exportAnalytics()

# Limpiar analytics guardados
clearAnalytics()

# Ver el tamaño de las imágenes
du -sh web/img

# Optimizar imágenes de nuevo
uv run python scripts/optimize_all_images.py
```

---

## 🎯 Próximos pasos después del deploy

1. 📊 Configura Cloudflare Web Analytics (10 min)
2. 🔍 Configura Google Search Console para SEO
3. 🌐 Comparte el link con tus amigos
4. 📈 Revisa las métricas después de unos días
5. 🎨 Ajusta según el feedback

---

## ❓ Troubleshooting

### El sitio no carga
- Verifica que el "Build output directory" sea `web`
- Revisa los logs de build en Cloudflare/Vercel/Netlify

### Las imágenes no cargan
- Verifica que las rutas sean relativas: `img/...` no `/img/...`
- Revisa la consola del navegador (F12)

### Analytics no funciona
- Abre la consola del navegador (F12)
- Escribe `viewAnalytics()` y verifica que hay eventos

### Custom domain no funciona
- Espera 15-30 minutos para propagación DNS
- Verifica el registro CNAME con: `dig cumpleona.tudominio.com`
- Verifica que el dominio esté en "Proxied" mode en Cloudflare

---

## 💡 Tips

- Usa **Cloudflare Pages** si quieres lo más simple y completo
- Usa **Vercel** si ya estás familiarizado con ellos
- Usa **Netlify** si solo quieres arrastrar y soltar

¡Buena suerte con el deploy! 🚀
