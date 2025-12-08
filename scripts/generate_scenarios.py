"""
Genera imágenes de escenarios leyendo un JSON de entrada.

Estructura esperada del JSON:
{
  "config": {
    "base_prompt": "...",
    "negative_prompt": "..."
  },
  "scenes": {
    "scene_id": {
      "prompt": "...",
      "output_file": "ruta/salida.png",      # obligatorio
      "use_reference_image": false,          # opcional
      "reference_image": "ruta/carpeta",     # carpeta con 1..N imágenes
      "generated": false                     # opcional, ignorado aquí
    }
  }
}

Uso:
  python scripts/generate_scenarios.py --prompts prompts/scenario_prompts.json --provider openai
  python scripts/generate_scenarios.py --prompts prompts/scenario_prompts.json --provider google
"""

import argparse
import json
import os
from pathlib import Path
from enum import Enum
import base64

import google.generativeai as genai
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv
import requests

try:
    from vertexai.preview.vision_models import ImageGenerationModel
    import vertexai
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False


class Provider(Enum):
    OPENAI = "openai"
    GOOGLE = "google"


# Configuración de modelos por proveedor
MODELS = {
    Provider.OPENAI: "dall-e-3",
    Provider.GOOGLE: "models/imagen-4.0-generate-001",
}


def load_prompts(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el fichero de prompts: {path}")
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict) or "scenes" not in raw:
        raise ValueError("El fichero de prompts debe tener clave 'scenes'.")

    config = raw.get("config", {})
    base_prompt = config.get(
        "base_prompt",
        "Digital art style, Stranger Things vibe, 80s movie atmosphere, cinematic lighting, neon and mist, synthwave color palette.",
    )
    negative_prompt = config.get("negative_prompt", "")
    scenes = raw.get("scenes", {})

    entries = []
    for scene_id, data in scenes.items():
        prompt = data.get("prompt")
        output_file = data.get("output_file")
        if not prompt or not output_file:
            print(f"⚠️ Escena {scene_id} sin prompt o sin output_file, se omite.")
            continue
        entries.append(
            {
                "id": scene_id,
                "prompt": prompt,
                "output": str(output_file),
                "ref_dir": data.get("reference_image"),
                "use_ref": data.get("use_reference_image", False),
                "generated": data.get("generated", False),
            }
        )
    return base_prompt, negative_prompt, entries, raw


def update_generated_flag(prompts_path: Path, scene_id: str, generated: bool):
    """Actualiza el flag 'generated' para una escena específica en el JSON."""
    try:
        with prompts_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if "scenes" in data and scene_id in data["scenes"]:
            data["scenes"][scene_id]["generated"] = generated

            # Guardar el JSON actualizado con formato bonito
            with prompts_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        return False
    except Exception as e:
        print(f"    ⚠️ No se pudo actualizar el JSON: {str(e)}")
        return False


def ensure_api_keys(provider: Provider):
    """Verifica que las API keys necesarias estén configuradas."""
    if provider == Provider.GOOGLE:
        if not VERTEX_AI_AVAILABLE:
            raise EnvironmentError("Vertex AI no está disponible. Instala: pip install google-cloud-aiplatform")

        # Para Vertex AI necesitamos project_id y location
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if not project_id:
            raise EnvironmentError(
                "Falta la variable de entorno GOOGLE_CLOUD_PROJECT.\n"
                "Debes especificar tu Project ID de Google Cloud."
            )

        if not credentials_path:
            print("⚠️  GOOGLE_APPLICATION_CREDENTIALS no está configurado.")
            print("   Se intentará usar las credenciales por defecto de gcloud.")

        # Inicializar Vertex AI
        try:
            vertexai.init(project=project_id, location=location)
            print(f"✅ Vertex AI inicializado: proyecto={project_id}, ubicación={location}")
        except Exception as e:
            raise EnvironmentError(f"Error inicializando Vertex AI: {str(e)}")

    elif provider == Provider.OPENAI:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("Falta la variable de entorno OPENAI_API_KEY.")


