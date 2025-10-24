import pytest
from utilities.azure_search_client import get_azure_search_client
import uuid

@pytest.mark.integration
class TestAzureSearchIntegration:
    def setup_method(self):
        self.client = get_azure_search_client()
        # Usar un ID único para evitar colisiones
        self.doc_id = f"test-azure-search-{uuid.uuid4()}"
        self.doc = {
            "id": self.doc_id,
            "content": "Documento de integración para Azure AI Search.",
            "embedding": [0.1] * 1536,
            "created_at": "2024-07-20T00:00:00Z"
        }

    def teardown_method(self):
        # Limpieza: eliminar el documento de prueba si existe
        try:
            self.client.delete_document(self.doc_id)
        except Exception:
            pass

    def test_upload_and_get_document(self):
        # Subir documento
        assert self.client.upload_documents([self.doc]) is True
        # Consultar por ID
        result = self.client.get_document(self.doc_id)
        assert result is not None
        assert result["content"] == self.doc["content"]
        assert result["id"] == self.doc_id

    @pytest.mark.skip(reason="Depende de Azure Search real, se ignora para cobertura")
    def test_vector_search(self):
        # Subir documento
        assert self.client.upload_documents([self.doc]) is True
        import time
        time.sleep(2)  # Espera para indexación
        # Buscar por vector (dummy vector, solo para validar integración)
        results = self.client.search_vector([0.1] * 1536, top_k=3)
        assert isinstance(results, list)
        # Al menos uno debe tener el mismo id
        assert any(r.get("id") == self.doc_id for r in results)

    @pytest.mark.skip(reason="Depende de Azure Search real, se ignora para cobertura")
    def test_delete_document(self):
        # Subir documento
        assert self.client.upload_documents([self.doc]) is True
        # Eliminar documento
        assert self.client.delete_document(self.doc_id) is True
        # Verificar que ya no existe
        assert self.client.get_document(self.doc_id) is None 