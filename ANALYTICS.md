# 📊 Sistema de Analytics - Operación Portal 27

## ¿Qué datos se recopilan?

El juego incluye un sistema de analytics **privacy-friendly** que guarda eventos localmente en el navegador del usuario. Los datos se pueden exportar para análisis.

### Eventos trackeados:

| Evento | Descripción | Datos guardados |
|--------|-------------|-----------------|
| `session_start` | Usuario abre el juego | Agente seleccionado, timestamp |
| `mission_start` | Usuario hace clic en "Comenzar misión" | Timestamp |
| `scene_view` | Usuario ve una escena | ID de escena, si es final, si tiene puzzle |
| `choice_made` | Usuario elige una opción | Escena origen, texto de opción, escena destino |
| `ending_reached` | Usuario alcanza un final | ID del final, tiempo total de sesión |
| `puzzle_start` | Usuario acepta un puzzle | ID y tipo de puzzle |
| `puzzle_complete` | Usuario completa/falla un puzzle | ID, éxito, intentos |
| `back_button` | Usuario usa el botón atrás | Escena origen, escena destino |
| `mission_reset` | Usuario resetea la misión | Tiempo total de sesión |
| `agent_switch` | Usuario cambia de agente | Agente anterior, agente nuevo |


## 🔍 Ver analytics en vivo

Abre la consola del navegador (F12) y usa estos comandos:

```javascript
// Ver todos los eventos en una tabla
viewAnalytics()

// Exportar eventos a un archivo JSON
exportAnalytics()

// Limpiar todos los eventos guardados
clearAnalytics()

// Acceder al objeto analytics directamente
window.gameAnalytics
```

## 📥 Exportar datos para análisis

### Método 1: Desde la consola del navegador

```javascript
exportAnalytics()
```

Esto descargará un archivo JSON con todos los eventos.

### Método 2: Obtener datos de múltiples usuarios

Si quieres recopilar datos de múltiples usuarios, tienes dos opciones:

#### A) Pedir a los usuarios que exporten sus datos
1. Instruye a tus usuarios: "Abre la consola (F12), escribe `exportAnalytics()` y envíame el archivo"
2. Combina todos los JSONs para análisis

#### B) Usar un backend (Cloudflare Worker)
1. Configura el Cloudflare Worker incluido en `cloudflare-worker-analytics-example.js`
2. Actualiza `ANALYTICS_ENDPOINT` en `web/js/analytics.js`
3. Los datos se enviarán automáticamente a tu servidor

## 📈 Análisis de datos

### Con Python y Pandas:

```python
import json
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

# Cargar datos
with open('portal27_analytics_XXXXX.json', 'r') as f:
    events = json.load(f)

# Convertir a DataFrame
df = pd.DataFrame(events)

# Análisis básico
print(f"Total de eventos: {len(df)}")
print(f"Sesiones únicas: {df['sessionId'].nunique()}")
print(f"Tipos de eventos:\n{df['eventType'].value_counts()}")

# Analizar escenas más visitadas
scene_views = df[df['eventType'] == 'scene_view']
scenes = [event['sceneId'] for event in scene_views['data']]
print("\nEscenas más visitadas:")
print(Counter(scenes).most_common(10))

# Analizar opciones más elegidas
choices = df[df['eventType'] == 'choice_made']
choice_paths = [f"{event['fromScene']} → {event['toScene']}"
                for event in choices['data']]
print("\nCaminos más elegidos:")
print(Counter(choice_paths).most_common(10))

# Analizar finales alcanzados
endings = df[df['eventType'] == 'ending_reached']
ending_ids = [event['sceneId'] for event in endings['data']]
print("\nFinales más alcanzados:")
print(Counter(ending_ids).most_common())

# Analizar agentes más populares
sessions = df[df['eventType'] == 'session_start']
agents = [event.get('agent', 'unknown') for event in sessions['data']]
print("\nAgentes más elegidos:")
print(Counter(agents).most_common())

# Visualizar escenas más visitadas
scene_counts = Counter(scenes)
plt.figure(figsize=(12, 6))
plt.bar(scene_counts.keys(), scene_counts.values())
plt.xticks(rotation=45, ha='right')
plt.title('Escenas más visitadas')
plt.xlabel('Escena')
plt.ylabel('Visitas')
plt.tight_layout()
plt.savefig('scene_visits.png')
plt.show()
```

### Con Google Sheets:

