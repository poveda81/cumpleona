# Reference Images

Esta carpeta contiene imágenes de referencia utilizadas para la generación de imágenes con IA. **No se publican** en la web.

## Estructura

```
reference/
├── scenarios/     # Imágenes de referencia para escenarios
│   └── intro/     # Ejemplo: carpeta con referencias para la escena "intro"
│       └── *.jpg
└── agents/        # Fotos de referencia para personajes
    └── nombre/    # Ejemplo: carpeta con fotos para el agente "nombre"
        └── *.jpg
```

## Uso

### Para escenarios:

1. Crea una carpeta con el nombre del escenario: `reference/scenarios/nombre_escena/`
2. Añade una o más imágenes de referencia en esa carpeta
3. En `prompts/scenario_prompts.json`, configura:
   ```json
   {
     "nombre_escena": {
       "prompt": "...",
       "output_file": "web/img/scenarios/nombre_escena.png",
       "use_reference_image": true,
       "reference_image": "reference/scenarios/nombre_escena"
     }
   }
   ```

### Para agentes:

1. Crea una carpeta con el nombre del agente: `reference/agents/nombre_agente/`
2. Añade fotos de referencia del agente en esa carpeta
3. En `prompts/agent_prompts.json`, configura:
   ```json
   {
     "nombre_agente": {
       "prompt": "...",
       "output_file": "web/img/agents/nombre_agente.png",
       "use_reference_image": true,
       "reference_image": "reference/agents/nombre_agente"
     }
   }
   ```

## Notas importantes

- ✅ Las imágenes de referencia **NO se suben a Git** (están en `.gitignore`)
- ✅ Solo se publican las imágenes generadas en `/web/img/`
- ⚠️ Asegúrate de tener permisos para usar las fotos de referencia
- 📝 El script toma la primera imagen válida de cada carpeta

## Formatos soportados

- `.jpg` / `.jpeg`
- `.png`
- `.webp`
