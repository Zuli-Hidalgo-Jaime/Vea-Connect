# API Documentation - VEA Connect

## Overview

VEA Connect es una aplicación web que proporciona servicios de gestión de contactos, eventos, donaciones y un bot de WhatsApp inteligente. Esta documentación describe todas las APIs disponibles.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://veaconnect-webapp-prod.azurewebsites.net`

## Authentication

La aplicación utiliza JWT (JSON Web Tokens) para autenticación.

### Login

```http
POST /api/auth/login/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Refresh Token

```http
POST /api/auth/refresh/
Content-Type: application/json

{
    "refresh": "your_refresh_token"
}
```

## Headers

Para todas las requests autenticadas, incluir:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## Core APIs

### 1. Dashboard

#### Get Dashboard Statistics

```http
GET /api/dashboard/stats/
```

**Response:**
```json
{
    "total_contacts": 150,
    "total_events": 25,
    "total_donations": 50000,
    "recent_activities": [
        {
            "id": 1,
            "type": "contact_created",
            "description": "Nuevo contacto agregado",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    ]
}
```

### 2. Contacts Management

#### List Contacts

```http
GET /api/contacts/
```

**Query Parameters:**
- `search`: Search by name, email, or phone
- `role`: Filter by role
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Response:**
```json
{
    "count": 150,
    "next": "http://api.example.com/contacts/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Juan Pérez",
            "email": "juan@example.com",
            "phone": "+525512345678",
            "role": "member",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

#### Create Contact

```http
POST /api/contacts/
Content-Type: application/json

{
    "name": "María García",
    "email": "maria@example.com",
    "phone": "+525512345679",
    "role": "volunteer",
    "notes": "Interesada en eventos"
}
```

#### Update Contact

```http
PUT /api/contacts/{id}/
Content-Type: application/json

{
    "name": "María García López",
    "email": "maria.garcia@example.com",
    "phone": "+525512345679",
    "role": "leader",
    "notes": "Líder de ministerio de jóvenes"
}
```

#### Delete Contact

```http
DELETE /api/contacts/{id}/
```

### 3. Events Management

#### List Events

```http
GET /api/events/
```

**Query Parameters:**
- `date_from`: Filter events from date (YYYY-MM-DD)
- `date_to`: Filter events to date (YYYY-MM-DD)
- `category`: Filter by category
- `search`: Search by title or description

**Response:**
```json
{
    "count": 25,
    "results": [
        {
            "id": 1,
            "title": "Conferencia de Jóvenes",
            "description": "Evento anual para jóvenes",
            "date": "2024-02-15T18:00:00Z",
            "location": "Auditorio Principal",
            "category": "youth",
            "is_active": true
        }
    ]
}
```

#### Create Event

```http
POST /api/events/
Content-Type: application/json

{
    "title": "Nuevo Evento",
    "description": "Descripción del evento",
    "date": "2024-03-15T18:00:00Z",
    "location": "Sede Principal",
    "category": "general"
}
```

### 4. Donations Management

#### List Donations

```http
GET /api/donations/
```

**Query Parameters:**
- `date_from`: Filter donations from date
- `date_to`: Filter donations to date
- `type`: Filter by donation type
- `amount_min`: Minimum amount
- `amount_max`: Maximum amount

**Response:**
```json
{
    "count": 100,
    "results": [
        {
            "id": 1,
            "amount": 1000.00,
            "type": "tithe",
            "donor_name": "Anónimo",
            "date": "2024-01-15T10:30:00Z",
            "notes": "Diezmo mensual"
        }
    ]
}
```

#### Create Donation

```http
POST /api/donations/
Content-Type: application/json

{
    "amount": 500.00,
    "type": "offering",
    "donor_name": "Juan Pérez",
    "notes": "Ofrenda especial"
}
```

### 5. Documents Management

#### List Documents

```http
GET /api/documents/
```

**Query Parameters:**
- `category`: Filter by category
- `search`: Search by title or description
- `is_processed`: Filter by processing status

**Response:**
```json
{
    "count": 50,
    "results": [
        {
            "id": 1,
            "title": "Manual de Procedimientos",
            "description": "Manual interno de la organización",
            "file": "https://storage.example.com/documents/manual.pdf",
            "category": "procedures",
            "is_processed": true,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

#### Upload Document

```http
POST /api/documents/
Content-Type: multipart/form-data

{
    "title": "Nuevo Documento",
    "description": "Descripción del documento",
    "category": "general",
    "file": <file_upload>
}
```

---

## WhatsApp Bot APIs

### 1. Bot Statistics

#### Get Bot Statistics

```http
GET /api/whatsapp/stats/
```

**Response:**
```json
{
    "total_interactions": 1500,
    "successful_interactions": 1420,
    "success_rate": 94.67,
    "template_usage": 800,
    "fallback_usage": 620,
    "top_templates": [
        {
            "template_name": "vea_contacto_ministerio",
            "count": 150
        }
    ]
}
```

### 2. Message History

#### Get Message History

```http
GET /api/whatsapp/history/{phone_number}/
```

**Response:**
```json
{
    "phone_number": "+525512345678",
    "total_messages": 25,
    "last_interaction": "2024-01-15T10:30:00Z",
    "messages": [
        {
            "id": 1,
            "message": "Hola, necesito información",
            "response": "Gracias por tu mensaje...",
            "intent": "general",
            "success": true,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    ]
}
```

### 3. Send Test Message

#### Send Test Message

```http
POST /api/whatsapp/send-test/
Content-Type: application/json

{
    "phone_number": "+525512345678",
    "message": "Mensaje de prueba"
}
```

**Response:**
```json
{
    "success": true,
    "message_id": "msg_123456",
    "to": "whatsapp:+525512345678"
}
```

---

## Health Check APIs

### 1. Application Health

#### Get Application Health

```http
GET /health/
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "services": {
        "database": "healthy",
        "redis": "healthy",
        "azure_storage": "healthy",
        "whatsapp": "healthy"
    }
}
```

### 2. Detailed Health Check

#### Get Detailed Health

```http
GET /health/detailed/
```

**Response:**
```json
{
    "status": "healthy",
    "uptime_seconds": 86400,
    "memory_usage_percent": 45.2,
    "cpu_usage_percent": 12.5,
    "disk_usage_percent": 23.1,
    "active_connections": 15,
    "services": {
        "database": {
            "status": "healthy",
            "response_time_ms": 45
        },
        "redis": {
            "status": "healthy",
            "response_time_ms": 12
        },
        "azure_storage": {
            "status": "healthy",
            "response_time_ms": 234
        },
        "whatsapp": {
            "status": "healthy",
            "last_message_sent": "2024-01-15T10:25:00Z"
        }
    }
}
```

---

## Performance Monitoring APIs

### 1. Performance Summary

#### Get Performance Summary

```http
GET /api/performance/summary/
```

**Response:**
```json
{
    "uptime_seconds": 86400,
    "metrics_count": 150,
    "system": {
        "system.cpu_percent": {
            "count": 60,
            "min": 5.2,
            "max": 45.8,
            "avg": 15.3,
            "latest": 12.5
        }
    },
    "http": {
        "response_time": {
            "count": 1200,
            "min": 45,
            "max": 2340,
            "avg": 234,
            "latest": 189
        }
    },
    "whatsapp": {
        "operation_duration": {
            "count": 150,
            "min": 120,
            "max": 4500,
            "avg": 890,
            "latest": 756
        }
    }
}
```

### 2. Performance Alerts

#### Get Performance Alerts

```http
GET /api/performance/alerts/
```

**Response:**
```json
[
    {
        "type": "high_cpu_usage",
        "severity": "warning",
        "message": "High CPU usage: 85.2%",
        "value": 85.2,
        "threshold": 80
    }
]
```

---

## Error Responses

### Standard Error Format

```json
{
    "error": "Error description",
    "code": "ERROR_CODE",
    "details": {
        "field": "Additional error details"
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

## Rate Limiting

- **General APIs**: 100 requests per minute
- **WhatsApp APIs**: 10 requests per minute
- **File Upload**: 5 requests per minute

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642234560
```

---

## Webhooks

### WhatsApp Webhook

```http
POST /webhooks/whatsapp/
Content-Type: application/json

{
    "event_type": "Microsoft.Communication.AdvancedMessageReceived",
    "data": {
        "from": "whatsapp:+525512345678",
        "content": "Hola, necesito información"
    }
}
```

### Event Grid Webhook

```http
POST /webhooks/eventgrid/
Content-Type: application/json

{
    "eventType": "Microsoft.Communication.AdvancedMessageReceived",
    "data": {
        "from": "whatsapp:+525512345678",
        "content": "Hola, necesito información"
    }
}
```

---

## SDK Examples

### Python SDK

```python
import requests

# Base configuration
BASE_URL = "https://veaconnect-webapp-prod.azurewebsites.net"
API_TOKEN = "your_api_token"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Get contacts
response = requests.get(f"{BASE_URL}/api/contacts/", headers=headers)
contacts = response.json()

# Create contact
new_contact = {
    "name": "Nuevo Contacto",
    "email": "nuevo@example.com",
    "phone": "+525512345678"
}
response = requests.post(f"{BASE_URL}/api/contacts/", 
                        json=new_contact, headers=headers)
```

### JavaScript SDK

```javascript
const BASE_URL = "https://veaconnect-webapp-prod.azurewebsites.net";
const API_TOKEN = "your_api_token";

const headers = {
    "Authorization": `Bearer ${API_TOKEN}`,
    "Content-Type": "application/json"
};

// Get contacts
fetch(`${BASE_URL}/api/contacts/`, { headers })
    .then(response => response.json())
    .then(contacts => console.log(contacts));

// Create contact
const newContact = {
    name: "Nuevo Contacto",
    email: "nuevo@example.com",
    phone: "+525512345678"
};

fetch(`${BASE_URL}/api/contacts/`, {
    method: "POST",
    headers,
    body: JSON.stringify(newContact)
})
.then(response => response.json())
.then(result => console.log(result));
```

---

## Support

Para soporte técnico o preguntas sobre las APIs:

- **Email**: support@veaconnect.com
- **Documentation**: https://docs.veaconnect.com
- **GitHub Issues**: https://github.com/veaconnect/webapp/issues

---

## Changelog

### Version 1.0.0 (2024-01-15)
- Initial API release
- Core CRUD operations for contacts, events, donations
- WhatsApp bot integration
- Performance monitoring
- Health check endpoints 