def generate_image_openai(base_prompt: str, prompt: str, negative: str, output_path: Path, ref_image_path: Path | None = None):
    """Genera imagen usando OpenAI DALL-E 3."""
    full_prompt = f"{base_prompt} {prompt}"
    if negative:
        full_prompt = f"{full_prompt} Avoid: {negative}"

    # DALL-E 3 tiene un límite de 4000 caracteres
    if len(full_prompt) > 4000:
        full_prompt = full_prompt[:3997] + "..."

    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        response = client.images.generate(
            model=MODELS[Provider.OPENAI],
            prompt=full_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        # Descargar la imagen generada
        image_url = response.data[0].url
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        # Crear el directorio de salida si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Guardar la imagen
        output_path.write_bytes(image_response.content)
        return output_path

    except Exception as e:
        raise RuntimeError(f"Error al generar imagen con OpenAI: {str(e)}") from e


def generate_image_google(base_prompt: str, prompt: str, negative: str, output_path: Path, ref_image_path: Path | None = None):
    """Genera imagen usando Google Imagen 4.0 via Vertex AI."""
    full_prompt = f"{base_prompt} {prompt}"
    if negative:
        full_prompt = f"{full_prompt}. Negative prompt: {negative}"

    # Imagen 3 en Vertex AI tiene límite de ~1000 caracteres
    if len(full_prompt) > 1000:
        full_prompt = full_prompt[:997] + "..."

    if ref_image_path:
        try:
            _ = Image.open(ref_image_path)
            print(f"    ⚠️  Las imágenes de referencia no están soportadas en Vertex AI Imagen.")
        except Exception:
            pass

    try:
        # Usar ImageGenerationModel de Vertex AI
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

        # Generar imagen
        images = model.generate_images(
            prompt=full_prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )

        if not images or len(images.images) == 0:
            raise RuntimeError("La API no devolvió imágenes.")

        # Crear el directorio de salida si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Guardar la imagen
        # El objeto GeneratedImage tiene el método save
        images.images[0].save(location=str(output_path))

        return output_path

    except Exception as e:
        raise RuntimeError(f"Error al generar imagen con Google Vertex AI: {str(e)}") from e


def generate_image(provider: Provider, base_prompt: str, prompt: str, negative: str, output_path: Path, ref_image_path: Path | None = None):
    """Genera imagen usando el proveedor especificado."""
    if provider == Provider.OPENAI:
        return generate_image_openai(base_prompt, prompt, negative, output_path, ref_image_path)
    elif provider == Provider.GOOGLE:
        return generate_image_google(base_prompt, prompt, negative, output_path, ref_image_path)
    else:
        raise ValueError(f"Proveedor no soportado: {provider}")


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Generar escenarios desde un JSON de prompts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s --prompts prompts/scenario_prompts.json --provider openai
  %(prog)s --prompts prompts/scenario_prompts.json --provider google
  %(prog)s --prompts prompts/scenario_prompts.json --provider openai --limit 5
        """
    )
    parser.add_argument(
        "--prompts",
        required=True,
        help="Ruta al fichero de prompts (obligatorio)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=[p.value for p in Provider],
        default=Provider.OPENAI.value,
        help="Proveedor de IA para generar imágenes (default: openai)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limitar el número de imágenes a generar (útil para testing)",
    )
    parser.add_argument(
        "--skip-generated",
        action="store_true",
        help="Omitir imágenes ya marcadas como generadas en el JSON",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerar todas las imágenes, incluso las ya generadas",
    )
    args = parser.parse_args()

    # Convertir el string del provider a enum
    provider = Provider(args.provider)

    prompts_path = Path(args.prompts)
    base_prompt, negative_prompt, prompts, raw_data = load_prompts(prompts_path)
    ensure_api_keys(provider)

    # Filtrar imágenes ya generadas si se especificó
    if args.skip_generated:
        original_count = len(prompts)
        prompts = [p for p in prompts if not p.get("generated", False)]
        skipped = original_count - len(prompts)
        if skipped > 0:
            print(f"⏭️  Omitiendo {skipped} imagen(es) ya generada(s)")

    # Aplicar límite si se especificó
    if args.limit:
        prompts = prompts[:args.limit]

    if not prompts:
        print("✅ No hay imágenes para generar. Todas están marcadas como generadas.")
        return

    print(f"🎨 Generando {len(prompts)} escenarios desde {prompts_path}...")
    print(f"📦 Proveedor: {provider.value.upper()}")
    if args.force:
        print(f"🔄 Modo: Regenerar todas las imágenes")
    print()

    for i, entry in enumerate(prompts, 1):
        scene_id = entry["id"]
        prompt = entry["prompt"]
        output_path = Path(entry["output"])

        # reference_image es carpeta; tomamos la primera imagen válida si use_ref es true
        ref_path = None
        if entry.get("use_ref") and entry.get("ref_dir"):
            ref_dir = Path(entry["ref_dir"])
            if ref_dir.is_dir():
                imgs = sorted(
                    p for p in ref_dir.iterdir()
                    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                )
                if imgs:
                    ref_path = imgs[0]
            elif ref_dir.exists():
                ref_path = ref_dir  # por compatibilidad si pasaron archivo

        # Mostrar si ya está generada
        status_icon = "🔄" if entry.get("generated", False) and args.force else "🎬"
        print(f"[{i}/{len(prompts)}] {status_icon} {scene_id} -> {output_path.name}")
        print(f"    Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
        print(f"    Referencia: {ref_path.name if ref_path else 'ninguna'}")

        try:
            # Generar la imagen
            generate_image(provider, base_prompt, prompt, negative_prompt, output_path, ref_path)
            print(f"    ✅ Guardada correctamente")

            # Marcar como generada en el JSON
            if update_generated_flag(prompts_path, scene_id, True):
                print(f"    📝 Actualizado 'generated: true' en el JSON")
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            # Continuar con la siguiente imagen en lugar de fallar completamente
            continue

        print()


if __name__ == "__main__":
    main()
