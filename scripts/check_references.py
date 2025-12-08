"""
Script para verificar el estado de las imágenes de referencia.

Muestra qué carpetas tienen imágenes de referencia y cuáles están vacías.

Uso:
  python scripts/check_references.py
"""

from pathlib import Path

def check_references():
    """Verifica el estado de las carpetas de referencia."""

    # Extensiones de imagen válidas
    image_extensions = {'.png', '.jpg', '.jpeg', '.webp'}

    print("=" * 70)
    print("📸 ESTADO DE IMÁGENES DE REFERENCIA")
    print("=" * 70)

    # Verificar escenarios
    scenarios_dir = Path("reference/scenarios")
    print("\n🎬 ESCENARIOS:\n")

    scenarios_with_images = []
    scenarios_empty = []

    for folder in sorted(scenarios_dir.iterdir()):
        if folder.is_dir() and not folder.name.startswith('.'):
            images = [
                f for f in folder.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

            if images:
                scenarios_with_images.append((folder.name, len(images)))
                print(f"  ✅ {folder.name:<35} ({len(images)} imagen{'es' if len(images) > 1 else ''})")
            else:
                scenarios_empty.append(folder.name)
                print(f"  ⚪ {folder.name:<35} (vacía)")

    print(f"\n  📊 Total: {len(scenarios_with_images)} con imágenes, {len(scenarios_empty)} vacías")

    # Verificar agentes
    agents_dir = Path("reference/agents")
    print("\n\n👤 AGENTES:\n")

    agents_with_images = []
    agents_empty = []

    for folder in sorted(agents_dir.iterdir()):
        if folder.is_dir() and not folder.name.startswith('.'):
            images = [
                f for f in folder.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

            if images:
                agents_with_images.append((folder.name, len(images)))
                print(f"  ✅ {folder.name:<20} ({len(images)} imagen{'es' if len(images) > 1 else ''})")
            else:
                agents_empty.append(folder.name)
                print(f"  ⚪ {folder.name:<20} (vacía)")

    print(f"\n  📊 Total: {len(agents_with_images)} con imágenes, {len(agents_empty)} vacías")

    # Resumen
    print("\n" + "=" * 70)
    print("📈 RESUMEN:")
    print("=" * 70)
    print(f"  Escenarios: {len(scenarios_with_images)}/{len(scenarios_with_images) + len(scenarios_empty)} tienen referencias")
    print(f"  Agentes:    {len(agents_with_images)}/{len(agents_with_images) + len(agents_empty)} tienen referencias")
    print()

    if scenarios_empty or agents_empty:
        print("💡 TIP: Para añadir referencias, coloca imágenes en las carpetas vacías")
        print("        y actualiza 'use_reference_image: true' en los prompts JSON.")

    print("=" * 70)


if __name__ == "__main__":
    check_references()