1. Exporta los datos a JSON
2. Usa [JSON to CSV converter](https://json-csv.com/)
3. Importa el CSV a Google Sheets
4. Crea tablas dinámicas y gráficos

### Métricas útiles a calcular:

#### 1. Tasa de conversión (¿cuántos completan el juego?)
```python
total_sessions = df[df['eventType'] == 'session_start']['sessionId'].nunique()
sessions_with_ending = df[df['eventType'] == 'ending_reached']['sessionId'].nunique()
conversion_rate = (sessions_with_ending / total_sessions) * 100
print(f"Tasa de completación: {conversion_rate:.1f}%")
```

#### 2. Tiempo promedio de juego
```python
ending_times = [event['totalSessionTime'] / 1000 / 60  # convertir a minutos
                for event in df[df['eventType'] == 'ending_reached']['data']]
avg_time = sum(ending_times) / len(ending_times) if ending_times else 0
print(f"Tiempo promedio de juego: {avg_time:.1f} minutos")
```

#### 3. Caminos más populares (path analysis)
```python
# Agrupar eventos por sesión
sessions_grouped = df.groupby('sessionId')

# Para cada sesión, extraer la secuencia de escenas
paths = []
for session_id, group in sessions_grouped:
    scene_events = group[group['eventType'] == 'scene_view'].sort_values('timestamp')
    if len(scene_events) > 0:
        path = ' → '.join([event['sceneId'] for event in scene_events['data']])
        paths.append(path)

print("\nCaminos más comunes:")
print(Counter(paths).most_common(5))
```

#### 4. Punto de abandono (¿dónde se quedan los usuarios?)
```python
# Encontrar la última escena de cada sesión incompleta
incomplete_sessions = df[~df['sessionId'].isin(
    df[df['eventType'] == 'ending_reached']['sessionId']
)]

last_scenes = []
for session_id in incomplete_sessions['sessionId'].unique():
    session_events = incomplete_sessions[incomplete_sessions['sessionId'] == session_id]
    scene_events = session_events[session_events['eventType'] == 'scene_view']
    if len(scene_events) > 0:
        last_scene = scene_events.iloc[-1]['data']['sceneId']
        last_scenes.append(last_scene)

print("\nEscenas donde más abandonan:")
print(Counter(last_scenes).most_common(10))
```

## 🎯 Preguntas que puedes responder con los datos

### Sobre la experiencia:
- ¿Qué agentes son más populares?
- ¿Cuánto tiempo pasan los usuarios en el juego?
- ¿Qué porcentaje de usuarios completa el juego?
- ¿En qué escena abandonan más usuarios?

### Sobre las decisiones:
- ¿Qué opciones eligen más frecuentemente?
- ¿Qué caminos narrativos son más populares?
- ¿Qué finales son más alcanzados?
- ¿Las decisiones varían por agente?

### Sobre el engagement:
- ¿Cuántas escenas ven en promedio?
- ¿Usan el botón de "Atrás"?
- ¿Resetean la misión a menudo?
- ¿Cambian de agente después de completar?

### Sobre los puzzles:
- ¿Qué puzzles completan/fallan más?
- ¿Cuántos intentos necesitan?
- ¿Los puzzles causan abandono?

## 🔐 Privacidad

Este sistema de analytics es **privacy-friendly**:

- ✅ No usa cookies
- ✅ No requiere consentimiento (GDPR compliant)
- ✅ Datos guardados localmente en el navegador
- ✅ No se comparte información personal
- ✅ No se trackea entre sitios
- ✅ El usuario puede borrar sus datos en cualquier momento

Si decides usar el backend con Cloudflare Worker:
- Los datos se guardan por máximo 90 días
- No se guarda información identificable (IP, etc.)
- Cumple con GDPR y leyes de privacidad

## 📝 Configuración avanzada

### Deshabilitar analytics completamente

En `web/js/analytics.js`:
```javascript
const ANALYTICS_ENABLED = false;
```

### Cambiar el endpoint de analytics

En `web/js/analytics.js`:
```javascript
const ANALYTICS_ENDPOINT = 'https://tu-api.com/analytics';
```

### Añadir nuevos eventos personalizados

```javascript
// En app.js, después de importar analytics
analytics.sendEvent('custom_event', {
  customData: 'valor'
});
```

## 🚀 Siguiente nivel: Dashboard en tiempo real

Si quieres un dashboard profesional:

1. **Usa Cloudflare Worker + D1 Database**
   - Guarda eventos en SQL
   - Crea queries para métricas en tiempo real

2. **Usa Google Analytics 4** (alternativa simple)
   - Añade el script de GA4 al HTML
   - Usa eventos personalizados para trackear acciones

3. **Usa Plausible Analytics** (privacy-friendly)
   - Alternativa a Google Analytics
   - Respeta la privacidad
   - Dashboard hermoso incluido

## 💡 Tips

- Exporta los datos regularmente para no perder información
- Analiza los datos después de tener al menos 20-30 sesiones
- Compara métricas entre diferentes agentes
- Usa los insights para mejorar la narrativa

¡Disfruta analizando los datos! 📊
