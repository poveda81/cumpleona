# Sistema de Generación de Personajes

Este sistema permite generar imágenes de personajes (agentes) en estilo comic book de los 80s usando Google Gemini Imagen 3.

## Estructura de Archivos

```
prompts/
├── agents_generation.json    # Configuración de todos los agentes
└── README_agents.md         # Este archivo

reference/agents/             # Carpeta con imágenes de referencia
├── paula/                   # Fotos reales de Paula
├── manuela/                 # Fotos reales de Manuela
├── claudia/                 # Fotos reales de Claudia
└── ...                      # etc.
```

## Configuración Inicial

### 1. Añadir Imágenes de Referencia

Para cada agente, coloca 1-4 fotos reales en su carpeta correspondiente:

```bash
# Ejemplo para Paula
cp foto1_paula.jpg reference/agents/paula/
cp foto2_paula.jpg reference/agents/paula/
```

**Recomendaciones para las fotos:**
- Fotos claras donde se vea bien la cara
- Diferentes ángulos (frontal, perfil)
- Buena iluminación
- Formatos soportados: .jpg, .jpeg, .png, .webp

### 2. Configurar Variables de Entorno

Asegúrate de tener tu API key de Google configurada:

```bash
export GOOGLE_API_KEY="tu-api-key-aqui"
```

O añádela al archivo `.env`:

```
GOOGLE_API_KEY=tu-api-key-aqui
```

## Uso del Script

### Generar Imágenes de Cuerpo Completo (Full Body)

```bash
uv run python scripts/generate_agents.py \
  --agents prompts/agents_generation.json \
  --type fullbody
```

### Generar Avatares (Retratos)

```bash
uv run python scripts/generate_agents.py \
  --agents prompts/agents_generation.json \
  --type avatar
```

### Generar Ambos Tipos

```bash
uv run python scripts/generate_agents.py \
  --agents prompts/agents_generation.json \
  --type both
```

### Generar Solo un Agente Específico

```bash
uv run python scripts/generate_agents.py \
  --agents prompts/agents_generation.json \
  --type both \
  --agent-id paula
```

### Opciones Adicionales

```bash
# Omitir imágenes ya generadas
uv run python scripts/generate_agents.py \
  --agents prompts/agents_generation.json \
  --type both \
  --skip-generated

# Limitar el número de agentes a procesar (útil para testing)
uv run python scripts/generate_agents.py \
  --agents prompts/agents_generation.json \
  --type fullbody \
  --limit 3
```

## Formato del JSON de Configuración

El archivo `agents_generation.json` tiene esta estructura:

```json
{
  "agents": {
    "agent_id": {
      "name": "Nombre del Personaje",
      "tag": "Habilidad Principal",
      "qualities": ["Cualidad 1", "Cualidad 2", "Cualidad 3"],
      "specialItem": "Objeto especial que porta",
      "reference_images": "prompts/agents_refs/agent_id",
      "fullbody_output": "web/img/agents/agent_id_fullbody.png",
      "avatar_output": "web/img/agents/agent_id_avatar.png",
      "fullbody_generated": false,
      "avatar_generated": false
    }
  }
}
```

### Campos Explicados

- **name**: Nombre del personaje
- **tag**: Habilidad o característica principal (ej: "Súper inteligencia")
- **qualities**: Array con 3 cualidades que definen al personaje
- **specialItem**: Objeto mágico/especial que lleva el personaje
- **reference_images**: Carpeta con fotos reales de referencia (ruta: `reference/agents/agent_id`)
- **fullbody_output**: Ruta donde se guardará la imagen de cuerpo completo
- **avatar_output**: Ruta donde se guardará el avatar
- **fullbody_generated**: Flag que indica si ya se generó (se actualiza automáticamente)
- **avatar_generated**: Flag que indica si ya se generó (se actualiza automáticamente)

## Prompts Utilizados

### Full Body Illustration

El script usa un prompt especial que:
- Emula el estilo de comic book vintage de los 80s
- Incorpora el "special item" del personaje
- Viste al personaje con ropa auténtica de la época (1983-1985)
- Usa las fotos de referencia para mantener los rasgos faciales
- Aplica iluminación dramática (chiaroscuro)
- Fondo plano con textura de halftone dots

### Avatar Portrait

Similar al full body pero:
- Solo muestra cabeza y hombros (bust)
- Sin objeto especial visible
- Mismo estilo visual retro 80s
- Expresión que refleja su tag y cualidades

## Tips y Recomendaciones

1. **Calidad de Referencias**: Cuanto mejores sean las fotos de referencia, mejor será el resultado
2. **Consistencia**: Si no te gusta el resultado, puedes regenerar borrando el flag `"generated": true`
3. **Experimentación**: Prueba con un solo agente primero (`--agent-id`) antes de generar todos
4. **Costos**: Cada imagen con Gemini Imagen 3 tiene un costo, usa `--limit` para hacer pruebas
5. **Verificación**: Revisa las imágenes generadas y ajusta los datos del personaje si es necesario

## Solución de Problemas

### Error: "GOOGLE_API_KEY no configurada"
- Asegúrate de tener la variable de entorno configurada
- Verifica que el archivo `.env` existe y está bien configurado

### Error: "No se encontraron imágenes de referencia"
- Verifica que la carpeta existe: `reference/agents/[agent_id]`
- Asegúrate de que las imágenes tienen extensiones válidas (.jpg, .png, etc.)

### El resultado no se parece al personaje
- Añade más fotos de referencia (hasta 4)
- Asegúrate de que las fotos sean claras y de buena calidad
- Prueba con fotos de diferentes ángulos
- Gemini Imagen 3 usa las imágenes de referencia directamente, así que deberías obtener mejores resultados

### Las imágenes son muy diferentes entre sí
- Gemini tiene variabilidad natural
- Puedes regenerar específicamente las que no te gusten
- Considera ajustar las cualidades en el JSON para guiar mejor el estilo
