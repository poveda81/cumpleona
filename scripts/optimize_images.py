"""
Optimiza imágenes para web reduciendo su tamaño y calidad.

Este script procesa imágenes PNG y JPEG, optimizándolas para uso web:
- Redimensiona imágenes grandes manteniendo la proporción
- Reduce la calidad JPEG
- Optimiza PNGs
- Genera un reporte de ahorro de espacio

Uso:
  python scripts/optimize_images.py --input web/img/scenarios --quality 85 --max-width 1920
  python scripts/optimize_images.py --input web/img/scenarios --quality 80 --backup
"""

import argparse
import shutil
from pathlib import Path
from PIL import Image
import os


def get_file_size_mb(path):
    """Retorna el tamaño del archivo en MB."""
    return os.path.getsize(path) / (1024 * 1024)


def optimize_image(input_path, output_path, max_width=1920, max_height=1080, quality=85, convert_to_jpeg=False):
    """
    Optimiza una imagen individual.

    Args:
        input_path: Ruta de la imagen de entrada
        output_path: Ruta de la imagen de salida
        max_width: Ancho máximo en píxeles
        max_height: Alto máximo en píxeles
        quality: Calidad para JPEG (1-100)
        convert_to_jpeg: Si True, convierte PNGs a JPEG

    Returns:
        Tuple con (tamaño_original_mb, tamaño_nuevo_mb, ahorro_porcentaje)
    """
    try:
        with Image.open(input_path) as img:
            original_size = get_file_size_mb(input_path)

            # Obtener dimensiones originales
            width, height = img.size

            # Calcular nuevas dimensiones si exceden el máximo
            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convertir a JPEG si se solicita
            if convert_to_jpeg and input_path.suffix.lower() == '.png':
                output_path = output_path.with_suffix('.jpg')

            # Convertir RGBA a RGB si es necesario para JPEG
            if img.mode == 'RGBA' and (convert_to_jpeg or output_path.suffix.lower() in ['.jpg', '.jpeg']):
                # Crear fondo blanco
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 3 es el canal alpha
                img = background

            # Guardar con optimización
            if output_path.suffix.lower() in ['.jpg', '.jpeg']:
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
            elif output_path.suffix.lower() == '.png':
                img.save(output_path, 'PNG', optimize=True)
            else:
                img.save(output_path, optimize=True)

            new_size = get_file_size_mb(output_path)
            savings = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0

            return original_size, new_size, savings

    except Exception as e:
        raise RuntimeError(f"Error al optimizar {input_path.name}: {str(e)}") from e


