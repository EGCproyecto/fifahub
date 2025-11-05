import csv
import os
import statistics


def parse_csv_metadata(file_path, delimiter=",", has_header=True, sample_rows=5):
    """
    Analiza un archivo CSV y extrae metadatos completos para datasets FIFA.

    Args:
        file_path (str): Ruta al archivo CSV
        delimiter (str): Separador de columnas (por defecto ',')
        has_header (bool): Si la primera fila contiene nombres de columnas
        sample_rows (int): Número de filas de muestra a extraer

    Returns:
        dict: Metadatos del CSV incluyendo:
            - n_rows: número de filas de datos
            - n_cols: número de columnas
            - file_size: tamaño del archivo en bytes
            - encoding: codificación detectada
            - delimiter: delimitador usado
            - has_header: si tiene cabecera
            - columns: lista con metadatos de cada columna
            - sample_rows: muestra de las primeras filas
    """
    if os.path.getsize(file_path) == 0:
        return _handle_empty_file(file_path, delimiter, has_header)

    encoding = _detect_encoding(file_path)
    MAX_ROWS_ANALYSIS = 10000

    meta = {
        "n_rows": 0,
        "n_cols": 0,
        "file_size": os.path.getsize(file_path),
        "encoding": encoding,
        "delimiter": delimiter,
        "has_header": has_header,
        "columns": [],
        "sample_rows": [],
    }

    with open(file_path, encoding=encoding, newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = next(reader) if has_header else None
        meta["n_cols"] = len(header) if header else 0

        all_values = [[] for _ in range(meta["n_cols"])]
        null_counts = [0] * meta["n_cols"]

        for i, row in enumerate(reader, start=1):
            if i > MAX_ROWS_ANALYSIS:
                break

            meta["n_rows"] += 1

            if i <= sample_rows:
                meta["sample_rows"].append(row)

            if not has_header and meta["n_cols"] == 0:
                meta["n_cols"] = len(row)
                header = [f"col_{idx}" for idx in range(meta["n_cols"])]
                all_values = [[] for _ in range(meta["n_cols"])]
                null_counts = [0] * meta["n_cols"]

            for j, val in enumerate(row[: meta["n_cols"]]):
                val = val.strip()

                if val == "" or val.lower() in {"na", "null", "n/a", "nan"}:
                    null_counts[j] += 1
                else:
                    all_values[j].append(val)

        for idx in range(meta["n_cols"]):
            col_name = header[idx] if header else f"col_{idx}"
            values = all_values[idx]

            col_metadata = _analyze_column_complete(values, col_name, null_counts[idx])
            meta["columns"].append(col_metadata)

    return meta


def _detect_encoding(file_path):
    """
    Detecta automáticamente la codificación del archivo CSV.

    Prueba diferentes encodings comunes hasta encontrar uno que funcione
    sin errores de decodificación Unicode.

    Args:
        file_path (str): Ruta al archivo

    Returns:
        str: Encoding detectado ('utf-8', 'latin1', 'cp1252', o 'iso-8859-1')
    """
    encodings_to_try = ["utf-8", "latin1", "cp1252", "iso-8859-1"]

    for encoding in encodings_to_try:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                f.read(1024)
            return encoding
        except UnicodeDecodeError:
            continue

    return "utf-8"


def _infer_dtype_specific(values):
    """
    Infiere el tipo de datos específico de una columna.

    Distingue entre enteros ('int'), flotantes ('float') y cadenas ('string')
    usando try/except. Limpia símbolos monetarios y de magnitud antes de
    intentar las conversiones numéricas.

    Args:
        values (list): Lista de valores de la columna (sin nulos)

    Returns:
        str: Tipo detectado ('int', 'float', o 'string')
    """
    if not values:
        return "string"

    sample = values[: min(100, len(values))]

    try:
        for val in sample:
            clean_val = (
                val.replace("€", "")
                .replace("$", "")
                .replace("M", "")
                .replace("K", "")
                .replace(",", "")
            )
            int(clean_val)
        return "int"
    except ValueError:
        pass

    try:
        for val in sample:
            clean_val = (
                val.replace("€", "")
                .replace("$", "")
                .replace("M", "")
                .replace("K", "")
                .replace(",", "")
            )
            float(clean_val)
        return "float"
    except ValueError:
        pass

    return "string"


def _calculate_numeric_stats(values, dtype):
    """
    Calcula estadísticas básicas para columnas numéricas.

    Usa el módulo statistics de Python para calcular mínimo, máximo,
    media y mediana. Limpia símbolos antes de convertir a números.

    Args:
        values (list): Lista de valores numéricos como strings
        dtype (str): Tipo de datos ('int' o 'float')

    Returns:
        dict o None: Diccionario con min, max, mean, median o None si hay error
    """
    try:
        numeric_values = []

        for val in values:
            clean_val = (
                val.replace("€", "")
                .replace("$", "")
                .replace("M", "")
                .replace("K", "")
                .replace(",", "")
            )

            if dtype == "int":
                numeric_values.append(int(clean_val))
            else:
                numeric_values.append(float(clean_val))

        if not numeric_values:
            return None

        return {
            "min": min(numeric_values),
            "max": max(numeric_values),
            "mean": statistics.mean(numeric_values),
            "median": statistics.median(numeric_values),
        }

    except (ValueError, statistics.StatisticsError):
        return None


def _analyze_column_complete(values, name, null_count):
    """
    Realiza el análisis completo de una columna individual.

    Combina la inferencia de tipos, conteo de únicos y cálculo de estadísticas
    en un solo análisis integral por columna.

    Args:
        values (list): Lista de valores válidos (sin nulos) de la columna
        name (str): Nombre de la columna
        null_count (int): Cantidad de valores nulos en la columna

    Returns:
        dict: Metadatos completos de la columna con name, dtype, conteos y stats
    """
    unique_count = len(set(values))
    dtype = _infer_dtype_specific(values)

    stats = None
    if dtype in ["int", "float"] and values:
        stats = _calculate_numeric_stats(values, dtype)

    return {
        "name": name,
        "dtype": dtype,
        "null_count": null_count,
        "non_null_count": len(values),
        "unique_count": unique_count,
        "stats": stats,
    }


def _handle_empty_file(file_path, delimiter, has_header):
    """
    Maneja archivos CSV vacíos sin provocar errores.

    Retorna una estructura de metadatos coherente con todos los contadores
    en cero y listas vacías para archivos sin contenido.

    Args:
        file_path (str): Ruta al archivo vacío
        delimiter (str): Delimitador especificado
        has_header (bool): Si se esperaba header

    Returns:
        dict: Estructura de metadatos vacía pero válida
    """
    return {
        "n_rows": 0,
        "n_cols": 0,
        "file_size": os.path.getsize(file_path),
        "encoding": "utf-8",
        "delimiter": delimiter,
        "has_header": has_header,
        "columns": [],
        "sample_rows": [],
    }
