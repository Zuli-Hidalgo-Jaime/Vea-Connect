import os
import json
import logging
from typing import List, Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from utils.env_utils import get_env

# Variables de entorno obligatorias
ENDPOINT = get_env("AZURE_SEARCH_ENDPOINT")
INDEX = get_env("AZURE_SEARCH_INDEX_NAME")
KEY = get_env("AZURE_SEARCH_KEY")

client = SearchClient(ENDPOINT, INDEX, AzureKeyCredential(KEY))

def search(query: str, top: int):
    result = client.search(
        search_text=query,
        top=top
    )
    return [r for r in result]
