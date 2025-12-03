from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Sequence, Set

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ClauseElement

from app import db
from app.modules.dataset.models import Author, BaseDataset, DSMetaData

MAX_RESULTS = 5

# Pesos para la fórmula de relevancia
WEIGHTS = {
    "tags": 0.40,
    "communities": 0.30,
    "authors": 0.20,
    "downloads": 0.05,
    "recency": 0.05,
}


@dataclass(frozen=True)
class _DatasetProfile:
    """Normalized metadata profile for similarity checks."""

    tags: Set[str]
    author_names: Set[str]
    author_orcids: Set[str]
    communities: Set[str]
    community_lookup_values: Set[object]
    # Nuevos campos para el scoring
    download_count: int
    created_at_ts: float

    def has_preferences(self) -> bool:
        """Indicate if the profile contains any useful matching attributes."""
        return bool(self.tags or self.author_names or self.author_orcids or self.communities)


class RecommendationService:
    """Provides related dataset recommendations based on shared metadata."""

    def __init__(self) -> None:
        self._community_attribute = getattr(BaseDataset, "communities", None)
        self._community_identifier_column = self._resolve_community_identifier_column()

    def get_related_datasets(self, dataset_id: int) -> list[BaseDataset]:
        """Return up to five datasets related to the provided dataset."""
        base_dataset = self._load_dataset(dataset_id)
        if base_dataset is None:
            return []

        base_profile = self._collect_profile(base_dataset)
        if not base_profile.has_preferences():
            # Sin preferencias (tags/autores/comunidades) no se consulta BD
            # y se devuelve vacío para escenarios de test sin esquema.
            return []

        # 1. Fetch candidates (Subissue 1)
        candidates = self._fetch_candidates(base_dataset, base_profile)
        if not candidates:
            return self._fallback_recommendations(base_dataset, exclude_ids={base_dataset.id})

        # 2. Score and Sort (Subissue 2 - Implementado aquí)
        scored_candidates = self._score_candidates(base_profile, candidates)
        if not scored_candidates:
            return self._fallback_recommendations(base_dataset, exclude_ids={base_dataset.id})

        # Devolvemos solo los datasets, ya ordenados por relevancia
        results = [dataset for dataset, _ in scored_candidates[:MAX_RESULTS]]

        # Completar con fallback si faltan slots (manteniendo pool común entre tipos)
        if len(results) < MAX_RESULTS:
            used_ids = {base_dataset.id} | {ds.id for ds in results if ds and ds.id}
            missing = MAX_RESULTS - len(results)
            fallback = self._fallback_recommendations(base_dataset, exclude_ids=used_ids, limit=missing)
            results.extend(fallback)

        return results[:MAX_RESULTS]

    def _fallback_recommendations(
        self, base_dataset: BaseDataset, exclude_ids: set[int] | None = None, limit: int | None = None
    ) -> list[BaseDataset]:
        """Fallback list when no profile preferences exist: top downloads excluding current dataset."""
        exclude_ids = exclude_ids or set()
        limit = limit or MAX_RESULTS
        return (
            db.session.query(BaseDataset)
            .options(*self._candidate_joinedloads())
            .join(DSMetaData)
            .filter(~BaseDataset.id.in_(exclude_ids))
            .order_by(BaseDataset.download_count.desc(), BaseDataset.created_at.desc())
            .limit(limit)
            .all()
        )

    def _load_dataset(self, dataset_id: int) -> BaseDataset | None:
        options = [joinedload(BaseDataset.ds_meta_data).joinedload(DSMetaData.authors)]
        if self._community_attribute is not None:
            options.append(joinedload(self._community_attribute))

        return db.session.query(BaseDataset).options(*options).filter(BaseDataset.id == dataset_id).one_or_none()

    def _fetch_candidates(self, base_dataset: BaseDataset, profile: _DatasetProfile) -> list[BaseDataset]:
        """Fetch datasets that share at least one attribute with the base profile."""
        query = (
            db.session.query(BaseDataset)
            .options(*self._candidate_joinedloads())
            .join(DSMetaData)
            .filter(BaseDataset.id != base_dataset.id)
        )

        match_clauses: list[ClauseElement] = []

        if profile.tags:
            tag_filters = [DSMetaData.tags.ilike(f"%{tag}%") for tag in profile.tags]
            tag_clause = self._combine_with_or(tag_filters)
            if tag_clause is not None:
                match_clauses.append(tag_clause)

        if profile.author_orcids or profile.author_names:
            query = query.outerjoin(Author)
            author_filters: list[ClauseElement] = []
            if profile.author_orcids:
                author_filters.append(Author.orcid.in_(profile.author_orcids))
            if profile.author_names:
                author_filters.append(func.lower(Author.name).in_(profile.author_names))
            author_clause = self._combine_with_or(author_filters)
            if author_clause is not None:
                match_clauses.append(author_clause)

        if (
            profile.community_lookup_values
            and self._community_attribute is not None
            and self._community_identifier_column is not None
        ):
            query = query.outerjoin(self._community_attribute)
            match_clauses.append(self._community_identifier_column.in_(profile.community_lookup_values))

        if not match_clauses:
            return []

        combined_clause = self._combine_with_or(match_clauses)
        if combined_clause is None:
            return []

        return query.filter(combined_clause).distinct().all()

    def _candidate_joinedloads(self) -> list[object]:
        options: list[object] = [joinedload(BaseDataset.ds_meta_data).joinedload(DSMetaData.authors)]
        if self._community_attribute is not None:
            options.append(joinedload(self._community_attribute))
        return options

    def _collect_profile(self, dataset: DataSet) -> _DatasetProfile:
        metadata = getattr(dataset, "ds_meta_data", None)
        tags = self._extract_tags(metadata)
        author_names, author_orcids = self._extract_authors(metadata)
        communities, lookup_values = self._extract_communities(dataset)

        # Nuevos campos extraídos para Subissue 2
        download_count = getattr(dataset, "download_count", 0) or 0
        created_at_ts = self._timestamp(getattr(dataset, "created_at", None))

        return _DatasetProfile(
            tags=tags,
            author_names=author_names,
            author_orcids=author_orcids,
            communities=communities,
            community_lookup_values=lookup_values,
            download_count=int(download_count),
            created_at_ts=created_at_ts,
        )

    # --- INICIO LÓGICA DE SCORING (SUBISSUE 2) ---

    def _score_candidates(
        self,
        base_profile: _DatasetProfile,
        candidates: Sequence[BaseDataset],
    ) -> list[tuple[BaseDataset, float]]:
        """Calcula el score para cada candidato y ordena la lista."""
        scored: list[tuple[BaseDataset, float]] = []
        for candidate in candidates:
            candidate_profile = self._collect_profile(candidate)
            score = self._compute_score(base_profile, candidate_profile)
            scored.append((candidate, score))

        # Ordenar: Mayor score primero. Desempates por descargas, fecha e ID.
        scored.sort(key=self._sort_key)
        return scored

    def _compute_score(self, base_profile: _DatasetProfile, candidate_profile: _DatasetProfile) -> float:
        score = 0.0

        # 1. Tags: Jaccard Similarity
        score += self._score_jaccard(base_profile.tags, candidate_profile.tags) * WEIGHTS["tags"]

        # 2. Autores: Jaccard combinando nombres y orcids
        base_authors = base_profile.author_names | base_profile.author_orcids
        cand_authors = candidate_profile.author_names | candidate_profile.author_orcids
        score += self._score_jaccard(base_authors, cand_authors) * WEIGHTS["authors"]

        # 3. Comunidades: Jaccard
        score += self._score_jaccard(base_profile.communities, candidate_profile.communities) * WEIGHTS["communities"]

        # 4. Descargas: Normalización Logarítmica
        score += self._score_downloads(candidate_profile)

        # 5. Recencia: Decaimiento lineal
        score += self._score_recency(candidate_profile)

        return score

    def _score_jaccard(self, set_a: Set[str], set_b: Set[str]) -> float:
        """Calcula Índice de Jaccard: (Intersección / Unión). Retorna 0.0 a 1.0."""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return float(intersection) / float(union) if union > 0 else 0.0

    def _score_downloads(self, profile: _DatasetProfile) -> float:
        """Normaliza descargas usando Log10 para suavizar valores altos."""
        count = max(profile.download_count, 0)
        if count == 0:
            return 0.0
        # log10(count + 1) para evitar log(0).
        # Asumiendo 100k descargas como "popularidad máxima" para normalizar a aprox 1.0
        # log10(100000) = 5. Dividimos por 5 para normalizar.
        log_score = math.log10(count + 1)
        normalized = min(log_score / 5.0, 1.0)
        return normalized * WEIGHTS["downloads"]

    def _score_recency(self, profile: _DatasetProfile) -> float:
        """Calcula frescura: 1.0 si es hoy, decae a 0.0 en 365 días."""
        if profile.created_at_ts == 0.0:
            return 0.0

        now_ts = datetime.utcnow().timestamp()
        age_seconds = max(now_ts - profile.created_at_ts, 0)
        days_old = age_seconds / 86400.0

        # Decaimiento lineal sobre 1 año
        freshness = max(1.0 - (days_old / 365.0), 0.0)
        return freshness * WEIGHTS["recency"]

    def _sort_key(self, item: tuple[BaseDataset, float]) -> tuple[float, float, float, int]:
        """Clave de ordenación para sort(). Negativo porque sort es ascendente por defecto."""
        dataset, score = item
        download_count = getattr(dataset, "download_count", 0) or 0
        created_ts = self._timestamp(getattr(dataset, "created_at", None))
        # Prioridad: Score -> Descargas -> Fecha -> ID
        return (-score, -float(download_count), -created_ts, dataset.id or 0)

    @staticmethod
    def _timestamp(value: datetime | None) -> float:
        return value.timestamp() if isinstance(value, datetime) else 0.0

    # --- FIN LÓGICA DE SCORING ---

    def _extract_tags(self, metadata: DSMetaData | None) -> Set[str]:
        if metadata is None or not metadata.tags:
            return set()
        return {normalized for normalized in map(self._normalize_text, metadata.tags.split(",")) if normalized}

    def _extract_authors(self, metadata: DSMetaData | None) -> tuple[Set[str], Set[str]]:
        names: Set[str] = set()
        orcids: Set[str] = set()
        if metadata is None or not metadata.authors:
            return names, orcids

        for author in metadata.authors:
            if author.name:
                normalized_name = self._normalize_text(author.name)
                if normalized_name:
                    names.add(normalized_name)
            if author.orcid:
                cleaned_orcid = author.orcid.strip()
                if cleaned_orcid:
                    orcids.add(cleaned_orcid)
        return names, orcids

    def _extract_communities(self, dataset: DataSet) -> tuple[Set[str], Set[object]]:
        normalized: Set[str] = set()
        lookup_values: Set[object] = set()
        communities = getattr(dataset, "communities", None)
        if not communities:
            return normalized, lookup_values

        for community in communities:
            raw_value = self._community_raw_value(community)
            if raw_value is None:
                continue
            lookup_values.add(raw_value)
            normalized_value = self._normalize_text(str(raw_value))
            if normalized_value:
                normalized.add(normalized_value)
        return normalized, lookup_values

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.strip().lower().split())

    def _community_raw_value(self, community: object) -> object | None:
        for attr_name in ("slug", "code", "name", "identifier", "id"):
            value = getattr(community, attr_name, None)
            if value is None:
                continue
            if isinstance(value, str):
                cleaned_value = value.strip()
                if cleaned_value:
                    return cleaned_value
            else:
                return value
        return None

    def _combine_with_or(self, clauses: Iterable[ClauseElement]) -> ClauseElement | None:
        clause_list = [clause for clause in clauses if clause is not None]
        if not clause_list:
            return None
        if len(clause_list) == 1:
            return clause_list[0]
        return or_(*clause_list)

    def _resolve_community_identifier_column(self) -> InstrumentedAttribute | None:
        if self._community_attribute is None:
            return None
        relationship_property = getattr(self._community_attribute, "property", None)
        mapper = getattr(relationship_property, "mapper", None) if relationship_property else None
        if mapper is None:
            return None
        target_class = mapper.class_
        for candidate_name in ("slug", "code", "name", "identifier", "id"):
            candidate = getattr(target_class, candidate_name, None)
            if isinstance(candidate, InstrumentedAttribute):
                column_property = getattr(candidate, "property", None)
                if getattr(column_property, "columns", None):
                    return candidate
        return None
