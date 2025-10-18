#!/usr/bin/env python3
"""
Storage Consistency Checker

Este script verifica la consistencia del almacenamiento de Azure Blob Storage
sin modificar la base de datos. Genera reportes de inconsistencias y ofrece
opciones para reconstruir el manifiesto.

Uso:
    python storage_consistency_check.py [--rebuild-manifest] [--output-format csv|markdown]
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.storage_service import AzureStorageService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StorageConsistencyChecker:
    """Verificador de consistencia del almacenamiento."""
    
    def __init__(self, storage_service: AzureStorageService):
        self.storage = storage_service
        self.container_name = storage_service.container_name
        
    def build_in_memory_index(self) -> Dict[str, Dict]:
        """
        Construye un índice en memoria de todos los blobs.
        
        Returns:
            Diccionario con índices por blob_name y original_name
        """
        logger.info("Construyendo índice en memoria...")
        
        index = {
            'by_blob_name': {},
            'by_original_name': defaultdict(list),
            'by_category': defaultdict(list),
            'manifest_entries': {},
            'stats': {
                'total_blobs': 0,
                'with_metadata': 0,
                'with_original_name': 0,
                'by_category': defaultdict(int)
            }
        }
        
        try:
            # Listar todos los blobs
            result = self.storage.list_blobs(
                container_name=self.container_name,
                max_results=10000  # Ajustar según necesidad
            )
            
            if not result['success']:
                logger.error(f"Error al listar blobs: {result['error']}")
                return index
            
            for blob_info in result['blobs']:
                blob_name = blob_info['name']
                index['by_blob_name'][blob_name] = blob_info
                index['stats']['total_blobs'] += 1
                
                # Obtener metadatos del blob
                try:
                    blob_client = self.storage.client.get_blob_client(
                        container=self.container_name, 
                        blob=blob_name
                    )
                    properties = blob_client.get_blob_properties()
                    
                    if properties.metadata:
                        index['stats']['with_metadata'] += 1
                        
                        original_name = properties.metadata.get('original_name')
                        category = properties.metadata.get('category', '')
                        
                        if original_name:
                            index['stats']['with_original_name'] += 1
                            original_name_lower = original_name.lower()
                            index['by_original_name'][original_name_lower].append({
                                'blob_name': blob_name,
                                'category': category,
                                'size': blob_info['size'],
                                'last_modified': blob_info['last_modified']
                            })
                        
                        if category:
                            index['stats']['by_category'][category] += 1
                            index['by_category'][category].append({
                                'blob_name': blob_name,
                                'original_name': original_name,
                                'size': blob_info['size']
                            })
                
                except Exception as e:
                    logger.warning(f"Error al obtener metadatos de {blob_name}: {e}")
            
            # Cargar manifiesto si existe
            index['manifest_entries'] = self._load_manifest()
            
            logger.info(f"Índice construido: {index['stats']['total_blobs']} blobs procesados")
            
        except Exception as e:
            logger.error(f"Error al construir índice: {e}")
        
        return index
    
    def _load_manifest(self) -> Dict:
        """Carga el manifiesto desde el almacenamiento."""
        try:
            manifest_blob = self.storage.client.get_blob_client(
                container=self.container_name, 
                blob="__manifest/manifest.json"
            )
            
            if manifest_blob.exists():
                manifest_data = manifest_blob.download_blob().readall()
                return json.loads(manifest_data.decode('utf-8'))
        
        except Exception as e:
            logger.warning(f"Error al cargar manifiesto: {e}")
        
        return {}
    
    def analyze_consistency(self, index: Dict) -> Dict:
        """
        Analiza la consistencia del almacenamiento.
        
        Args:
            index: Índice en memoria del almacenamiento
            
        Returns:
            Reporte de análisis
        """
        logger.info("Analizando consistencia...")
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'container': self.container_name,
            'issues': {
                'stale_manifest_entries': [],
                'duplicate_original_names': [],
                'missing_metadata': [],
                'orphaned_blobs': []
            },
            'stats': index['stats'],
            'recommendations': []
        }
        
        # 1. Verificar entradas obsoletas del manifiesto
        for original_name, entry in index['manifest_entries'].items():
            blob_name = entry.get('blob')
            if blob_name not in index['by_blob_name']:
                report['issues']['stale_manifest_entries'].append({
                    'original_name': original_name,
                    'manifest_blob': blob_name,
                    'manifest_category': entry.get('category', '')
                })
        
        # 2. Verificar nombres originales duplicados
        for original_name, entries in index['by_original_name'].items():
            if len(entries) > 1:
                report['issues']['duplicate_original_names'].append({
                    'original_name': original_name,
                    'entries': entries
                })
        
        # 3. Verificar blobs sin metadatos de original_name
        for blob_name, blob_info in index['by_blob_name'].items():
            if not any(entry['blob_name'] == blob_name 
                      for entries in index['by_original_name'].values() 
                      for entry in entries):
                report['issues']['missing_metadata'].append({
                    'blob_name': blob_name,
                    'size': blob_info['size'],
                    'last_modified': blob_info['last_modified']
                })
        
        # 4. Verificar blobs huérfanos (no en manifiesto ni con metadatos)
        manifest_blobs = {entry['blob'] for entry in index['manifest_entries'].values()}
        metadata_blobs = {entry['blob_name'] 
                         for entries in index['by_original_name'].values() 
                         for entry in entries}
        
        for blob_name in index['by_blob_name']:
            if blob_name not in manifest_blobs and blob_name not in metadata_blobs:
                report['issues']['orphaned_blobs'].append({
                    'blob_name': blob_name,
                    'size': index['by_blob_name'][blob_name]['size']
                })
        
        # Generar recomendaciones
        if report['issues']['stale_manifest_entries']:
            report['recommendations'].append(
                "Reconstruir manifiesto para eliminar entradas obsoletas"
            )
        
        if report['issues']['missing_metadata']:
            report['recommendations'].append(
                "Considerar normalizar blobs existentes para incluir metadatos"
            )
        
        if report['issues']['duplicate_original_names']:
            report['recommendations'].append(
                "Revisar archivos con nombres originales duplicados"
            )
        
        logger.info(f"Análisis completado: {len(report['issues']['stale_manifest_entries'])} entradas obsoletas, "
                   f"{len(report['issues']['duplicate_original_names'])} duplicados")
        
        return report
    
    def rebuild_manifest(self, index: Dict) -> bool:
        """
        Reconstruye el manifiesto basado en el índice actual.
        
        Args:
            index: Índice en memoria del almacenamiento
            
        Returns:
            True si se reconstruyó exitosamente
        """
        logger.info("Reconstruyendo manifiesto...")
        
        try:
            new_manifest = {}
            
            # Construir manifiesto desde metadatos
            for original_name, entries in index['by_original_name'].items():
                # Tomar la entrada más reciente si hay duplicados
                latest_entry = max(entries, key=lambda x: x['last_modified'] or '')
                
                new_manifest[original_name] = {
                    'blob': latest_entry['blob_name'],
                    'category': latest_entry['category'],
                    'uploaded_at': latest_entry['last_modified'],
                    'size': latest_entry['size']
                }
            
            # Subir nuevo manifiesto
            manifest_json = json.dumps(new_manifest, indent=2)
            result = self.storage.upload_data(
                data=manifest_json.encode('utf-8'),
                blob_name="__manifest/manifest.json",
                container_name=self.container_name,
                content_type="application/json",
                category="system"
            )
            
            if result['success']:
                logger.info(f"Manifiesto reconstruido con {len(new_manifest)} entradas")
                return True
            else:
                logger.error(f"Error al subir manifiesto: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Error al reconstruir manifiesto: {e}")
            return False
    
    def generate_report(self, report: Dict, output_format: str = 'markdown') -> str:
        """
        Genera un reporte en el formato especificado.
        
        Args:
            report: Reporte de análisis
            output_format: Formato de salida ('markdown' o 'csv')
            
        Returns:
            Reporte formateado
        """
        if output_format == 'csv':
            return self._generate_csv_report(report)
        else:
            return self._generate_markdown_report(report)
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """Genera reporte en formato Markdown."""
        lines = []
        
        # Encabezado
        lines.append("# Reporte de Consistencia de Almacenamiento")
        lines.append(f"**Fecha:** {report['timestamp']}")
        lines.append(f"**Contenedor:** {report['container']}")
        lines.append("")
        
        # Estadísticas
        lines.append("## Estadísticas Generales")
        stats = report['stats']
        lines.append(f"- **Total de blobs:** {stats['total_blobs']}")
        lines.append(f"- **Con metadatos:** {stats['with_metadata']}")
        lines.append(f"- **Con nombre original:** {stats['with_original_name']}")
        lines.append("")
        
        lines.append("### Blobs por Categoría")
        for category, count in stats['by_category'].items():
            lines.append(f"- **{category}:** {count}")
        lines.append("")
        
        # Problemas encontrados
        lines.append("## Problemas Encontrados")
        
        # Entradas obsoletas del manifiesto
        stale_entries = report['issues']['stale_manifest_entries']
        if stale_entries:
            lines.append(f"### Entradas Obsoletas del Manifiesto ({len(stale_entries)})")
            for entry in stale_entries[:10]:  # Mostrar solo las primeras 10
                lines.append(f"- `{entry['original_name']}` → `{entry['manifest_blob']}`")
            if len(stale_entries) > 10:
                lines.append(f"- ... y {len(stale_entries) - 10} más")
            lines.append("")
        
        # Nombres originales duplicados
        duplicates = report['issues']['duplicate_original_names']
        if duplicates:
            lines.append(f"### Nombres Originales Duplicados ({len(duplicates)})")
            for dup in duplicates[:5]:  # Mostrar solo las primeras 5
                lines.append(f"- `{dup['original_name']}`:")
                for entry in dup['entries']:
                    lines.append(f"  - `{entry['blob_name']}` ({entry['category']})")
            if len(duplicates) > 5:
                lines.append(f"- ... y {len(duplicates) - 5} más")
            lines.append("")
        
        # Blobs sin metadatos
        missing_metadata = report['issues']['missing_metadata']
        if missing_metadata:
            lines.append(f"### Blobs Sin Metadatos ({len(missing_metadata)})")
            for blob in missing_metadata[:10]:
                lines.append(f"- `{blob['blob_name']}` ({blob['size']} bytes)")
            if len(missing_metadata) > 10:
                lines.append(f"- ... y {len(missing_metadata) - 10} más")
            lines.append("")
        
        # Blobs huérfanos
        orphaned = report['issues']['orphaned_blobs']
        if orphaned:
            lines.append(f"### Blobs Huérfanos ({len(orphaned)})")
            for blob in orphaned[:10]:
                lines.append(f"- `{blob['blob_name']}` ({blob['size']} bytes)")
            if len(orphaned) > 10:
                lines.append(f"- ... y {len(orphaned) - 10} más")
            lines.append("")
        
        # Recomendaciones
        if report['recommendations']:
            lines.append("## Recomendaciones")
            for rec in report['recommendations']:
                lines.append(f"- {rec}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_csv_report(self, report: Dict) -> str:
        """Genera reporte en formato CSV."""
        lines = []
        
        # Encabezado
        lines.append("tipo_problema,detalle,blob_name,original_name,categoria,tamaño")
        
        # Entradas obsoletas
        for entry in report['issues']['stale_manifest_entries']:
            lines.append(f"entrada_obsoleta,{entry['manifest_blob']},"
                        f"{entry['manifest_blob']},{entry['original_name']},"
                        f"{entry['manifest_category']},")
        
        # Duplicados
        for dup in report['issues']['duplicate_original_names']:
            for entry in dup['entries']:
                lines.append(f"nombre_duplicado,{dup['original_name']},"
                            f"{entry['blob_name']},{dup['original_name']},"
                            f"{entry['category']},{entry['size']}")
        
        # Sin metadatos
        for blob in report['issues']['missing_metadata']:
            lines.append(f"sin_metadatos,{blob['blob_name']},"
                        f"{blob['blob_name']},,,{blob['size']}")
        
        # Huérfanos
        for blob in report['issues']['orphaned_blobs']:
            lines.append(f"blob_huérfano,{blob['blob_name']},"
                        f"{blob['blob_name']},,,{blob['size']}")
        
        return "\n".join(lines)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Verificador de consistencia del almacenamiento de Azure Blob Storage"
    )
    parser.add_argument(
        '--rebuild-manifest',
        action='store_true',
        help='Reconstruir el manifiesto basado en metadatos actuales'
    )
    parser.add_argument(
        '--output-format',
        choices=['markdown', 'csv'],
        default='markdown',
        help='Formato de salida del reporte'
    )
    parser.add_argument(
        '--output-file',
        help='Archivo de salida (si no se especifica, imprime a stdout)'
    )
    
    args = parser.parse_args()
    
    # Inicializar servicio de almacenamiento
    storage_service = AzureStorageService()
    if not storage_service.client:
        logger.error("No se pudo inicializar el servicio de almacenamiento")
        sys.exit(1)
    
    # Crear verificador
    checker = StorageConsistencyChecker(storage_service)
    
    # Construir índice
    index = checker.build_in_memory_index()
    
    # Analizar consistencia
    report = checker.analyze_consistency(index)
    
    # Reconstruir manifiesto si se solicita
    if args.rebuild_manifest:
        if checker.rebuild_manifest(index):
            logger.info("Manifiesto reconstruido exitosamente")
        else:
            logger.error("Error al reconstruir manifiesto")
            sys.exit(1)
    
    # Generar reporte
    report_content = checker.generate_report(report, args.output_format)
    
    # Guardar o imprimir reporte
    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"Reporte guardado en: {args.output_file}")
    else:
        print(report_content)


if __name__ == '__main__':
    main()
