"""
Дополнительные утилиты для работы с НСПД
Содержит вспомогательные функции для обработки данных, преобразования координат и работы с геометрией.
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from pyproj import Transformer


def create_bbox_from_wgs84(lat: float, lon: float, size_meters: float = 100) -> str:
    """
    Создает BBOX в EPSG:3857 из координат в WGS84 (EPSG:4326).
    
    Args:
        lat: Широта в градусах (WGS84)
        lon: Долгота в градусах (WGS84)
        size_meters: Размер BBOX в метрах (половина стороны квадрата)
    
    Returns:
        str: BBOX в формате "minX,minY,maxX,maxY" (EPSG:3857)
    """
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    center_x, center_y = transformer.transform(lon, lat)
    
    half_size = size_meters / 2
    min_x = center_x - half_size
    min_y = center_y - half_size
    max_x = center_x + half_size
    max_y = center_y + half_size
    
    return f"{min_x},{min_y},{max_x},{max_y}"


def convert_wgs84_to_epsg3857(latitude: float, longitude: float) -> Tuple[float, float]:
    """
    Преобразует координаты из WGS84 (EPSG:4326) в EPSG:3857
    
    Args:
        latitude: Широта в градусах
        longitude: Долгота в градусах
    
    Returns:
        Tuple[float, float]: Координаты в EPSG:3857 (x, y)
    """
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x, y = transformer.transform(longitude, latitude)
    return x, y


def convert_epsg3857_to_wgs84(x: float, y: float) -> Tuple[float, float]:
    """
    Преобразует координаты из EPSG:3857 в WGS84 (EPSG:4326)
    
    Args:
        x: Координата X в EPSG:3857
        y: Координата Y в EPSG:3857
    
    Returns:
        Tuple[float, float]: Координаты в WGS84 (широта, долгота)
    """
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lat, lon


def extract_features_from_json(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Извлекает список features из JSON ответа НСПД
    
    Args:
        json_data: JSON данные от НСПД
    
    Returns:
        List[Dict]: Список features
    """
    if not json_data or not isinstance(json_data, dict):
        return []
    
    if 'features' in json_data and isinstance(json_data['features'], list):
        return json_data['features']
    
    return []


def extract_properties_from_feature(feature: Dict[str, Any]) -> Dict[str, Any]:
    """
    Извлекает properties из feature
    
    Args:
        feature: Объект feature из JSON ответа
    
    Returns:
        Dict: Словарь properties или пустой словарь
    """
    if not feature or not isinstance(feature, dict):
        return {}
    
    return feature.get('properties', {})


