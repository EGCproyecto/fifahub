# app/modules/tabular/utils/parser.py
import csv


def parse_csv_metadata(file_path, delimiter=",", has_header=True, sample_rows=5):
    """
    Lee un CSV y extrae metadatos básicos (sin usar pandas).
    Devuelve: un diccionario con info general + columnas + muestra de filas.
    """
    meta = {
        "n_rows": 0,  # número total de filas
        "n_cols": 0,  # número de columnas
        "columns": [],  # lista con info de cada columna
        "sample_rows": [],  # las primeras N filas como ejemplo
    }

    with open(file_path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = next(reader) if has_header else None
        meta["n_cols"] = len(header) if header else 0

        # Inicializamos estructuras para contar valores por columna
        counts = [0] * meta["n_cols"]  # valores no nulos por columna
        uniques = [set() for _ in range(meta["n_cols"])]  # valores únicos
        numeric_flags = [True] * meta["n_cols"]  # si todos los valores son numéricos

        for i, row in enumerate(reader, start=1):
            meta["n_rows"] += 1
            if i <= sample_rows:
                meta["sample_rows"].append(row)

            for j, val in enumerate(row):
                val = val.strip()
                # tratamos valores vacíos o nulos
                if val == "" or val.lower() in {"na", "null"}:
                    continue

                counts[j] += 1
                uniques[j].add(val)

                # comprobamos si sigue siendo numérico
                if numeric_flags[j]:
                    try:
                        float(val)
                    except ValueError:
                        numeric_flags[j] = False

        # Construimos la lista de columnas con sus metadatos
        for idx, name in enumerate(header or range(meta["n_cols"])):
            dtype = "numeric" if numeric_flags[idx] else "string"
            meta["columns"].append(
                {
                    "name": name,
                    "dtype": dtype,
                    "non_null_count": counts[idx],
                    "unique_count": len(uniques[idx]),
                }
            )

    return meta
