"""
Genera archivos de texto con prompts para cada agente.

Este script lee el archivo agents.json y crea archivos .txt con los prompts
listos para copiar y pegar en la interfaz web de generación de imágenes.

Uso:
  python scripts/generate_prompts.py --agents prompts/agents_generation.json --type fullbody
  python scripts/generate_prompts.py --agents prompts/agents_generation.json --type avatar
  python scripts/generate_prompts.py --agents prompts/agents_generation.json --type both
"""

import argparse
import json
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv


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


def format_character_data(agent_data: dict) -> str:
    """Formatea los datos del agente para incluirlos en el prompt."""
    return f"""{{
  "name": "{agent_data['name']}",
  "tag": "{agent_data['tag']}",
  "qualities": "{', '.join(agent_data['qualities'])}",
  "specialItem": "{agent_data['specialItem']}"
}}"""


def generate_prompt_file(agent_id: str, agent_data: dict, image_type: ImageType, output_path: Path):
    """Genera un archivo de texto con el prompt para un agente."""
    # Seleccionar el prompt base según el tipo
    if image_type == ImageType.FULLBODY:
        base_prompt = FULLBODY_BASE_PROMPT
    else:  # AVATAR
        base_prompt = AVATAR_BASE_PROMPT

    # Insertar datos del personaje en el prompt
    character_data = format_character_data(agent_data)
    prompt = base_prompt.replace("{{CHARACTER_DATA}}", character_data)

    # Añadir información adicional al principio del archivo
    header = f"""# Prompt para {agent_data['name']} - {image_type.value.upper()}

Agente: {agent_id}
Nombre: {agent_data['name']}
Tag: {agent_data['tag']}
Imágenes de referencia: {agent_data['reference_images']}

INSTRUCCIONES:
1. Abre tu herramienta de generación de imágenes
2. Sube las imágenes de referencia de la carpeta: {agent_data['reference_images']}
3. Copia y pega el prompt que está después de esta línea
4. Genera la imagen

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
        description="Generar archivos de texto con prompts para cada agente.",
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
        help="Tipo de imagen a generar prompts (fullbody, avatar, o both)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="prompts/generated",
        help="Directorio donde guardar los archivos de prompts",
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        help="Generar solo para un agente específico (ID del agente)",
    )

    args = parser.parse_args()

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

    output_dir = Path(args.output_dir)
    print(f"📝 Generando archivos de prompts...")
    print(f"📦 Tipo: {image_type.value}")
    print(f"📁 Directorio de salida: {output_dir}")
    print(f"👥 Agentes a procesar: {len(agents)}\n")

    for agent_id, agent_data in agents.items():
        print(f"👤 Procesando: {agent_data['name']} ({agent_id})")

        # Generar prompt de full body si se requiere
        if image_type in [ImageType.FULLBODY, ImageType.BOTH]:
            fullbody_path = output_dir / f"{agent_id}_fullbody_prompt.txt"
            print(f"    📄 Generando prompt full body -> {fullbody_path.name}")
            try:
                generate_prompt_file(agent_id, agent_data, ImageType.FULLBODY, fullbody_path)
                print(f"    ✅ Prompt full body guardado")
            except Exception as e:
                print(f"    ❌ Error en full body: {str(e)}")

        # Generar prompt de avatar si se requiere
        if image_type in [ImageType.AVATAR, ImageType.BOTH]:
            avatar_path = output_dir / f"{agent_id}_avatar_prompt.txt"
            print(f"    📄 Generando prompt avatar -> {avatar_path.name}")
            try:
                generate_prompt_file(agent_id, agent_data, ImageType.AVATAR, avatar_path)
                print(f"    ✅ Prompt avatar guardado")
            except Exception as e:
                print(f"    ❌ Error en avatar: {str(e)}")

        print()

    print(f"\n✅ Prompts generados en: {output_dir}")
    print(f"\nPuedes encontrar los archivos .txt con los prompts listos para usar.")


if __name__ == "__main__":
    main()
