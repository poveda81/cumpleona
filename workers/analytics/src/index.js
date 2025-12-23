/**
 * Cloudflare Worker para analytics de Portal 27
 *
 * Endpoints:
 * - POST /api/analytics/track - Recibe eventos de analytics
 * - GET /api/analytics/events - Obtiene eventos (requiere auth)
 * - GET /api/analytics/stats - Obtiene estadísticas agregadas (requiere auth)
 */

// CORS helper
function corsHeaders(origin) {
  const allowedOrigins = [
    'https://cumpleona.pages.dev',
    'http://localhost:8000',
    'http://127.0.0.1:8000'
  ];

  const allowed = allowedOrigins.includes(origin) ? origin : allowedOrigins[0];

  return {
    'Access-Control-Allow-Origin': allowed,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400',
  };
}

// Handle OPTIONS for CORS preflight
function handleOptions(request) {
  const origin = request.headers.get('Origin');
  return new Response(null, {
    status: 204,
    headers: corsHeaders(origin)
  });
}

// Auth check with API token validation
function isAuthorized(request, env) {
  const authHeader = request.headers.get('Authorization');
  const token = authHeader?.replace('Bearer ', '');

  // Si no hay API_TOKEN configurado, acepta cualquier Bearer token
  if (!env.API_TOKEN) {
    return authHeader && authHeader.startsWith('Bearer ');
  }

  // Si hay API_TOKEN, validar contra él
  return token === env.API_TOKEN;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin');

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return handleOptions(request);
    }

    try {
      // POST /api/analytics/track - Guardar evento
      if (url.pathname === '/api/analytics/track' && request.method === 'POST') {
        const event = await request.json();

        // Validar evento
        if (!event.type || !event.sessionId) {
          return new Response(JSON.stringify({ error: 'Invalid event data' }), {
            status: 400,
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders(origin)
            }
          });
        }

        // Insertar en D1
        await env.DB.prepare(`
          INSERT INTO analytics_events (
            session_id, event_type, agent_id, scene_id, choice_text,
            target_scene, puzzle_id, ending_id, timestamp, user_agent,
            referrer, metadata
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).bind(
          event.sessionId,
          event.type,
          event.agentId || null,
          event.sceneId || null,
          event.choiceText || null,
          event.targetScene || null,
          event.puzzleId || null,
          event.endingId || null,
          event.timestamp || Date.now(),
          request.headers.get('User-Agent') || null,
          request.headers.get('Referer') || null,
          JSON.stringify(event.metadata || {})
        ).run();

        return new Response(JSON.stringify({ success: true }), {
          status: 201,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders(origin)
          }
        });
      }

      // GET /api/analytics/events - Obtener eventos (requiere auth)
      if (url.pathname === '/api/analytics/events' && request.method === 'GET') {
        if (!isAuthorized(request, env)) {
          return new Response(JSON.stringify({ error: 'Unauthorized' }), {
            status: 401,
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders(origin)
            }
          });
        }

        const limit = parseInt(url.searchParams.get('limit') || '1000');
        const offset = parseInt(url.searchParams.get('offset') || '0');
        const sessionId = url.searchParams.get('sessionId');

        let query = 'SELECT * FROM analytics_events';
        let bindings = [];

        if (sessionId) {
          query += ' WHERE session_id = ?';
          bindings.push(sessionId);
        }

        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?';
        bindings.push(limit, offset);

        const { results } = await env.DB.prepare(query).bind(...bindings).all();

        return new Response(JSON.stringify({ events: results }), {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders(origin)
          }
        });
      }

      // GET /api/analytics/stats - Estadísticas agregadas (requiere auth)
      if (url.pathname === '/api/analytics/stats' && request.method === 'GET') {
        if (!isAuthorized(request, env)) {
          return new Response(JSON.stringify({ error: 'Unauthorized' }), {
            status: 401,
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders(origin)
            }
          });
        }

        // Total sessions
        const { results: totalSessions } = await env.DB.prepare(`
          SELECT COUNT(DISTINCT session_id) as count
          FROM analytics_events
        `).all();

        // Total events
        const { results: totalEvents } = await env.DB.prepare(`
          SELECT COUNT(*) as count
          FROM analytics_events
        `).all();

        // Events by type
        const { results: eventsByType } = await env.DB.prepare(`
          SELECT event_type, COUNT(*) as count
          FROM analytics_events
          GROUP BY event_type
          ORDER BY count DESC
        `).all();

        // Most popular agents
        const { results: agentStats } = await env.DB.prepare(`
          SELECT agent_id, COUNT(*) as count
          FROM analytics_events
          WHERE agent_id IS NOT NULL AND event_type = 'session_start'
          GROUP BY agent_id
          ORDER BY count DESC
          LIMIT 10
        `).all();

        // Most visited scenes
        const { results: sceneStats } = await env.DB.prepare(`
          SELECT scene_id, COUNT(*) as count
          FROM analytics_events
          WHERE scene_id IS NOT NULL AND event_type = 'scene_view'
          GROUP BY scene_id
          ORDER BY count DESC
          LIMIT 10
        `).all();

        // Endings reached
        const { results: endingStats } = await env.DB.prepare(`
          SELECT ending_id, COUNT(*) as count
          FROM analytics_events
          WHERE ending_id IS NOT NULL AND event_type = 'ending_reached'
          GROUP BY ending_id
          ORDER BY count DESC
        `).all();

        return new Response(JSON.stringify({
          totalSessions: totalSessions[0]?.count || 0,
          totalEvents: totalEvents[0]?.count || 0,
          eventsByType,
          agentStats,
          sceneStats,
          endingStats
        }), {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders(origin)
          }
        });
      }

      // GET /api/analytics/paths - Obtener caminos por sesión (requiere auth)
      if (url.pathname === '/api/analytics/paths' && request.method === 'GET') {
        if (!isAuthorized(request, env)) {
          return new Response(JSON.stringify({ error: 'Unauthorized' }), {
            status: 401,
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders(origin)
            }
          });
        }

        const limit = parseInt(url.searchParams.get('limit') || '10');
        const agentId = url.searchParams.get('agentId');

        // Obtener todas las sesiones con sus eventos ordenados
        let query = `
          SELECT session_id, agent_id, event_type, scene_id, choice_text,
                 target_scene, ending_id, timestamp
          FROM analytics_events
        `;

        let bindings = [];
        if (agentId) {
          query += ' WHERE agent_id = ?';
          bindings.push(agentId);
        }

        query += ' ORDER BY session_id, timestamp ASC';

        const { results } = await env.DB.prepare(query).bind(...bindings).all();

        // Agrupar eventos por sesión
        const sessions = {};
        results.forEach(event => {
          if (!sessions[event.session_id]) {
            sessions[event.session_id] = {
              sessionId: event.session_id,
              agentId: event.agent_id,
              events: []
            };
          }
          sessions[event.session_id].events.push(event);
        });

        // Convertir a array y limitar
        const sessionArray = Object.values(sessions).slice(0, limit);

        return new Response(JSON.stringify({
          sessions: sessionArray,
          total: Object.keys(sessions).length
        }), {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders(origin)
          }
        });
      }

      // Default: 404
      return new Response(JSON.stringify({ error: 'Not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders(origin)
        }
      });

    } catch (error) {
      console.error('Worker error:', error);
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders(origin)
        }
      });
    }
  }
};
