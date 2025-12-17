"""
Genera imágenes de agentes (personajes) usando Google Gemini Imagen 3.

Este script lee el archivo agents.json y genera:
1. Full body illustrations (personajes de cuerpo completo)
2. Avatar portraits (retratos para avatares)

Uso:
  python scripts/generate_agents.py --type fullbody --agents prompts/agents_generation.json
  python scripts/generate_agents.py --type avatar --agents prompts/agents_generation.json
  python scripts/generate_agents.py --type both --agents prompts/agents_generation.json
"""

import argparse
import json
import os
from pathlib import Path
from enum import Enum
import base64
import io

from vertexai.preview.vision_models import ImageGenerationModel
from PIL import Image
from dotenv import load_dotenv
import vertexai


class ImageType(Enum):
    FULLBODY = "fullbody"
    AVATAR = "avatar"
    BOTH = "both"


# Prompt base para cuerpo completo (full body)
FULLBODY_BASE_PROMPT = """### Full body Illustration Instructions:

Act as an expert vintage comic book illustrator from the 1980s. I am going to provide you with real images of a girl and a character data sheet.

YOUR TASK: Generate an illustration of that specific girl, transforming her real features into the requested comic book style, incorporating her "special item," and dressing her in random clothing that strictly respects the fashion of the "Stranger Things" era (early-to-mid 80s).

VISUAL STYLE REFERENCE (Crucial):
The result must perfectly emulate the retro 80s horror/adventure comic book style.
- Line work: Thick, defined black outlines.
- Shading: Heavy use of black ink shadows and halftone dot patterns to give volume and texture.
- Color: Muted, textured, and aged color palette (mustard yellows, petrol blues, dark reds, teal greens).
- Lighting: Dramatic, high-contrast lighting (chiaroscuro), usually emanating from the special object she carries.
- Background: A flat, solid muted color background with comic book texture (halftone dots), devoid of any complex scenery, depth, or objects.
- NEGATIVE CONSTRAINT (Very Important): Do NOT include any text, speech bubbles, sound effect words (onomatopoeia), or QR codes in the illustration. The image should only contain the character and the flat background.

CHARACTER DATA TO INTEGRATE:
Use this information to define her pose, expression, and the object she carries:
{{CHARACTER_DATA}}

GENERATION INSTRUCTIONS:
1. FACE AND HAIR: Base the facial features and hairstyle on the attached REAL PHOTOS, but adapt them to the comic drawing style defined above.
2. POSE AND EXPRESSION: Her pose must reflect her "tag" and "qualities". (For example, if she has "Super intelligence" and is "Attentive", she should have a concentrated expression, perhaps listening intently or analyzing something).
3. SPECIAL ITEM: She must hold her "specialItem" prominently. The object should appear active or supernatural (glowing, emitting light, or having visual sound waves).
4. WARDROBE (Random Stranger Things style): Dress her in a random but authentic outfit of American youth fashion from 1983-1985. Examples (choose one randomly for this image): sherpa-lined corduroy jacket, denim overalls, striped ringer t-shirt, puffer vest, retro colorful windbreaker. Do not use stereotypical costumes, but clothing that would look real in the series."""

# Prompt base para avatar
AVATAR_BASE_PROMPT = """### Avatar Portrait Instructions:

Act as an expert vintage comic book illustrator from the 1980s. I am going to provide you with real images of a girl and a character data sheet.

YOUR TASK: Generate a portrait-style avatar illustration of that specific girl in the same comic book style used for full body illustrations.

VISUAL STYLE REFERENCE (Crucial):
The result must perfectly emulate the retro 80s horror/adventure comic book style.
- Line work: Thick, defined black outlines.
- Shading: Heavy use of black ink shadows and halftone dot patterns to give volume and texture.
- Color: Muted, textured, and aged color palette (mustard yellows, petrol blues, dark reds, teal greens).
- Framing: Head and shoulders portrait (bust), centered.
- Background: A flat, solid muted color background with comic book texture (halftone dots).
- NEGATIVE CONSTRAINT (Very Important): Do NOT include any text, speech bubbles, sound effect words (onomatopoeia), or QR codes.

CHARACTER DATA TO INTEGRATE:
{{CHARACTER_DATA}}

GENERATION INSTRUCTIONS:
1. FACE AND HAIR: Base the facial features and hairstyle on the attached REAL PHOTOS, but adapt them to the comic drawing style defined above.
2. EXPRESSION: Her expression should reflect her "tag" and main "quality".
3. FRAMING: Portrait style - head and shoulders only, no full body.
4. CLOTHING: Show just the top/collar of her 80s style clothing visible in the portrait frame."""


def load_agents_config(path: Path):
    """Carga la configuración de agentes desde el JSON."""
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el fichero de agentes: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "agents" not in data:
        raise ValueError("El fichero debe tener una clave 'agents'.")

    return data


def update_generated_flag(config_path: Path, agent_id: str, image_type: str, generated: bool):
    """Actualiza el flag 'generated' para un tipo de imagen específico en el JSON."""
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if "agents" in data and agent_id in data["agents"]:
            if image_type == "fullbody":
                data["agents"][agent_id]["fullbody_generated"] = generated
            elif image_type == "avatar":
                data["agents"][agent_id]["avatar_generated"] = generated

            # Guardar el JSON actualizado
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        return False
    except Exception as e:
        print(f"    ⚠️ No se pudo actualizar el JSON: {str(e)}")
        return False


