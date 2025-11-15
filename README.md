<div style="text-align: center;">
  <img src="https://github.com/EGCproyecto/fifahub/blob/e088df0bfbb1c1208bf134426631f2f107392aa8/app/static/img/logos/logo-fifahub-definitivo.png" alt="Logo">
</div>

# fifahub

Repository for feature models, datasets with Fakenodo integrated.

# WI-fakenodo - Fakenodo service implementation

The **Fakenodo** module is a lightweight internal service emulating Zenodo for development and testing.  
It supports creation, upload, publication, and deletion of dataset depositions, generating unique DOIs using UUIDs.

## Overview

Fakenodo enables:

- Creation of dataset depositions  
- File upload 
- Automatic DOI generation using UUID4 
- Complete CRUD lifecycle  
- Integration with the fifahub dataset metadata model  

It is designed for local development, CI/CD, and testing workflows.

---

## Data Model

Each deposition is represented in the `Fakenodo` table:

| Field        | Type         | Description                                        |
|--------------|--------------|----------------------------------------------------|
| `id`         | Integer      | Unique numeric identifier                          |
| `meta_data`  | JSON         | Title, authors, description, keywords, etc.        |
| `status`     | String       | `draft` or `published`                             |
| `doi`        | String       | Unique DOI automatically generated for each entry  |

### DOI Format

The DOI format is: 10.5281/fakenodo.<uuid4>
This guarantees uniqueness even under extreme concurrency or Locust load tests.

# Fakenodo API Endpoints

## 1. Create a Deposition
**POST** `/fakenodo/depositions`

Creates a new deposition tied to an existing dataset.
The responses are: 201 if created, 400 for bad request and 404 if not found.


## WI-105 - Download counter

- `data_set.download_count` contabiliza cada descarga registrada desde `/dataset/download/<id>`, visible en la ficha del dataset y en la API (`/api/datasets/<id>` y `/datasets/<id>/stats`).
- Suite de pruebas: `source venv/bin/activate && python -m rosemary test dataset -k download` valida el servicio y el endpoint.
- Cobertura CI: `python -m rosemary coverage dataset --html` genera el reporte consumido por los pipelines featuretas → trunk → main.
- Tras desplegar en `main`, verifica que el contador sube tras cada descarga real; este check es el criterio de aceptación del WI-105 (no se usa pull request en este flujo).
