/**
 * Cloudflare Worker para recibir y almacenar eventos de analytics
 *
 * Para deployar:
 * 1. Ve a Cloudflare Dashboard → Workers & Pages
 * 2. Crea un nuevo Worker
 * 3. Pega este código
 * 4. Crea una KV namespace llamada "ANALYTICS"
 * 5. Vincula el namespace al worker
 * 6. Deploy
 *
 * URL del worker será algo como: https://tu-worker.tu-cuenta.workers.dev
 */

export default {
  async fetch(request, env) {
    // Manejar CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    }

    const url = new URL(request.url);

    // Endpoint para recibir eventos
    if (url.pathname === '/analytics' && request.method === 'POST') {
      try {
        const event = await request.json();

        // Generar key única para el evento
        const timestamp = Date.now();
        const key = `event:${event.sessionId}:${timestamp}`;

        // Guardar en KV
        await env.ANALYTICS.put(key, JSON.stringify(event), {
          expirationTtl: 60 * 60 * 24 * 90 // 90 días
        });

        return new Response(JSON.stringify({ success: true }), {
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          }
        });
      }
    }

    // Endpoint para ver estadísticas (proteger con auth en producción!)
    if (url.pathname === '/analytics/stats' && request.method === 'GET') {
      try {
        // Obtener todos los eventos (limitado a 1000)
        const list = await env.ANALYTICS.list({ limit: 1000 });
        const events = [];

        for (const key of list.keys) {
          const value = await env.ANALYTICS.get(key.name);
          if (value) {
            events.push(JSON.parse(value));
          }
        }

        // Calcular estadísticas
        const stats = {
          totalEvents: events.length,
          uniqueSessions: new Set(events.map(e => e.sessionId)).size,
          eventTypes: {},
          sceneViews: {},
          choicesMade: {},
          endingsReached: {},
          agents: {}
        };

        events.forEach(event => {
          // Contar tipos de eventos
          stats.eventTypes[event.eventType] = (stats.eventTypes[event.eventType] || 0) + 1;

          // Estadísticas específicas por tipo
          if (event.eventType === 'scene_view') {
            stats.sceneViews[event.data.sceneId] = (stats.sceneViews[event.data.sceneId] || 0) + 1;
          }

          if (event.eventType === 'choice_made') {
            const choice = `${event.data.fromScene} → ${event.data.toScene}`;
            stats.choicesMade[choice] = (stats.choicesMade[choice] || 0) + 1;
          }

          if (event.eventType === 'ending_reached') {
            stats.endingsReached[event.data.sceneId] = (stats.endingsReached[event.data.sceneId] || 0) + 1;
          }

          if (event.eventType === 'session_start') {
            stats.agents[event.data.agent] = (stats.agents[event.data.agent] || 0) + 1;
          }
        });

        return new Response(JSON.stringify(stats, null, 2), {
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          }
        });
      }
    }

    // Endpoint para exportar todos los eventos como JSON
    if (url.pathname === '/analytics/export' && request.method === 'GET') {
      try {
        const list = await env.ANALYTICS.list({ limit: 1000 });
        const events = [];

        for (const key of list.keys) {
          const value = await env.ANALYTICS.get(key.name);
          if (value) {
            events.push(JSON.parse(value));
          }
        }

        return new Response(JSON.stringify(events, null, 2), {
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Content-Disposition': 'attachment; filename="analytics-export.json"'
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          }
        });
      }
    }

    return new Response('Cloudflare Worker Analytics API\n\nEndpoints:\nPOST /analytics - Receive event\nGET /analytics/stats - View statistics\nGET /analytics/export - Export all events', {
      headers: { 'Content-Type': 'text/plain' }
    });
  }
};
