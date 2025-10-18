import os
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential

def get_openai_client():
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_EMBEDDINGS_API_VERSION"),
    )

def get_search_client(index_name: str):
    return SearchClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=index_name,
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")),
    )
