# Sistema de Generación de Posters

Este sistema genera posters en estilo comic book de los 80s combinando a Ona con cada uno de los agentes en diferentes escenarios.

## Estructura de Archivos

```
reference/agents/ona/
├── ona_full.png              # Imagen de cuerpo completo de Ona (REQUERIDA)

web/img/agents/
├── paula_fullbody.png        # Imágenes fullbody de cada agente
├── manuela_fullbody.png
├── claudia_fullbody.png
└── ...

prompts/poster_scenes.json    # Definición de las 15 escenas disponibles

web/img/posters/              # Carpeta de salida con los posters generados
├── ona_paula_scene01.png
├── ona_paula_scene02.png
└── ...
```

## Requisitos Previos

### 1. Imagen de Ona

**MUY IMPORTANTE**: Debes colocar la imagen de cuerpo completo de Ona en:
```
reference/agents/ona/ona_full.png
```

Esta imagen se combinará con cada agente para generar los posters.

### 2. Imágenes Fullbody de Agentes

Cada agente debe tener su imagen de cuerpo completo generada:
```
web/img/agents/{agent_id}_fullbody.png
```

Puedes generar estas imágenes con:
```bash
uv run python scripts/generate_agents.py \
  --agents prompts/agents_generation.json \
  --type fullbody
```

### 3. API Key de OpenAI

Asegúrate de tener configurada tu API key:
```bash
export OPENAI_API_KEY="tu-api-key"
```

## Verificación del Setup

Antes de generar posters, verifica que todo esté configurado:

```bash
uv run python scripts/check_posters_setup.py
```

Este script te dirá:
- ✅ Si la API key está configurada
- ✅ Si existe la imagen de Ona
- ✅ Cuántos agentes tienen imágenes disponibles
- ✅ Cuántas escenas hay disponibles
- ⚠️ Qué falta por configurar

## Escenas Disponibles

El archivo `prompts/poster_scenes.json` contiene 15 escenas diferentes:

1. **The Abandoned Railway** - Vías abandonadas en el bosque
2. **The Treehouse** - Casa del árbol con equipos de radio
3. **The School Hallway** - Pasillo de escuela de noche
4. **The Cornfield** - Campo de maíz denso
5. **The Basement** - Sótano con símbolos extraños
6. **The Storm Drain** - Tubería de desagüe con graffiti
7. **The Radio Tower** - Torre de radio con vallas
8. **The Laboratory Exterior** - Exterior del laboratorio
9. **The Bike Drop** - Esquina suburbana con bicicletas
10. **The Junkyard** - Desguace con coches aplastados
11. **The Attic** - Ático polvoriento
12. **The Restricted Area** - Zona restringida con vegetación extraña
13. **The Diner** - Diner retro de noche
14. **The Old Bridge** - Puente de madera cubierto
15. **The Bus Stop** - Parada de autobús solitaria

Cada escena incluye:
- **theme**: Nombre de la escena
- **scene_description**: Descripción de la acción
- **lighting_mood**: Ambiente de iluminación

## Uso del Script

### Opción 1: Un Agente, Una Escena Aleatoria

Perfecto para hacer pruebas:

```bash
uv run python scripts/generate_posters.py \
  --agent paula \
  --scene random
```

### Opción 2: Un Agente, Escena Específica

```bash
uv run python scripts/generate_posters.py \
  --agent paula \
  --scene 5
```

### Opción 3: Un Agente, Todas las Escenas

Genera 15 posters (uno por cada escena):

```bash
uv run python scripts/generate_posters.py \
  --agent paula \
  --scene all
```

### Opción 4: Todos los Agentes, Una Escena

```bash
uv run python scripts/generate_posters.py \
  --agent all \
  --scene 5
```

### Opción 5: Generar Todos los Posters Posibles

⚠️ **CUIDADO**: Esto generará 17 agentes × 15 escenas = 255 posters
Costo aproximado: ~$250 USD con DALL-E 3

```bash
uv run python scripts/generate_posters.py \
  --agent all \
  --scene all
```

### Opción 6: Directorio de Salida Personalizado

```bash
uv run python scripts/generate_posters.py \
  --agent paula \
  --scene random \
  --output-dir mi_carpeta_posters
```

## Formato del Prompt

El script usa este prompt base que combina:

