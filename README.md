<div style="text-align: center;">
  <img src="https://www.uvlhub.io/static/img/logos/logo-light.svg" alt="Logo">
</div>

# uvlhub.io

Repository of feature models in UVL format integrated with Zenodo and flamapy following Open Science principles - Developed by DiversoLab

## Official documentation

You can consult the official documentation of the project at [docs.uvlhub.io](https://docs.uvlhub.io/)

## WI-105 · Download counter

- `data_set.download_count` contabiliza cada descarga registrada desde `/dataset/download/<id>`, visible en la ficha del dataset y en la API (`/api/datasets/<id>` y `/datasets/<id>/stats`).
- Suite de pruebas: `source venv/bin/activate && python -m rosemary test dataset -k download` valida el servicio y el endpoint.
- Cobertura CI: `python -m rosemary coverage dataset --html` genera el reporte consumido por los pipelines featuretas → trunk → main.
- Tras desplegar en `main`, verifica que el contador sube tras cada descarga real; este check es el criterio de aceptación del WI-105 (no se usa pull request en este flujo).