def extract_geometry_from_feature(feature: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Извлекает geometry из feature
    
    Args:
        feature: Объект feature из JSON ответа
    
    Returns:
        Dict: Словарь geometry или None
    """
    if not feature or not isinstance(feature, dict):
        return None
    
    return feature.get('geometry')


def filter_features_by_property(
    features: List[Dict[str, Any]], 
    property_key: str, 
    property_value: Any,
    exact_match: bool = True
) -> List[Dict[str, Any]]:
    """
    Фильтрует features по значению свойства
    
    Args:
        features: Список features
        property_key: Ключ свойства для фильтрации
        property_value: Значение для сравнения
        exact_match: Если True, точное совпадение, иначе проверка вхождения
    
    Returns:
        List[Dict]: Отфильтрованный список features
    """
    filtered = []
    for feature in features:
        properties = extract_properties_from_feature(feature)
        value = properties.get(property_key)
        
        if exact_match:
            if value == property_value:
                filtered.append(feature)
        else:
            if value and property_value in str(value):
                filtered.append(feature)
    
    return filtered


def extract_cadastral_numbers_from_features(features: List[Dict[str, Any]]) -> List[str]:
    """
    Извлекает кадастровые номера из списка features
    
    Args:
        features: Список features
    
    Returns:
        List[str]: Список кадастровых номеров
    """
    cad_numbers = []
    
    for feature in features:
        properties = extract_properties_from_feature(feature)
        options = properties.get('options', {})
        
        # Пробуем разные варианты ключей для кадастрового номера
        cad_num = (
            options.get('cad_num') or 
            options.get('cadNumber') or 
            options.get('cad_number') or
            properties.get('cad_num') or
            properties.get('cadNumber') or
            properties.get('cad_number') or
            properties.get('descr', '').strip()
        )
        
        if cad_num and cad_num not in cad_numbers:
            cad_numbers.append(cad_num)
    
    return cad_numbers


def save_json_to_file(data: Any, filepath: str, indent: int = 2, ensure_ascii: bool = False) -> bool:
    """
    Сохраняет данные в JSON файл
    
    Args:
        data: Данные для сохранения
        filepath: Путь к файлу
        indent: Отступ для форматирования
        ensure_ascii: Сохранять ли ASCII символы как есть
    
    Returns:
        bool: True если успешно, False в случае ошибки
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        return True
    except Exception as e:
        print(f"Ошибка при сохранении JSON в файл {filepath}: {e}")
        return False


def load_json_from_file(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Загружает данные из JSON файла
    
    Args:
        filepath: Путь к файлу
    
    Returns:
        Dict: Данные из файла или None в случае ошибки
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка при загрузке JSON из файла {filepath}: {e}")
        return None


def extract_coordinates_from_geometry(geometry: Dict[str, Any]) -> List[Tuple[float, float]]:
    """
    Извлекает координаты из geometry объекта
    
    Args:
        geometry: Объект geometry
    
    Returns:
        List[Tuple[float, float]]: Список координат (x, y) в EPSG:3857
    """
    coordinates = []
    
    if not geometry or not isinstance(geometry, dict):
        return coordinates
    
    geom_type = geometry.get('type')
    coords = geometry.get('coordinates', [])
    
    if geom_type == 'Point':
        if len(coords) >= 2:
            coordinates.append((coords[0], coords[1]))
    elif geom_type == 'Polygon':
        # Polygon имеет структуру [[[x1,y1], [x2,y2], ...]]
        if coords and isinstance(coords[0], list):
            for ring in coords:
                if isinstance(ring, list):
                    for point in ring:
                        if isinstance(point, list) and len(point) >= 2:
                            coordinates.append((point[0], point[1]))
    elif geom_type == 'MultiPolygon':
        # MultiPolygon имеет структуру [[[[x1,y1], [x2,y2], ...]]]
        for polygon in coords:
            if isinstance(polygon, list):
                for ring in polygon:
                    if isinstance(ring, list):
                        for point in ring:
                            if isinstance(point, list) and len(point) >= 2:
                                coordinates.append((point[0], point[1]))
    elif geom_type == 'LineString':
        for point in coords:
            if isinstance(point, list) and len(point) >= 2:
                coordinates.append((point[0], point[1]))
    
    return coordinates


def convert_geometry_to_wgs84(geometry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Преобразует координаты geometry из EPSG:3857 в WGS84
    
    Args:
        geometry: Объект geometry в EPSG:3857
    
    Returns:
        Dict: Объект geometry с координатами в WGS84 или None
    """
    if not geometry or not isinstance(geometry, dict):
        return None
    
    geom_type = geometry.get('type')
    coords = geometry.get('coordinates', [])
    
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    
    def transform_coords(coords_data):
        """Рекурсивно преобразует координаты"""
        if isinstance(coords_data, list):
            if len(coords_data) > 0 and isinstance(coords_data[0], (int, float)):
                # Это точка [x, y]
                if len(coords_data) >= 2:
                    lon, lat = transformer.transform(coords_data[0], coords_data[1])
                    return [lon, lat] + coords_data[2:]
            else:
                # Это список координат
                return [transform_coords(item) for item in coords_data]
        return coords_data
    
    new_geometry = {
        'type': geom_type,
        'coordinates': transform_coords(coords)
    }
    
    return new_geometry


def get_category_id_by_type(object_type: str) -> Optional[str]:
    """
    Получает categoryId по типу объекта
    
    Args:
        object_type: Тип объекта:
            - "ЗУ" или "Земельный участок" -> 36368
            - "Здание" (ОКС) -> 36369
            - "Сооружение" (ОКС) -> 36383
            - "Объект незавершенного строительства" или "ОНС" (ОКС) -> 36384
    
    Returns:
        str: categoryId или None
    """
    category_ids = {
        'ЗУ': '36368',
        'Земельный участок': '36368',  # Альтернативное название
        'Здание': '36369',
        'Сооружение': '36383',
        'Объект незавершенного строительства': '36384',
        'ОНС': '36384'  # Сокращение
    }
    
    return category_ids.get(object_type)


def get_type_by_category_id(category_id: str) -> Optional[str]:
    """
    Получает тип объекта по categoryId
    
    Args:
        category_id: categoryId объекта:
            - 36368 -> "ЗУ" (Земельный участок)
            - 36369 -> "Здание" (ОКС)
            - 36383 -> "Сооружение" (ОКС)
            - 36384 -> "Объект незавершенного строительства" (ОКС)
    
    Returns:
        str: Тип объекта или None
    """
    category_id_to_type = {
        '36368': 'ЗУ',  # Земельный участок
        '36369': 'Здание',  # ОКС
        '36383': 'Сооружение',  # ОКС
        '36384': 'Объект незавершенного строительства'  # ОКС
    }
    
    return category_id_to_type.get(str(category_id))


def is_oks_type(object_type: str) -> bool:
    """
    Проверяет, является ли тип объекта ОКС (Объект капитального строительства)
    
    ОКС включает: Здание, Сооружение, Объект незавершенного строительства
    
    Args:
        object_type: Тип объекта
    
    Returns:
        bool: True если это ОКС (Здание, Сооружение или ОНС)
    """
    oks_types = ['Здание', 'Сооружение', 'Объект незавершенного строительства']
    return object_type in oks_types


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Проверяет валидность координат WGS84
    
    Args:
        lat: Широта в градусах
        lon: Долгота в градусах
    
    Returns:
        bool: True если координаты валидны
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180


def format_cadastral_number(cad_num: str) -> str:
    """
    Форматирует кадастровый номер (удаляет лишние пробелы и символы)
    
    Args:
        cad_num: Кадастровый номер
    
    Returns:
        str: Отформатированный кадастровый номер
    """
    if not cad_num:
        return ""
    
    # Удаляем лишние пробелы и форматируем
    formatted = ' '.join(cad_num.split())
    return formatted.strip()


def extract_descr_from_features(features: List[Dict[str, Any]]) -> List[str]:
    """
    Извлекает описания (descr) из списка features
    
    Args:
        features: Список features
    
    Returns:
        List[str]: Список описаний
    """
    descr_list = []
    
    for feature in features:
        properties = extract_properties_from_feature(feature)
        descr = properties.get('descr', '').strip()
        
        if descr and descr not in descr_list:
            descr_list.append(descr)
    
    return descr_list


def merge_features_by_property(
    features: List[Dict[str, Any]], 
    property_key: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Группирует features по значению свойства
    
    Args:
        features: Список features
        property_key: Ключ свойства для группировки
    
    Returns:
        Dict: Словарь, где ключ - значение свойства, значение - список features
    """
    grouped = {}
    
    for feature in features:
        properties = extract_properties_from_feature(feature)
        value = properties.get(property_key)
        
        if value is not None:
            key = str(value)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(feature)
    
    return grouped

