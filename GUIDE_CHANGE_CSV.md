# Guía: Cómo realizar el cambio "Añadir Columna Description"

Esta guía explica detalladamente qué ficheros tocar para cumplir con la propuesta de añadir la columna `Description` a los CSVs.

## 1. Modificar la Validación (El Código)

El archivo que decide qué columnas son obligatorias es `forms.py`.

**Archivo:** `app/modules/tabular/forms.py`

Busca la lista `FIFA_REQUIRED_COLUMNS` y añade `"Description"`.

```python
FIFA_REQUIRED_COLUMNS = [
    "ID",
    "Name",
    "Age",
    # ... otras columnas ...
    "Weight",
    "Description",  # <--- AÑADIR ESTA LÍNEA
]
```

## 2. Actualizar los Tests (La Verificación)

Al cambiar la regla de validación, todos los tests que usan CSVs antiguos fallarán porque les falta esa columna. Tienes que actualizarlos.

### Localizar los archivos de prueba
Los archivos CSV que usa el sistema de tests están en:
`app/modules/tabular/tests/data/`

Probablemente encuentres archivos como `test_dataset.csv` o similares.

### Editar los CSVs
Debes abrir CADA archivo `.csv` en esa carpeta y añadir la columna `Description` en la cabecera y un valor en las filas.

**Ejemplo de cambio en CSV:**

*Antes:*
```csv
ID,Name,Age,Nationality,...
1,Messi,34,Argentina,...
```

*Después:*
```csv
ID,Name,Age,Nationality,...,Description
1,Messi,34,Argentina,...,"Jugador legendario"
```
> **Nota:** Asegúrate de añadir la coma y el valor en CADA fila del CSV de prueba.

## 3. Comandos para verificar

Una vez hechos los cambios, ejecuta los tests para asegurarte de que todo funciona:

```bash
# Ejecutar solo los tests del módulo tabular
pytest app/modules/tabular/tests/
```

Si todo está verde (Green/Pasado), el cambio está listo.

## Resumen de archivos afectados
1.  `app/modules/tabular/forms.py` (Lógica de validación)
2.  `app/modules/tabular/tests/data/*.csv` (Datos de prueba)
