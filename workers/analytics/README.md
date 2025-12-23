# Portal 27 Analytics Worker

Cloudflare Worker para capturar y analizar eventos de analytics del juego Portal 27.

## Estructura

```
workers/analytics/
├── src/
│   └── index.js        # Worker principal
├── schema.sql          # Schema de D1 database
├── wrangler.toml       # Configuración de Wrangler
└── README.md           # Este archivo
```

## Setup rápido

```bash
# 1. Login en Cloudflare
wrangler login

# 2. Crear base de datos
wrangler d1 create portal27-analytics

# 3. Actualizar database_id en wrangler.toml

# 4. Crear schema
wrangler d1 execute portal27-analytics --file=schema.sql

# 5. Deploy
wrangler deploy
```

## API Endpoints

### POST /api/analytics/track
Guarda un evento de analytics.

**Body:**
```json
{
  "sessionId": "12345-abcde",
  "type": "scene_view",
  "agentId": "ada",
  "sceneId": "scene01",
  "timestamp": 1234567890,
  "metadata": {}
}
```

**Response:** `201 Created`

### GET /api/analytics/events
Obtiene eventos (requiere auth).

**Query params:**
- `limit`: Número de eventos (default: 1000)
- `offset`: Offset para paginación (default: 0)
- `sessionId`: Filtrar por sesión específica

**Headers:**
```
Authorization: Bearer your-token
```

**Response:**
```json
{
  "events": [...]
}
```

### GET /api/analytics/stats
Obtiene estadísticas agregadas (requiere auth).

**Headers:**
```
Authorization: Bearer your-token
```

**Response:**
```json
{
  "totalSessions": 150,
  "totalEvents": 5432,
  "eventsByType": [...],
  "agentStats": [...],
  "sceneStats": [...],
  "endingStats": [...]
}
```

## Testing local

```bash
# Dev mode con D1 local
wrangler dev --local

# Dev mode con D1 remoto
wrangler dev --remote
```

## Ver logs

```bash
wrangler tail
```

## Queries útiles

```bash
# Ver últimos eventos
wrangler d1 execute portal27-analytics --command="SELECT * FROM analytics_events ORDER BY timestamp DESC LIMIT 10"

# Contar eventos por tipo
wrangler d1 execute portal27-analytics --command="SELECT event_type, COUNT(*) FROM analytics_events GROUP BY event_type"

# Ver sesiones únicas
wrangler d1 execute portal27-analytics --command="SELECT COUNT(DISTINCT session_id) FROM analytics_events"
```

## Ver documentación completa

Consulta [CLOUDFLARE_ANALYTICS.md](../../CLOUDFLARE_ANALYTICS.md) para la guía completa de setup.
