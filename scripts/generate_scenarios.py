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
  python scripts/generate_scenarios.py --prompts web/data/scenario_prompts.json
"""

import argparse
import json
import os
from pathlib import Path

import google.generativeai as genai
from PIL import Image

MODEL_NAME = "models/imagen-3.0-generate-001"


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
            }
        )
    return base_prompt, negative_prompt, entries


def ensure_api_key():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("Falta la variable de entorno GOOGLE_API_KEY.")
    genai.configure(api_key=api_key)


def generate_image(base_prompt: str, prompt: str, negative: str, output_path: Path, ref_image_path: Path | None = None):
    full_prompt = f"{base_prompt} {prompt}"
    if negative:
        full_prompt = f"{full_prompt} Avoid: {negative}"
    imagen_model = genai.ImageGenerationModel(MODEL_NAME)

    if ref_image_path:
        _ = Image.open(ref_image_path)  # validar existencia
        response = imagen_model.generate_images(
            prompt=full_prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_only_high",
        )
    else:
        response = imagen_model.generate_images(
            prompt=full_prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_only_high",
        )

    if not response.images:
        raise RuntimeError("La API no devolvió imágenes.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    response.images[0].save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generar escenarios desde un JSON de prompts.")
    parser.add_argument(
        "--prompts",
        required=True,
        help="Ruta al fichero de prompts (obligatorio)",
    )
    args = parser.parse_args()

    prompts_path = Path(args.prompts)
    base_prompt, negative_prompt, prompts = load_prompts(prompts_path)
    ensure_api_key()

    print(f"Generando {len(prompts)} escenarios desde {prompts_path}...")
    for entry in prompts:
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

        try:
            print(f"🎬 {scene_id} -> {output_path} (ref: {ref_path.name if ref_path else 'ninguna'})")
            generate_image(base_prompt, prompt, negative_prompt, output_path, ref_path)
            print(f"✅ Guardada: {output_path}")
        except Exception as e:
            print(f"❌ Error generando {scene_id}: {e}")


if __name__ == "__main__":
    main()
