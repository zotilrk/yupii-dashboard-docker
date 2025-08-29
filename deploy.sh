#!/bin/bash

# Script de deployment local para Yupii Dashboard
# Este script facilita el testing y deployment local

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Banner
echo -e "${BLUE}"
echo "██╗   ██╗██╗   ██╗██████╗ ██╗██╗    ██████╗  █████╗ ███████╗██╗  ██╗██████╗  ██████╗  █████╗ ██████╗ ██████╗ "
echo "╚██╗ ██╔╝██║   ██║██╔══██╗██║██║    ██╔══██╗██╔══██╗██╔════╝██║  ██║██╔══██╗██╔═══██╗██╔══██╗██╔══██╗██╔══██╗"
echo " ╚████╔╝ ██║   ██║██████╔╝██║██║    ██║  ██║███████║███████╗███████║██████╔╝██║   ██║███████║██████╔╝██║  ██║"
echo "  ╚██╔╝  ██║   ██║██╔═══╝ ██║██║    ██║  ██║██╔══██║╚════██║██╔══██║██╔══██╗██║   ██║██╔══██║██╔══██╗██║  ██║"
echo "   ██║   ╚██████╔╝██║     ██║██║    ██████╔╝██║  ██║███████║██║  ██║██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝"
echo "   ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ "
echo -e "${NC}"
echo "🚀 Yupii Dashboard - Local Deployment Script"
echo "=============================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "Dockerfile" ] || [ ! -f "docker-compose.yml" ]; then
    error "Este script debe ejecutarse desde el directorio docker-deployment"
    exit 1
fi

# Función para verificar dependencias
check_dependencies() {
    log "Verificando dependencias..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado"
        exit 1
    fi
    
    success "Dependencias verificadas"
}

# Función para verificar variables de entorno
check_env() {
    log "Verificando variables de entorno..."
    
    if [ ! -f ".env" ]; then
        warning "Archivo .env no encontrado, creando desde .env.example"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            warning "Por favor edita el archivo .env con tus credenciales AWS"
            echo "Variables requeridas:"
            echo "  - AWS_ACCESS_KEY_ID"
            echo "  - AWS_SECRET_ACCESS_KEY"
            echo "  - AWS_DEFAULT_REGION"
            echo "  - S3_BUCKET_NAME"
            read -p "Presiona Enter cuando hayas configurado el archivo .env..."
        else
            error "Archivo .env.example no encontrado"
            exit 1
        fi
    fi
    
    # Cargar variables de entorno
    source .env
    
    # Verificar variables críticas
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$S3_BUCKET_NAME" ]; then
        error "Variables de entorno AWS no configuradas correctamente"
        exit 1
    fi
    
    success "Variables de entorno configuradas"
}

# Función para build y deploy
build_and_deploy() {
    log "Construyendo y desplegando aplicación..."
    
    # Detener contenedores existentes
    log "Deteniendo contenedores existentes..."
    docker-compose down --remove-orphans || true
    
    # Limpiar imágenes antiguas
    log "Limpiando imágenes antiguas..."
    docker system prune -f || true
    
    # Construir imágenes
    log "Construyendo nuevas imágenes..."
    docker-compose build --no-cache
    
    # Iniciar servicios
    log "Iniciando servicios..."
    docker-compose up -d
    
    success "Aplicación desplegada exitosamente"
}

# Función para mostrar status
show_status() {
    log "Estado de los servicios:"
    docker-compose ps
    
    echo ""
    log "Logs recientes:"
    docker-compose logs --tail=20
    
    echo ""
    success "URLs de acceso:"
    echo "  📊 Dashboard Principal: http://localhost:8501"
    echo "  🌍 Dashboard Global:    http://localhost:8502"
    echo ""
    echo "Para ver logs en tiempo real:"
    echo "  docker-compose logs -f"
}

# Función para testing
run_tests() {
    log "Ejecutando tests básicos..."
    
    # Test de sintaxis Python
    log "Verificando sintaxis Python..."
    docker run --rm -v $(pwd)/src:/app/src python:3.11-slim \
        sh -c "cd /app && python -m py_compile src/app.py src/global_dashboard.py src/s3_manager.py"
    
    # Test de importaciones
    log "Verificando importaciones..."
    docker run --rm -v $(pwd):/app -w /app python:3.11-slim \
        sh -c "pip install -r requirements.txt && python -c 'import streamlit, pandas, matplotlib, seaborn, boto3; print(\"✅ Todas las dependencias importadas correctamente\")'"
    
    success "Tests completados exitosamente"
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandos disponibles:"
    echo "  build    - Construir y desplegar la aplicación"
    echo "  start    - Iniciar servicios existentes"
    echo "  stop     - Detener servicios"
    echo "  restart  - Reiniciar servicios"
    echo "  status   - Mostrar estado de servicios"
    echo "  logs     - Mostrar logs en tiempo real"
    echo "  test     - Ejecutar tests básicos"
    echo "  clean    - Limpiar contenedores e imágenes"
    echo "  help     - Mostrar esta ayuda"
    echo ""
    echo "Si no se especifica comando, se ejecuta 'build'"
}

# Función para limpiar
clean() {
    log "Limpiando contenedores e imágenes..."
    docker-compose down --volumes --remove-orphans
    docker system prune -a -f --volumes
    success "Limpieza completada"
}

# Main execution
main() {
    local command=${1:-build}
    
    case $command in
        "build")
            check_dependencies
            check_env
            run_tests
            build_and_deploy
            show_status
            ;;
        "start")
            docker-compose start
            show_status
            ;;
        "stop")
            docker-compose stop
            success "Servicios detenidos"
            ;;
        "restart")
            docker-compose restart
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "test")
            check_dependencies
            run_tests
            ;;
        "clean")
            clean
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Comando desconocido: $command"
            show_help
            exit 1
            ;;
    esac
}

# Manejar Ctrl+C
trap 'echo -e "\n\n🛑 Deployment interrumpido por el usuario"; exit 1' INT

# Ejecutar función principal
main "$@"
