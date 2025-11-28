import io

from app.modules.conftest import login, logout
from app.modules.tabular.forms import FIFA_REQUIRED_COLUMNS


def _post_tabular_upload(test_client, csv_bytes, filename="dataset.csv"):
    data = {
        "name": "FIFA sample upload",
        "delimiter": ",",
        "encoding": "utf-8",
        "has_header": "y",
        "sample_rows": "20",
        "csv_file": (io.BytesIO(csv_bytes), filename),
    }
    return test_client.post("/tabular/upload", data=data, content_type="multipart/form-data")


def test_upload_rejects_non_fifa_schema(test_client):
    login(test_client, "test@example.com", "test1234")
    csv_bytes = b"ID,Name,Age\n1,Lionel Messi,36\n"

    response = _post_tabular_upload(test_client, csv_bytes, filename="invalid.csv")

    assert response.status_code == 400
    assert b"ValidationError" in response.data

    logout(test_client)


def test_upload_accepts_valid_fifa_schema(test_client):
    login(test_client, "test@example.com", "test1234")
    header = ",".join(FIFA_REQUIRED_COLUMNS)
    row = ",".join(
        [
            "10",
            "Kylian Mbappe",
            "24",
            "France",
            "91",
            "95",
            "PSG",
            "160000000",
            "900000",
            "Right",
            "4",
            "5",
            "ST",
            "178",
            "73",
        ]
    )
    csv_bytes = f"{header}\n{row}\n".encode("utf-8")

    response = _post_tabular_upload(test_client, csv_bytes, filename="fifa_valid.csv")

    assert response.status_code == 302
    assert "/tabular/" in response.headers.get("Location", "")

    detail_response = test_client.get(response.headers["Location"])
    assert detail_response.status_code == 200

    logout(test_client)
