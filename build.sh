#!/bin/bash
set -e

echo "📦 Building static site for Cloudflare Pages..."

# Verificar que web/ existe
if [ ! -d "web" ] || [ ! -f "web/index.html" ]; then
    echo "❌ Error: web/ directory or index.html not found"
    exit 1
fi

# Copiar archivos de web/ a _output/
mkdir -p _output
cp -r web/* _output/

echo "✅ Build complete - $(find _output -type f | wc -l | xargs) files ready"
