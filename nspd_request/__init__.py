"""
Библиотека для работы с НСПД (Национальная система пространственных данных)
Предоставляет упрощенные функции для получения данных по кадастровым номерам и геометриям.
"""

from .nspd_request import NSPD
from .utils import (
    create_bbox_from_wgs84,
    convert_wgs84_to_epsg3857,
    convert_epsg3857_to_wgs84,
    extract_features_from_json,
    extract_properties_from_feature,
    extract_geometry_from_feature,
    filter_features_by_property,
    extract_cadastral_numbers_from_features,
    save_json_to_file,
    load_json_from_file,
    extract_coordinates_from_geometry,
    convert_geometry_to_wgs84,
    get_category_id_by_type,
    get_type_by_category_id,
    is_oks_type,
    validate_coordinates,
    format_cadastral_number,
    extract_descr_from_features,
    merge_features_by_property
)
from .version import __version__

__author__ = "Logar1t"
__email__ = "logar1t.official@gmail.com"
__description__ = "Python-библиотека для работы с НСПД"

__all__ = [
    # Основные классы
    "NSPD",
    # Утилиты
    "create_bbox_from_wgs84",
    "convert_wgs84_to_epsg3857",
    "convert_epsg3857_to_wgs84",
    "extract_features_from_json",
    "extract_properties_from_feature",
    "extract_geometry_from_feature",
    "filter_features_by_property",
    "extract_cadastral_numbers_from_features",
    "save_json_to_file",
    "load_json_from_file",
    "extract_coordinates_from_geometry",
    "convert_geometry_to_wgs84",
    "get_category_id_by_type",
    "get_type_by_category_id",
    "is_oks_type",
    "validate_coordinates",
    "format_cadastral_number",
    "extract_descr_from_features",
    "merge_features_by_property",
    # Версия
    "__version__"
]