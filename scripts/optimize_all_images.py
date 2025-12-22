"""
Script para optimizar todas las imágenes en web/img recursivamente.
"""

import sys
from pathlib import Path
from optimize_images import process_directory


def process_recursive(base_dir, quality=85, max_width=1920, max_height=1080):
    """Procesa todas las subcarpetas recursivamente."""
    base_path = Path(base_dir)

    if not base_path.exists():
        print(f"❌ El directorio {base_dir} no existe")
        return

    print(f"🔍 Buscando carpetas con imágenes en {base_dir}...")
    print()

    # Encontrar todas las carpetas que contienen imágenes
    image_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
    directories_with_images = set()

    for img_path in base_path.rglob('*'):
        if img_path.is_file() and img_path.suffix.lower() in image_extensions:
            directories_with_images.add(img_path.parent)

    directories_with_images = sorted(directories_with_images)

    if not directories_with_images:
        print(f"⚠️  No se encontraron imágenes en {base_dir}")
        return

    print(f"📁 Encontradas {len(directories_with_images)} carpetas con imágenes:")
    for dir_path in directories_with_images:
        rel_path = dir_path.relative_to(base_path.parent)
        print(f"   - {rel_path}")
    print()

    # Procesar cada directorio
    total_original = 0
    total_new = 0
    total_images = 0

    for i, dir_path in enumerate(directories_with_images, 1):
        rel_path = dir_path.relative_to(base_path.parent)
        print(f"{'='*60}")
        print(f"📂 [{i}/{len(directories_with_images)}] Procesando: {rel_path}")
        print(f"{'='*60}")

        # Contar imágenes antes de procesar
        images_before = list(dir_path.glob('*'))
        images_before = [f for f in images_before if f.is_file() and f.suffix.lower() in image_extensions]

        # Calcular tamaños antes
        size_before = sum(f.stat().st_size for f in images_before) / (1024 * 1024)

        # Procesar directorio
        process_directory(
            input_dir=str(dir_path),
            output_dir=None,  # Sobrescribir in-place
            max_width=max_width,
            max_height=max_height,
            quality=quality,
            backup=False,  # Ya hicimos backup global
            dry_run=False
        )

        # Calcular tamaños después
        images_after = list(dir_path.glob('*'))
        images_after = [f for f in images_after if f.is_file() and f.suffix.lower() in image_extensions]
        size_after = sum(f.stat().st_size for f in images_after) / (1024 * 1024)

        total_original += size_before
        total_new += size_after
        total_images += len(images_before)

        print()

    # Resumen global
    print()
    print("=" * 60)
    print("🎉 RESUMEN GLOBAL")
    print("=" * 60)
    print(f"📁 Carpetas procesadas: {len(directories_with_images)}")
    print(f"🖼️  Imágenes procesadas: {total_images}")
    print(f"📦 Tamaño original total: {total_original:.2f} MB")
    print(f"📦 Tamaño optimizado total: {total_new:.2f} MB")
    total_savings = ((total_original - total_new) / total_original * 100) if total_original > 0 else 0
    print(f"💾 Ahorro total: {total_original - total_new:.2f} MB ({total_savings:.1f}%)")
    print("=" * 60)
    print()
    print("✅ ¡Optimización completada!")
    print(f"💡 Las imágenes originales están en: img_originals_backup/")


if __name__ == "__main__":
    print("🖼️  Optimizador de imágenes recursivo")
    print("=" * 60)
    print()

    process_recursive(
        base_dir="web/img",
        quality=85,
        max_width=1920,
        max_height=1080
    )
