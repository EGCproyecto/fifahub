import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.modules.dataset.models import Author, DataSet, DSMetaData
from app.modules.dataset.services.recommendation_service import RecommendationService


class TestRecommendationService(unittest.TestCase):

    def setUp(self):
        self.service = RecommendationService()
        self.base_time = datetime.now(timezone.utc)

    def create_mock_dataset(
        self, ds_id, title="Test", tags="", authors=None, downloads=0, days_ago=0, community_id=None
    ):
        ds = MagicMock(spec=DataSet)
        ds.id = ds_id
        ds.download_count = downloads
        ds.created_at = self.base_time - timedelta(days=days_ago)
        ds.community_id = community_id

        meta = MagicMock(spec=DSMetaData)
        meta.title = title
        meta.tags = tags
        meta.description = "Description"
        meta.dataset_doi = f"doi/{ds_id}"

        author_objs = []
        if authors:
            for name in authors:
                a = MagicMock(spec=Author)
                a.name = name
                a.orcid = ""
                author_objs.append(a)
        meta.authors = author_objs

        ds.ds_meta_data = meta
        ds.communities = []
        return ds

    # --- TESTS DE SCORING ---

    def test_scoring_weights_logic(self):
        """
        Prueba que los pesos se aplican bien:
        Un dataset con el mismo TAG (peso 0.4) debe ganar a uno con el mismo AUTOR (peso 0.2).
        """
        base = self.create_mock_dataset(1, tags="ultimate team", authors=["EA_Sports"])
        base_profile = self.service._collect_profile(base)

        c1 = self.create_mock_dataset(2, tags="ultimate team", authors=["PlayerOne"])
        c1_profile = self.service._collect_profile(c1)
        score_c1 = self.service._compute_score(base_profile, c1_profile)

        c2 = self.create_mock_dataset(3, tags="career mode", authors=["EA_Sports"])
        c2_profile = self.service._collect_profile(c2)
        score_c2 = self.service._compute_score(base_profile, c2_profile)

        self.assertGreater(
            score_c1, score_c2, "Coincidir en 'Ultimate Team' debería valer más que coincidir solo en el autor"
        )

    def test_recency_scoring(self):
        base = self.create_mock_dataset(1, tags="test")
        base_profile = self.service._collect_profile(base)

        new_ds = self.create_mock_dataset(2, tags="test", days_ago=0)
        old_ds = self.create_mock_dataset(3, tags="test", days_ago=365)

        score_new = self.service._compute_score(base_profile, self.service._collect_profile(new_ds))
        score_old = self.service._compute_score(base_profile, self.service._collect_profile(old_ds))

        self.assertGreater(score_new, score_old)

    def test_edge_case_empty_metadata_strict(self):
        """
        Test corregido: Hacemos que el candidato sea muy viejo (400 días)
        para que la Recencia sea 0.0 y podamos probar que sin tags/autores da 0 total.
        """
        base = self.create_mock_dataset(1, tags="", authors=[])
        # days_ago=400 asegura recencia = 0.0
        candidate = self.create_mock_dataset(2, tags=None, authors=None, days_ago=400)
        candidate.ds_meta_data.tags = None
        candidate.ds_meta_data.authors = None

        profile_base = self.service._collect_profile(base)
        profile_cand = self.service._collect_profile(candidate)
        score = self.service._compute_score(profile_base, profile_cand)

        self.assertEqual(score, 0.0)

    # --- TESTS DE INTEGRACIÓN MOCKEADA (Main flow) ---

    @patch("app.modules.dataset.services.recommendation_service.db.session.query")
    def test_get_related_datasets_sorting_and_limit(self, mock_query):
        """
        Prueba que el sistema ordena bien:
        Un dataset de FIFA (stats) debe salir antes que uno de otro tema (ej. clima),
        simulando la respuesta de la base de datos.
        """
        base_ds = self.create_mock_dataset(99, tags="player stats, pace", authors=["FifaAnalyst"])

        c1 = self.create_mock_dataset(1, tags="player stats, shooting", authors=["FifaAnalyst"])

        c2 = self.create_mock_dataset(2, tags="global warming", authors=["Scientist"])

        self.service._load_dataset = MagicMock(return_value=base_ds)
        self.service._fetch_candidates = MagicMock(return_value=[c1, c2])

        results = self.service.get_related_datasets(99)

        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].id, 1, "El dataset de FIFA (ID 1) debería ser el primero recomendado")

    def test_get_related_datasets_returns_empty_if_not_found(self):
        # Caso: Dataset ID no existe en DB
        with patch.object(self.service, "_load_dataset", return_value=None):
            self.assertEqual(self.service.get_related_datasets(999), [])

    def test_get_related_datasets_returns_empty_if_no_preferences(self):
        # Caso: Dataset existe pero no tiene tags ni autores ni nada
        empty_ds = self.create_mock_dataset(1, tags="", authors=[])
        empty_ds.ds_meta_data.tags = None
        empty_ds.ds_meta_data.authors = []
        empty_ds.communities = []

        with patch.object(self.service, "_load_dataset", return_value=empty_ds):
            self.assertEqual(self.service.get_related_datasets(1), [])

    # --- TESTS UNITARIOS DE FUNCIONES DE EXTRACCIÓN ----
    def test_extract_tags(self):
        """Prueba directa de _extract_tags para cubrir la lógica de limpieza."""
        # Caso normal
        meta = MagicMock()
        meta.tags = " AI,  Machine Learning , python "
        tags = self.service._extract_tags(meta)
        self.assertEqual(tags, {"ai", "machine learning", "python"})

        # Caso vacío
        self.assertEqual(self.service._extract_tags(None), set())

    def test_extract_authors(self):
        """Prueba directa de _extract_authors."""
        meta = MagicMock()
        a1 = MagicMock(spec=Author)
        a1.name = "John Doe "
        a1.orcid = " 0000-1111 "
        a2 = MagicMock(spec=Author)
        a2.name = " Jane "
        a2.orcid = None
        meta.authors = [a1, a2]

        names, orcids = self.service._extract_authors(meta)

        self.assertIn("john doe", names)
        self.assertIn("jane", names)
        self.assertIn("0000-1111", orcids)

    def test_community_raw_value_logic(self):
        """Prueba la extracción de identificadores de comunidad."""
        # Objeto simulando una comunidad con atributo 'slug'
        comm = MagicMock()
        comm.slug = "   my-community  "
        comm.id = 123
        del comm.code  # Asegurar que prueba el loop

        val = self.service._community_raw_value(comm)
        self.assertEqual(val, "my-community")

    def test_normalize_text(self):
        self.assertEqual(self.service._normalize_text("  HOLA   Mundo  "), "hola mundo")