def encode_image_to_base64(image_path: Path) -> str:
    """Convierte una imagen a base64 para enviarla a la API."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_reference_images(ref_dir: Path) -> list[Path]:
    """Obtiene todas las imágenes de referencia de una carpeta."""
    if not ref_dir.exists() or not ref_dir.is_dir():
        return []

    images = sorted(
        p for p in ref_dir.iterdir()
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )
    return images


def format_character_data(agent_data: dict) -> str:
    """Formatea los datos del agente para incluirlos en el prompt."""
    return f"""{{
  "name": "{agent_data['name']}",
  "tag": "{agent_data['tag']}",
  "qualities": "{', '.join(agent_data['qualities'])}",
  "specialItem": "{agent_data['specialItem']}"
}}"""


def generate_agent_image(agent_id: str, agent_data: dict, image_type: ImageType, output_path: Path, ref_images: list[Path]):
    """Genera una imagen de agente usando Google Vertex AI Imagen 3."""
    # Inicializar Vertex AI
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    vertexai.init(project=project_id, location=location)

    # Cargar el modelo Imagen 3
    model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

    # Seleccionar el prompt base según el tipo
    if image_type == ImageType.FULLBODY:
        base_prompt = FULLBODY_BASE_PROMPT
    else:  # AVATAR
        base_prompt = AVATAR_BASE_PROMPT

    # Insertar datos del personaje en el prompt
    character_data = format_character_data(agent_data)
    prompt = base_prompt.replace("{{CHARACTER_DATA}}", character_data)

    try:
        # Cargar la primera imagen de referencia (Imagen 3 soporta una imagen de referencia)
        reference_image = None
        if ref_images:
            try:
                # Usar la primera imagen como referencia principal
                reference_image = Image.open(ref_images[0])
            except Exception as e:
                print(f"    ⚠️ No se pudo cargar imagen de referencia: {str(e)}")

        # Generar la imagen con Vertex AI Imagen 3
        if reference_image:
            # Generar con imagen de referencia
            response = model.generate_images(
                prompt=prompt,
                reference_images=[reference_image],
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_only_high",
                person_generation="allow_all",
            )
        else:
            # Generar sin imagen de referencia
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_only_high",
                person_generation="allow_all",
            )

        # Obtener la primera imagen generada
        generated_image = response.images[0]

        # Crear el directorio de salida si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Guardar la imagen
        generated_image._pil_image.save(output_path, format='PNG')
        return output_path

    except Exception as e:
        raise RuntimeError(f"Error al generar imagen con Vertex AI: {str(e)}") from e


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generar imágenes de agentes usando ChatGPT con DALL-E.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--agents",
        required=True,
        help="Ruta al fichero JSON de configuración de agentes",
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=[t.value for t in ImageType],
        default=ImageType.BOTH.value,
        help="Tipo de imagen a generar (fullbody, avatar, o both)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limitar el número de agentes a procesar",
    )
    parser.add_argument(
        "--skip-generated",
        action="store_true",
        help="Omitir imágenes ya generadas",
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        help="Generar solo para un agente específico (ID del agente)",
    )

    args = parser.parse_args()

    # Verificar configuración de Google Cloud
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        raise EnvironmentError("Falta la variable de entorno GOOGLE_CLOUD_PROJECT")

    config_path = Path(args.agents)
    config = load_agents_config(config_path)

    image_type = ImageType(args.type)
    agents = config["agents"]

    # Filtrar por agente específico si se especificó
    if args.agent_id:
        if args.agent_id not in agents:
            print(f"❌ Agente '{args.agent_id}' no encontrado en el JSON")
            return
        agents = {args.agent_id: agents[args.agent_id]}

    # Aplicar límite si se especificó
    if args.limit:
        agents = dict(list(agents.items())[:args.limit])

    print(f"🎨 Generando imágenes de agentes...")
    print(f"📦 Tipo: {image_type.value}")
    print(f"👥 Agentes a procesar: {len(agents)}\n")

    for agent_id, agent_data in agents.items():
        print(f"👤 Procesando: {agent_data['name']} ({agent_id})")

        # Obtener imágenes de referencia
        ref_dir = Path(agent_data.get("reference_images", ""))
        ref_images = get_reference_images(ref_dir)

        if ref_images:
            print(f"    📸 Referencias encontradas: {len(ref_images)}")
        else:
            print(f"    ⚠️  Sin imágenes de referencia")
            exit(1)

        # Generar full body si se requiere
        if image_type in [ImageType.FULLBODY, ImageType.BOTH]:
            if args.skip_generated and agent_data.get("fullbody_generated", False):
                print(f"    ⏭️  Full body ya generado, omitiendo...")
            else:
                fullbody_path = Path(agent_data["fullbody_output"])
                print(f"    🎬 Generando full body -> {fullbody_path.name}")

                try:
                    generate_agent_image(agent_id, agent_data, ImageType.FULLBODY, fullbody_path, ref_images)
                    print(f"    ✅ Full body guardado correctamente")
                    update_generated_flag(config_path, agent_id, "fullbody", True)
                except Exception as e:
                    print(f"    ❌ Error en full body: {str(e)}")

        # Generar avatar si se requiere
        if image_type in [ImageType.AVATAR, ImageType.BOTH]:
            if args.skip_generated and agent_data.get("avatar_generated", False):
                print(f"    ⏭️  Avatar ya generado, omitiendo...")
            else:
                avatar_path = Path(agent_data["avatar_output"])
                print(f"    🎬 Generando avatar -> {avatar_path.name}")

                try:
                    generate_agent_image(agent_id, agent_data, ImageType.AVATAR, avatar_path, ref_images)
                    print(f"    ✅ Avatar guardado correctamente")
                    update_generated_flag(config_path, agent_id, "avatar", True)
                except Exception as e:
                    print(f"    ❌ Error en avatar: {str(e)}")

        print()


if __name__ == "__main__":
    main()
