import json
import os
import sys
import requests

WEBHOOK_URL = os.environ.get(
    "WEBAPP_WHATSAPP_WEBHOOK_URL",
    "https://vea-webapp-prod.azurewebsites.net/api/v1/whatsapp/webhook/",
)

def main() -> int:
    payload = {
        "from": "whatsapp:+520000000000",
        "to": "whatsapp:+520000000001",
        "message": {"text": "Prueba RAG desde proxy"},
        "timestamp": "2025-10-19T12:00:00Z",
    }
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"ERR: {e}")
        return 2
    print(f"status={resp.status_code}")
    try:
        print(resp.json())
    except Exception:
        print(resp.text[:500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())




