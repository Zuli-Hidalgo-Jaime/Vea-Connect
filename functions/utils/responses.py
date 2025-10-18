import json
import azure.functions as func
from typing import Union, Dict, List, Any

def create_response(payload: Union[Dict[str, Any], List[Any]], status_code: int = 200) -> func.HttpResponse:
    """
    Create a standard HTTP response compatible with Azure Functions.
    This function always returns a func.HttpResponse object.
    """
    return func.HttpResponse(
        body=json.dumps(payload, ensure_ascii=False, default=str),
        status_code=status_code,
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
        }
    )
