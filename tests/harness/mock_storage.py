"""
Mock puro de Azure Storage para testing sin dependencias de Django.

Este módulo proporciona mocks de las funciones principales de Azure Storage
para testing aislado sin necesidad de configuración de Django.
"""

import json
import time
import uuid
import base64
from typing import Dict, List, Any, Optional, Union, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class MockBlobProperties:
    """Mock de propiedades de blob."""
    name: str
    size: int
    content_type: str = "application/octet-stream"
    last_modified: datetime = None
    etag: str = None
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.last_modified is None:
            self.last_modified = datetime.now()
        if self.etag is None:
            self.etag = f"\"{uuid.uuid4().hex}\""


@dataclass
class MockBlob:
    """Mock de un blob de Azure Storage."""
    name: str
    content: bytes
    properties: MockBlobProperties = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = MockBlobProperties(
                name=self.name,
                size=len(self.content),
                content_type=self._guess_content_type()
            )
    
    def _guess_content_type(self) -> str:
        """Adivinar content type basado en la extensión del archivo."""
        if self.name.endswith('.pdf'):
            return 'application/pdf'
        elif self.name.endswith('.jpg') or self.name.endswith('.jpeg'):
            return 'image/jpeg'
        elif self.name.endswith('.png'):
            return 'image/png'
        elif self.name.endswith('.txt'):
            return 'text/plain'
        elif self.name.endswith('.json'):
            return 'application/json'
        else:
            return 'application/octet-stream'


@dataclass
class MockContainer:
    """Mock de un contenedor de Azure Storage."""
    name: str
    blobs: Dict[str, MockBlob] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)
    public_access: str = "private"
    
    def add_blob(self, blob: MockBlob):
        """Agregar blob al contenedor."""
        self.blobs[blob.name] = blob
    
    def get_blob(self, name: str) -> Optional[MockBlob]:
        """Obtener blob por nombre."""
        return self.blobs.get(name)
    
    def delete_blob(self, name: str) -> bool:
        """Eliminar blob por nombre."""
        if name in self.blobs:
            del self.blobs[name]
            return True
        return False
    
    def list_blobs(self, name_starts_with: str = None) -> List[MockBlob]:
        """Listar blobs con filtro opcional."""
        blobs = list(self.blobs.values())
        if name_starts_with:
            blobs = [b for b in blobs if b.name.startswith(name_starts_with)]
        return blobs


class MockBlobServiceClient:
    """Mock del cliente de servicio de blobs de Azure Storage."""
    
    def __init__(self, account_url: Optional[str] = None, credential: Optional[str] = None):
        """
        Inicializar mock del cliente de blob service.
        
        Args:
            account_url: URL de la cuenta (ignorada en mock)
            credential: Credencial (ignorada en mock)
        """
        self.account_url = account_url or "https://mockstorage.blob.core.windows.net"
        self.credential = credential or "mock-credential"
        self._containers = self._create_mock_containers()
        
    def _create_mock_containers(self) -> Dict[str, MockContainer]:
        """Crear contenedores mock para testing."""
        containers = {}
        
        # Contenedor principal
        main_container = MockContainer(name="vea-documents")
        
        # Agregar algunos blobs de ejemplo
        sample_blobs = [
            {
                "name": "documents/ai_guide.pdf",
                "content": b"Mock PDF content for AI guide",
                "content_type": "application/pdf"
            },
            {
                "name": "documents/django_guide.pdf", 
                "content": b"Mock PDF content for Django guide",
                "content_type": "application/pdf"
            },
            {
                "name": "images/logo.png",
                "content": b"Mock PNG image content",
                "content_type": "image/png"
            },
            {
                "name": "data/config.json",
                "content": json.dumps({"version": "1.0", "environment": "test"}).encode(),
                "content_type": "application/json"
            },
            {
                "name": "temp/upload_123.txt",
                "content": b"Mock text file content",
                "content_type": "text/plain"
            }
        ]
        
        for blob_data in sample_blobs:
            blob = MockBlob(
                name=blob_data["name"],
                content=blob_data["content"]
            )
            blob.properties.content_type = blob_data["content_type"]
            main_container.add_blob(blob)
        
        containers["vea-documents"] = main_container
        
        # Contenedor de backups
        backup_container = MockContainer(name="vea-backups")
        backup_container.add_blob(MockBlob(
            name="backup_2024_01_15.zip",
            content=b"Mock backup content"
        ))
        containers["vea-backups"] = backup_container
        
        return containers
    
    def get_container_client(self, container_name: str) -> 'MockContainerClient':
        """
        Obtener cliente de contenedor.
        
        Args:
            container_name: Nombre del contenedor
            
        Returns:
            MockContainerClient
        """
        return MockContainerClient(self, container_name)
    
    def get_blob_client(self, container_name: str, blob_name: str) -> 'MockBlobClient':
        """
        Obtener cliente de blob.
        
        Args:
            container_name: Nombre del contenedor
            blob_name: Nombre del blob
            
        Returns:
            MockBlobClient
        """
        return MockBlobClient(self, container_name, blob_name)
    
    def list_containers(self) -> List[Dict[str, Any]]:
        """
        Listar contenedores.
        
        Returns:
            Lista de contenedores
        """
        return [
            {
                "name": name,
                "metadata": container.metadata,
                "public_access": container.public_access
            }
            for name, container in self._containers.items()
        ]


