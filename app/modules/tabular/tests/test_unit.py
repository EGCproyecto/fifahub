import csv
import os
import tempfile

from app.modules.tabular.utils.parser import parse_csv_metadata


def test_basic_structure():
    """
    Prueba la lectura básica de estructura del CSV.

    Verifica que el parser lee correctamente el número de filas, columnas,
    detecta headers y genera la lista de metadatos de columnas.
    """
    csv_data = [["Name", "Age", "Position"], ["Messi", "36", "RW"], ["Ronaldo", "38", "ST"]]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
        csv_path = f.name

    try:
        result = parse_csv_metadata(csv_path)

        assert result["n_rows"] == 2
        assert result["n_cols"] == 3
        assert len(result["columns"]) == 3
        assert result["has_header"] == True

    finally:
        os.unlink(csv_path)


def test_column_type_inference():
    """
    Prueba la inferencia correcta de tipos de datos.

    Verifica que el parser distingue entre enteros, flotantes y strings,
    y calcula estadísticas para los tipos numéricos.
    """
    csv_data = [
        ["Name", "Rating", "Position", "Active", "Value", "Age"],
        ["Messi", "9.5", "RW", "False", "90M", "38"],
        ["Ronaldo", "9.0", "ST", "NULL", "85M", "40"],
        ["Neymar", "8.5", "NA", "True", "80M", "35"],
    ]

    with tempfile.NamedTemporaryFile(mode="w", delete=False, newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
        csv_path = f.name

    try:
        result = parse_csv_metadata(csv_path)
        cols = {col["name"]: col for col in result["columns"]}

        assert cols["Name"]["dtype"] == "string"
        assert cols["Rating"]["dtype"] == "float"
        assert cols["Position"]["dtype"] == "string"
        assert cols["Value"]["dtype"] == "int"
        assert cols["Age"]["dtype"] == "int"

        assert cols["Rating"]["stats"] is not None
        assert cols["Age"]["stats"]["min"] == 35
        assert cols["Age"]["stats"]["max"] == 40

    finally:
        os.unlink(csv_path)


def test_null_counting():
    """
    Prueba el conteo correcto de valores nulos.

    Verifica que el parser cuenta adecuadamente diferentes representaciones
    de valores faltantes ('', 'NULL', 'NA', etc.).
    """
    csv_data = [
        ["Name", "Club", "Value"],
        ["Messi", "Inter Miami", "35M"],
        ["", "Barcelona", "50M"],
        ["Neymar", "", "89M"],
        ["Pedri", "NULL", "NA"],
    ]

    with tempfile.NamedTemporaryFile(mode="w", delete=False, newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
        csv_path = f.name

    try:
        result = parse_csv_metadata(csv_path)
        cols = {col["name"]: col for col in result["columns"]}

        assert cols["Name"]["null_count"] == 1
        assert cols["Club"]["null_count"] == 2
        assert cols["Value"]["null_count"] == 1

    finally:
        os.unlink(csv_path)


def test_sample_data():
    """
    Prueba la extracción de muestra de datos.

    Verifica que el parser extrae correctamente las primeras N filas
    como muestra, respetando el parámetro sample_rows.
    """
    csv_data = [["Name", "Age"], ["Messi", "36"], ["Ronaldo", "38"], ["Mbappé", "24"], ["Neymar", "31"]]

    with tempfile.NamedTemporaryFile(mode="w", delete=False, newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
        csv_path = f.name

    try:
        result = parse_csv_metadata(csv_path, sample_rows=2)

        assert len(result["sample_rows"]) == 2
        assert result["sample_rows"][0] == ["Messi", "36"]
        assert result["sample_rows"][1] == ["Ronaldo", "38"]

    finally:
        os.unlink(csv_path)


def test_file_metadata():
    """
    Prueba la inclusión de metadatos del archivo.

    Verifica que el parser incluye información sobre el archivo como
    tamaño, encoding detectado y delimitador usado.
    """
    csv_data = [["Name", "Age"], ["Messi", "36"]]

    with tempfile.NamedTemporaryFile(mode="w", delete=False, newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
        csv_path = f.name

    try:
        result = parse_csv_metadata(csv_path, delimiter=",")

        assert "file_size" in result
        assert result["file_size"] > 0
        assert "encoding" in result
        assert result["delimiter"] == ","

    finally:
        os.unlink(csv_path)


def test_empty_file():
    """
    Prueba el manejo de archivos vacíos.

    Verifica que el parser no falla con archivos vacíos y retorna
    una estructura coherente con todos los valores en cero.
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, newline="") as f:
        pass
        csv_path = f.name

    try:
        result = parse_csv_metadata(csv_path)

        assert result["n_rows"] == 0
        assert result["n_cols"] == 0
        assert result["file_size"] == 0
        assert result["columns"] == []

    finally:
        os.unlink(csv_path)


if __name__ == "__main__":
    test_basic_structure()
    test_column_type_inference()
    test_null_counting()
    test_sample_data()
    test_file_metadata()
    test_empty_file()
