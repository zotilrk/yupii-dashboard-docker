# Setup AWS y EC2 para Yupii Dashboard

## 1. Configuración de AWS S3

### Crear Bucket S3
```bash
# Crear bucket
aws s3 mb s3://xideralaws-curso-carlos --region us-east-1

# Configurar estructura de carpetas
aws s3api put-object --bucket xideralaws-curso-carlos --key pedidos/
aws s3api put-object --bucket xideralaws-curso-carlos --key datasets/
```

### Configurar permisos del bucket
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "YupiiDashboardAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::ACCOUNT-ID:user/yupii-dashboard-user"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::xideralaws-curso-carlos",
                "arn:aws:s3:::xideralaws-curso-carlos/*"
            ]
        }
    ]
}
```

## 2. Configuración de ECR (Elastic Container Registry)

### Crear repositorio ECR
```bash
# Crear repositorio
aws ecr create-repository --repository-name yupii-dashboard --region us-east-1

# Obtener URI del repositorio
aws ecr describe-repositories --repository-names yupii-dashboard --region us-east-1
```

## 3. Configuración de EC2

### Lanzar instancia EC2
- **Tipo**: t3.medium o superior (para mejor rendimiento)
- **AMI**: Amazon Linux 2023
- **Security Group**: Permitir puertos 22 (SSH), 8501 (Dashboard), 8502 (Global Dashboard)
- **Storage**: 20 GB SSD mínimo
- **IAM Role**: Con permisos para ECR y S3

### Security Group Rules
```
Type            Protocol    Port Range    Source
SSH             TCP         22           Your IP
Custom TCP      TCP         8501         0.0.0.0/0
Custom TCP      TCP         8502         0.0.0.0/0
HTTP            TCP         80           0.0.0.0/0
HTTPS           TCP         443          0.0.0.0/0
```

### Configurar instancia EC2
```bash
# Conectar a la instancia
ssh -i your-key.pem ec2-user@your-ec2-ip

# Actualizar sistema
sudo yum update -y

# Instalar Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Instalar AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Instalar SSM Agent (para GitHub Actions)
sudo yum install -y amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
sudo systemctl enable amazon-ssm-agent

# Crear directorio para la aplicación
mkdir -p /home/ec2-user/yupii-dashboard
```

## 4. IAM Roles y Permisos

### Role para EC2 (EC2-Yupii-Dashboard-Role)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::xideralaws-curso-carlos",
                "arn:aws:s3:::xideralaws-curso-carlos/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:SendCommand",
                "ssm:ListCommands",
                "ssm:ListCommandInvocations",
                "ssm:DescribeInstanceInformation",
                "ssm:GetCommandInvocation"
            ],
            "Resource": "*"
        }
    ]
}
```

### Usuario para GitHub Actions (GitHub-Actions-User)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:PutImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:SendCommand"
            ],
            "Resource": [
                "arn:aws:ec2:us-east-1:ACCOUNT-ID:instance/INSTANCE-ID",
                "arn:aws:ssm:us-east-1::document/AWS-RunShellScript"
            ]
        }
    ]
}
```

## 5. Configuración de GitHub Repository

### Secrets requeridos en GitHub
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
EC2_INSTANCE_ID=i-1234567890abcdef0
S3_BUCKET_NAME=xideralaws-curso-carlos
```

### Variables de entorno para el repository
```
AWS_DEFAULT_REGION=us-east-1
ECR_REPOSITORY=yupii-dashboard
```

## 6. Deployment Manual (primera vez)

```bash
# En tu máquina local
cd docker-deployment

# Construir imagen
docker build -t yupii-dashboard .

# Login a ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com

# Tag y push
docker tag yupii-dashboard:latest ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/yupii-dashboard:latest
docker push ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/yupii-dashboard:latest

# En EC2
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com

# Ejecutar contenedores
sudo docker run -d --name yupii-dashboard-app \
  -p 8501:8501 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e S3_BUCKET_NAME=xideralaws-curso-carlos \
  --restart unless-stopped \
  ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/yupii-dashboard:latest

sudo docker run -d --name yupii-dashboard-global \
  -p 8502:8501 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e S3_BUCKET_NAME=xideralaws-curso-carlos \
  --restart unless-stopped \
  ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/yupii-dashboard:latest \
  streamlit run src/global_dashboard.py --server.port=8501 --server.address=0.0.0.0
```

## 7. Monitoreo y Logs

```bash
# Ver logs de los contenedores
sudo docker logs yupii-dashboard-app
sudo docker logs yupii-dashboard-global

# Ver estado de los contenedores
sudo docker ps

# Reiniciar contenedores si es necesario
sudo docker restart yupii-dashboard-app
sudo docker restart yupii-dashboard-global
```

## 8. URLs de Acceso

Una vez deployado, las aplicaciones estarán disponibles en:
- **Dashboard Principal**: `http://YOUR-EC2-PUBLIC-IP:8501`
- **Dashboard Global**: `http://YOUR-EC2-PUBLIC-IP:8502`

## 9. Estructura de archivos en S3

```
s3://xideralaws-curso-carlos/
├── pedidos/
│   ├── repartidor1.txt
│   ├── repartidor2.txt
│   └── ...
└── datasets/
    └── dataset_global.csv
```

## 10. Troubleshooting

### Problemas comunes:
1. **Error de permisos S3**: Verificar IAM roles y policies
2. **Contenedor no inicia**: Verificar logs con `docker logs`
3. **No puede conectar a ECR**: Verificar login y permisos
4. **GitHub Actions falla**: Verificar secrets y permisos SSM

### Comandos útiles:
```bash
# Ver todos los contenedores
sudo docker ps -a

# Limpiar imágenes antiguas
sudo docker system prune -f

# Ver uso de recursos
sudo docker stats

# Backup de dataset
aws s3 cp s3://xideralaws-curso-carlos/datasets/dataset_global.csv ./backup_$(date +%Y%m%d).csv
```