```
A vintage 1980s horror/adventure comic book panel illustration.
The art style must strictly adhere to heavy black ink outlines,
bold line work, and prominent halftone dot shading (Ben-Day dots)
throughout the entire image for texture and color, mimicking aged paper.

You have to use the uploaded photos of the two characters.
They will be standing together in a full-body or three-quarter view shot.

Both characters are rendered consistently in the aforementioned comic book style,
maintaining their unique items if applicable (e.g., flashlights, calculators).
The clothing is styled in the 80s retro aesthetic and can be a mix of casual
and adventure-ready outfits (jackets, hoodies, rolled-up jeans, retro sneakers,
backpacks, etc...) always in Stranger Things style.

The scene is set in: [DESCRIPCIÓN DE LA ESCENA DEL JSON]

NOTE: The aspect ratio of the image must be 1:1 (square).
```

## Nombres de Archivos

Los posters se guardan con este formato:
```
ona_{agent_id}_scene{numero}.png
```

Ejemplos:
- `ona_paula_scene01.png` - Ona y Paula en "The Abandoned Railway"
- `ona_manuela_scene05.png` - Ona y Manuela en "The Basement"
- `ona_claudia_scene12.png` - Ona y Claudia en "The Restricted Area"

## Tips y Recomendaciones

### 1. Empieza con Pruebas

Genera primero un poster de prueba:
```bash
uv run python scripts/generate_posters.py --agent paula --scene random
```

Revisa el resultado antes de generar más.

### 2. Generación por Lotes

Para generar posters de forma organizada:

```bash
# Primero todos los de Paula
uv run python scripts/generate_posters.py --agent paula --scene all

# Luego todos los de Manuela
uv run python scripts/generate_posters.py --agent manuela --scene all

# Y así sucesivamente...
```

### 3. Control de Costos

- Cada imagen con DALL-E 3 cuesta aproximadamente $0.04 USD
- Un agente con todas las escenas = 15 imágenes = ~$0.60 USD
- Todos los agentes con todas las escenas = ~$10.20 USD (255 imágenes)

### 4. Escenas Favoritas

Si solo quieres usar ciertas escenas, puedes ejecutar:
```bash
# Escenas más icónicas (5, 8, 10, 12)
uv run python scripts/generate_posters.py --agent all --scene 5
uv run python scripts/generate_posters.py --agent all --scene 8
uv run python scripts/generate_posters.py --agent all --scene 10
uv run python scripts/generate_posters.py --agent all --scene 12
```

### 5. Organización de Resultados

Considera crear subdirectorios por agente:
```bash
uv run python scripts/generate_posters.py \
  --agent paula \
  --scene all \
  --output-dir web/img/posters/paula
```

## Solución de Problemas

### Error: "No se encontró la imagen de Ona"

Verifica que existe el archivo:
```bash
ls -la reference/agents/ona/ona_full.png
```

Si no existe, coloca la imagen de Ona en esa ubicación.

### Error: "No se encontró la imagen del agente"

El agente necesita tener su imagen fullbody generada primero:
```bash
uv run python scripts/generate_agents.py \
  --agents prompts/agents_generation.json \
  --type fullbody \
  --agent-id paula
```

### Error: "OPENAI_API_KEY no configurada"

Configura tu API key:
```bash
export OPENAI_API_KEY="sk-..."
```

O añádela al archivo `.env`:
```
OPENAI_API_KEY=sk-...
```

### El resultado no coincide con las fotos

El sistema primero usa GPT-4o para analizar las imágenes y crear un prompt refinado, luego DALL-E 3 genera la imagen. Debido a la naturaleza de DALL-E, puede haber variaciones. Puedes:
- Regenerar el poster (cada vez será ligeramente diferente)
- Ajustar la descripción de la escena en `poster_scenes.json`
- Usar imágenes fullbody más claras

## Workflow Completo Recomendado

1. **Preparación**:
   ```bash
   # Verificar configuración
   uv run python scripts/check_posters_setup.py
   ```

2. **Prueba inicial**:
   ```bash
   # Generar un poster de prueba
   uv run python scripts/generate_posters.py --agent paula --scene 5
   ```

3. **Generación por agente**:
   ```bash
   # Si el resultado es bueno, generar todas las escenas de ese agente
   uv run python scripts/generate_posters.py --agent paula --scene all
   ```

4. **Revisión y ajustes**:
   - Revisa los resultados
   - Ajusta escenas si es necesario
   - Regenera los que no te gusten

5. **Producción completa** (opcional):
   ```bash
   # Solo si estás satisfecho con los resultados
   uv run python scripts/generate_posters.py --agent all --scene all
   ```

## Personalización de Escenas

Puedes modificar o añadir escenas editando `prompts/poster_scenes.json`:

```json
{
  "id": 16,
  "theme": "Mi Escena Personalizada",
  "scene_description": "descripción de la acción...",
  "lighting_mood": "descripción de la iluminación..."
}
```

Después de añadir escenas nuevas, el script las detectará automáticamente.
