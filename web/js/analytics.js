/**
 * Sistema de analytics personalizado para tracking de caminos y decisiones
 *
 * Envía eventos a un endpoint para analizar:
 * - Qué escenas visitan los usuarios
 * - Qué opciones eligen
 * - Qué finales alcanzan
 * - Cuánto tiempo pasan en cada escena
 * - Qué puzzles completan
 */

const ANALYTICS_ENABLED = true; // Cambiar a false para deshabilitar
const ANALYTICS_ENDPOINT = 'https://portal27-analytics.jlpoveda.workers.dev/api/analytics/track'; // Cambiar después de deploy

class GameAnalytics {
  constructor() {
    this.sessionId = this.generateSessionId();
    this.sessionStart = Date.now();
    this.currentScene = null;
    this.sceneStartTime = null;
    this.events = [];
  }

  generateSessionId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Envía un evento al servidor de analytics
   */
  async sendEvent(eventType, data) {
    if (!ANALYTICS_ENABLED) return;

    const event = {
      sessionId: this.sessionId,
      type: eventType,
      timestamp: Date.now(),
      sessionDuration: Date.now() - this.sessionStart,
      agentId: data.agentId || data.agent,
      sceneId: data.sceneId || data.fromScene,
      choiceText: data.choiceText,
      targetScene: data.toScene || data.nextSceneId,
      puzzleId: data.puzzleId,
      endingId: data.sceneId && eventType === 'ending_reached' ? data.sceneId : null,
      metadata: data
    };

    // Guardar en localStorage como backup
    this.saveEventLocally({
      sessionId: this.sessionId,
      timestamp: Date.now(),
      sessionDuration: Date.now() - this.sessionStart,
      eventType,
      data,
      userAgent: navigator.userAgent,
      screen: {
        width: window.screen.width,
        height: window.screen.height
      },
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      }
    });

    // Intentar enviar al servidor (solo si el endpoint está configurado)
    if (ANALYTICS_ENDPOINT && !ANALYTICS_ENDPOINT.includes('YOUR_SUBDOMAIN')) {
      try {
        await fetch(ANALYTICS_ENDPOINT, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(event)
        });
        console.log('📊 Analytics sent:', eventType);
      } catch (error) {
        console.warn('Failed to send analytics:', error);
        // No pasa nada, el evento ya está guardado localmente
      }
    } else {
      // Solo log para debugging si no hay endpoint configurado
      console.log('📊 Analytics Event (local only):', eventType, data);
    }
  }

  /**
   * Guarda eventos localmente para análisis offline
   */
  saveEventLocally(event) {
    try {
      const key = 'portal27_analytics';
      const stored = localStorage.getItem(key);
      const events = stored ? JSON.parse(stored) : [];
      events.push(event);

      // Mantener solo los últimos 100 eventos
      if (events.length > 100) {
        events.shift();
      }

      localStorage.setItem(key, JSON.stringify(events));
    } catch (e) {
      // Si localStorage está lleno o no disponible, ignorar
    }
  }

  /**
   * Trackea el inicio de sesión
   */
  trackSessionStart(agent) {
    this.sendEvent('session_start', {
      agent: agent?.name || 'unknown',
      agentId: new URLSearchParams(window.location.search).get('agent')
    });
  }

  /**
   * Trackea cuando se inicia la misión
   */
  trackMissionStart() {
    this.sendEvent('mission_start', {});
  }

  /**
   * Trackea cuando se visita una escena
   */
  trackSceneView(sceneId, sceneData) {
    // Si había una escena anterior, calcular tiempo en ella
    if (this.currentScene && this.sceneStartTime) {
      const timeInScene = Date.now() - this.sceneStartTime;
      this.sendEvent('scene_time', {
        sceneId: this.currentScene,
        duration: timeInScene
      });
    }

    // Registrar nueva escena
    this.currentScene = sceneId;
    this.sceneStartTime = Date.now();

    this.sendEvent('scene_view', {
      sceneId,
      isEnding: sceneData?.ending === true,
      hasChoices: Array.isArray(sceneData?.choices) && sceneData.choices.length > 0,
      hasPuzzle: !!sceneData?.puzzle
    });
  }

  /**
   * Trackea cuando se elige una opción
   */
  trackChoice(sceneId, choiceText, nextSceneId) {
    this.sendEvent('choice_made', {
      fromScene: sceneId,
      choiceText,
      toScene: nextSceneId
    });
  }

  /**
   * Trackea cuando se alcanza un final
   */
  trackEnding(sceneId) {
    this.sendEvent('ending_reached', {
      sceneId,
      totalSessionTime: Date.now() - this.sessionStart
    });
  }

  /**
   * Trackea cuando se inicia un puzzle
   */
  trackPuzzleStart(puzzleId, puzzleType) {
    this.sendEvent('puzzle_start', {
      puzzleId,
      puzzleType
    });
  }

  /**
   * Trackea cuando se completa un puzzle
   */
  trackPuzzleComplete(puzzleId, success, attempts) {
    this.sendEvent('puzzle_complete', {
      puzzleId,
      success,
      attempts
    });
  }

  /**
   * Trackea cuando se usa el botón de atrás
   */
  trackBackButton(fromScene, toScene) {
    this.sendEvent('back_button', {
      fromScene,
      toScene
    });
  }

  /**
   * Trackea cuando se reinicia la misión
   */
  trackReset() {
    this.sendEvent('mission_reset', {
      totalSessionTime: Date.now() - this.sessionStart
    });
  }

  /**
   * Trackea cuando se cambia de agente
   */
  trackAgentSwitch(fromAgent, toAgent) {
    this.sendEvent('agent_switch', {
      fromAgent,
      toAgent
    });
  }

  /**
   * Obtiene todos los eventos guardados localmente
   */
  getStoredEvents() {
    try {
      const key = 'portal27_analytics';
      const stored = localStorage.getItem(key);
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      return [];
    }
  }

  /**
   * Limpia los eventos guardados localmente
   */
  clearStoredEvents() {
    try {
      localStorage.removeItem('portal27_analytics');
    } catch (e) {
      // Ignorar
    }
  }

  /**
   * Exporta los eventos a JSON para análisis
   */
  exportEvents() {
    const events = this.getStoredEvents();
    const dataStr = JSON.stringify(events, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `portal27_analytics_${Date.now()}.json`;
    link.click();

    URL.revokeObjectURL(url);
  }
}

// Exponer funciones globales para debugging
window.gameAnalytics = new GameAnalytics();
window.exportAnalytics = () => window.gameAnalytics.exportEvents();
window.clearAnalytics = () => window.gameAnalytics.clearStoredEvents();
window.viewAnalytics = () => console.table(window.gameAnalytics.getStoredEvents());

export default GameAnalytics;
