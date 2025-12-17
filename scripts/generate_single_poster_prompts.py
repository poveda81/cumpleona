"""
Genera UN archivo de prompt por cada agente, distribuyendo las escenas sin repetir.

Este script lee el archivo agents.json y poster_scenes.json, y crea UN archivo .txt
por cada agente, asignando una escena diferente a cada uno.

Uso:
  python scripts/generate_single_poster_prompts.py --agents web/data/agents.json --scenes prompts/poster_scenes.json
"""

import argparse
import json
from pathlib import Path
from dotenv import load_dotenv


# Prompt base para posters
POSTER_BASE_PROMPT = """A vintage 1980s horror/adventure comic book panel illustration.
The art style must strictly adhere to heavy black ink outlines, bold line work, and prominent halftone dot shading (Ben-Day dots) throughout the entire image for texture and color, mimicking aged paper.

You have to use the uploaded photos of the two characters.
They will be standing together in a full-body or three-quarter view shot.

Both characters are rendered consistently in the aforementioned comic book style, maintaining their unique items if applicable (e.g., flashlights, calculators).
The clothing is styled in the 80s retro aesthetic and can be a mix of casual and adventure-ready outfits (jackets, hoodies, rolled-up jeans, retro sneakers, backpacks, etc...) always in Stranger Things style.

The scene is set in:
{{SCENE_DESCRIPTION}}

NOTE: The aspect ratio of the image must be 2:3 (portrait, like a playing card or trading card format - 63mm x 88mm proportions)."""


def load_agents_config(path: Path):
    """Carga la configuración de agentes desde el JSON."""
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el fichero de agentes: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def load_scenes_config(path: Path):
    """Carga la configuración de escenas desde el JSON."""
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el fichero de escenas: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def format_scene_description(scene_data: dict) -> str:
    """Formatea la descripción de la escena."""
    description = f"""**{scene_data['theme']}**

{scene_data['scene_description']}

Lighting/Mood: {scene_data['lighting_mood']}"""
    return description


def generate_poster_prompt_file(agent_id: str, agent_name: str, scene_id: int, scene_data: dict, output_path: Path, agent_image_path: str):
    """Genera un archivo de texto con el prompt para un poster."""
    # Formatear la descripción de la escena
    scene_description = format_scene_description(scene_data)

    # Insertar la descripción de la escena en el prompt
    prompt = POSTER_BASE_PROMPT.replace("{{SCENE_DESCRIPTION}}", scene_description)

    # Añadir información adicional al principio del archivo
    header = f"""# Prompt para Poster: Ona + {agent_name} - Escena {scene_id}

Personajes: Ona + {agent_name}
Escena: {scene_data['theme']}
Imagen de Ona: reference/agents/ona/ona_full.png
Imagen de {agent_name}: {agent_image_path}

INSTRUCCIONES:
1. Abre tu herramienta de generación de imágenes
2. Sube las dos imágenes:
   - reference/agents/ona/ona_full.png (imagen de Ona)
   - {agent_image_path} (imagen de {agent_name})
3. Copia y pega el prompt que está después de esta línea
4. Genera la imagen (formato 2:3, tipo carta de naipes)
5. Guarda el resultado como: ona_{agent_id}_scene{scene_id:02d}.png

================================================================================
PROMPT:
================================================================================

"""

    # Crear el contenido completo
    full_content = header + prompt

    # Crear el directorio de salida si no existe
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Guardar el archivo
    output_path.write_text(full_content, encoding="utf-8")
    return output_path


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generar UN prompt de poster por cada agente con Ona, distribuyendo escenas sin repetir.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--agents",
        required=True,
        help="Ruta al fichero JSON de configuración de agentes",
    )
    parser.add_argument(
        "--scenes",
        required=True,
        help="Ruta al fichero JSON de configuración de escenas",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="prompts/posters_final",
        help="Directorio donde guardar los archivos de prompts",
    )

    args = parser.parse_args()

    agents_path = Path(args.agents)
    scenes_path = Path(args.scenes)

    agents = load_agents_config(agents_path)
    scenes = load_scenes_config(scenes_path)

    output_dir = Path(args.output_dir)

    # Obtener lista de agentes
    agent_list = list(agents.items())
    num_agents = len(agent_list)
    num_scenes = len(scenes)

    print(f"📝 Generando UN prompt de poster por agente...")
    print(f"📁 Directorio de salida: {output_dir}")
    print(f"👥 Agentes: {num_agents}")
    print(f"🎬 Escenas disponibles: {num_scenes}")
    print(f"📄 Total de prompts a generar: {num_agents}\n")

    # Asignar una escena diferente a cada agente, ciclando si hay más agentes que escenas
    for idx, (agent_id, agent_data) in enumerate(agent_list):
        agent_name = agent_data['name']
        agent_image_path = f"web/img/agents/{agent_id}_fullbody.png"

        # Asignar escena de forma circular (sin repetir hasta que se agoten)
        scene = scenes[idx % num_scenes]
        scene_id = scene['id']
        scene_theme = scene['theme']

        output_filename = f"ona_{agent_id}_scene{scene_id:02d}_prompt.txt"
        output_path = output_dir / output_filename

        try:
            generate_poster_prompt_file(
                agent_id,
                agent_name,
                scene_id,
                scene,
                output_path,
                agent_image_path
            )
            print(f"✅ {agent_name:15} -> Escena {scene_id:2d}: {scene_theme}")
        except Exception as e:
            print(f"❌ Error con {agent_name}: {str(e)}")

    print(f"\n✅ {num_agents} prompts de posters generados en: {output_dir}")
    print(f"\nCada agente tiene una escena diferente (sin repetir).")


if __name__ == "__main__":
    main()
