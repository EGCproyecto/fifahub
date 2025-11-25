# app/modules/dataset/services/__init__.py

# Importa los servicios clásicos desde el archivo que acabas de mover
from .services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
    SizeService,
)

# Importa los servicios de versionado
from .versioning_service import VersioningService
from .versioning_strategies import TabularVersionStrategy, UVLVersionStrategy

__all__ = [
    "AuthorService",
    "DataSetService",
    "DOIMappingService",
    "DSDownloadRecordService",
    "DSMetaDataService",
    "DSViewRecordService",
    "SizeService",
    "VersioningService",
    "TabularVersionStrategy",
    "UVLVersionStrategy",
]
