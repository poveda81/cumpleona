#!/usr/bin/env python3
"""
Script para generar códigos QR para cada agente.

Genera un código QR para cada agente con la URL:
https://cumpleona.pages.dev/?agent={agent_id}

Uso:
    python scripts/generate_qr_codes.py
    python scripts/generate_qr_codes.py --base-url https://tu-dominio.com
"""

import json
import argparse
from pathlib import Path
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask


def load_agents(agents_file):
    """Carga los agentes desde el archivo JSON."""
    with open(agents_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_qr_code(agent_id, agent_data, base_url, output_dir, style='simple'):
    """
    Genera un código QR para un agente.

    Args:
        agent_id: ID del agente
        agent_data: Datos del agente (nombre, etc.)
        base_url: URL base del sitio
        output_dir: Directorio donde guardar los QR
        style: 'simple' o 'styled' (con esquinas redondeadas)
    """
    # Crear URL
    url = f"{base_url}/?agent={agent_id}"

    # Configurar QR code
    qr = qrcode.QRCode(
        version=1,  # Tamaño automático
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta corrección de errores
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Generar imagen
    if style == 'styled':
        # QR con estilo (esquinas redondeadas y color)
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=SolidFillColorMask(
                back_color=(255, 255, 255),  # Fondo blanco
                front_color=(229, 9, 20)      # Rojo Stranger Things
            )
        )
    else:
        # QR simple blanco y negro
        img = qr.make_image(fill_color="black", back_color="white")

    # Guardar imagen
    agent_name = agent_data.get('name', agent_id)
    filename = f"qr_{agent_id}.png"
    filepath = output_dir / filename

    img.save(filepath)

    return filepath, url, agent_name


def main():
    parser = argparse.ArgumentParser(
        description="Genera códigos QR para cada agente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s
  %(prog)s --base-url https://mi-dominio.com
  %(prog)s --output-dir qr_codes --style styled
        """
    )

    parser.add_argument(
        "--base-url",
        default="https://cumpleona.pages.dev",
        help="URL base del sitio (default: https://cumpleona.pages.dev)"
    )

    parser.add_argument(
        "--output-dir",
        default="web/img/qr",
        help="Directorio de salida para los QR codes (default: web/img/qr)"
    )

    parser.add_argument(
        "--agents-file",
        default="web/data/agents.json",
        help="Archivo JSON con los agentes (default: web/data/agents.json)"
    )

    parser.add_argument(
        "--style",
        choices=['simple', 'styled'],
        default='simple',
        help="Estilo del QR: simple (blanco/negro) o styled (con color y esquinas redondeadas)"
    )

    args = parser.parse_args()

    # Cargar agentes
    agents_file = Path(args.agents_file)
    if not agents_file.exists():
        print(f"❌ Error: No se encuentra el archivo {agents_file}")
        return 1

    agents = load_agents(agents_file)

    # Crear directorio de salida
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🔲 GENERADOR DE CÓDIGOS QR - OPERACIÓN PORTAL 27")
    print("=" * 60)
    print()
    print(f"📁 Agentes encontrados: {len(agents)}")
    print(f"🌐 URL base: {args.base_url}")
    print(f"💾 Directorio de salida: {output_dir}")
    print(f"🎨 Estilo: {args.style}")
    print()

    # Generar QR codes
    generated = []

    for agent_id, agent_data in agents.items():
        try:
            filepath, url, agent_name = generate_qr_code(
                agent_id, agent_data, args.base_url, output_dir, args.style
            )
            generated.append({
                'id': agent_id,
                'name': agent_name,
                'url': url,
                'file': filepath
            })
            print(f"  ✅ {agent_name:20} → {filepath.name}")
        except Exception as e:
            print(f"  ❌ {agent_id}: {str(e)}")

    print()
    print("=" * 60)
    print(f"✅ Generados {len(generated)} códigos QR")
    print("=" * 60)
    print()

    # Crear archivo index con todos los códigos
    create_index_html(generated, output_dir, args.base_url)

    print(f"📄 Índice HTML creado: {output_dir}/index.html")
    print()
    print("💡 Tip: Abre el archivo index.html para ver todos los QR codes")
    print()


def create_index_html(qr_codes, output_dir, base_url):
    """Crea un archivo HTML con todos los códigos QR."""
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Códigos QR - Operación Portal 27</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            text-align: center;
            color: #e50914;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 40px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .card img {{
            width: 200px;
            height: 200px;
            margin: 0 auto 10px;
            display: block;
        }}
        .card h3 {{
            margin: 10px 0 5px;
            color: #333;
        }}
        .card .url {{
            font-size: 12px;
            color: #666;
            word-break: break-all;
            margin-top: 5px;
        }}
        .card button {{
            margin-top: 10px;
            padding: 8px 16px;
            background: #e50914;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        .card button:hover {{
            background: #b00710;
        }}
        .info {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <h1>🔲 Códigos QR - Operación Portal 27</h1>
    <p class="subtitle">Escanea para jugar con tu agente favorito</p>

    <div class="info">
        <p><strong>URL base:</strong> {base_url}</p>
        <p><strong>Total de agentes:</strong> {len(qr_codes)}</p>
    </div>

    <div class="grid">
"""

    for qr in sorted(qr_codes, key=lambda x: x['name']):
        html += f"""
        <div class="card">
            <img src="{qr['file'].name}" alt="QR {qr['name']}">
            <h3>{qr['name']}</h3>
            <div class="url">{qr['url']}</div>
            <button onclick="window.open('{qr['url']}', '_blank')">Abrir</button>
        </div>
"""

    html += """
    </div>

    <div class="info">
        <h3>📱 Cómo usar los códigos QR:</h3>
        <ol>
            <li>Imprime o muestra los códigos QR</li>
            <li>Los jugadores escanean el código con su móvil</li>
            <li>Se abre el juego directamente con su agente seleccionado</li>
        </ol>
    </div>
</body>
</html>
"""

    index_file = output_dir / "index.html"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == "__main__":
    main()
