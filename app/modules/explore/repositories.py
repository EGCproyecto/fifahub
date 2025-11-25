import re
from datetime import datetime

import unidecode
from sqlalchemy import any_, or_

from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from app.modules.tabular.models import TabularColumn, TabularDataset, TabularMetaData
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def filter(
        self,
        query="",
        sorting="newest",
        publication_type="any",
        tags=None,
        dataset_type="any",
        facets=None,
        **kwargs,
    ):
        tags = tags or []
        facets = facets or {}
        words = self._normalize_query(query)
        dataset_type = (dataset_type or "any").lower()

        results = []
        if dataset_type in ("any", "uvl"):
            results.extend(self._filter_uvl(words, publication_type, tags))
        if dataset_type in ("any", "tabular"):
            results.extend(self._filter_tabular(words, publication_type, tags, facets))

        reverse = sorting != "oldest"
        unique = {dataset.id: dataset for dataset in results}
        ordered = sorted(unique.values(), key=lambda ds: ds.created_at or datetime.min, reverse=reverse)
        return ordered

    def _normalize_query(self, query: str):
        normalized_query = unidecode.unidecode((query or "")).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)
        return [word for word in cleaned_query.split() if word]

    def _matching_publication_type(self, publication_type: str):
        if not publication_type or publication_type == "any":
            return None
        publication_type = publication_type.lower()
        for member in PublicationType:
            if member.value.lower() == publication_type:
                return member
        return None

    def _apply_publication_type_filter(self, query, publication_type):
        matching = self._matching_publication_type(publication_type)
        if matching is not None:
            query = query.filter(DSMetaData.publication_type == matching)
        return query

    def _build_common_filters(self, words):
        filters = []
        for word in words:
            filters.append(DSMetaData.title.ilike(f"%{word}%"))
            filters.append(DSMetaData.description.ilike(f"%{word}%"))
            filters.append(Author.name.ilike(f"%{word}%"))
            filters.append(Author.affiliation.ilike(f"%{word}%"))
            filters.append(Author.orcid.ilike(f"%{word}%"))
            filters.append(DSMetaData.tags.ilike(f"%{word}%"))
        return filters

    def _build_uvl_filters(self, words):
        filters = []
        for word in words:
            filters.append(FMMetaData.uvl_filename.ilike(f"%{word}%"))
            filters.append(FMMetaData.title.ilike(f"%{word}%"))
            filters.append(FMMetaData.description.ilike(f"%{word}%"))
            filters.append(FMMetaData.publication_doi.ilike(f"%{word}%"))
            filters.append(FMMetaData.tags.ilike(f"%{word}%"))
        return filters

    def _build_tabular_filters(self, words):
        filters = []
        for word in words:
            filters.append(TabularMetaData.columns.any(TabularColumn.name.ilike(f"%{word}%")))
            filters.append(TabularMetaData.columns.any(TabularColumn.dtype.ilike(f"%{word}%")))
        return filters

    def _filter_uvl(self, words, publication_type, tags):
        filters = self._build_common_filters(words) + self._build_uvl_filters(words)
        datasets = (
            self.model.query.join(DataSet.ds_meta_data)
            .join(DSMetaData.authors)
            .outerjoin(DataSet.feature_models)
            .outerjoin(FeatureModel.fm_meta_data)
            .filter(DSMetaData.dataset_doi.isnot(None))
        )
        if filters:
            datasets = datasets.filter(or_(*filters))
        datasets = self._apply_publication_type_filter(datasets, publication_type)
        if tags:
            datasets = datasets.filter(DSMetaData.tags.ilike(any_(f"%{tag}%" for tag in tags)))
        return datasets.distinct().all()

    def _filter_tabular(self, words, publication_type, tags, facets):
        filters = self._build_common_filters(words) + self._build_tabular_filters(words)
        datasets = (
            TabularDataset.query.join(TabularDataset.ds_meta_data)
            .join(DSMetaData.authors)
            .join(TabularDataset.meta_data)
            .filter(DSMetaData.dataset_doi.isnot(None))
        )
        if filters:
            datasets = datasets.filter(or_(*filters))
        datasets = self._apply_publication_type_filter(datasets, publication_type)
        if tags:
            datasets = datasets.filter(DSMetaData.tags.ilike(any_(f"%{tag}%" for tag in tags)))

        dtype_values = facets.get("dtype")
        if dtype_values:
            datasets = datasets.filter(TabularMetaData.columns.any(TabularColumn.dtype.in_(dtype_values)))

        has_nulls = facets.get("has_nulls")
        if has_nulls:
            wants_yes = "yes" in has_nulls and "no" not in has_nulls
            wants_no = "no" in has_nulls and "yes" not in has_nulls
            if wants_yes:
                datasets = datasets.filter(TabularMetaData.columns.any(TabularColumn.null_count > 0))
            elif wants_no:
                datasets = datasets.filter(~TabularMetaData.columns.any(TabularColumn.null_count > 0))

        return datasets.distinct().all()
