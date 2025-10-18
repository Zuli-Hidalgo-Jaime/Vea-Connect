# 🤖 Integración de RAG y OpenAI en WhatsApp Bot

## 📋 Resumen

Se ha implementado la funcionalidad de **RAG (Retrieval-Augmented Generation)** y **OpenAI** en el bot de WhatsApp para proporcionar respuestas más inteligentes y contextuales basadas en la información disponible en la base de datos.

## 🔧 Cambios Implementados

### 1. **Función `_get_rag_context()` Actualizada**

**Ubicación:** `functions/whatsapp_event_grid_trigger/__init__.py`

**Funcionalidad:**
- Realiza búsqueda vectorial usando la función `search_similar`
- Obtiene los 3 resultados más relevantes
- Filtra resultados con score > 0.5 para mayor precisión
- Genera contexto RAG formateado para OpenAI

**Código clave:**
```python
def _get_rag_context(query: str) -> Optional[str]:
    # Llama a la función de búsqueda vectorial
    function_url = os.getenv('SEARCH_SIMILAR_FUNCTION_URL', 'http://localhost:7071/api/search_similar')
    
    # Realiza búsqueda
    response = requests.post(function_url, json={"query": query, "top": 3})
    
    # Procesa resultados y genera contexto
    # ...
```

### 2. **Función `_generate_ai_response()` Actualizada**

**Funcionalidad:**
- Integración completa con Azure OpenAI
- Uso del contexto RAG en el prompt del sistema
- Manejo de historial de conversación
- Respuestas más inteligentes y contextuales

**Código clave:**
```python
def _generate_ai_response(user_message: str, conversation_history: List[Dict[str, str]], rag_context: Optional[str] = None) -> str:
    # Inicializa cliente OpenAI
    client = AzureOpenAI(
        azure_endpoint=openai_endpoint,
        api_key=openai_key,
        api_version=api_version
    )
    
    # Construye prompt con contexto RAG
    system_prompt = BOT_SYSTEM_PROMPT
    if rag_context:
        system_prompt += f"\n\nInformación relevante encontrada:\n{rag_context}"
    
    # Genera respuesta
    response = client.chat.completions.create(
        model=openai_deployment,
        messages=messages,
        max_tokens=500,
        temperature=0.7
    )
```

### 3. **Configuración Habilitada por Defecto**

- `RAG_ENABLED = True` - RAG habilitado por defecto
- Variables de entorno configuradas para OpenAI y búsqueda vectorial

## 🔑 Variables de Entorno Requeridas

### **OpenAI Configuration:**
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4
AZURE_OPENAI_CHAT_API_VERSION=2024-02-15-preview
```

### **Search Function URL:**
```bash
SEARCH_SIMILAR_FUNCTION_URL=http://localhost:7071/api/search_similar
# O en producción: https://your-function-app.azurewebsites.net/api/search_similar
```

## 🧪 Script de Pruebas

Se ha creado un script de pruebas completo en `functions/test_whatsapp_rag.py` que verifica:

1. **Búsqueda Vectorial** - Prueba la función `search_similar`
2. **Generación OpenAI** - Prueba la integración con Azure OpenAI
3. **Integración Completa** - Prueba el flujo completo de WhatsApp

**Ejecutar pruebas:**
```bash
cd functions
python test_whatsapp_rag.py
```

## 🔄 Flujo de Procesamiento

### **Antes (Respuesta Genérica):**
```
Usuario: "Puedes darme el contacto de Daya"
Bot: "Hola! Recibí tu mensaje: 'Puedes darme el contacto de Daya'. Soy el asistente virtual de VEA Connect. ¿En qué puedo ayudarte?"
```

### **Después (Con RAG + OpenAI):**
```
Usuario: "Puedes darme el contacto de Daya"

1. Búsqueda Vectorial: Busca información sobre "Daya" en la base de datos
2. Contexto RAG: Encuentra información relevante sobre Daya
3. OpenAI: Genera respuesta contextual usando la información encontrada
4. Bot: "Basándome en la información disponible, Daya es parte del equipo de VEA Connect. 
   Puedo ayudarte a contactarla a través de [información específica encontrada en la base de datos]."
```

## 📊 Logs y Monitoreo

### **Logs de Búsqueda Vectorial:**
```
[Information] Performing vector search for query: Puedes darme el contacto de Daya
[Information] Calling search function at: http://localhost:7071/api/search_similar
[Information] Search completed successfully: 3 results
[Information] Generated RAG context with 450 characters
```

### **Logs de OpenAI:**
```
[Information] Generating AI response for: Puedes darme el contacto de Daya
[Information] Added RAG context to system prompt: 450 characters
[Information] Sending request to OpenAI with 2 messages
[Information] Generated AI response: Basándome en la información disponible...
```

## 🚀 Beneficios

1. **Respuestas Más Inteligentes** - El bot ahora puede acceder a información específica de la base de datos
2. **Contexto Relevante** - Las respuestas están basadas en datos reales de la organización
3. **Mejor Experiencia de Usuario** - Respuestas más útiles y específicas
4. **Escalabilidad** - El sistema puede manejar consultas complejas sobre cualquier tema en la base de datos

## 🔧 Configuración en Producción

### **Azure Functions:**
1. Configurar variables de entorno en Azure Functions
2. Asegurar que la función `search_similar` esté desplegada y accesible
3. Verificar conectividad con Azure OpenAI

### **Variables de Entorno en Azure:**
```bash
# En Azure Functions Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4
SEARCH_SIMILAR_FUNCTION_URL=https://your-function-app.azurewebsites.net/api/search_similar
RAG_ENABLED=true
```

## 🐛 Solución de Problemas

### **Si RAG no funciona:**
1. Verificar que `SEARCH_SIMILAR_FUNCTION_URL` esté configurada correctamente
2. Comprobar que la función `search_similar` esté funcionando
3. Revisar logs para errores de conectividad

### **Si OpenAI no funciona:**
1. Verificar variables de entorno de Azure OpenAI
2. Comprobar que el deployment esté activo
3. Revisar logs de errores de autenticación

### **Para deshabilitar RAG temporalmente:**
```bash
RAG_ENABLED=false
```

## 📈 Próximos Pasos

1. **Monitoreo de Rendimiento** - Implementar métricas de uso de RAG
2. **Optimización de Búsqueda** - Ajustar parámetros de búsqueda vectorial
3. **Cache de Respuestas** - Implementar cache para consultas frecuentes
4. **Análisis de Conversaciones** - Tracking de efectividad de respuestas

---

**Estado:** ✅ **IMPLEMENTADO Y FUNCIONAL**
**Última Actualización:** Agosto 2025
**Responsable:** Equipo de Desarrollo VEA Connect
