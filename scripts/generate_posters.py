"""
Genera posters combinando a Ona con cada agente en diferentes escenarios.

Este script:
1. Lee los agentes de web/data/agents.json
2. Lee las escenas de prompts/poster_scenes.json
3. Combina la imagen de Ona (reference/agents/ona/ona_full.png)
   con cada agente (web/img/agents/{agent}_fullbody.png)
4. Genera posters en estilo comic book de los 80s

Uso:
  python scripts/generate_posters.py --agent paula --scene 1
  python scripts/generate_posters.py --agent all --scene random
  python scripts/generate_posters.py --agent paula --scene all
"""

import argparse
import json
import os
import random
from pathlib import Path
import base64

from openai import OpenAI
from dotenv import load_dotenv
import requests


# Prompt base para los posters
POSTER_BASE_PROMPT = """A vintage 1980s horror/adventure comic book panel illustration. The art style must strictly adhere to heavy black ink outlines, bold line work, and prominent halftone dot shading (Ben-Day dots) throughout the entire image for texture and color, mimicking aged paper.

You have to use the uploaded photos of the two characters. They will be standing together in a full-body or three-quarter view shot.

Both characters are rendered consistently in the aforementioned comic book style, maintaining their unique items if applicable (e.g., flashlights, calculators).
The clothing is styled in the 80s retro aesthetic and can be a mix of casual and adventure-ready outfits (jackets, hoodies, rolled-up jeans, retro sneakers, backpacks, etc...) always in Stranger Things style.

The scene is set in: {{SCENE_DESCRIPTION}}

NOTE: The aspect ratio of the image must be 1:1 (square)."""


