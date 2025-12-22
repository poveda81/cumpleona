#!/bin/bash
set -e

echo "📦 Building static site..."
echo "📁 Source directory: web/"

# Verificar que web/ existe y tiene archivos
if [ ! -d "web" ]; then
    echo "❌ Error: web/ directory not found"
    exit 1
fi

if [ ! -f "web/index.html" ]; then
    echo "❌ Error: web/index.html not found"
    exit 1
fi

echo "✅ Found web/index.html"

# Contar archivos
file_count=$(find web -type f | wc -l)
echo "📊 Total files in web/: $file_count"

# Listar estructura
echo "📂 Directory structure:"
ls -lh web/ | head -10

echo "✅ Build complete - files ready in web/ directory"
