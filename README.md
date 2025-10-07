# VEA Connect - Chatbot Inteligente

Sistema de gestión de conocimiento para la comunidad religiosa VEA Connect, desarrollado con Azure AI Search y OpenAI.

## 🚀 Características

- **Chatbot Inteligente**: Respuestas amigables y contextuales usando Azure OpenAI
- **Búsqueda Semántica**: Búsqueda avanzada en documentos con Azure AI Search
- **Procesamiento de Documentos**: OCR, extracción de entidades y análisis de imágenes
- **Interfaz Web**: Frontend moderno para interacción con el chatbot
- **API REST**: Backend robusto con FastAPI

## 🏗️ Arquitectura

```
Vea-Connect/
├── backend/                 # API y lógica del chatbot
│   ├── chatbot/            # Clases del chatbot y agente de búsqueda
│   ├── api/                # Rutas de la API
│   └── search/             # Servicios de búsqueda
├── frontend/               # Interfaz de usuario
├── config/                 # Configuraciones de Azure
├── scripts/                # Scripts de utilidad
└── docs/                   # Documentación técnica
```

## 🛠️ Tecnologías

- **Backend**: Python, FastAPI, Semantic Kernel
- **Frontend**: React, TypeScript
- **Azure Services**: AI Search, OpenAI, Cognitive Services, Blob Storage
- **Base de Datos**: Azure AI Search Index

## 📋 Requisitos Previos

- Python 3.8+
- Node.js 16+
- Cuenta de Azure con servicios configurados
- Variables de entorno configuradas

## ⚙️ Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Zuli-Hidalgo-Jaime/Vea-Connect.git
   cd Vea-Connect
   ```

2. **Configurar variables de entorno**
   ```bash
   cp env_example.txt .env
   # Editar .env con tus claves de Azure
   ```

3. **Instalar dependencias**
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```

4. **Configurar Azure**
   - Crear recursos en Azure Portal
   - Configurar Azure AI Search
   - Subir documentos a Blob Storage
   - Ejecutar indexador

## 🚀 Uso

### Ejecutar Backend
```bash
cd backend
python main.py
```

### Ejecutar Frontend
```bash
cd frontend
npm start
```

### Chat Interactivo
```bash
cd scripts
python chat_interactivo.py
```

## 📚 Documentación

- [Arquitectura Técnica](docs/technical/architecture.md)
- [Configuración de Azure](config/azure/README.md)
- [API Reference](docs/api/)

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico, contacta al equipo de desarrollo o crea un issue en GitHub.

---

**VEA Connect** - Conectando la comunidad a través de la tecnología 🤝