class MockContainerClient:
    """Mock del cliente de contenedor."""
    
    def __init__(self, service_client: MockBlobServiceClient, container_name: str):
        """
        Inicializar mock del cliente de contenedor.
        
        Args:
            service_client: Cliente de servicio
            container_name: Nombre del contenedor
        """
        self.service_client = service_client
        self.container_name = container_name
        self._container = service_client._containers.get(container_name)
        
    def get_blob_client(self, blob_name: str) -> 'MockBlobClient':
        """
        Obtener cliente de blob.
        
        Args:
            blob_name: Nombre del blob
            
        Returns:
            MockBlobClient
        """
        return MockBlobClient(self.service_client, self.container_name, blob_name)
    
    def list_blobs(self, name_starts_with: str = None) -> List[Dict[str, Any]]:
        """
        Listar blobs en el contenedor.
        
        Args:
            name_starts_with: Prefijo para filtrar
            
        Returns:
            Lista de blobs
        """
        if not self._container:
            return []
        
        blobs = self._container.list_blobs(name_starts_with)
        return [
            {
                "name": blob.name,
                "size": blob.properties.size,
                "content_type": blob.properties.content_type,
                "last_modified": blob.properties.last_modified,
                "etag": blob.properties.etag,
                "metadata": blob.properties.metadata
            }
            for blob in blobs
        ]
    
    def upload_blob(self, name: str, data: Union[bytes, str], **kwargs) -> Dict[str, Any]:
        """
        Subir blob al contenedor.
        
        Args:
            name: Nombre del blob
            data: Datos a subir
            **kwargs: Argumentos adicionales
            
        Returns:
            Información del blob subido
        """
        if not self._container:
            raise ValueError(f"Container {self.container_name} not found")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        blob = MockBlob(name=name, content=data)
        blob.properties.content_type = kwargs.get('content_type', 'application/octet-stream')
        blob.properties.metadata = kwargs.get('metadata', {})
        
        self._container.add_blob(blob)
        
        return {
            "name": blob.name,
            "size": blob.properties.size,
            "etag": blob.properties.etag
        }
    
    def delete_blob(self, name: str, **kwargs) -> bool:
        """
        Eliminar blob del contenedor.
        
        Args:
            name: Nombre del blob
            **kwargs: Argumentos adicionales
            
        Returns:
            True si se eliminó, False si no existía
        """
        if not self._container:
            return False
        
        return self._container.delete_blob(name)


