#!/bin/bash

# Script para verificar y configurar el bucket S3 de Yupii Dashboard
# Bucket: xideralaws-curso-carlos

set -e

BUCKET_NAME="xideralaws-curso-carlos"
REGION="us-east-1"

echo "🚀 Configurando bucket S3 para Yupii Dashboard"
echo "Bucket: $BUCKET_NAME"
echo "Región: $REGION"
echo "==============================================="

# Verificar si AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI no está instalado"
    exit 1
fi

# Verificar credenciales
echo "📋 Verificando credenciales AWS..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ No se pudieron verificar las credenciales AWS"
    echo "Configura AWS CLI con: aws configure"
    exit 1
fi

echo "✅ Credenciales AWS verificadas"

# Verificar si el bucket existe
echo "🔍 Verificando si el bucket existe..."
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "✅ El bucket $BUCKET_NAME ya existe"
else
    echo "⚠️ El bucket $BUCKET_NAME no existe o no tienes acceso"
    read -p "¿Quieres intentar crearlo? (y/N): " create_bucket
    if [[ $create_bucket =~ ^[Yy]$ ]]; then
        echo "🔨 Creando bucket $BUCKET_NAME..."
        aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"
        echo "✅ Bucket creado exitosamente"
    else
        echo "ℹ️ Asegúrate de que el bucket exista antes de continuar"
        exit 1
    fi
fi

# Crear estructura de carpetas
echo "📁 Configurando estructura de carpetas..."

# Crear carpeta pedidos/
echo "Creando carpeta pedidos/..."
aws s3api put-object --bucket "$BUCKET_NAME" --key "pedidos/" --region "$REGION"

# Crear carpeta datasets/
echo "Creando carpeta datasets/..."
aws s3api put-object --bucket "$BUCKET_NAME" --key "datasets/" --region "$REGION"

echo "✅ Estructura de carpetas creada"

# Verificar estructura
echo "🔍 Verificando estructura del bucket..."
echo "Contenido del bucket:"
aws s3 ls "s3://$BUCKET_NAME/" --recursive

echo ""
echo "✅ Configuración completada exitosamente!"
echo ""
echo "📊 Próximos pasos:"
echo "1. Sube archivos .txt de repartidores a la carpeta 'pedidos/'"
echo "2. Configura las variables de entorno en tu archivo .env:"
echo "   AWS_ACCESS_KEY_ID=tu_access_key"
echo "   AWS_SECRET_ACCESS_KEY=tu_secret_key"
echo "   AWS_DEFAULT_REGION=$REGION"
echo "   S3_BUCKET_NAME=$BUCKET_NAME"
echo "3. Ejecuta el dashboard con: ./deploy.sh build"
echo ""
echo "🔗 Para subir archivos de ejemplo:"
echo "   aws s3 cp archivo_repartidor.txt s3://$BUCKET_NAME/pedidos/"
