"""
Ejemplo de Uso del Canary de Ingesta - VEA Connect

Este script demuestra cómo usar el canary de ingesta para procesar documentos
sin afectar el pipeline de producción.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def create_test_documents():
    """Crear documentos de prueba para el canary."""
    test_dir = Path("test_canary_documents")
    test_dir.mkdir(exist_ok=True)
    
    # Crear archivo de texto simulado
    text_content = """
    Documento de Prueba - Donaciones Ministeriales
    
    Este documento describe los procesos de donaciones para ministerios gubernamentales.
    Incluye información sobre requisitos, procedimientos y contactos necesarios.
    
    Requisitos para Donaciones:
    1. Formulario de solicitud completo
    2. Documentación de identidad
    3. Justificación del proyecto
    4. Presupuesto detallado
    
    Contactos:
    - Email: donaciones@ministerio.gob.pe
    - Teléfono: (01) 123-4567
    - Horario: Lunes a Viernes 8:00 - 17:00
    
    Proceso de Aprobación:
    1. Revisión inicial (5 días hábiles)
    2. Evaluación técnica (10 días hábiles)
    3. Aprobación final (3 días hábiles)
    4. Notificación al solicitante
    
    Este proceso asegura que las donaciones se manejen de manera transparente
    y eficiente, beneficiando a la comunidad en general.
    """
    
    # Crear archivo de texto
    text_file = test_dir / "documento_prueba.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    # Crear archivo PDF simulado (contenido de texto)
    pdf_content = """
    Guía de Eventos Comunitarios
    
    Esta guía proporciona información completa para la organización
    de eventos comunitarios exitosos.
    
    Planificación del Evento:
    - Definir objetivos y público objetivo
    - Establecer presupuesto
    - Seleccionar fecha y ubicación
    - Coordinar con autoridades locales
    
    Checklist de Organización:
    □ Permisos y licencias
    □ Seguridad y primeros auxilios
    □ Logística y equipamiento
    □ Comunicación y marketing
    □ Voluntarios y personal
    
    Presupuesto Estimado:
    - Alquiler de espacio: $500
    - Equipamiento: $300
    - Marketing: $200
    - Seguridad: $150
    - Contingencia: $100
    Total: $1,250
    
    Mejores Prácticas:
    1. Comenzar la planificación con anticipación
    2. Involucrar a la comunidad desde el inicio
    3. Mantener comunicación clara y frecuente
    4. Tener planes de contingencia
    5. Evaluar y documentar lecciones aprendidas
    """
    
    # Crear archivo PDF simulado
    pdf_file = test_dir / "guia_eventos.pdf"
    with open(pdf_file, 'w', encoding='utf-8') as f:
        f.write(pdf_content)
    
    # Crear archivo de imagen simulado
    image_content = """
    Manual de Contactos de Emergencia
    
    Lista completa de contactos de emergencia para diferentes situaciones.
    
    Emergencias Médicas:
    - Ambulancia: 116
    - Cruz Roja: (01) 265-8787
    - Hospital más cercano: (01) 234-5678
    
    Emergencias de Seguridad:
    - Policía: 105
    - Bomberos: 116
    - Defensa Civil: 119
    
    Emergencias Eléctricas:
    - Compañía eléctrica: (01) 345-6789
    - Servicio técnico: (01) 456-7890
    
    Protocolos de Emergencia:
    1. Mantener la calma
    2. Evaluar la situación
    3. Llamar al número correspondiente
    4. Proporcionar información clara
    5. Seguir instrucciones del operador
    
    Información a Proporcionar:
    - Tipo de emergencia
    - Ubicación exacta
    - Número de personas afectadas
    - Condiciones actuales
    - Nombre y teléfono del reportante
    """
    
    # Crear archivo de imagen simulado
    image_file = test_dir / "contactos_emergencia.jpg"
    with open(image_file, 'w', encoding='utf-8') as f:
        f.write(image_content)
    
    print(f"✅ Documentos de prueba creados en: {test_dir}")
    print(f"   - {text_file.name}")
    print(f"   - {pdf_file.name}")
    print(f"   - {image_file.name}")
    
    return test_dir

def run_canary_ingestion(test_dir):
    """Ejecutar el canary de ingesta."""
    print("\n🚀 Ejecutando Canary de Ingesta")
    print("=" * 50)
    
    # Verificar si el canary está habilitado
    if not os.getenv('CANARY_INGEST_ENABLED'):
        print("⚠️ Canary no está habilitado. Configurando...")
        os.environ['CANARY_INGEST_ENABLED'] = 'True'
    
    # Ejecutar comando de ingesta
    import subprocess
    
    cmd = [
        'python', 'manage.py', 'ingest_canary',
        '--path', str(test_dir),
        '--chunk-size', '800',
        '--overlap', '150',
        '--output-format', 'summary',
        '--verbose'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        print("📋 Salida del Canary:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Errores:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error ejecutando canary: {e}")

def run_hybrid_search_canary():
    """Ejecutar el canary de búsqueda híbrida."""
    print("\n🔍 Ejecutando Canary de Búsqueda Híbrida")
    print("=" * 50)
    
    # Ejecutar script de búsqueda híbrida
    import subprocess
    
    cmd = ['python', 'scripts/search/hybrid_canary.py']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        print("📋 Salida del Canary de Búsqueda:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Errores:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error ejecutando canary de búsqueda: {e}")

def cleanup_test_documents(test_dir):
    """Limpiar documentos de prueba."""
    try:
        shutil.rmtree(test_dir)
        print(f"\n🧹 Documentos de prueba eliminados: {test_dir}")
    except Exception as e:
        print(f"⚠️ Error eliminando documentos de prueba: {e}")

def main():
    """Función principal del ejemplo."""
    print("🧪 Ejemplo de Canary de Ingesta y Búsqueda Híbrida")
    print("=" * 60)
    
    # Crear documentos de prueba
    test_dir = create_test_documents()
    
    try:
        # Ejecutar canary de ingesta
        run_canary_ingestion(test_dir)
        
        # Ejecutar canary de búsqueda híbrida
        run_hybrid_search_canary()
        
    finally:
        # Limpiar documentos de prueba
        cleanup_test_documents(test_dir)
    
    print("\n✅ Ejemplo completado")
    print("\n💡 Para usar con documentos reales:")
    print("   1. Configurar variables de entorno")
    print("   2. Crear carpeta con documentos reales")
    print("   3. Ejecutar: python manage.py ingest_canary --path /ruta/documentos")
    print("   4. Ejecutar: python scripts/search/hybrid_canary.py")

if __name__ == "__main__":
    main()

