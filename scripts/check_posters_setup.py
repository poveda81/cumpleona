"""
Script de verificación para comprobar que todo está listo
para generar posters de Ona con los agentes.
"""

import json
from pathlib import Path
import os
from dotenv import load_dotenv


def check_api_key():
    """Verifica que la API key de OpenAI esté configurada."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        print("✅ OPENAI_API_KEY configurada")
        return True
    else:
        print("❌ OPENAI_API_KEY no encontrada")
        return False


def check_ona_image():
    """Verifica que existe la imagen de Ona."""
    ona_path = Path("reference/agents/ona/ona_full.png")
    if ona_path.exists():
        print(f"✅ Imagen de Ona encontrada: {ona_path}")
        return True
    else:
        print(f"❌ No se encontró la imagen de Ona: {ona_path}")
        print("   Necesitas colocar la imagen de Ona en esa ubicación")
        return False


def check_agents_json():
    """Verifica que existe el JSON de agentes."""
    agents_path = Path("web/data/agents.json")
    if not agents_path.exists():
        print(f"❌ No se encontró: {agents_path}")
        return False

    try:
        with agents_path.open("r", encoding="utf-8") as f:
            agents = json.load(f)

        print(f"✅ Agentes cargados: {len(agents)} agentes")
        return True, agents
    except Exception as e:
        print(f"❌ Error al leer agentes: {str(e)}")
        return False


def check_scenes_json():
    """Verifica que existe el JSON de escenas."""
    scenes_path = Path("prompts/poster_scenes.json")
    if not scenes_path.exists():
        print(f"❌ No se encontró: {scenes_path}")
        return False

    try:
        with scenes_path.open("r", encoding="utf-8") as f:
            scenes = json.load(f)

        print(f"✅ Escenas cargadas: {len(scenes)} escenas")
        return True, scenes
    except Exception as e:
        print(f"❌ Error al leer escenas: {str(e)}")
        return False


def check_agent_images(agents):
    """Verifica qué agentes tienen imágenes fullbody disponibles."""
    agents_with_images = []
    agents_without_images = []

    for agent_id, agent_data in agents.items():
        agent_image = Path(f"web/img/agents/{agent_id}_fullbody.png")
        if agent_image.exists():
            agents_with_images.append(agent_id)
        else:
            agents_without_images.append(agent_id)

    print(f"\n📸 Imágenes de agentes fullbody:")
    print(f"   Con imagen: {len(agents_with_images)}/{len(agents)}")

    if agents_without_images:
        print(f"\n⚠️  Agentes sin imagen fullbody:")
        for agent_id in agents_without_images[:5]:
            print(f"   - {agent_id} (web/img/agents/{agent_id}_fullbody.png)")
        if len(agents_without_images) > 5:
            print(f"   ... y {len(agents_without_images) - 5} más")

    return len(agents_with_images) > 0


def check_output_directory():
    """Verifica el directorio de salida."""
    output_dir = Path("web/img/posters")
    if output_dir.exists():
        existing_posters = list(output_dir.glob("ona_*_scene*.png"))
        print(f"\n📁 Directorio de salida: {output_dir}")
        if existing_posters:
            print(f"   Ya existen {len(existing_posters)} posters generados")
    else:
        print(f"\n📁 Directorio de salida: {output_dir} (se creará automáticamente)")

    return True


def show_examples():
    """Muestra ejemplos de uso."""
    print("\n" + "="*60)
    print("📋 Ejemplos de uso:")
    print()
    print("1. Generar un poster de Paula con escena aleatoria:")
    print("   uv run python scripts/generate_posters.py --agent paula --scene random")
    print()
    print("2. Generar todos los posters de Paula (todas las escenas):")
    print("   uv run python scripts/generate_posters.py --agent paula --scene all")
    print()
    print("3. Generar posters de todos los agentes con escena específica:")
    print("   uv run python scripts/generate_posters.py --agent all --scene 5")
    print()
    print("4. Generar todos los posters posibles (¡cuidado con el costo!):")
    print("   uv run python scripts/generate_posters.py --agent all --scene all")


def main():
    # Cargar variables de entorno desde .env
    load_dotenv()

    print("🔍 Verificando configuración de generación de posters...\n")

    checks = []

    # Verificación de API key
    checks.append(("API Key", check_api_key()))

    # Verificación de imagen de Ona
    checks.append(("Imagen de Ona", check_ona_image()))

    # Verificación de JSON de agentes
    result = check_agents_json()
    if isinstance(result, tuple):
        checks.append(("JSON de agentes", result[0]))
        agents = result[1] if result[0] else {}
    else:
        checks.append(("JSON de agentes", result))
        agents = {}

    # Verificación de JSON de escenas
    result = check_scenes_json()
    if isinstance(result, tuple):
        checks.append(("JSON de escenas", result[0]))
    else:
        checks.append(("JSON de escenas", result))

    # Si hay agentes, verificar imágenes
    if agents:
        checks.append(("Imágenes de agentes", check_agent_images(agents)))

    # Verificar directorio de salida
    checks.append(("Directorio de salida", check_output_directory()))

    # Resumen
    print("\n" + "="*60)
    all_ok = all(check[1] for check in checks if isinstance(check[1], bool))

    if all_ok:
        print("✅ Todo está configurado correctamente")
        show_examples()
    else:
        print("⚠️  Hay problemas de configuración")
        print("\nRevisando:")
        for name, result in checks:
            if isinstance(result, bool):
                status = "✅" if result else "❌"
                print(f"  {status} {name}")


if __name__ == "__main__":
    main()
