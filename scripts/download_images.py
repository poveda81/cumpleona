#!/usr/bin/env python3
"""
Script para descargar todas las imágenes de la web del Colegio Sagrada Familia Elda
Hace crawling de todas las páginas del sitio
"""

import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path
from bs4 import BeautifulSoup

def create_download_folder():
    """Crea la carpeta de descargas si no existe"""
    folder = Path("web/img/cole_sagrada_familia")
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def sanitize_filename(url):
    """Crea un nombre de archivo válido desde una URL"""
    # Extraer el nombre del archivo de la URL
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)

    # Si no hay nombre de archivo, usar un hash de la URL
    if not filename or filename == '/':
        filename = f"image_{abs(hash(url))}.jpg"

    # Limpiar caracteres no válidos
    filename = re.sub(r'[^\w\-_\.]', '_', filename)

    # Limitar longitud del nombre
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:190] + ext

    return filename

def is_same_domain(url, base_domain):
    """Verifica si una URL pertenece al mismo dominio"""
    parsed = urlparse(url)
    return parsed.netloc == base_domain or parsed.netloc == '' or parsed.netloc == f'www.{base_domain}'

def download_image(url, folder, session, downloaded_images):
    """Descarga una imagen desde una URL"""
    # Evitar descargar la misma imagen dos veces
    if url in downloaded_images:
        return True

    try:
        response = session.get(url, timeout=15, stream=True)
        response.raise_for_status()

        # Verificar que es una imagen
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type.lower():
            return False

        filename = sanitize_filename(url)
        filepath = folder / filename

        # Si ya existe con ese nombre, añadir un número
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while filepath.exists():
            filename = f"{base_name}_{counter}{ext}"
            filepath = folder / filename
            counter += 1

        # Guardar la imagen
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"  ✓ {filename}")
        downloaded_images.add(url)
        return True

    except Exception as e:
        print(f"  ✗ Error: {str(e)[:50]}")
        return False

def find_all_images(soup, base_url):
    """Encuentra todas las URLs de imágenes en la página"""
    image_urls = set()

    # Buscar en etiquetas <img>
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if src:
            full_url = urljoin(base_url, src)
            image_urls.add(full_url)

    # Buscar en etiquetas <source> (para picture elements)
    for source in soup.find_all('source'):
        srcset = source.get('srcset')
        if srcset:
            # srcset puede contener múltiples URLs
            urls = [url.split()[0] for url in srcset.split(',')]
            for url in urls:
                full_url = urljoin(base_url, url.strip())
                image_urls.add(full_url)

    # Buscar en estilos inline y CSS (background-image)
    for element in soup.find_all(style=True):
        style = element.get('style', '')
        matches = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
        for match in matches:
            full_url = urljoin(base_url, match)
            if any(ext in full_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                image_urls.add(full_url)

    # Buscar en atributos data-* comunes
    for element in soup.find_all(attrs={'data-bg': True}):
        bg_url = element.get('data-bg')
        if bg_url:
            full_url = urljoin(base_url, bg_url)
            image_urls.add(full_url)

    return image_urls

def find_all_links(soup, base_url, base_domain):
    """Encuentra todos los enlaces internos de la página"""
    links = set()

    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if not href:
            continue

        # Construir URL completa
        full_url = urljoin(base_url, href)

        # Limpiar fragmentos y parámetros de query innecesarios
        parsed = urlparse(full_url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Solo añadir si es del mismo dominio y no es un archivo
        if is_same_domain(clean_url, base_domain):
            # Ignorar archivos PDF, ZIP, etc.
            if not any(clean_url.lower().endswith(ext) for ext in ['.pdf', '.zip', '.doc', '.docx', '.xls', '.xlsx']):
                links.add(clean_url)

    return links

def crawl_website(start_url, max_pages=100):
    """Hace crawling de todo el sitio web"""
    print("🏫 Descargando imágenes del Colegio Sagrada Familia Elda")
    print(f"📍 URL inicial: {start_url}\n")

    # Crear carpeta de descargas
    download_folder = create_download_folder()
    print(f"📁 Carpeta de destino: {download_folder}\n")

    # Crear sesión HTTP con headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    # Obtener dominio base
    base_domain = urlparse(start_url).netloc.replace('www.', '')

    # Sets para tracking
    visited_urls = set()
    to_visit = {start_url}
    all_images = set()
    downloaded_images = set()

    print("🔍 Iniciando crawling del sitio...\n")

    page_count = 0

    while to_visit and page_count < max_pages:
        current_url = to_visit.pop()

        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)
        page_count += 1

        print(f"[{page_count}] Explorando: {current_url}")

        try:
            response = session.get(current_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Encontrar imágenes en esta página
            images = find_all_images(soup, current_url)
            new_images = images - all_images

            if new_images:
                print(f"  📸 Encontradas {len(new_images)} imágenes nuevas")
                all_images.update(new_images)

            # Encontrar enlaces para seguir explorando
            links = find_all_links(soup, current_url, base_domain)
            new_links = links - visited_urls - to_visit
            to_visit.update(new_links)

            # Pequeña pausa para no saturar el servidor
            time.sleep(0.5)

        except Exception as e:
            print(f"  ✗ Error al explorar: {str(e)[:100]}")
            continue

    print(f"\n📊 Crawling completado!")
    print(f"   Páginas visitadas: {len(visited_urls)}")
    print(f"   Imágenes encontradas: {len(all_images)}\n")

    if not all_images:
        print("❌ No se encontraron imágenes")
        return

    print("⬇️  Descargando imágenes...\n")

    # Descargar todas las imágenes
    success_count = 0
    for i, img_url in enumerate(all_images, 1):
        print(f"[{i}/{len(all_images)}] {img_url}")
        if download_image(img_url, download_folder, session, downloaded_images):
            success_count += 1

        # Pausa breve entre descargas
        time.sleep(0.2)

    print(f"\n✅ Descarga completada!")
    print(f"📊 {success_count} de {len(all_images)} imágenes descargadas correctamente")
    print(f"📁 Ubicación: {download_folder.absolute()}")

def main():
    url = "https://sagradafamiliaelda.com/"

    try:
        # Limitar a 100 páginas para evitar crawling infinito
        crawl_website(url, max_pages=100)
    except KeyboardInterrupt:
        print("\n\n⚠️  Descarga interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")

if __name__ == "__main__":
    main()