def process_directory(input_dir, output_dir=None, max_width=1920, max_height=1080, quality=85, backup=False, dry_run=False, convert_to_jpeg=False):
    """
    Procesa todas las imágenes en un directorio.

    Args:
        input_dir: Directorio con imágenes originales
        output_dir: Directorio de salida (si None, sobrescribe originales)
        max_width: Ancho máximo en píxeles
        max_height: Alto máximo en píxeles
        quality: Calidad para JPEG (1-100)
        backup: Si True, crea backup antes de sobrescribir
        dry_run: Si True, solo muestra qué haría sin modificar archivos
        convert_to_jpeg: Si True, convierte PNGs a JPEG
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"El directorio no existe: {input_path}")

    # Si output_dir es None, sobrescribir originales
    in_place = output_dir is None
    output_path = Path(output_dir) if output_dir else input_path

    # Crear directorio de salida si no existe
    if not dry_run and not in_place:
        output_path.mkdir(parents=True, exist_ok=True)

    # Crear backup si se solicita
    backup_dir = None
    if backup and in_place and not dry_run:
        backup_dir = input_path.parent / f"{input_path.name}_backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"📦 Creando backup en: {backup_dir}")

    # Buscar todas las imágenes
    image_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
    image_files = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if not image_files:
        print(f"⚠️  No se encontraron imágenes en {input_path}")
        return

    print(f"\n🖼️  Encontradas {len(image_files)} imágenes")
    print(f"📐 Dimensiones máximas: {max_width}x{max_height}px")
    print(f"🎚️  Calidad JPEG: {quality}")
    if dry_run:
        print(f"🔍 Modo DRY RUN - No se modificarán archivos")
    print()

    total_original = 0
    total_new = 0
    successful = 0
    failed = 0

    for img_file in image_files:
        try:
            # Crear backup si es necesario
            if backup_dir and not dry_run:
                shutil.copy2(img_file, backup_dir / img_file.name)

            # Determinar ruta de salida
            out_file = output_path / img_file.name if not in_place else img_file

            # Si se va a convertir a JPEG, cambiar extensión
            if convert_to_jpeg and img_file.suffix.lower() == '.png':
                out_file = out_file.with_suffix('.jpg')

            if dry_run:
                # Solo calcular sin modificar
                with Image.open(img_file) as img:
                    original_size = get_file_size_mb(img_file)
                    width, height = img.size
                    will_resize = width > max_width or height > max_height

                    print(f"  {img_file.name}")
                    print(f"    Tamaño actual: {original_size:.2f} MB ({width}x{height}px)")
                    if will_resize:
                        ratio = min(max_width / width, max_height / height)
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)
                        print(f"    Se redimensionaría a: {new_width}x{new_height}px")
                    else:
                        print(f"    No se redimensionaría (ya está dentro de límites)")

                    total_original += original_size
            else:
                # Optimizar imagen
                original_size, new_size, savings = optimize_image(
                    img_file, out_file, max_width, max_height, quality, convert_to_jpeg
                )

                print(f"  ✅ {img_file.name}")
                print(f"     {original_size:.2f} MB → {new_size:.2f} MB (ahorro: {savings:.1f}%)")

                total_original += original_size
                total_new += new_size
                successful += 1

        except Exception as e:
            print(f"  ❌ {img_file.name}: {str(e)}")
            failed += 1
            continue

    # Resumen final
    print()
    print("=" * 60)
    if dry_run:
        print(f"📊 RESUMEN (DRY RUN):")
        print(f"   Imágenes encontradas: {len(image_files)}")
        print(f"   Tamaño total actual: {total_original:.2f} MB")
    else:
        print(f"📊 RESUMEN:")
        print(f"   Imágenes procesadas: {successful}/{len(image_files)}")
        if failed > 0:
            print(f"   Errores: {failed}")
        print(f"   Tamaño original: {total_original:.2f} MB")
        print(f"   Tamaño nuevo: {total_new:.2f} MB")
        total_savings = ((total_original - total_new) / total_original * 100) if total_original > 0 else 0
        print(f"   Ahorro total: {total_original - total_new:.2f} MB ({total_savings:.1f}%)")

        if backup_dir:
            print(f"\n💾 Backup guardado en: {backup_dir}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Optimiza imágenes para uso web.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s --input web/img/scenarios
  %(prog)s --input web/img/scenarios --quality 80 --max-width 1920
  %(prog)s --input web/img/scenarios --output web/img/scenarios_optimized
  %(prog)s --input web/img/scenarios --backup --quality 85
  %(prog)s --input web/img/scenarios --dry-run
        """
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Directorio con las imágenes a optimizar"
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Directorio de salida (si no se especifica, sobrescribe originales)"
    )

    parser.add_argument(
        "--max-width",
        type=int,
        default=1920,
        help="Ancho máximo en píxeles (default: 1920)"
    )

    parser.add_argument(
        "--max-height",
        type=int,
        default=1080,
        help="Alto máximo en píxeles (default: 1080)"
    )

    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="Calidad JPEG 1-100 (default: 85)"
    )

    parser.add_argument(
        "--backup",
        action="store_true",
        help="Crear backup antes de sobrescribir (solo si no se usa --output)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar qué se haría sin modificar archivos"
    )

    parser.add_argument(
        "--convert-to-jpeg",
        action="store_true",
        help="Convertir imágenes PNG a JPEG (reduce mucho el tamaño)"
    )

    args = parser.parse_args()

    # Validar calidad
    if not 1 <= args.quality <= 100:
        print("❌ Error: La calidad debe estar entre 1 y 100")
        return

    try:
        process_directory(
            input_dir=args.input,
            output_dir=args.output,
            max_width=args.max_width,
            max_height=args.max_height,
            quality=args.quality,
            backup=args.backup,
            dry_run=args.dry_run,
            convert_to_jpeg=args.convert_to_jpeg
        )
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
