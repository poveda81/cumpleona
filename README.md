# Portal 27 · Choose Your Own Adventure

This is a Stranger Things–themed choose-your-own-adventure built for the web. Story, agents, puzzles, and assets are all data-driven so you can iterate quickly.

## Project layout

- `web/` – everything that gets published (point GitHub Pages to this folder)
  - `web/index.html` – main page
  - `web/css/` – styles
  - `web/js/` – app logic and puzzle manager
  - `web/data/` – story, agents, puzzles (runtime data)
  - `web/img/` – generated images (scenarios, agents)
- `prompts/` – prompt files for image generation (not published)
  - `prompts/scenario_prompts.json` – scene background prompts
  - `prompts/agent_prompts.json` – agent character prompts
- `reference/` – reference images for generation (not published)
  - `reference/scenarios/` – reference images for scenes
  - `reference/agents/` – reference photos for character generation
- `scripts/` – helper scripts (not published)
  - `scripts/generate_scenarios.py` – generate scene images from prompts
  - `scripts/optimize_images.py` – optimize images for web
  - `scripts/check_references.py` – verify reference images status

## Running locally

1) Serve `web/` with any static server (examples):
```bash
cd web
python3 -m http.server 8000
# or
npx serve .
```
2) Open `http://localhost:8000`.

## Image generation

El script de generación de imágenes soporta múltiples proveedores de IA:
- **OpenAI DALL-E 3** (default, recomendado)
- **Google Imagen 4.0** (requiere facturación activa)

### Configuración

1. Copia el archivo de ejemplo y añade tu API key:
```bash
cp .env.sample .env
```

2. Edita `.env` y añade la clave del proveedor que vayas a usar:
```bash
# Para OpenAI (recomendado)
OPENAI_API_KEY=tu-api-key-aqui

# Para Google Imagen (opcional)
GOOGLE_API_KEY=tu-api-key-aqui
```

### Uso

#### Scenarios (scene backgrounds)
- Prompts file: `prompts/scenario_prompts.json`
- Comandos:
```bash
# Usando OpenAI DALL-E 3 (default)
uv run python scripts/generate_scenarios.py --prompts prompts/scenario_prompts.json

# Usando Google Vertex AI Imagen
uv run python scripts/generate_scenarios.py --prompts prompts/scenario_prompts.json --provider google

# Generar solo las primeras 5 imágenes (para testing)
uv run python scripts/generate_scenarios.py --prompts prompts/scenario_prompts.json --limit 5

# Omitir imágenes ya generadas
uv run python scripts/generate_scenarios.py --prompts prompts/scenario_prompts.json --skip-generated
```

#### Agents (full-body + avatars)
- Prompts file: `prompts/agent_prompts.json`
- Usa el mismo script:
```bash
uv run python scripts/generate_scenarios.py --prompts prompts/agent_prompts.json --provider openai
```

### Gestión de referencias

Para verificar qué carpetas tienen imágenes de referencia:
```bash
uv run python scripts/check_references.py
```

Para añadir referencias:
1. Coloca imágenes en `reference/scenarios/nombre_escena/` o `reference/agents/nombre_agente/`
2. Actualiza `use_reference_image: true` en el archivo de prompts correspondiente
3. Las carpetas ya están creadas para todos los escenarios y agentes

### Notas
- Cada escena **debe** incluir `output_file`.
- `reference_image` apunta a una carpeta en `reference/scenarios/` o `reference/agents/`
- Si `use_reference_image` es true, el script tomará la primera imagen válida como referencia.
- El output siempre es un archivo único por escena.
- Las imágenes de referencia NO se publican (están fuera de `/web`).

## Optimización de imágenes

Las imágenes generadas por IA suelen ser muy grandes. Usa el script de optimización para reducir su tamaño:

```bash
# Ver qué haría sin modificar archivos (dry-run)
uv run python scripts/optimize_images.py --input web/img/scenarios --dry-run --convert-to-jpeg

# Optimizar imágenes en un nuevo directorio
uv run python scripts/optimize_images.py --input web/img/scenarios --output web/img/scenarios_opt --convert-to-jpeg --quality 85

# Optimizar imágenes in-place con backup automático
uv run python scripts/optimize_images.py --input web/img/scenarios --backup --convert-to-jpeg --quality 85

# Solo optimizar sin convertir a JPEG (mantiene PNG)
uv run python scripts/optimize_images.py --input web/img/scenarios --quality 85
```

### Opciones del optimizador:
- `--input`: Directorio con imágenes a optimizar (requerido)
- `--output`: Directorio de salida (opcional, si no se especifica sobrescribe originales)
- `--quality`: Calidad JPEG 1-100 (default: 85)
- `--max-width`: Ancho máximo en píxeles (default: 1920)
- `--max-height`: Alto máximo en píxeles (default: 1080)
- `--convert-to-jpeg`: Convierte PNG a JPEG (ahorro ~90%)
- `--backup`: Crea backup antes de sobrescribir
- `--dry-run`: Muestra qué haría sin modificar archivos

### Resultados esperados:
- Conversión PNG → JPEG: **~90% de reducción** de tamaño
- Optimización sin conversión: **~10-30% de reducción**

## Data files

- `web/data/story.json` – scenes, choices, and puzzle hooks.
- `web/data/agents.json` – agent profiles, including `generated` flag for image generation tracking.
- `web/data/puzzles.json` – definitions for puzzle types and defaults.

## Notes

- `scripts/` is kept outside `web/` to avoid being served on GitHub Pages.
- Scene image fallback in the app expects `img/scenarios/{sceneId}.png` unless overridden by `scene.image`.
- Puzzles open in a modal; supported types include sorting, pattern (with sound/colors), and jigsaw.

## Environment

- Browser-based app; no build step required.
- Python 3.11+ for the generation script.

### Instalación de dependencias

Usando uv (recomendado):
```bash
uv sync
```

O usando pip:
```bash
pip install google-generativeai openai Pillow python-dotenv requests
```

### Variables de entorno

Crea un archivo `.env` basado en `.env.sample`:
```bash
cp .env.sample .env
```

Y añade tus API keys:
- `OPENAI_API_KEY` – para usar OpenAI DALL-E 3
- `GOOGLE_API_KEY` – para usar Google Imagen 4.0

El script carga automáticamente estas variables usando `python-dotenv`.
