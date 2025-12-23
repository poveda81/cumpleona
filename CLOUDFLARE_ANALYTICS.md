# Cloudflare Analytics - Guía de Setup

Esta guía te ayudará a configurar el sistema de analytics centralizado usando Cloudflare Workers + D1 Database.

## Arquitectura

```
┌─────────────────┐
│   Usuario web   │
│  (cumpleona.    │
│  pages.dev)     │
└────────┬────────┘
         │
         │ POST /api/analytics/track
         ▼
┌─────────────────┐      ┌──────────────┐
│ Cloudflare      │─────▶│ D1 Database  │
│ Worker          │      │ (SQL)        │
│ (portal27-      │◀─────│              │
│  analytics)     │      └──────────────┘
└────────┬────────┘
         │
         │ GET /api/analytics/stats
         ▼
┌─────────────────┐
│   Dashboard     │
│  analytics-     │
│  dashboard.html │
└─────────────────┘
```

## 🚀 Paso 1: Crear D1 Database

```bash
cd workers/analytics

# Login en Cloudflare (abrirá el navegador)
wrangler login

# Crear base de datos D1
wrangler d1 create portal27-analytics
```

Cloudflare te devolverá algo como:

```toml
[[d1_databases]]
binding = "DB"
database_name = "portal27-analytics"
database_id = "xxxx-xxxx-xxxx-xxxx"
```

**Copia el `database_id`** y actualízalo en `workers/analytics/wrangler.toml`

## 🗄️ Paso 2: Crear el schema de la base de datos

```bash
# Ejecutar el schema en la base de datos
wrangler d1 execute portal27-analytics --file=schema.sql
```

Esto creará la tabla `analytics_events` con todos los índices necesarios.

## 📤 Paso 3: Deploy del Worker

```bash
# Deploy a producción
wrangler deploy
```

Cloudflare te devolverá una URL como:
```
https://portal27-analytics.YOUR_SUBDOMAIN.workers.dev
```

**Copia esta URL** - la necesitarás en los siguientes pasos.

## 🔧 Paso 4: Configurar el frontend

### 4.1 Actualizar analytics.js

Edita `web/js/analytics.js` línea 13:

```javascript
// Antes
const ANALYTICS_ENDPOINT = 'https://portal27-analytics.YOUR_SUBDOMAIN.workers.dev/api/analytics/track';

// Después (usa tu URL real del Worker)
const ANALYTICS_ENDPOINT = 'https://portal27-analytics.tu-subdomain.workers.dev/api/analytics/track';
```

### 4.2 Actualizar el dashboard

Edita `web/analytics-dashboard.html` línea 169:

```javascript
// Antes
const API_BASE = 'https://portal27-analytics.YOUR_SUBDOMAIN.workers.dev/api/analytics';

// Después (usa tu URL real del Worker)
const API_BASE = 'https://portal27-analytics.tu-subdomain.workers.dev/api/analytics';
```

### 4.3 Actualizar wrangler.toml (opcional)

Si quieres permitir tu dominio local para testing:

```toml
[vars]
ALLOWED_ORIGINS = "https://cumpleona.pages.dev,http://localhost:8000"
```

## 🔐 Paso 5: Configurar autenticación (Producción)

Por defecto, el Worker acepta cualquier request con un header `Authorization`.

Para producción, **debes** implementar validación real:

### Opción A: API Key simple (Recomendado)

1. Genera un token único:
   ```bash
   openssl rand -hex 32
   ```

2. Guarda el token en Wrangler secrets:
   ```bash
   wrangler secret put API_TOKEN
   # Pega tu token cuando te lo pida
   ```

3. Actualiza `workers/analytics/src/index.js`:
   ```javascript
   function isAuthorized(request, env) {
     const authHeader = request.headers.get('Authorization');
     const token = authHeader?.replace('Bearer ', '');
     return token === env.API_TOKEN;
   }
   ```

4. Usa ese token en el dashboard cuando te pida autenticación.

### Opción B: Cloudflare Access (Más seguro)

Si quieres proteger el dashboard con login de Google/GitHub:

1. Ve a Cloudflare Dashboard → Zero Trust → Access
2. Crea una Application para tu Worker
3. Configura las reglas de acceso (e.g., solo tu email)

## 📊 Paso 6: Acceder al Dashboard

1. Haz deploy de tus cambios a Cloudflare Pages:
   ```bash
   git add .
   git commit -m "Configure Cloudflare Analytics"
   git push
   ```