class MockBlobClient:
    """Mock del cliente de blob."""
    
    def __init__(self, service_client: MockBlobServiceClient, container_name: str, blob_name: str):
        """
        Inicializar mock del cliente de blob.
        
        Args:
            service_client: Cliente de servicio
            container_name: Nombre del contenedor
            blob_name: Nombre del blob
        """
        self.service_client = service_client
        self.container_name = container_name
        self.blob_name = blob_name
        self._container = service_client._containers.get(container_name)
        
    def get_blob_properties(self) -> Optional[MockBlobProperties]:
        """
        Obtener propiedades del blob.
        
        Returns:
            Propiedades del blob o None si no existe
        """
        if not self._container:
            return None
        
        blob = self._container.get_blob(self.blob_name)
        return blob.properties if blob else None
    
    def download_blob(self) -> MockBlob:
        """
        Descargar blob.
        
        Returns:
            MockBlob con el contenido
            
        Raises:
            ValueError: Si el blob no existe
        """
        if not self._container:
            raise ValueError(f"Container {self.container_name} not found")
        
        blob = self._container.get_blob(self.blob_name)
        if not blob:
            raise ValueError(f"Blob {self.blob_name} not found")
        
        return blob
    
    def upload_blob(self, data: Union[bytes, str], **kwargs) -> Dict[str, Any]:
        """
        Subir blob.
        
        Args:
            data: Datos a subir
            **kwargs: Argumentos adicionales
            
        Returns:
            Información del blob subido
        """
        if not self._container:
            raise ValueError(f"Container {self.container_name} not found")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        blob = MockBlob(name=self.blob_name, content=data)
        blob.properties.content_type = kwargs.get('content_type', 'application/octet-stream')
        blob.properties.metadata = kwargs.get('metadata', {})
        
        self._container.add_blob(blob)
        
        return {
            "name": blob.name,
            "size": blob.properties.size,
            "etag": blob.properties.etag
        }
    
    def delete_blob(self, **kwargs) -> bool:
        """
        Eliminar blob.
        
        Args:
            **kwargs: Argumentos adicionales
            
        Returns:
            True si se eliminó, False si no existía
        """
        if not self._container:
            return False
        
        return self._container.delete_blob(self.blob_name)
    
    def generate_sas(self, permission: str = "r", expiry: datetime = None, **kwargs) -> str:
        """
        Generar SAS token mock.
        
        Args:
            permission: Permisos (r=read, w=write, d=delete)
            expiry: Fecha de expiración
            **kwargs: Argumentos adicionales
            
        Returns:
            SAS token simulado
        """
        if expiry is None:
            expiry = datetime.now() + timedelta(hours=1)
        
        # Generar token SAS simulado
        token_data = {
            "container": self.container_name,
            "blob": self.blob_name,
            "permission": permission,
            "expiry": expiry.isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
        token_json = json.dumps(token_data)
        token_b64 = base64.b64encode(token_json.encode()).decode()
        
        return f"sv=2020-08-04&ss=bfqt&srt=sco&sp={permission}&se={expiry.strftime('%Y-%m-%dT%H:%M:%SZ')}&st={datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}&spr=https&sig={token_b64}"


# Funciones de conveniencia para testing
def create_mock_blob_service_client() -> MockBlobServiceClient:
    """
    Crear cliente mock de blob service.
    
    Returns:
        MockBlobServiceClient configurado para testing
    """
    return MockBlobServiceClient()


def create_mock_container_client(container_name: str = "vea-documents") -> MockContainerClient:
    """
    Crear cliente mock de contenedor.
    
    Args:
        container_name: Nombre del contenedor
        
    Returns:
        MockContainerClient configurado para testing
    """
    service_client = create_mock_blob_service_client()
    return service_client.get_container_client(container_name)


def create_mock_blob_client(container_name: str = "vea-documents", blob_name: str = "test.txt") -> MockBlobClient:
    """
    Crear cliente mock de blob.
    
    Args:
        container_name: Nombre del contenedor
        blob_name: Nombre del blob
        
    Returns:
        MockBlobClient configurado para testing
    """
    service_client = create_mock_blob_service_client()
    return service_client.get_blob_client(container_name, blob_name)


def create_mock_blob(name: str, content: Union[bytes, str], content_type: str = None) -> MockBlob:
    """
    Crear blob mock.
    
    Args:
        name: Nombre del blob
        content: Contenido del blob
        content_type: Tipo de contenido
        
    Returns:
        MockBlob
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    blob = MockBlob(name=name, content=content)
    if content_type:
        blob.properties.content_type = content_type
    
    return blob


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de uso del mock
    service_client = create_mock_blob_service_client()
    
    # Listar contenedores
    containers = service_client.list_containers()
    print(f"Contenedores disponibles: {[c['name'] for c in containers]}")
    
    # Obtener cliente de contenedor
    container_client = service_client.get_container_client("vea-documents")
    
    # Listar blobs
    blobs = container_client.list_blobs()
    print(f"Blobs en contenedor: {len(blobs)}")
    
    # Subir nuevo blob
    result = container_client.upload_blob(
        "test/new_file.txt",
        "Contenido de prueba",
        content_type="text/plain",
        metadata={"test": "true"}
    )
    print(f"Blob subido: {result}")
    
    # Obtener cliente de blob específico
    blob_client = service_client.get_blob_client("vea-documents", "documents/ai_guide.pdf")
    
    # Obtener propiedades
    properties = blob_client.get_blob_properties()
    if properties:
        print(f"Tamaño del archivo: {properties.size} bytes")
    
    # Generar SAS token
    sas_token = blob_client.generate_sas(permission="r")
    print(f"SAS Token: {sas_token[:50]}...")