def load_agents():
    """Carga los agentes desde web/data/agents.json."""
    agents_path = Path("web/data/agents.json")
    if not agents_path.exists():
        raise FileNotFoundError(f"No se encontró: {agents_path}")

    with agents_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_scenes():
    """Carga las escenas desde prompts/poster_scenes.json."""
    scenes_path = Path("prompts/poster_scenes.json")
    if not scenes_path.exists():
        raise FileNotFoundError(f"No se encontró: {scenes_path}")

    with scenes_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def encode_image_to_base64(image_path: Path) -> str:
    """Convierte una imagen a base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def build_scene_description(scene_data: dict) -> str:
    """Construye la descripción completa de la escena."""
    theme = scene_data.get("theme", "")
    scene_desc = scene_data.get("scene_description", "")
    lighting = scene_data.get("lighting_mood", "")

    # Combinar toda la información de la escena
    full_description = f"{theme}. The characters are {scene_desc} The scene is {lighting}."
    return full_description


def generate_poster(
    agent_id: str,
    agent_name: str,
    scene_id: int,
    scene_data: dict,
    ona_image: Path,
    agent_image: Path,
    output_path: Path
):
    """Genera un poster combinando a Ona con un agente en una escena."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Verificar que las imágenes existen
    if not ona_image.exists():
        raise FileNotFoundError(f"No se encontró la imagen de Ona: {ona_image}")
    if not agent_image.exists():
        raise FileNotFoundError(f"No se encontró la imagen del agente: {agent_image}")

    # Construir la descripción de la escena
    scene_description = build_scene_description(scene_data)

    # Reemplazar en el prompt
    prompt = POSTER_BASE_PROMPT.replace("{{SCENE_DESCRIPTION}}", scene_description)

    # Preparar las imágenes en base64
    ona_base64 = encode_image_to_base64(ona_image)
    agent_base64 = encode_image_to_base64(agent_image)

    # Construir el mensaje con las dos imágenes
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{ona_base64}"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{agent_base64}"
                    }
                }
            ]
        }
    ]

    try:
        # Primero usar GPT-4o para refinar el prompt con las imágenes
        print(f"    📝 Refinando prompt con GPT-4o...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500
        )

        refined_prompt = response.choices[0].message.content

        # Ahora generar la imagen con DALL-E 3
        print(f"    🎨 Generando imagen con DALL-E 3...")
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=refined_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        # Descargar la imagen generada
        image_url = image_response.data[0].url
        download_response = requests.get(image_url)
        download_response.raise_for_status()

        # Crear el directorio de salida si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Guardar la imagen
        output_path.write_bytes(download_response.content)
        return output_path

    except Exception as e:
        raise RuntimeError(f"Error al generar poster: {str(e)}") from e


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generar posters combinando a Ona con agentes en diferentes escenarios.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--agent",
        required=True,
        help="ID del agente (ej: paula) o 'all' para todos los agentes",
    )
    parser.add_argument(
        "--scene",
        required=True,
        help="ID de la escena (1-15) o 'random' para aleatoria, o 'all' para todas",
    )
    parser.add_argument(
        "--output-dir",
        default="web/img/posters",
        help="Directorio de salida para los posters (default: web/img/posters)",
    )

    args = parser.parse_args()

    # Verificar API key
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError("Falta la variable de entorno OPENAI_API_KEY")

    # Cargar datos
    agents = load_agents()
    scenes = load_scenes()

    # Determinar agentes a procesar
    if args.agent == "all":
        agent_ids = list(agents.keys())
    else:
        if args.agent not in agents:
            print(f"❌ Agente '{args.agent}' no encontrado")
            print(f"   Agentes disponibles: {', '.join(agents.keys())}")
            return
        agent_ids = [args.agent]

    # Determinar escenas a procesar
    if args.scene == "all":
        scene_ids = [s["id"] for s in scenes]
    elif args.scene == "random":
        scene_ids = [random.choice(scenes)["id"]]
    else:
        try:
            scene_id = int(args.scene)
            if not any(s["id"] == scene_id for s in scenes):
                print(f"❌ Escena {scene_id} no encontrada")
                print(f"   Escenas disponibles: 1-{len(scenes)}")
                return
            scene_ids = [scene_id]
        except ValueError:
            print(f"❌ '{args.scene}' no es un ID de escena válido")
            return

    # Ruta a la imagen de Ona
    ona_image = Path("reference/agents/ona/ona_full.png")
    if not ona_image.exists():
        print(f"❌ No se encontró la imagen de Ona: {ona_image}")
        return

    output_dir = Path(args.output_dir)

    print(f"🎬 Generando posters...")
    print(f"👥 Agentes: {len(agent_ids)}")
    print(f"🎭 Escenas: {len(scene_ids)}")
    print(f"📁 Salida: {output_dir}\n")

    total_combinations = len(agent_ids) * len(scene_ids)
    current = 0

    for agent_id in agent_ids:
        agent_data = agents[agent_id]
        agent_name = agent_data["name"]
        agent_image = Path(f"web/img/agents/{agent_id}_fullbody.png")

        if not agent_image.exists():
            print(f"⚠️  Omitiendo {agent_name}: imagen no encontrada ({agent_image})")
            continue

        for scene_id in scene_ids:
            current += 1
            # Buscar los datos de la escena
            scene_data = next((s for s in scenes if s["id"] == scene_id), None)
            if not scene_data:
                continue

            scene_theme = scene_data["theme"]
            output_filename = f"ona_{agent_id}_scene{scene_id:02d}.png"
            output_path = output_dir / output_filename

            print(f"[{current}/{total_combinations}] 🎨 Generando:")
            print(f"    Agentes: Ona & {agent_name}")
            print(f"    Escena: {scene_theme}")
            print(f"    Archivo: {output_filename}")

            try:
                generate_poster(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    scene_id=scene_id,
                    scene_data=scene_data,
                    ona_image=ona_image,
                    agent_image=agent_image,
                    output_path=output_path
                )
                print(f"    ✅ Poster guardado correctamente\n")
            except Exception as e:
                print(f"    ❌ Error: {str(e)}\n")
                continue

    print(f"\n✅ Proceso completado!")
    print(f"📁 Posters guardados en: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
