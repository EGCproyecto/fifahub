import pytest

from app.modules.fakenodo.app.storage import inmemory as st


@pytest.fixture(autouse=True)
def clear_db():
    # asegurar DB esta limpia antes y despues de cada test
    st.DB.clear()
    yield
    st.DB.clear()


def test_create_deposition_stores_in_db():
    dep = st.create_deposition({"title": "Test"})
    assert dep.id in st.DB


def test_create_deposition_initial_metadata_is_set():
    dep = st.create_deposition({"title": "Test"})
    assert dep.versions[0].metadata["title"] == "Test"


def test_get_deposition_returns_same_object():
    dep = st.create_deposition({"title": "Test"})
    same = st.get_deposition(dep.id)
    assert same is dep


def test_update_metadata_overwrites_existing_title():
    dep = st.create_deposition({"title": "Old"})
    st.update_metadata(dep.id, {"title": "New"})
    assert dep.versions[0].metadata["title"] == "New"


def test_put_file_adds_filename_to_files():
    dep = st.create_deposition({"title": "Files"})
    draft = st.put_file(dep.id, "data.csv", b"1,2,3\n")
    assert "data.csv" in draft.files


def test_put_file_stores_file_content_correctly():
    dep = st.create_deposition({"title": "Files"})
    draft = st.put_file(dep.id, "data.csv", b"1,2,3\n")
    assert draft.files["data.csv"] == b"1,2,3\n"


def test_list_versions_returns_single_draft_version():
    dep = st.create_deposition({"title": "Ver"})
    out = st.list_versions(dep.id)

    assert len(out["versions"]) == 1


def test_list_versions_returns_correct_conceptrecid():
    dep = st.create_deposition({"title": "Ver"})
    out = st.list_versions(dep.id)

    assert out["conceptrecid"] == dep.conceptrecid


def test_list_versions_draft_has_version_zero_and_draft_state():
    dep = st.create_deposition({"title": "Ver"})
    out = st.list_versions(dep.id)

    v = out["versions"][0]
    assert v["version"] == 0
    assert v["state"] == "draft"


def test_get_deposition_unknown_returns_none():
    result = st.get_deposition("no_such_id")
    assert result is None
