# Yupii Dashboard - Versión Dockerizada con S3

Dashboard de análisis de pedidos para repartidores de Yupii, dockerizado y configurado para usar AWS S3 como almacenamiento de archivos.

## 🚀 Características

- **Dashboard Principal**: Análisis individual por repartidor
- **Dashboard Global**: Análisis consolidado de todos los repartidores
- **Integración S3**: Carga archivos directamente desde AWS S3
- **Dockerizado**: Fácil deployment en cualquier entorno
- **CI/CD**: GitHub Actions para deployment automático en EC2
- **Filtrado Inteligente**: Identificación automática de productos vs instrucciones
- **Normalización**: Unificación de nombres de establecimientos similares

## 📁 Estructura del Proyecto

```
docker-deployment/
├── src/
│   ├── app.py                 # Dashboard principal
│   ├── global_dashboard.py    # Dashboard global
│   └── s3_manager.py          # Manejo de S3
├── .github/workflows/
│   └── deploy.yml             # CI/CD pipeline
├── Dockerfile                 # Configuración Docker
├── docker-compose.yml         # Desarrollo local
├── requirements.txt           # Dependencias Python
├── .env.example              # Variables de entorno ejemplo
├── AWS_SETUP.md              # Guía de configuración AWS
└── README.md                 # Este archivo
```

## 🛠️ Instalación y Configuración

### 1. Prerrequisitos

- Docker y Docker Compose
- Cuenta AWS con S3 y ECR configurados
- (Opcional) Instancia EC2 para deployment

### 2. Configuración Local

```bash
# Clonar el repositorio
git clone <repository-url>
cd docker-deployment

# Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales AWS

# Construir y ejecutar con Docker Compose
docker-compose up --build
```

Las aplicaciones estarán disponibles en:
- Dashboard Principal: http://localhost:8501
- Dashboard Global: http://localhost:8502

### 3. Variables de Entorno Requeridas

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=xideralaws-curso-carlos
```

## 📊 Uso del Dashboard

### Dashboard Principal (Puerto 8501)

1. **Selección de Archivo**: Elige un archivo .txt de la lista disponible en S3
2. **Configuración**: Ajusta el nombre del repartidor si es necesario
3. **Análisis**: Selecciona rango de fechas y presiona "Analizar"
4. **Resultados**: 
   - KPIs principales (envíos, ingresos, pagos)
   - Gráficas por día de la semana
   - Exportación a PNG y CSV

### Dashboard Global (Puerto 8502)

1. **Carga de Dataset**: Se carga automáticamente desde S3
2. **Filtros**: Selecciona rango de fechas y repartidores
3. **Análisis Consolidado**:
   - Métricas globales del período
   - Rendimiento por repartidor
   - Tendencias temporales
   - Top establecimientos
   - Exportación de resultados

## 🏗️ Estructura de S3

Tu bucket S3 debe tener la siguiente estructura:

```
s3://xideralaws-curso-carlos/
├── pedidos/
│   ├── carlos.txt
│   ├── maria.txt
│   ├── jose.txt
│   └── ...
└── datasets/
    └── dataset_global.csv
```

### Formato de Archivos de Pedidos

Los archivos .txt deben contener mensajes de WhatsApp con el formato:

```
_*Recoger en*_
📍Nombre del Establecimiento
_*Pedido*_
Descripción del producto
_*Entregar en*_
Dirección del cliente
_*Cobrar*_
$amount
[DD/MM/YY, HH:MM:SS]
```

## 🚀 Deployment en EC2

### Configuración Automática con GitHub Actions

1. **Fork del repositorio** y configura los secrets:
   ```
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY
   EC2_INSTANCE_ID
   S3_BUCKET_NAME
   ```

2. **Push a main** para activar el deployment automático

3. **Acceso a la aplicación**:
   - Dashboard Principal: `http://YOUR-EC2-IP:8501`
   - Dashboard Global: `http://YOUR-EC2-IP:8502`

### Deployment Manual

Ver [AWS_SETUP.md](AWS_SETUP.md) para instrucciones detalladas de configuración manual.

## 🐳 Comandos Docker Útiles

```bash
# Desarrollo local
docker-compose up --build

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Construir imagen production
docker build -t yupii-dashboard .

# Ejecutar contenedor individual
docker run -p 8501:8501 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e S3_BUCKET_NAME=xideralaws-curso-carlos \
  yupii-dashboard
```

## 📈 Funcionalidades Principales

### Filtrado Inteligente
- Identifica automáticamente productos reales vs instrucciones de envío
- Filtra textos como "tiene un envío", "a nombre de", etc.
- Mantiene solo productos válidos para análisis preciso

### Normalización de Establecimientos
- Unifica variaciones del mismo establecimiento
- Ej: "McDonald's", "Mc Donald's", "Mac Donalds" → "Mcdonalds"
- Mejora la precisión del análisis por establecimiento

### Análisis Temporal
- Tendencias diarias de envíos e ingresos
- Análisis por días de la semana
- Identificación de patrones temporales

### Métricas de Rendimiento
- KPIs por repartidor (envíos, ingresos, promedio diario)
- Comparación entre repartidores
- Análisis de fin de semana vs días laborales

## 🔧 Troubleshooting

### Problemas Comunes

1. **Error de conexión S3**
   - Verificar credenciales AWS
   - Confirmar permisos del bucket
   - Revisar región configurada

2. **Archivos no aparecen en S3**
   - Verificar estructura de carpetas (`pedidos/`)
   - Confirmar formato .txt
   - Revisar permisos de lectura

3. **Dashboard no carga**
   - Verificar puertos (8501, 8502)
   - Revisar logs: `docker logs container_name`
   - Confirmar variables de entorno

### Logs y Monitoreo

```bash
# Ver logs en tiempo real
docker-compose logs -f yupii-dashboard
docker-compose logs -f yupii-global-dashboard

# Ver estado de contenedores
docker ps

# Recursos utilizados
docker stats
```

## 🤝 Contribución

1. Fork del repositorio
2. Crear branch feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto es propiedad de Yupii y está destinado para uso interno.

## 📞 Soporte

Para soporte técnico o preguntas sobre el deployment:
- Revisar [AWS_SETUP.md](AWS_SETUP.md) para configuración
- Verificar logs de contenedores
- Contactar al equipo de desarrollo

---

**Colores Corporativos Yupii**: #185E8D (Azul), #00AEEF (Cian), #000000 (Negro)
