"""
VEA Connect - Search Agent
Agente de búsqueda para documentos de la comunidad religiosa usando Semantic Kernel
"""

import os
import re
from typing import List, Dict, Any
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv

load_dotenv()

class SearchAgent:
    """Agente de búsqueda para documentos de VEA Connect"""
    
    def __init__(self):
        """Inicializar el agente de búsqueda"""
        self.search_endpoint = os.getenv('SEARCH_SERVICE_ENDPOINT')
        self.search_key = os.getenv('SEARCH_SERVICE_KEY')
        self.search_index = os.getenv('SEARCH_INDEX_NAME')
        
        if not all([self.search_endpoint, self.search_key, self.search_index]):
            raise ValueError("Faltan variables de entorno para Azure AI Search")
        
        # Crear cliente de búsqueda
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.search_index,
            credential=AzureKeyCredential(self.search_key)
        )
    
    @kernel_function(
        description="Busca documentos de la comunidad religiosa VEA Connect incluyendo eventos, medicamentos, servicios, líderes y donaciones"
    )
    def search_documents(
        self, 
        query: str, 
        category: str = None, 
        max_results: int = 5
    ) -> str:
        """
        Buscar documentos en el índice de VEA Connect
        
        Args:
            query: Consulta de búsqueda
            category: Categoría específica (eventos, medicamentos, servicios, lideres, donaciones)
            max_results: Número máximo de resultados
            
        Returns:
            Resultados de búsqueda formateados
        """
        try:
            # NO usar filtro de categoría porque los documentos no tienen categoría asignada
            # En su lugar, buscar por palabras clave en el contenido
            filter_expression = None
            
            # Realizar búsqueda simple
            search_results = self.search_client.search(
                search_text=query,
                filter=filter_expression,
                top=max_results,
                include_total_count=True,
                select=[
                    "content", "merged_content", "category", "document_type",
                    "metadata_storage_name", "url", "keyphrases", "locations"
                ]
            )
            
            # Formatear resultados de manera más específica
            results = []
            for result in search_results:
                # Usar merged_content si content está vacío
                content = result.get("merged_content") or result.get("content", "")
                
                # Buscar texto relevante que contenga la consulta
                query_lower = query.lower()
                content_lower = content.lower()
                
                # Encontrar la parte más relevante del contenido
                if query_lower in content_lower:
                    # Buscar el contexto alrededor de la palabra clave
                    start_idx = content_lower.find(query_lower)
                    context_start = max(0, start_idx - 100)
                    context_end = min(len(content), start_idx + len(query_lower) + 200)
                    relevant_content = content[context_start:context_end]
                    if context_start > 0:
                        relevant_content = "..." + relevant_content
                    if context_end < len(content):
                        relevant_content = relevant_content + "..."
                else:
                    # Si no encuentra la palabra exacta, tomar el inicio
                    relevant_content = content[:300] + "..." if len(content) > 300 else content
                
                result_dict = {
                    "titulo": result.get("metadata_storage_name", "Sin título").replace(".jpg", "").replace("_", " ").title(),
                    "contenido": relevant_content,
                    "categoria": result.get("category", "documentos"),
                    "tipo_documento": result.get("document_type", "general"),
                    "archivo": result.get("metadata_storage_name", ""),
                    "url": result.get("url", ""),
                    "frases_clave": result.get("keyphrases", []),
                    "ubicaciones": result.get("locations", []),
                    "full_content": content
                }
                results.append(result_dict)
            
            # Si la pregunta es tipo "¿qué es ...?" o similar, devolver definición concisa
            ql = query.lower().strip()
            # Remover signos iniciales como ¿ ¡
            ql = re.sub(r'^[¿¡\s]+', '', ql)
            term = None
            m = re.match(r"^(qué|que|quién|quien)\s+(es|significa)\s+(?P<term>.+)$", ql, flags=re.IGNORECASE)
            if m:
                term = m.group('term').strip(" ?!.:,;")

            if term and results:
                # Elegir el primer documento cuyo contenido contenga el término
                for res in results:
                    text = (res.get("full_content") or res.get("contenido") or "")
                    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
                    selected = None
                    for s in sentences:
                        if term in s.lower():
                            selected = s.strip()
                            break
                    if not selected and sentences:
                        selected = sentences[0].strip()
                    if selected:
                        concise = selected
                        if len(concise) > 280:
                            concise = concise[:277].rstrip() + "..."
                        return concise

            # Formatear respuesta de manera más concisa
            if not results:
                return "No encontré información específica sobre tu consulta. ¿Podrías ser más específico?"
            
            # Si solo hay un resultado, ser más directo (una línea breve)
            if len(results) == 1:
                r = results[0]
                text = (r.get("full_content") or r.get("contenido") or "").strip()
                # Tomar la primera oración
                parts = re.split(r"(?<=[.!?])\s+|\n+", text)
                one_line = parts[0].strip() if parts and parts[0] else text[:200]
                if len(one_line) > 220:
                    one_line = one_line[:217].rstrip() + "..."
                return f"{one_line}"
            
            # Si solo hay un resultado, ser más directo
            if len(results) == 1:
                result = results[0]
                return f"**{result['titulo']}**\n\n{result['contenido']}"
            
            # Si hay múltiples resultados, mostrar los más relevantes
            response = f"Encontré {len(results)} resultado(s):\n\n"
            
            for i, result in enumerate(results[:3], 1):  # Solo mostrar los primeros 3
                response += f"**{i}. {result['titulo']}**\n"
                response += f"{result['contenido']}\n\n"
            
            return response
            
        except Exception as e:
            return f"Error al buscar documentos: {str(e)}"
    
    @kernel_function(
        description="Busca eventos específicos de la comunidad religiosa"
    )
    def search_events(
        self, 
        event_query: str, 
        max_results: int = 3
    ) -> str:
        """
        Buscar eventos específicos
        
        Args:
            event_query: Consulta sobre eventos
            max_results: Número máximo de resultados
            
        Returns:
            Eventos encontrados
        """
        return self.search_documents(
            query=event_query,
            category="eventos",
            max_results=max_results
        )
    
    @kernel_function(
        description="Busca información sobre medicamentos disponibles en la farmacia"
    )
    def search_medications(
        self, 
        medication_query: str, 
        max_results: int = 3
    ) -> str:
        """
        Buscar medicamentos disponibles
        
        Args:
            medication_query: Consulta sobre medicamentos
            max_results: Número máximo de resultados
            
        Returns:
            Medicamentos encontrados
        """
        return self.search_documents(
            query=medication_query,
            category="medicamentos",
            max_results=max_results
        )
    
    @kernel_function(
        description="Busca información sobre líderes de la comunidad religiosa"
    )
    def search_leaders(
        self, 
        leader_query: str, 
        max_results: int = 3
    ) -> str:
        """
        Buscar líderes de la comunidad
        
        Args:
            leader_query: Consulta sobre líderes
            max_results: Número máximo de resultados
            
        Returns:
            Líderes encontrados
        """
        return self.search_documents(
            query=leader_query,
            category="lideres",
            max_results=max_results
        )
    
    @kernel_function(
        description="Busca información sobre servicios y ministerios"
    )
    def search_services(
        self, 
        service_query: str, 
        max_results: int = 3
    ) -> str:
        """
        Buscar servicios y ministerios
        
        Args:
            service_query: Consulta sobre servicios
            max_results: Número máximo de resultados
            
        Returns:
            Servicios encontrados
        """
        return self.search_documents(
            query=service_query,
            category="servicios",
            max_results=max_results
        )
    
    @kernel_function(
        description="Busca información sobre donaciones y ofrendas"
    )
    def search_donations(
        self, 
        donation_query: str, 
        max_results: int = 3
    ) -> str:
        """
        Buscar información sobre donaciones
        
        Args:
            donation_query: Consulta sobre donaciones
            max_results: Número máximo de resultados
            
        Returns:
            Información de donaciones encontrada
        """
        return self.search_documents(
            query=donation_query,
            category="donaciones",
            max_results=max_results
        )

def create_search_agent_plugin(kernel: Kernel) -> None:
    """
    Crear plugin del agente de búsqueda en el kernel
    
    Args:
        kernel: Instancia del Semantic Kernel
    """
    try:
        search_agent = SearchAgent()
        
        # Registrar funciones del agente en el kernel
        kernel.add_plugin(
            search_agent,
            "SearchAgent"
        )
        
        print("Plugin SearchAgent registrado en el kernel")
        
    except Exception as e:
        print(f"Error al crear plugin SearchAgent: {str(e)}")
        raise

# Ejemplo de uso
if __name__ == "__main__":
    from semantic_kernel import Kernel
    
    # Crear kernel
    kernel = Kernel()
    
    # Crear plugin
    create_search_agent_plugin(kernel)
    
    # Ejemplo de búsqueda
    search_agent = SearchAgent()
    result = search_agent.search_documents("eventos de esta semana")
    print(result)
