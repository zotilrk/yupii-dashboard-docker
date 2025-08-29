import boto3
import streamlit as st
from botocore.exceptions import NoCredentialsError, ClientError
import os
from typing import List, Tuple

class S3Manager:
    """Maneja las operaciones con AWS S3"""
    
    def __init__(self):
        """Inicializa el cliente S3 con las credenciales de las variables de entorno"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-1')
            )
            self.bucket_name = os.getenv('S3_BUCKET_NAME', 'xideralaws-curso-carlos')
        except Exception as e:
            st.error(f"Error al configurar S3: {str(e)}")
            self.s3_client = None
            self.bucket_name = None
    
    def list_files(self, prefix: str = "pedidos/") -> List[Tuple[str, str]]:
        """
        Lista los archivos en el bucket S3
        
        Args:
            prefix: Prefijo para filtrar archivos (por defecto "pedidos/")
            
        Returns:
            Lista de tuplas (nombre_archivo, key_completa)
        """
        if not self.s3_client:
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Solo incluir archivos .txt y evitar directorios
                    if key.endswith('.txt') and not key.endswith('/'):
                        filename = key.split('/')[-1]  # Obtener solo el nombre del archivo
                        files.append((filename, key))
            
            return sorted(files)
            
        except ClientError as e:
            st.error(f"Error al listar archivos de S3: {str(e)}")
            return []
        except NoCredentialsError:
            st.error("Credenciales de AWS no encontradas")
            return []
    
    def download_file(self, key: str) -> str:
        """
        Descarga un archivo de S3 y retorna su contenido como string
        
        Args:
            key: Clave del archivo en S3
            
        Returns:
            Contenido del archivo como string
        """
        if not self.s3_client:
            return ""
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            return content
            
        except ClientError as e:
            st.error(f"Error al descargar archivo de S3: {str(e)}")
            return ""
        except Exception as e:
            st.error(f"Error inesperado al descargar archivo: {str(e)}")
            return ""
    
    def upload_file(self, content: str, key: str) -> bool:
        """
        Sube un archivo a S3
        
        Args:
            content: Contenido del archivo como string
            key: Clave para el archivo en S3
            
        Returns:
            True si la subida fue exitosa, False en caso contrario
        """
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType='text/plain'
            )
            return True
            
        except ClientError as e:
            st.error(f"Error al subir archivo a S3: {str(e)}")
            return False
        except Exception as e:
            st.error(f"Error inesperado al subir archivo: {str(e)}")
            return False
    
    def save_dataset(self, df, filename: str = "dataset_global.csv") -> bool:
        """
        Guarda el dataset global en S3
        
        Args:
            df: DataFrame a guardar
            filename: Nombre del archivo
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if not self.s3_client:
            return False
        
        try:
            csv_content = df.to_csv(index=False)
            key = f"datasets/{filename}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=csv_content.encode('utf-8'),
                ContentType='text/csv'
            )
            return True
            
        except Exception as e:
            st.error(f"Error al guardar dataset en S3: {str(e)}")
            return False
    
    def load_dataset(self, filename: str = "dataset_global.csv"):
        """
        Carga el dataset global desde S3
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            DataFrame o None si no se pudo cargar
        """
        if not self.s3_client:
            return None
        
        try:
            key = f"datasets/{filename}"
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            import pandas as pd
            from io import StringIO
            
            df = pd.read_csv(StringIO(content))
            return df
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # El archivo no existe, retornar DataFrame vacío
                import pandas as pd
                return pd.DataFrame()
            else:
                st.error(f"Error al cargar dataset desde S3: {str(e)}")
                return None
        except Exception as e:
            st.error(f"Error inesperado al cargar dataset: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con S3
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False
        except NoCredentialsError:
            return False
