<div style="text-align: center;">
  <img src="https://www.uvlhub.io/static/img/logos/logo-light.svg" alt="Logo">
</div>

# uvlhub.io

Repository of feature models in UVL format integrated with Zenodo and flamapy following Open Science principles - Developed by DiversoLab

## Official documentation

You can consult the official documentation of the project at [docs.uvlhub.io](https://docs.uvlhub.io/)

## Docker

- Requirements: Docker Engine and the Docker Compose plugin installed locally
- Bootstrap: `cp .env.example .env` and adjust secrets/ports as needed (DB host for containers is `db`)
- Build image: `docker build -t fifahub:latest .`
- Run image: `docker run --env-file .env -p ${APP_PORT:-5000}:5000 fifahub:latest`
- Local stack: `docker compose up --build -d` then `docker compose logs -f web` to follow logs; tear down with `docker compose down`
- Data: MariaDB data persists inside the named `db_data` volume so repeated compose runs keep existing data
