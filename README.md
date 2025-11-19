<div style="text-align: center;">
  <img src="https://github.com/EGCproyecto/fifahub/blob/8612385a9c809cdbd583ba2a7941e2be5e6f3541/app/static/img/logos/fifa-hub.svg" alt="Logo" width="200">
</div>

# Fifahub

Fifahub is a repository for feature models, datasets with Fakenodo integrated.

# Containerized deployment

The repository now ships with a production-ready `Dockerfile` and a top-level `docker-compose.yml` stack that provisions the Flask app together with MariaDB.

## 1. Configure the environment

1. Install Docker Engine 24+ and Docker Compose v2.
2. Copy one of the provided samples and tailor the values:
   - Local: `cp .env.docker.example .env`
   - Staging/Production: `cp .env.docker.production.example .env`
3. Set the `MARIADB_*` secrets to match your database of choice and adjust `APP_PORT` if you need to expose the API on a port other than 5000. The Compose file automatically loads the `.env` file for both services.

## 2. Build and run the API image

```bash
docker build -t fifahub:latest .
```

The resulting image expects the same `.env` file:

```bash
# Optional: boot the bundled database first
docker compose up -d db

docker run --rm \
  --env-file .env \
  --network=fifahub_default \
  -p "${APP_PORT:-5000}:5000" \
  fifahub:latest
```

The bundled entrypoint waits for MariaDB, applies Alembic migrations, and starts Gunicorn.

## 3. Orchestrate the full stack with Docker Compose

```bash
# Build images (only needed the first time or after changing dependencies)
docker compose --env-file .env build

# Start every service
docker compose --env-file .env up -d

# Stream logs
docker compose logs -f app
```

- `app` exposes `APP_PORT` on the host and bind-mounts `./uploads` so user assets persist outside the container.
- `db` stores its files in the named `mariadb_data` volume. Run `docker compose down -v` to reset it.
- Update code or dependencies and rebuild with `docker compose up -d --build`.
- If you already run MariaDB on your host, change `DB_PORT_HOST` in `.env` (for example `3307`) so the Compose database binds to a free port while the containers keep talking over `MARIADB_PORT=3306`.

## Deployment recipes

1. **Local development** – Use `.env.docker.example`, keep `APP_PORT=5000`, and run `docker compose up -d` to get Flask+MariaDB locally.
2. **Server/Staging** – Base `.env` on `.env.docker.production.example`, supply domains/secrets, then either:
   - Build locally and push the `fifahub:latest` image to your registry, or
   - Build remotely: `docker build -t registry.example.com/fifahub:$(git rev-parse --short HEAD) .`

   Once the image is available on the server, run `docker compose --env-file .env up -d` (or target specific services such as `app`). The entrypoint keeps migrations in sync, so deployments are idempotent.

# WI-fakenodo - Fakenodo service implementation

The **Fakenodo** module is a lightweight internal service emulating Zenodo for development and testing.  
It supports creation, upload, publication, and deletion of dataset depositions, generating unique DOIs using UUIDs.

## Overview

Fakenodo enables:

- Creation of dataset depositions  
- File upload 
- Automatic DOI generation using UUID4
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

## Fakenodo API Endpoints

### 1. Create a Deposition
**POST** `/fakenodo/depositions`
Creates a new deposition tied to an existing dataset.
The responses are: 201 if created, 400 for bad request and 404 if not found.

### 2. Upload a file to a deposition
**POST** `/fakenodo/depositions/<dep_id>/upload`
Used typically after creating a deposition to upload a file.
The responses are: 200 ok and 404 if not found.

### 3. Publish a deposition
**POST** `/fakenodo/depositions/<dep_id>/publish`
Changes a deposition from draft to published, making it immutable.
The responses are: 200 ok and 404 if not found.

### 4. Delete Deposition
**DELETE** `/fakenodo/depositions/<dep_id>`
Deletes a deposition and its metadata.
The responses are: 200 ok and 404 if not found.

## Internal workflow
The Fakenodo module follows a clean multi-layer architecture:

Route (HTTP layer) → Service (logic) → Repository (DB access) → Model

### Creation flow

1. Route Layer
The client sends a `POST /fakenodo/depositions` request containing a `dataset_id`.
The route validates the input, retrieves the dataset using the `DataSetRepository`, and then forwards the request to the `FakenodoService`.

2. Service Layer
The `create_new_deposition()` method generates a unique DOI using a UUID, constructs the deposition metadata based on the dataset fields, and prepares the data needed, DOI and metadata, to create the deposition. Once everything is ready, it calls the repository.

3. Repository Layer
The repository creates a new Fakenodo object with the metadata, DOI, and the `draft` default status.
It adds this object to the SQLAlchemy session, commits to the database, and returns the created deposition.

4. Model Layer
The Fakenodo model defines the database schema for depositions, including the fields `id`, `meta_data`, `status`, and `doi`.

## Testing

The Fakenodo module supports both unit testing and load testing with Locust. These tests are designed to validate functionality, API behavior and performance.

To run all fakenodo unit tests: 
- `rosemary test fakenodo`

To run Locust load testing: 
- `locust -f path/locustfile.py`
- Then open `http://localhost:8089` and start the load testing.

# WI-105 - Download counter

- `data_set.download_count` contabiliza cada descarga registrada desde `/dataset/download/<id>`, visible en la ficha del dataset y en la API (`/api/datasets/<id>` y `/datasets/<id>/stats`).
- Suite de pruebas: `source venv/bin/activate && python -m rosemary test dataset -k download` valida el servicio y el endpoint.
- Cobertura CI: `python -m rosemary coverage dataset --html` genera el reporte consumido por los pipelines featuretas → trunk → main.
- Tras desplegar en `main`, verifica que el contador sube tras cada descarga real; este check es el criterio de aceptación del WI-105 (no se usa pull request en este flujo).
