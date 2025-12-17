"""
Script de verificación para comprobar que todo está configurado correctamente
antes de generar imágenes de agentes.
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv


def check_api_key():
    """Verifica que Google Cloud Project esté configurado."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if project_id:
        print(f"✅ GOOGLE_CLOUD_PROJECT configurado: {project_id}")
        return True
    else:
        print("❌ GOOGLE_CLOUD_PROJECT no encontrado")
        print("   Configúralo con: export GOOGLE_CLOUD_PROJECT='tu-project-id'")
        return False


def check_agents_json(json_path):
    """Verifica que el JSON de agentes existe y es válido."""
    if not json_path.exists():
        print(f"❌ No se encontró el archivo: {json_path}")
        return False

    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if "agents" not in data:
            print("❌ El JSON no tiene la clave 'agents'")
            return False

        print(f"✅ JSON de agentes válido ({len(data['agents'])} agentes)")
        return True, data
    except Exception as e:
        print(f"❌ Error al leer el JSON: {str(e)}")
        return False


def check_reference_images(data):
    """Verifica que existan las carpetas e imágenes de referencia."""
    agents = data["agents"]
    total_agents = len(agents)
    agents_with_refs = 0
    agents_without_refs = []
    total_images = 0

    for agent_id, agent_data in agents.items():
        ref_dir = Path(agent_data.get("reference_images", ""))

        if not ref_dir.exists():
            agents_without_refs.append(agent_id)
            continue

        # Contar imágenes
        images = [
            p for p in ref_dir.iterdir()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ]

        if images:
            agents_with_refs += 1
            total_images += len(images)
        else:
            agents_without_refs.append(agent_id)

    print(f"\n📸 Referencias de imágenes:")
    print(f"   Agentes con referencias: {agents_with_refs}/{total_agents}")
    print(f"   Total de imágenes: {total_images}")

    if agents_without_refs:
        print(f"\n⚠️  Agentes sin imágenes de referencia:")
        for agent_id in agents_without_refs[:5]:  # Mostrar solo los primeros 5
            print(f"   - {agent_id}")
        if len(agents_without_refs) > 5:
            print(f"   ... y {len(agents_without_refs) - 5} más")

    return agents_with_refs > 0


def check_output_directories(data):
    """Verifica que los directorios de salida existan o puedan crearse."""
    output_dirs = set()

    for agent_data in data["agents"].values():
        fullbody_path = Path(agent_data["fullbody_output"])
        avatar_path = Path(agent_data["avatar_output"])

        output_dirs.add(fullbody_path.parent)
        output_dirs.add(avatar_path.parent)

    print(f"\n📁 Directorios de salida:")
    for output_dir in output_dirs:
        if output_dir.exists():
            print(f"   ✅ {output_dir}")
        else:
            print(f"   ⚠️  {output_dir} (se creará automáticamente)")

    return True


def check_generation_status(data):
    """Muestra el estado de generación de cada agente."""
    agents = data["agents"]
    total = len(agents)

    fullbody_generated = sum(1 for a in agents.values() if a.get("fullbody_generated", False))
    avatar_generated = sum(1 for a in agents.values() if a.get("avatar_generated", False))

    print(f"\n🎨 Estado de generación:")
    print(f"   Full body: {fullbody_generated}/{total} generados")
    print(f"   Avatar: {avatar_generated}/{total} generados")

    if fullbody_generated == total and avatar_generated == total:
        print("   ✅ Todas las imágenes ya están generadas")
    else:
        remaining_fullbody = total - fullbody_generated
        remaining_avatar = total - avatar_generated
        print(f"\n   Pendientes:")
        print(f"   - Full body: {remaining_fullbody}")
        print(f"   - Avatar: {remaining_avatar}")

    return True


def main():
    # Cargar variables de entorno desde .env
    load_dotenv()

    print("🔍 Verificando configuración de generación de agentes...\n")

    json_path = Path("prompts/agents_generation.json")

    # Verificaciones
    checks = [
        ("API Key", check_api_key()),
        ("Archivo JSON", check_agents_json(json_path)),
    ]

    # Si el JSON es válido, hacer verificaciones adicionales
    if checks[1][1]:
        result = checks[1][1]
        if isinstance(result, tuple):
            valid, data = result
            if valid:
                checks.append(("Imágenes de referencia", check_reference_images(data)))
                checks.append(("Directorios de salida", check_output_directories(data)))
                checks.append(("Estado de generación", check_generation_status(data)))

    # Resumen
    print("\n" + "="*60)
    all_ok = all(check[1] for check in checks if isinstance(check[1], bool))

    if all_ok:
        print("✅ Todo está configurado correctamente")
        print("\nPuedes ejecutar:")
        print("  uv run python scripts/generate_agents.py --agents prompts/agents_generation.json --type both")
    else:
        print("⚠️  Hay problemas de configuración")
        print("\nRevisando:")
        for name, result in checks:
            if isinstance(result, bool):
                status = "✅" if result else "❌"
                print(f"  {status} {name}")


if __name__ == "__main__":
    main()
