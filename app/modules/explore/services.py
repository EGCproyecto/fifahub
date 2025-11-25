from app.modules.explore.repositories import ExploreRepository
from core.services.BaseService import BaseService


class ExploreService(BaseService):
    def __init__(self):
        super().__init__(ExploreRepository())

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
        return self.repository.filter(
            query,
            sorting,
            publication_type,
            tags or [],
            dataset_type,
            facets or {},
            **kwargs,
        )
