# Rutas Oficiales del Proyecto VEA Connect

## Directory
| Nombre de ruta           | Path                        | Vista asociada         |
|-------------------------|-----------------------------|------------------------|
| directory:list          | /directory/                 | contact_list           |
| directory:create        | /directory/create/          | contact_create         |
| directory:edit          | /directory/edit/<int:pk>/   | contact_edit           |
| directory:delete        | /directory/delete/<int:pk>/ | contact_delete         |

## Documents
| Nombre de ruta           | Path                          | Vista asociada         |
|-------------------------|-------------------------------|------------------------|
| documents:document_list | /documents/                   | document_list          |
| documents:create        | /documents/create/            | upload_document        |
| documents:edit          | /documents/edit/<int:pk>/     | edit_document          |
| documents:delete        | /documents/delete/<int:pk>/   | delete_document        |
| documents:download      | /documents/download/<int:pk>/ | download_document      |

## Events
| Nombre de ruta           | Path                        | Vista asociada         |
|-------------------------|-----------------------------|------------------------|
| events:events           | /events/                    | event_list             |
| events:create           | /events/create/             | event_create           |
| events:edit             | /events/edit/<int:pk>/      | event_edit             |
| events:delete           | /events/delete/<int:pk>/    | event_delete           |

## Embeddings
| Nombre de ruta                | Path                                 | Vista asociada         |
|------------------------------|--------------------------------------|------------------------|
| embeddings:home              | /embeddings/                         | home                   |
| embeddings:create            | /embeddings/create/                  | create_embedding       |
| embeddings:list              | /embeddings/list/                    | list_embeddings        |
| embeddings:search            | /embeddings/search/                  | search_embeddings      |
| embeddings:stats             | /embeddings/stats/                   | embeddings_stats       |
| embeddings:bulk_upload       | /embeddings/bulk-upload/             | bulk_upload            |
| embeddings:detail            | /embeddings/<int:pk>/                | embedding_detail       |
| embeddings:update            | /embeddings/<int:pk>/update/         | update_embedding       |
| embeddings:delete            | /embeddings/<int:pk>/delete/         | delete_embedding       |
| embeddings:simple_health_check| /embeddings/health-simple/           | simple_health_check    |

## Vision
| Nombre de ruta                | Path                                 | Vista asociada         |
|------------------------------|--------------------------------------|------------------------|
| vision:extract_text          | /vision/extract-text/                | extract_text_from_file |
| vision:service_status        | /vision/service-status/              | check_service_status   |
| vision:supported_formats     | /vision/supported-formats/           | get_supported_formats  | 