2. Accede al dashboard:
   ```
   https://cumpleona.pages.dev/analytics-dashboard.html
   ```

3. Introduce tu token de API (el que configuraste en el Paso 5)

4. ¡Listo! Ya puedes ver las estadísticas en tiempo real.

## 🧪 Testing local

Para probar localmente antes de hacer deploy:

```bash
# Terminal 1: Worker en modo dev
cd workers/analytics
wrangler dev --local

# Terminal 2: Servidor web local
cd ../..
cd web
python3 -m http.server 8000
```

Abre http://localhost:8000 y verifica que los eventos se envían correctamente (F12 → Console).

## 📈 Qué se trackea

El sistema captura automáticamente:

- ✅ **session_start**: Inicio de sesión con agente seleccionado
- ✅ **mission_start**: Cuando se inicia la misión
- ✅ **scene_view**: Cada escena visitada
- ✅ **choice_made**: Cada decisión tomada
- ✅ **ending_reached**: Finales alcanzados
- ✅ **puzzle_start**: Inicio de puzzles
- ✅ **puzzle_complete**: Puzzles completados
- ✅ **back_button**: Uso del botón atrás
- ✅ **mission_reset**: Reinicio de misión
- ✅ **agent_switch**: Cambio de agente

## 🔍 Consultas SQL útiles

Puedes ejecutar queries personalizadas con:

```bash
wrangler d1 execute portal27-analytics --command="SELECT * FROM analytics_events LIMIT 10"
```

### Ver últimos 10 eventos:
```sql
SELECT * FROM analytics_events ORDER BY timestamp DESC LIMIT 10
```

### Ver agentes más populares:
```sql
SELECT agent_id, COUNT(*) as count
FROM analytics_events
WHERE event_type = 'session_start'
GROUP BY agent_id
ORDER BY count DESC
```

### Ver tasa de completación:
```sql
SELECT
  (SELECT COUNT(DISTINCT session_id) FROM analytics_events WHERE event_type = 'ending_reached') * 100.0 /
  (SELECT COUNT(DISTINCT session_id) FROM analytics_events WHERE event_type = 'session_start') as completion_rate
```

### Ver camino más común:
```sql
SELECT scene_id, COUNT(*) as visits
FROM analytics_events
WHERE event_type = 'scene_view'
GROUP BY scene_id
ORDER BY visits DESC
LIMIT 10
```

## 🆓 Límites del plan gratuito

Cloudflare Workers + D1 ofrece:

- ✅ **100,000 requests/día** - Suficiente para ~3,000 jugadores/día
- ✅ **5 GB almacenamiento** - Millones de eventos
- ✅ **5 millones reads/día** - Para consultar stats
- ✅ **100,000 writes/día** - Para guardar eventos

Para la mayoría de casos de uso, el plan gratuito es más que suficiente.

## 🐛 Troubleshooting

### Error: "D1 binding not found"
- Verifica que `database_id` esté configurado en `wrangler.toml`
- Re-deploy el worker: `wrangler deploy`

### Error: "Table not found"
- Ejecuta el schema: `wrangler d1 execute portal27-analytics --file=schema.sql`

### CORS errors en el navegador
- Verifica que tu dominio esté en `ALLOWED_ORIGINS` en `wrangler.toml`
- Re-deploy el worker después de cambios

### El dashboard no muestra datos
- Verifica que el token de API sea correcto
- Abre DevTools → Network para ver si hay errores
- Verifica que el Worker esté deployed correctamente

### Los eventos no se envían desde el frontend
- Verifica que `ANALYTICS_ENDPOINT` esté configurado correctamente
- Abre DevTools → Console para ver logs de analytics
- Verifica que no haya errores de CORS

## 📚 Recursos

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [D1 Database Docs](https://developers.cloudflare.com/d1/)
- [Wrangler CLI Docs](https://developers.cloudflare.com/workers/wrangler/)

## 🔄 Siguientes pasos

1. **Mejorar autenticación**: Implementar API key validation real
2. **Añadir más visualizaciones**: Gráficos de tiempo, funnels, etc.
3. **Exportar datos**: Crear endpoint para exportar a CSV/JSON
4. **Alertas**: Notificaciones cuando se alcancen milestones
5. **A/B Testing**: Experimentar con diferentes caminos narrativos

---

**¿Necesitas ayuda?** Revisa los logs del Worker:
```bash
wrangler tail
```

Esto mostrará en tiempo real todos los requests y errores.
