# Configuración de Google Vertex AI para Imagen 3.0

Esta guía te ayudará a configurar Google Vertex AI para generar imágenes con Imagen 3.0.

## Prerrequisitos

- Cuenta de Google Cloud con facturación activa
- Proyecto de Google Cloud creado

## Paso 1: Configurar el Proyecto de Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)

2. Crea un proyecto nuevo o selecciona uno existente:
   - Haz clic en el selector de proyectos en la parte superior
   - Haz clic en "Nuevo proyecto"
   - Dale un nombre y anota el **Project ID** (lo necesitarás después)

3. Activa la facturación:
   - Ve a [Facturación](https://console.cloud.google.com/billing)
   - Vincula una cuenta de facturación al proyecto
   - Añade un método de pago si no lo has hecho

## Paso 2: Habilitar las APIs necesarias

1. Ve a [APIs & Services](https://console.cloud.google.com/apis/library)

2. Busca y habilita las siguientes APIs:
   - **Vertex AI API**: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
   - **Cloud Resource Manager API**: https://console.cloud.google.com/apis/library/cloudresourcemanager.googleapis.com

3. Haz clic en "Habilitar" para cada una

## Paso 3: Crear una Service Account

1. Ve a [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)

2. Haz clic en **"Create Service Account"**

3. Configura la cuenta:
   - **Service account name**: `imagen-generator` (o el nombre que prefieras)
   - **Service account ID**: Se generará automáticamente
   - Haz clic en **"Create and Continue"**

4. Asigna los roles necesarios:
   - Haz clic en **"Select a role"**
   - Busca y selecciona: **Vertex AI User**
   - Haz clic en **"Continue"**

5. Haz clic en **"Done"**

## Paso 4: Crear y descargar la clave JSON

1. En la lista de Service Accounts, encuentra la que acabas de crear

2. Haz clic en los tres puntos (⋮) a la derecha y selecciona **"Manage keys"**

3. Haz clic en **"Add Key"** → **"Create new key"**

4. Selecciona **JSON** como tipo de clave

5. Haz clic en **"Create"**

6. Se descargará un archivo JSON automáticamente. **Guárdalo en un lugar seguro** (por ejemplo: `~/.config/gcloud/imagen-generator-key.json`)

   ⚠️ **IMPORTANTE**: Este archivo contiene credenciales sensibles. Nunca lo subas a un repositorio público.

## Paso 5: Configurar las variables de entorno

1. Edita tu archivo `.env` en el proyecto:
   ```bash
   nano .env
   ```

2. Añade las siguientes variables:
   ```bash
   # Google Cloud Vertex AI
   GOOGLE_CLOUD_PROJECT=tu-project-id-aqui
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=/ruta/completa/al/archivo-de-credenciales.json
   ```

   Reemplaza:
   - `tu-project-id-aqui` con el Project ID de tu proyecto
   - `/ruta/completa/al/archivo-de-credenciales.json` con la ruta completa al archivo JSON que descargaste

3. Guarda el archivo

## Paso 6: (Alternativa) Autenticación con gcloud CLI

Si prefieres no usar un archivo de credenciales, puedes autenticarte con gcloud CLI:

1. Instala gcloud CLI:
   - macOS: `brew install google-cloud-sdk`
   - Linux/Windows: https://cloud.google.com/sdk/docs/install

2. Autentica tu cuenta:
   ```bash
   gcloud auth application-default login
   ```

3. Configura el proyecto:
   ```bash
   gcloud config set project TU-PROJECT-ID
   ```

4. En tu `.env`, solo necesitas:
   ```bash
   GOOGLE_CLOUD_PROJECT=tu-project-id-aqui
   GOOGLE_CLOUD_LOCATION=us-central1
   # GOOGLE_APPLICATION_CREDENTIALS no es necesario
   ```

## Paso 7: Probar la configuración

Ejecuta el script de prueba:

```bash
uv run python scripts/generate_scenarios.py \
  --prompts web/data/scenario_prompts.json \
  --provider google \
  --skip-generated \
  --limit 1
```

Si todo está configurado correctamente, deberías ver:
```
✅ Vertex AI inicializado: proyecto=tu-project-id, ubicación=us-central1
🎨 Generando 1 escenarios...
📦 Proveedor: GOOGLE
[1/1] 🎬 escena -> imagen.png
    ✅ Guardada correctamente
```

## Solución de problemas

### Error: "Permission denied"
- Verifica que la Service Account tiene el rol **Vertex AI User**
- Asegúrate de que las APIs están habilitadas

### Error: "Project not found"
- Verifica que el GOOGLE_CLOUD_PROJECT es correcto
- Asegúrate de tener acceso al proyecto

### Error: "Could not load credentials"
- Verifica que la ruta en GOOGLE_APPLICATION_CREDENTIALS es correcta y absoluta
- El archivo JSON debe existir y ser accesible
- O intenta autenticarte con `gcloud auth application-default login`

### Error: "Quota exceeded"
- Verifica que tienes créditos en tu cuenta de Google Cloud
- Revisa los límites en https://console.cloud.google.com/iam-admin/quotas

## Costos aproximados

- **Imagen 3.0**: ~$0.02-0.04 por imagen (1024x1024)
- Facturación mensual mínima: Depende del uso

Puedes monitorear tus costos en:
https://console.cloud.google.com/billing

## Seguridad

⚠️ **Importante**:
- Nunca subas el archivo de credenciales JSON a Git
- El `.gitignore` ya está configurado para ignorar archivos `.json` de credenciales
- Mantén tus credenciales seguras y rota las claves periódicamente

## Recursos adicionales

- [Documentación de Vertex AI Imagen](https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview)
- [Precios de Vertex AI](https://cloud.google.com/vertex-ai/pricing)
- [Guía de Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
