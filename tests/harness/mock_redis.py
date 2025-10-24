"""
Mock puro de Redis para testing sin dependencias de Django.

Este módulo proporciona mocks de las funciones principales de Redis
para testing aislado sin necesidad de configuración de Django.
"""

import json
import time
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class MockRedisValue:
    """Mock de un valor en Redis."""
    value: Any
    ttl: Optional[int] = None
    created_at: float = None
    namespace: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def is_expired(self) -> bool:
        """Verificar si el valor ha expirado."""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)
    
    def get_remaining_ttl(self) -> Optional[int]:
        """Obtener TTL restante en segundos."""
        if self.ttl is None:
            return None
        remaining = (self.created_at + self.ttl) - time.time()
        return max(0, int(remaining))


class MockRedis:
    """Mock de Redis para testing."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, **kwargs):
        """
        Inicializar mock de Redis.
        
        Args:
            host: Host de Redis (ignorado en mock)
            port: Puerto de Redis (ignorado en mock)
            db: Base de datos (ignorado en mock)
            **kwargs: Argumentos adicionales (ignorados)
        """
        self.host = host
        self.port = port
        self.db = db
        self._data: Dict[str, MockRedisValue] = {}
        self._connection_available = True
        self._simulate_timeout = False
        self._timeout_probability = 0.0  # 0.0 = nunca, 1.0 = siempre
        
    def _get_full_key(self, key: str, namespace: str = "") -> str:
        """Obtener clave completa con namespace."""
        if namespace:
            return f"{namespace}:{key}"
        return key
    
    def _cleanup_expired(self):
        """Limpiar valores expirados."""
        expired_keys = [
            key for key, value in self._data.items()
            if value.is_expired()
        ]
        for key in expired_keys:
            del self._data[key]
    
    def _simulate_connection_issue(self) -> bool:
        """Simular problemas de conexión."""
        if not self._connection_available:
            return True
        
        if self._simulate_timeout:
            return True
        
        if self._timeout_probability > 0:
            import random
            if random.random() < self._timeout_probability:
                return True
        
        return False
    
    def set(self, key: str, value: Any, ex: Optional[int] = None, nx: bool = False, xx: bool = False, **kwargs) -> bool:
        """
        Establecer valor en Redis.
        
        Args:
            key: Clave
            value: Valor a almacenar
            ex: TTL en segundos
            nx: Solo si no existe
            xx: Solo si existe
            **kwargs: Argumentos adicionales
            
        Returns:
            True si se estableció correctamente
        """
        if self._simulate_connection_issue():
            return False
        
        self._cleanup_expired()
        
        full_key = self._get_full_key(key)
        
        # Verificar condiciones nx/xx
        if nx and full_key in self._data:
            return False
        if xx and full_key not in self._data:
            return False
        
        # Serializar valor si es necesario
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif not isinstance(value, (str, bytes, int, float)):
            value = str(value)
        
        self._data[full_key] = MockRedisValue(
            value=value,
            ttl=ex
        )
        
        return True
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor de Redis.
        
        Args:
            key: Clave
            
        Returns:
            Valor o None si no existe o expiró
        """
        if self._simulate_connection_issue():
            return None
        
        self._cleanup_expired()
        
        full_key = self._get_full_key(key)
        value_obj = self._data.get(full_key)
        
        if value_obj is None or value_obj.is_expired():
            return None
        
        # Intentar deserializar JSON si es posible
        if isinstance(value_obj.value, str):
            try:
                return json.loads(value_obj.value)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return value_obj.value
    
    def delete(self, *keys: str) -> int:
        """
        Eliminar claves de Redis.
        
        Args:
            *keys: Claves a eliminar
            
        Returns:
            Número de claves eliminadas
        """
        if self._simulate_connection_issue():
            return 0
        
        deleted_count = 0
        for key in keys:
            full_key = self._get_full_key(key)
            if full_key in self._data:
                del self._data[full_key]
                deleted_count += 1
        
        return deleted_count
    
    def exists(self, *keys: str) -> int:
        """
        Verificar si existen claves.
        
        Args:
            *keys: Claves a verificar
            
        Returns:
            Número de claves que existen
        """
        if self._simulate_connection_issue():
            return 0
        
        self._cleanup_expired()
        
        existing_count = 0
        for key in keys:
            full_key = self._get_full_key(key)
            if full_key in self._data and not self._data[full_key].is_expired():
                existing_count += 1
        
        return existing_count
    
    def ttl(self, key: str) -> int:
        """
        Obtener TTL de una clave.
        
        Args:
            key: Clave
            
        Returns:
            TTL en segundos, -1 si no tiene TTL, -2 si no existe
        """
        if self._simulate_connection_issue():
            return -2
        
        self._cleanup_expired()
        
        full_key = self._get_full_key(key)
        value_obj = self._data.get(full_key)
        
        if value_obj is None or value_obj.is_expired():
            return -2
        
        remaining = value_obj.get_remaining_ttl()
        return remaining if remaining is not None else -1
    
    def expire(self, key: str, time: int) -> bool:
        """
        Establecer TTL para una clave.
        
        Args:
            key: Clave
            time: TTL en segundos
            
        Returns:
            True si se estableció correctamente
        """
        if self._simulate_connection_issue():
            return False
        
        full_key = self._get_full_key(key)
        if full_key not in self._data:
            return False
        
        self._data[full_key].ttl = time
        self._data[full_key].created_at = time.time()
        return True
    
    def keys(self, pattern: str = "*") -> List[str]:
        """
        Buscar claves por patrón.
        
        Args:
            pattern: Patrón de búsqueda (solo soporta * al final)
            
        Returns:
            Lista de claves que coinciden
        """
        if self._simulate_connection_issue():
            return []
        
        self._cleanup_expired()
        
        matching_keys = []
        for key in self._data.keys():
            if not self._data[key].is_expired():
                if pattern == "*" or key.startswith(pattern.rstrip("*")):
                    matching_keys.append(key)
        
        return matching_keys
    
    def flushdb(self) -> bool:
        """
        Limpiar toda la base de datos.
        
        Returns:
            True si se limpió correctamente
        """
        if self._simulate_connection_issue():
            return False
        
        self._data.clear()
        return True
    
    def ping(self) -> bool:
        """
        Verificar conectividad.
        
        Returns:
            True si Redis está disponible
        """
        return self._connection_available and not self._simulate_timeout
    
    def info(self, section: str = None) -> Dict[str, Any]:
        """
        Obtener información del servidor.
        
        Args:
            section: Sección específica (ignorada en mock)
            
        Returns:
            Información simulada del servidor
        """
        if self._simulate_connection_issue():
            return {}
        
        return {
            "redis_version": "6.2.0",
            "connected_clients": 1,
            "used_memory": len(self._data) * 100,  # Simulado
            "total_commands_processed": 0,
            "keyspace_hits": 0,
            "keyspace_misses": 0
        }
    
    # Métodos específicos para el proyecto VEA
    def get_emb(self, text: str) -> Optional[List[float]]:
        """
        Obtener embedding cacheado.
        
        Args:
            text: Texto para buscar embedding
            
        Returns:
            Embedding o None si no existe
        """
        key = f"vea:emb:{hashlib.md5(text.encode()).hexdigest()}"
        return self.get(key)
    
    def set_emb(self, text: str, embedding: List[float], ttl: int = 3600) -> bool:
        """
        Cachear embedding.
        
        Args:
            text: Texto
            embedding: Embedding a cachear
            ttl: TTL en segundos
            
        Returns:
            True si se cacheó correctamente
        """
        key = f"vea:emb:{hashlib.md5(text.encode()).hexdigest()}"
        return self.set(key, embedding, ex=ttl)
    
    def get_ans(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Obtener respuesta de AI Search cacheada.
        
        Args:
            query: Query de búsqueda
            
        Returns:
            Respuesta o None si no existe
        """
        key = f"vea:ans:{hashlib.md5(query.encode()).hexdigest()}"
        return self.get(key)
    
    def set_ans(self, query: str, response: Dict[str, Any], ttl: int = 1800) -> bool:
        """
        Cachear respuesta de AI Search.
        
        Args:
            query: Query de búsqueda
            response: Respuesta a cachear
            ttl: TTL en segundos
            
        Returns:
            True si se cacheó correctamente
        """
        key = f"vea:ans:{hashlib.md5(query.encode()).hexdigest()}"
        return self.set(key, response, ex=ttl)
    
    def get_sas(self, blob_path: str) -> Optional[str]:
        """
        Obtener SAS token cacheado.
        
        Args:
            blob_path: Ruta del blob
            
        Returns:
            SAS token o None si no existe
        """
        key = f"vea:sas:{hashlib.md5(blob_path.encode()).hexdigest()}"
        return self.get(key)
    
    def set_sas(self, blob_path: str, sas_token: str, ttl: int = 300) -> bool:
        """
        Cachear SAS token.
        
        Args:
            blob_path: Ruta del blob
            sas_token: SAS token a cachear
            ttl: TTL en segundos
            
        Returns:
            True si se cacheó correctamente
        """
        key = f"vea:sas:{hashlib.md5(blob_path.encode()).hexdigest()}"
        return self.set(key, sas_token, ex=ttl)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del cache.
        
        Returns:
            Estadísticas del cache
        """
        if self._simulate_connection_issue():
            return {}
        
        self._cleanup_expired()
        
        stats = {
            "total_keys": len(self._data),
            "namespaces": {},
            "memory_usage": len(self._data) * 100,  # Simulado
            "uptime": int(time.time() - 1000000),  # Simulado
        }
        
        # Contar por namespace
        for key, value in self._data.items():
            if not value.is_expired():
                namespace = key.split(":")[0] if ":" in key else "default"
                if namespace not in stats["namespaces"]:
                    stats["namespaces"][namespace] = 0
                stats["namespaces"][namespace] += 1
        
        return stats
    
    def clear_cache(self, namespace: str = None) -> int:
        """
        Limpiar cache por namespace.
        
        Args:
            namespace: Namespace específico o None para limpiar todo
            
        Returns:
            Número de claves eliminadas
        """
        if self._simulate_connection_issue():
            return 0
        
        if namespace is None:
            return self.flushdb()
        
        keys_to_delete = []
        for key in self._data.keys():
            if key.startswith(f"{namespace}:"):
                keys_to_delete.append(key)
        
        return self.delete(*keys_to_delete)
    
    # Métodos para simular problemas de conexión
    def simulate_connection_failure(self, available: bool = False):
        """Simular fallo de conexión."""
        self._connection_available = available
    
    def simulate_timeout(self, timeout: bool = True):
        """Simular timeout."""
        self._simulate_timeout = timeout
    
    def set_timeout_probability(self, probability: float):
        """Establecer probabilidad de timeout (0.0 a 1.0)."""
        self._timeout_probability = max(0.0, min(1.0, probability))


# Funciones de conveniencia para testing
def create_mock_redis_client() -> MockRedis:
    """
    Crear cliente mock de Redis.
    
    Returns:
        MockRedis configurado para testing
    """
    return MockRedis()


def create_mock_redis_with_data(data: Dict[str, Any]) -> MockRedis:
    """
    Crear cliente mock de Redis con datos predefinidos.
    
    Args:
        data: Diccionario con datos iniciales
        
    Returns:
        MockRedis con datos cargados
    """
    client = MockRedis()
    for key, value in data.items():
        client.set(key, value)
    return client


def create_mock_redis_unavailable() -> MockRedis:
    """
    Crear cliente mock de Redis no disponible.
    
    Returns:
        MockRedis configurado para simular fallos
    """
    client = MockRedis()
    client.simulate_connection_failure(available=False)
    return client


def create_mock_redis_with_timeouts(probability: float = 0.3) -> MockRedis:
    """
    Crear cliente mock de Redis con timeouts intermitentes.
    
    Args:
        probability: Probabilidad de timeout (0.0 a 1.0)
        
    Returns:
        MockRedis configurado para simular timeouts
    """
    client = MockRedis()
    client.set_timeout_probability(probability)
    return client


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de uso del mock
    redis_client = create_mock_redis_client()
    
    # Probar operaciones básicas
    redis_client.set("test:key", "test_value", ex=60)
    value = redis_client.get("test:key")
    print(f"Valor obtenido: {value}")
    
    # Probar cache de embeddings
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    redis_client.set_emb("Hola mundo", embedding)
    cached_embedding = redis_client.get_emb("Hola mundo")
    print(f"Embedding cacheado: {cached_embedding}")
    
    # Probar cache de respuestas
    response = {"results": [{"id": "1", "content": "test"}], "total": 1}
    redis_client.set_ans("query test", response)
    cached_response = redis_client.get_ans("query test")
    print(f"Respuesta cacheada: {cached_response}")
    
    # Probar estadísticas
    stats = redis_client.get_cache_stats()
    print(f"Estadísticas: {stats}")
    
    # Probar limpieza
    deleted = redis_client.clear_cache("vea")
    print(f"Claves eliminadas: {deleted}")
