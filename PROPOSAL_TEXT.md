# 7.1 Cambio propuesto
**Título:** Mejora de la calidad de datos mediante estandarización de esquema CSV

**Objetivo:**
Garantizar que todos los datasets subidos a la plataforma contengan información descriptiva esencial directamente en el archivo fuente. Se añade la obligatoriedad de una columna `Description` en los archivos CSV para mejorar la indexación y comprensión de los datos por parte de otros investigadores.

**Criterios de aceptación:**
- El sistema rechaza archivos CSV que no contengan la columna `Description`.
- La columna `Description` se utiliza para pre-rellenar los metadatos del dataset automáticamente si es posible.
- Los tests de ingesta validan la presencia de esta nueva columna.
- No se rompe la visualización de datasets antiguos (retrocompatibilidad o migración no requerida para el alcance actual).

# 7.2 Pasos detallados

## Crear issue
**Issue:** Enforce 'Description' column in CSV upload
**Descripción:** Modificar el esquema de validación para requerir la columna `Description`.
**Objetivo/Impacto:** Mejorar la calidad de los metadatos desde la fuente.

## Crear rama
```bash
git checkout main
git pull
git checkout -b feat/csv-description-column
```

## Implementación

### Backend
- **Archivo:** `app/modules/tabular/forms.py`
- **Cambio:** Añadir `"Description"` a la lista `FIFA_REQUIRED_COLUMNS`.

### Tests
- **Archivo:** `app/modules/tabular/tests/data/*.csv`
- **Cambio:** Actualizar todos los CSV de prueba para incluir la columna `Description`.

## Verificación Local
1. Ejecutar tests existentes con `pytest` para confirmar que fallan con los CSV antiguos (si no se actualizan).
2. Actualizar CSVs y verificar que los tests pasan (`pytest`).
3. Subir manual de un CSV válido (con Description) y uno inválido (sin Description) en la interfaz web.

## Commit e Integración
```bash
git add .
git commit -m "feat(tabular): enforce Description column in CSV schema"
git checkout main
git merge feat/csv-description-column
git push
```
