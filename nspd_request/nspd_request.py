"""
Основной класс для работы с НСПД (Национальная система пространственных данных)
Предоставляет удобный интерфейс для всех типов запросов к НСПД.
"""

import requests
import warnings
import urllib3
import json
import math
import time
from pyproj import Transformer

# Отключаем предупреждения о SSL сертификатах
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Проверка доступности shapely
try:
    from shapely.geometry import Polygon as ShapelyPolygon
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

# Константы для типов объектов
# 36368 = ЗУ (Земельный участок)
# ОКС (Объект капитального строительства) включает:
#   36369 = Здание
#   36383 = Сооружение
#   36384 = ОНС (Объект незавершенного строительства)
CATEGORY_IDS = {
    'ЗУ': '36368',  # Земельный участок
    'Здание': '36369',  # ОКС
    'Сооружение': '36383',  # ОКС
    'ОНС': '36384'  # ОКС (Объект незавершенного строительства)
}

# Типы объектов, относящиеся к ОКС (Объект капитального строительства)
OKS_TYPES = ['Здание', 'Сооружение', 'ОНС']

# Константы для слоев WMS
LAYER_IDS = {
    'ko': '36945',     # Кадастровые округа
    'kk': '36071',     # Кадастровые кварталы
    'kr': '36070',     # Кадастровые районы
    'zu': '36048',     # Земельные участки
    'oks': '36049'     # Объекты капитального строительства
}


class NSPD:
    """
    Основной класс для работы с НСПД.
    Объединяет все функции для удобной работы с НСПД.
    """
    
    def __init__(self, timeout=30):
        """
        Инициализация клиента
        
        :param timeout: Таймаут для запросов в секундах (по умолчанию 30)
        """
        self.timeout = timeout
        self.base_headers = {
            "accept": "*/*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }
        self.transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    
    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================
    
    def _create_bbox_from_wgs84(self, lat, lon, size_meters=100):
        """
        Создает BBOX в EPSG:3857 из координат в WGS84 (EPSG:4326).
        
        Args:
            lat (float): Широта в градусах (WGS84)
            lon (float): Долгота в градусах (WGS84)
            size_meters (float): Размер BBOX в метрах (половина стороны квадрата)
        
        Returns:
            str: BBOX в формате "minX,minY,maxX,maxY" (EPSG:3857)
        """
        center_x, center_y = self.transformer.transform(lon, lat)
        half_size = size_meters / 2
        min_x = center_x - half_size
        min_y = center_y - half_size
        max_x = center_x + half_size
        max_y = center_y + half_size
        return f"{min_x},{min_y},{max_x},{max_y}"
    
    def _make_wms_request(self, layer_id, lat, lon, size_meters=100, referer_url=None):
        """
        Выполняет WMS GetFeatureInfo запрос
        
        Args:
            layer_id (str): ID слоя для запроса
            lat (float): Широта в градусах (WGS84)
            lon (float): Долгота в градусах (WGS84)
            size_meters (float): Размер BBOX в метрах
            referer_url (str): URL для заголовка referer
        
        Returns:
            dict: JSON данные ответа или None в случае ошибки
        """
        url = f"https://nspd.gov.ru/api/aeggis/v3/{layer_id}/wms"
        headers = {
            **self.base_headers,
            "referer": referer_url or f"https://nspd.gov.ru/map?thematic=Default&active_layers={layer_id}"
        }
        params = {
            'REQUEST': 'GetFeatureInfo',
            'QUERY_LAYERS': layer_id,
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'FORMAT': 'image/png',
            'STYLES': '',
            'TRANSPARENT': 'true',
            'LAYERS': layer_id,
            'RANDOM': '0.9717107542714147',
            'INFO_FORMAT': 'application/json',
            'FEATURE_COUNT': '10',
            'I': '146',
            'J': '182',
            'WIDTH': '512',
            'HEIGHT': '512',
            'CRS': 'EPSG:3857',
            'BBOX': self._create_bbox_from_wgs84(lat, lon, size_meters)
        }
        try:
            response = requests.get(url, params=params, headers=headers, verify=False, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return None
    
    def _extract_geom_id(self, response_data):
        """Извлекает geomId из ответа НСПД"""
        try:
            if isinstance(response_data, dict) and 'data' in response_data:
                data = response_data['data']
                if isinstance(data, dict) and 'features' in data:
                    features = data['features']
                    if isinstance(features, list) and len(features) > 0:
                        first_feature = features[0]
                        if isinstance(first_feature, dict) and 'id' in first_feature:
                            return first_feature['id']
            
            possible_paths = [
                ['data', 'id'], ['id'], ['geometry', 'id'],
                ['objectId'], ['featureId']
            ]
            
            for path in possible_paths:
                current = response_data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break
                if current is not None:
                    return current
            return None
        except Exception:
            return None
    
    def _extract_category_id(self, response_data):
        """Извлекает categoryId из ответа НСПД"""
        try:
            if isinstance(response_data, dict) and 'meta' in response_data:
                meta = response_data['meta']
                if isinstance(meta, list) and len(meta) > 0:
                    meta_item = meta[0]
                    if isinstance(meta_item, dict) and 'categoryId' in meta_item:
                        return str(meta_item['categoryId'])
            return None
        except Exception:
            return None
    
    def _extract_registers_id(self, response_data):
        """
        Извлекает registersId из ответа НСПД.
        Ищет сначала в options, затем на верхнем уровне properties.
        
        Args:
            response_data: Данные ответа от НСПД (результат search_by_cadastral_number)
        
        Returns:
            int/str: registersId или None
        """
        try:
            inner_data = (response_data.get('data') or {}) if isinstance(response_data, dict) else {}
            if isinstance(inner_data, dict):
                features = inner_data.get('features') or []
                if features and isinstance(features, list) and len(features) > 0:
                    props = features[0].get('properties') or {}
                    if isinstance(props, dict):
                        options = props.get('options') or {}
                        return options.get('registersId') or props.get('registersId')
            return None
        except Exception:
            return None
    
    # ==================== МЕТОДЫ ПОЛУЧЕНИЯ КАДАСТРОВЫХ ДАННЫХ ====================
    
    def get_cadastral_districts(self, lat, lon, size_meters=100):
        """
        Получает данные о кадастровых округах по координатам
        
        Args:
            lat (float): Широта в градусах (WGS84)
            lon (float): Долгота в градусах (WGS84)
            size_meters (float): Размер BBOX в метрах (по умолчанию 100)
        
        Returns:
            dict: JSON данные с информацией о кадастровых округах или None
        """
        return self._make_wms_request(
            LAYER_IDS['ko'], lat, lon, size_meters,
            referer_url="https://nspd.gov.ru/map?thematic=PKK&zoom=9.418866654256114&coordinate_x=4161705.996407278&coordinate_y=7476079.661860194&theme_id=1&is_copy_url=true&active_layers=36945"
        )
    
    def get_cadastral_quarters(self, lat, lon, size_meters=100):
        """
        Получает данные о кадастровых кварталах по координатам
        
        Args:
            lat (float): Широта в градусах (WGS84)
            lon (float): Долгота в градусах (WGS84)
            size_meters (float): Размер BBOX в метрах (по умолчанию 100)
        
        Returns:
            dict: JSON данные с информацией о кадастровых кварталах или None
        """
        json_data = self._make_wms_request(
            LAYER_IDS['kk'], lat, lon, size_meters,
            referer_url="https://nspd.gov.ru/map?thematic=Default&zoom=12.991584994290786&coordinate_x=4197848.0753117725&coordinate_y=7511403.423208106&theme_id=1&is_copy_url=true&active_layers=36071"
        )
        
        if json_data and 'features' in json_data and isinstance(json_data['features'], list):
            json_data['features'] = [
                feature for feature in json_data['features']
                if not (feature.get('properties', {}).get('descr', '').endswith('0000000'))
            ]
        return json_data
    
    def get_cadastral_regions(self, lat, lon, size_meters=1):
        """
        Получает данные о кадастровых районах по координатам
        
        Args:
            lat (float): Широта в градусах (WGS84)
            lon (float): Долгота в градусах (WGS84)
            size_meters (float): Размер BBOX в метрах (по умолчанию 1)
        
        Returns:
            dict: JSON данные с информацией о кадастровых районах или None
        """
        json_data = self._make_wms_request(
            LAYER_IDS['kr'], lat, lon, size_meters,
            referer_url="https://nspd.gov.ru/map?thematic=Default&zoom=9.052266605613186&coordinate_x=4179847.4293297087&coordinate_y=7491747.432488616&baseLayerId=235&theme_id=1&is_copy_url=true&active_layers=36070"
        )
        
        if json_data and 'features' in json_data and isinstance(json_data['features'], list):
            json_data['features'] = [
                feature for feature in json_data['features']
                if not (feature.get('properties', {}).get('descr', '').endswith(':00'))
            ]
        return json_data
    
    # ==================== МЕТОДЫ РАБОТЫ С КАДАСТРОВЫМИ НОМЕРАМИ ====================
    
    def search_by_cadastral_number(self, kad_number):
        """
        Получает данные из НСПД по кадастровому номеру
        
        Args:
            kad_number: Кадастровый номер
        
        Returns:
            dict: Данные из НСПД или словарь с ошибкой
        """
        url_template = "https://nspd.gov.ru/api/geoportal/v2/search/geoportal?query={}&thematicSearchId=1"
        headers = {
            **self.base_headers,
            "referer": "https://nspd.gov.ru/map?thematic=PKK&zoom=20&coordinate_x=4187280.1010340527&coordinate_y=7507815.775997361&theme_id=1&is_copy_url=true&active_layers=%E8%B3%91%2C%E8%B3%90"
        }
        url = url_template.format(kad_number)
        
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=self.timeout)
            if response.status_code == 200:
                response_data = response.json()
                if response_data is None:
                    return {"error": f"Не нашли данные в ответе НСПД для кадастрового номера {kad_number}"}
                
                # Проверяем, что данные действительно содержат информацию об объекте
                # Если нет features в data, значит объект не найден
                has_features = False
                if 'data' in response_data and isinstance(response_data['data'], dict):
                    features = response_data['data'].get('features', [])
                    if features and len(features) > 0:
                        has_features = True
                
                # Если нет features, объект не найден
                if not has_features:
                    return {"error": f"Объект с кадастровым номером {kad_number} не найден в НСПД"}
                
                response_data["kad_number"] = kad_number
                geom_id = self._extract_geom_id(response_data)
                if geom_id:
                    response_data["geom_id"] = geom_id
                return response_data
            else:
                return {"error": f"Ошибка HTTP {response.status_code} для кадастрового номера {kad_number}"}
        except requests.RequestException as e:
            return {"error": f"Исключение при запросе для кадастрового номера {kad_number}: {e}"}
    
    def get_object_info(self, kad_number, include_geom_id=False, include_object_type=False, include_related=False):
        """
        Универсальная функция для получения информации об объекте
        
        Args:
            kad_number: Кадастровый номер
            include_geom_id: Включить geom_id в результат
            include_object_type: Включить object_type в результат
            include_related: Включить связанные объекты в результат
        
        Returns:
            dict: Словарь с данными и дополнительными полями (если запрошены)
        """
        data = self.search_by_cadastral_number(kad_number)
        
        if "error" in data:
            return data
        
        if include_geom_id:
            geom_id = data.get("geom_id")
            if not geom_id:
                geom_id = self._extract_geom_id(data)
            data["geom_id"] = geom_id
        
        if include_object_type:
            category_id = self._extract_category_id(data)
            if category_id:
                for obj_type, cat_id in CATEGORY_IDS.items():
                    if cat_id == category_id:
                        data["object_type"] = obj_type
                        break
        
        if include_related:
            geom_id = data.get("geom_id")
            object_type = data.get("object_type")
            if not object_type:
                category_id = self._extract_category_id(data)
                if category_id:
                    for obj_type, cat_id in CATEGORY_IDS.items():
                        if cat_id == category_id:
                            object_type = obj_type
                            break
            
            if geom_id and object_type:
                if object_type == "ЗУ":
                    # Для ЗУ получаем связанные ОКС
                    related = self.get_oks_by_land_plot(geom_id)
                    # Резервный поиск, если основной не нашёл связей
                    if not related:
                        related = self._get_oks_by_land_plot_fallback(geom_id, data)
                elif self._is_oks_type(object_type):
                    # Для всех типов ОКС получаем связанные ЗУ
                    related = self.get_land_plots_by_oks(geom_id)
                    # Резервный поиск, если основной не нашёл связей
                    if not related:
                        related = self._get_land_plots_by_oks_fallback(geom_id, data)
                else:
                    related = []
                data["related"] = related if related else []
        
        return data
    
    def get_geom_id(self, kad_number):
        """
        Получает только geom_id по кадастровому номеру
        
        Args:
            kad_number: Кадастровый номер
        
        Returns:
            str: geom_id или None в случае ошибки или если объект не найден
        """
        if not kad_number or not kad_number.strip():
            return None
        
        data = self.search_by_cadastral_number(kad_number)
        if "error" in data:
            return None
        
        # Проверяем, что данные действительно содержат информацию об объекте
        # Если нет features в data, значит объект не найден
        if 'data' in data and isinstance(data['data'], dict):
            features = data['data'].get('features', [])
            if not features or len(features) == 0:
                return None
        
        geom_id = data.get("geom_id")
        
        # Если geom_id не найден в данных, пробуем извлечь его напрямую
        if not geom_id:
            geom_id = self._extract_geom_id(data)
        
        # Проверяем, что geom_id валиден (может быть int или str)
        if geom_id is None:
            return None
        
        # Конвертируем в строку, если это число
        if isinstance(geom_id, int):
            return str(geom_id)
        elif isinstance(geom_id, str):
            # Проверяем, что строка не пустая
            if not geom_id.strip():
                return None
            return geom_id
        else:
            # Если это другой тип, конвертируем в строку
            return str(geom_id)
    
    def get_object_type(self, kad_number):
        """
        Определяет точный тип объекта по кадастровому номеру
        
        Args:
            kad_number: Кадастровый номер
        
        Returns:
            str: Тип объекта ("ЗУ", "Здание", "Сооружение", "ОНС") или None
        """
        data = self.search_by_cadastral_number(kad_number)
        if "error" in data:
            return None
        
        category_id = self._extract_category_id(data)
        if category_id:
            for obj_type, cat_id in CATEGORY_IDS.items():
                if cat_id == category_id:
                    return obj_type
        return None
    
    # ==================== МЕТОДЫ ПОЛУЧЕНИЯ СВЯЗАННЫХ ОБЪЕКТОВ ====================
    
    def get_land_plots_by_oks(self, geom_id, debug=False):
        """
        Получает список ЗУ (Земельных участков) по geomId ОКС (Объект капитального строительства)
        Работает для всех типов ОКС: Здание, Сооружение, ОНС
        
        Args:
            geom_id: ID геометрии ОКС
            debug: Включить отладочную информацию
        
        Returns:
            list: Список ЗУ или None в случае ошибки
        """
        try:
            url = f"https://nspd.gov.ru/api/geoportal/v1/tab-values-data"
            category_ids = [CATEGORY_IDS['Здание'], CATEGORY_IDS['Сооружение'], CATEGORY_IDS['ОНС']]
            
            for category_id in category_ids:
                params = {
                    'tabClass': 'landLinks',
                    'categoryId': category_id,
                    'geomId': geom_id
                }
                headers = {
                    **self.base_headers,
                    'referer': 'https://nspd.gov.ru/map?thematic=PKK&zoom=17.690976575074885&coordinate_x=4191326.8832895053&coordinate_y=7501296.123874589&theme_id=1&baseLayerId=235&is_copy_url=true&active_layers=36049,36048'
                }
                
                if debug:
                    print(f"Запрос списка ЗУ для ОКС geomId: {geom_id} с categoryId: {category_id}")
                
                response = requests.get(url, params=params, headers=headers, verify=False, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    zu_list = []
                    
                    if isinstance(data, dict) and 'value' in data and isinstance(data['value'], list):
                        zu_list = [value.strip() for value in data['value'] if value and value.strip()]
                    elif isinstance(data, dict) and 'object' in data and isinstance(data['object'], list):
                        for obj in data['object']:
                            if isinstance(obj, dict) and 'value' in obj and isinstance(obj['value'], list):
                                for value in obj['value']:
                                    if value and value.strip():
                                        zu_list.append(value.strip())
                    
                    if debug:
                        print(f"Найдено ЗУ: {len(zu_list)} с categoryId: {category_id}")
                    
                    if zu_list:
                        return zu_list
                elif response.status_code == 500:
                    try:
                        error_data = response.json()
                        if error_data.get('code') == 1023:
                            if debug:
                                print(f"Получена ошибка 500 с кодом 1023 для categoryId: {category_id}, пробуем следующий...")
                            continue
                    except:
                        pass
            
            return None
        except Exception as e:
            if debug:
                print(f"Исключение при запросе списка ЗУ для geomId {geom_id}: {e}")
            return None
    
    def get_oks_by_land_plot(self, geom_id, debug=False):
        """
        Получает список ОКС (Объект капитального строительства) по geomId ЗУ
        Возвращает все типы ОКС: Здание, Сооружение, ОНС
        
        Args:
            geom_id: ID геометрии ЗУ (Земельный участок)
            debug: Включить отладочную информацию
        
        Returns:
            list: Список ОКС или None в случае ошибки
        """
        try:
            url = f"https://nspd.gov.ru/api/geoportal/v1/tab-group-data"
            params = {
                'tabClass': 'objectsList',
                'categoryId': CATEGORY_IDS['ЗУ'],
                'geomId': geom_id
            }
            headers = {
                **self.base_headers,
                'referer': 'https://nspd.gov.ru/map?thematic=PKK&zoom=17.690976575074885&coordinate_x=4191326.8832895053&coordinate_y=7501296.123874589&theme_id=1&baseLayerId=235&is_copy_url=true&active_layers=36049,36048'
            }
            
            if debug:
                print(f"Запрос списка ОКС для ЗУ geomId: {geom_id}")
            
            response = requests.get(url, params=params, headers=headers, verify=False, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                oks_list = []
                
                if isinstance(data, dict) and 'object' in data and isinstance(data['object'], list):
                    for obj in data['object']:
                        if isinstance(obj, dict) and 'value' in obj and isinstance(obj['value'], list):
                            for value in obj['value']:
                                if value and value.strip():
                                    oks_list.append(value.strip())
                elif isinstance(data, dict):
                    if 'data' in data and isinstance(data['data'], list):
                        oks_list = data['data']
                    elif 'items' in data and isinstance(data['items'], list):
                        oks_list = data['items']
                    elif 'objects' in data and isinstance(data['objects'], list):
                        oks_list = data['objects']
                    elif 'features' in data and isinstance(data['features'], list):
                        oks_list = data['features']
                elif isinstance(data, list):
                    oks_list = data
                
                if debug:
                    print(f"Найдено ОКС: {len(oks_list)}")
                
                return oks_list if oks_list else None
            else:
                if debug:
                    print(f"Ошибка запроса списка ОКС: {response.status_code} для geomId: {geom_id}")
                return None
        except Exception as e:
            if debug:
                print(f"Исключение при запросе списка ОКС для geomId {geom_id}: {e}")
            return None
    
    def _get_land_plots_by_oks_fallback(self, geom_id, response_data, debug=False):
        """
        Резервный метод получения связанных ЗУ для ОКС через tab-values-data
        с параметрами objdocId и registersId.
        Используется, когда основной метод get_land_plots_by_oks не нашёл связей.
        
        Args:
            geom_id: ID геометрии ОКС (будет использован как objdocId)
            response_data: Полные данные ответа от search_by_cadastral_number
            debug: Включить отладочную информацию
        
        Returns:
            list: Список кадастровых номеров ЗУ или None
        """
        try:
            registers_id = self._extract_registers_id(response_data)
            
            # Если registersId не найден — используем значение по умолчанию
            if registers_id is None:
                registers_id = 36441
            
            if debug:
                print(f"Fallback: запрос tab-values-data с objdocId={geom_id}, registersId={registers_id}")
            
            url = "https://nspd.gov.ru/api/geoportal/v1/tab-values-data"
            params = {
                'tabClass': 'landLinks',
                'objdocId': geom_id,
                'registersId': registers_id
            }
            headers = {
                **self.base_headers,
                'referer': (
                    'https://nspd.gov.ru/map?thematic=PKK&theme_id=1&is_copy_url=true'
                    '&active_layers=36329%2C36328%2C36049%2C36945'
                )
            }
            
            response = requests.get(url, params=params, headers=headers, verify=False, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                zu_list = []
                
                if isinstance(data, dict) and 'value' in data and isinstance(data['value'], list):
                    zu_list = [v.strip() for v in data['value'] if v and v.strip()]
                
                if debug:
                    print(f"Fallback: найдено ЗУ: {len(zu_list)}")
                
                return zu_list if zu_list else None
            else:
                if debug:
                    print(f"Fallback: ошибка HTTP {response.status_code}")
                return None
        except Exception as e:
            if debug:
                print(f"Fallback: исключение при запросе tab-values-data: {e}")
            return None
    
    def _get_oks_by_land_plot_fallback(self, geom_id, response_data, debug=False):
        """
        Резервный метод получения связанных ОКС для ЗУ через tab-group-data
        с параметрами objdocId и registersId.
        Используется, когда основной метод get_oks_by_land_plot не нашёл связей.
        
        Args:
            geom_id: ID геометрии ЗУ (будет использован как objdocId)
            response_data: Полные данные ответа от search_by_cadastral_number
            debug: Включить отладочную информацию
        
        Returns:
            list: Список кадастровых номеров ОКС или None
        """
        try:
            registers_id = self._extract_registers_id(response_data)
            
            if registers_id is None:
                registers_id = 36440
            
            if debug:
                print(f"Fallback ЗУ→ОКС: запрос tab-group-data с objdocId={geom_id}, registersId={registers_id}")
            
            url = "https://nspd.gov.ru/api/geoportal/v1/tab-group-data"
            params = {
                'tabClass': 'objectsList',
                'objdocId': geom_id,
                'registersId': registers_id
            }
            headers = {
                **self.base_headers,
                'referer': (
                    'https://nspd.gov.ru/map?thematic=PKK&theme_id=1&is_copy_url=true'
                    '&active_layers=36329%2C36328%2C36049%2C36945'
                )
            }
            
            response = requests.get(url, params=params, headers=headers, verify=False, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                oks_list = []
                
                # Кадастры из object[*].value
                if isinstance(data, dict) and 'object' in data and isinstance(data['object'], list):
                    for obj in data['object']:
                        if isinstance(obj, dict) and 'value' in obj and isinstance(obj['value'], list):
                            for value in obj['value']:
                                if value and value.strip():
                                    oks_list.append(value.strip())
                
                if debug:
                    print(f"Fallback ЗУ→ОКС: найдено ОКС: {len(oks_list)}")
                
                return oks_list if oks_list else None
            else:
                if debug:
                    print(f"Fallback ЗУ→ОКС: ошибка HTTP {response.status_code}")
                return None
        except Exception as e:
            if debug:
                print(f"Fallback ЗУ→ОКС: исключение при запросе tab-group-data: {e}")
            return None
    
    def _is_oks_type(self, object_type):
        """
        Проверяет, является ли тип объекта ОКС (Объект капитального строительства)
        
        Args:
            object_type: Тип объекта
        
        Returns:
            bool: True если это ОКС (Здание, Сооружение или ОНС)
        """
        return object_type in OKS_TYPES
    
    def _determine_object_type_from_data(self, data):
        """
        Определяет точный тип объекта из уже полученных данных
        
        Args:
            data: Данные ответа от НСПД
        
        Returns:
            str: "ЗУ" (Земельный участок), "Здание" (ОКС), "Сооружение" (ОКС), 
                 "ОНС" (ОКС) или None
        """
        # Извлекаем categoryId из meta
        category_id = self._extract_category_id(data)
        
        # Определяем точный тип по categoryId
        if category_id:
            for obj_type, cat_id in CATEGORY_IDS.items():
                if cat_id == category_id:
                    return obj_type
        
        # Если не удалось определить по categoryId, пробуем через связи
        geom_id = data.get("geom_id")
        if geom_id:
            # Пробуем получить ОКС (если это ЗУ)
            oks_list = self.get_oks_by_land_plot(geom_id)
            if oks_list and len(oks_list) > 0:
                return "ЗУ"
            
            # Пробуем получить ЗУ (если это ОКС - любой тип: Здание, Сооружение или ОНС)
            zu_list = self.get_land_plots_by_oks(geom_id)
            if zu_list and len(zu_list) > 0:
                # Если нашли ЗУ, значит это какой-то тип ОКС, но точный тип неизвестен
                # Возвращаем None, чтобы попробовать определить точнее
                return None
        
        return None
    
    def get_related_objects(self, kad_number, debug=False):
        """
        Получает связанные объекты по кадастровому номеру
        
        Args:
            kad_number: Кадастровый номер
            debug: Включить отладочную информацию
        
        Returns:
            dict: Словарь с данными объекта и связанными объектами.
                  type может быть: "ЗУ", "Здание", "Сооружение", "ОНС"
        """
        result = {
            "data": None,
            "geom_id": None,
            "related": [],
            "type": None,
            "error": None
        }
        
        data = self.search_by_cadastral_number(kad_number)
        
        if "error" in data and data["error"]:
            result["error"] = data["error"]
            return result
        
        result["data"] = data
        result["geom_id"] = data.get("geom_id")
        
        if not result["geom_id"]:
            result["error"] = "Не удалось извлечь geomId из ответа"
            return result
        
        if debug:
            print(f"Извлечен geomId: {result['geom_id']}")
        
        # Определяем точный тип объекта
        object_type = self._determine_object_type_from_data(data)
        if not object_type:
            # Пробуем определить тип через category_id напрямую
            category_id = self._extract_category_id(data)
            if category_id:
                for obj_type, cat_id in CATEGORY_IDS.items():
                    if cat_id == category_id:
                        object_type = obj_type
                        break
            
            if not object_type:
                result["error"] = "Не удалось определить тип объекта"
                return result
        
        result["type"] = object_type
        
        # Для ЗУ (Земельный участок) получаем связанные ОКС
        if object_type == "ЗУ":
            oks_list = self.get_oks_by_land_plot(result["geom_id"], debug)
            if oks_list:
                result["related"] = oks_list
                if debug:
                    print(f"Найдено связанных ОКС: {len(oks_list)}")
            else:
                # Резервный поиск через tab-group-data с objdocId/registersId
                if debug:
                    print("Основной поиск ОКС не дал результатов, пробуем fallback (tab-group-data с objdocId)...")
                oks_list_fallback = self._get_oks_by_land_plot_fallback(result["geom_id"], data, debug)
                if oks_list_fallback:
                    result["related"] = oks_list_fallback
                    if debug:
                        print(f"Fallback: найдено связанных ОКС: {len(oks_list_fallback)}")
        # Для всех типов ОКС (Объект капитального строительства: Здание, Сооружение, ОНС) получаем связанные ЗУ
        elif self._is_oks_type(object_type):
            zu_list = self.get_land_plots_by_oks(result["geom_id"], debug)
            if zu_list:
                result["related"] = zu_list
                if debug:
                    print(f"Найдено связанных ЗУ: {len(zu_list)}")
            else:
                # Резервный поиск через tab-values-data с objdocId/registersId
                if debug:
                    print("Основной поиск ЗУ не дал результатов, пробуем fallback (tab-values-data с objdocId)...")
                zu_list_fallback = self._get_land_plots_by_oks_fallback(result["geom_id"], data, debug)
                if zu_list_fallback:
                    result["related"] = zu_list_fallback
                    if debug:
                        print(f"Fallback: найдено связанных ЗУ: {len(zu_list_fallback)}")
        
        return result
    
    # ==================== МЕТОДЫ ПОЛУЧЕНИЯ ПО КООРДИНАТАМ ====================
    
    def get_by_coordinates(self, latitude, longitude, object_type='land_plot', bbox_size=0.05):
        """
        Универсальная функция для получения кадастрового номера по координатам
        
        Args:
            latitude: Широта в градусах (WGS84)
            longitude: Долгота в градусах (WGS84)
            object_type: Тип объекта ('land_plot' или 'zu' для ЗУ, 'oks' для ОКС - любого типа)
            bbox_size: Размер BBOX в метрах (по умолчанию 0.05)
        
        Returns:
            str: Кадастровый номер или None в случае ошибки
        """
        if object_type == 'land_plot' or object_type == 'zu':
            return self.get_land_plot_by_coordinates(latitude, longitude, bbox_size)
        elif object_type == 'oks':
            return self.get_oks_by_coordinates(latitude, longitude, bbox_size)
        else:
            raise ValueError(f"Неизвестный тип объекта: {object_type}. Используйте 'land_plot' или 'oks'")
    
    def get_land_plot_by_coordinates(self, latitude, longitude, bbox_size=0.05):
        """
        Получает кадастровый номер ЗУ по координатам
        
        Args:
            latitude: Широта в градусах (WGS84)
            longitude: Долгота в градусах (WGS84)
            bbox_size: Размер BBOX в метрах (по умолчанию 0.05)
        
        Returns:
            str: Кадастровый номер ЗУ или None в случае ошибки
        """
        try:
            bbox = self._create_bbox_from_wgs84(latitude, longitude, bbox_size)
            url = f"https://nspd.gov.ru/api/aeggis/v3/{LAYER_IDS['zu']}/wms"
            
            params = {
                'REQUEST': 'GetFeatureInfo',
                'QUERY_LAYERS': LAYER_IDS['zu'],
                'SERVICE': 'WMS',
                'VERSION': '1.3.0',
                'FORMAT': 'image/png',
                'STYLES': '',
                'TRANSPARENT': 'true',
                'LAYERS': LAYER_IDS['zu'],
                'RANDOM': '0.915965686899393',
                'INFO_FORMAT': 'application/json',
                'FEATURE_COUNT': '10',
                'I': '305',
                'J': '183',
                'WIDTH': '512',
                'HEIGHT': '512',
                'CRS': 'EPSG:3857',
                'BBOX': bbox
            }
            
            headers = {
                **self.base_headers,
                'referer': 'https://nspd.gov.ru/map?thematic=PKK&zoom=17.690976575074885&coordinate_x=4191326.8832895053&coordinate_y=7501296.123874589&theme_id=1&baseLayerId=235&is_copy_url=true&active_layers=36048'
            }
            
            response = requests.get(url, params=params, headers=headers, verify=False, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'features' in data and data['features']:
                    feature = data['features'][0]
                    properties = feature.get('properties', {})
                    options = properties.get('options', {})
                    cad_num = options.get('cad_num', '')
                    return cad_num if cad_num else None
            return None
        except Exception:
            return None
    
    def get_oks_by_coordinates(self, latitude, longitude, bbox_size=0.05):
        """
        Получает кадастровый номер ОКС по координатам
        
        Args:
            latitude: Широта в градусах (WGS84)
            longitude: Долгота в градусах (WGS84)
            bbox_size: Размер BBOX в метрах (по умолчанию 0.05)
        
        Returns:
            str: Кадастровый номер ОКС или None в случае ошибки
        """
        try:
            bbox = self._create_bbox_from_wgs84(latitude, longitude, bbox_size)
            url = f"https://nspd.gov.ru/api/aeggis/v3/{LAYER_IDS['oks']}/wms"
            
            params = {
                'REQUEST': 'GetFeatureInfo',
                'QUERY_LAYERS': LAYER_IDS['oks'],
                'SERVICE': 'WMS',
                'VERSION': '1.3.0',
                'FORMAT': 'image/png',
                'STYLES': '',
                'TRANSPARENT': 'true',
                'LAYERS': LAYER_IDS['oks'],
                'RANDOM': '0.915965686899393',
                'INFO_FORMAT': 'application/json',
                'FEATURE_COUNT': '10',
                'I': '305',
                'J': '183',
                'WIDTH': '512',
                'HEIGHT': '512',
                'CRS': 'EPSG:3857',
                'BBOX': bbox
            }
            
            headers = {
                **self.base_headers,
                'referer': 'https://nspd.gov.ru/map?thematic=PKK&zoom=17.690976575074885&coordinate_x=4191326.8832895053&coordinate_y=7501296.123874589&theme_id=1&baseLayerId=235&is_copy_url=true&layers=36049'
            }
            
            response = requests.get(url, params=params, headers=headers, verify=False, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'features' in data and data['features']:
                    feature = data['features'][0]
                    properties = feature.get('properties', {})
                    options = properties.get('options', {})
                    cad_num = options.get('cad_num') or options.get('cadNumber') or options.get('cad_number', '')
                    return cad_num if cad_num else None
            return None
        except Exception:
            return None
    
    # ==================== МЕТОДЫ ДЛЯ GRID ====================
    
    def _extract_polygons_from_features(self, json_data):
        """Извлекает координаты полигонов из features"""
        polygons = []
        if not json_data or 'features' not in json_data:
            return polygons
        
        for feature in json_data.get('features', []):
            geometry = feature.get('geometry', {})
            geom_type = geometry.get('type')
            coords = geometry.get('coordinates', [])
            properties = feature.get('properties', {})
            feature_id = feature.get('id', '')
            
            try:
                if geom_type == 'Polygon':
                    outer_ring = coords[0] if coords else []
                    if outer_ring and len(outer_ring) > 0:
                        polygon_coords = [list(point) for point in outer_ring]
                        if polygon_coords[0] != polygon_coords[-1]:
                            polygon_coords.append(polygon_coords[0])
                        polygons.append({
                            'coords': polygon_coords,
                            'properties': properties,
                            'id': feature_id
                        })
                elif geom_type == 'MultiPolygon':
                    for polygon_group in coords:
                        if polygon_group and len(polygon_group) > 0:
                            outer_ring = polygon_group[0]
                            if outer_ring and len(outer_ring) > 0:
                                polygon_coords = [list(point) for point in outer_ring]
                                if polygon_coords[0] != polygon_coords[-1]:
                                    polygon_coords.append(polygon_coords[0])
                                polygons.append({
                                    'coords': polygon_coords,
                                    'properties': properties,
                                    'id': feature_id
                                })
            except Exception as e:
                print(f"Ошибка при извлечении полигона: {e}")
                continue
        
        return polygons
    
    def _calculate_polygon_area_3857(self, coords):
        """Вычисляет площадь полигона в квадратных метрах (EPSG:3857)"""
        if not SHAPELY_AVAILABLE or len(coords) < 3:
            return 0
        
        try:
            coords_list = coords[:-1] if len(coords) > 1 and coords[0] == coords[-1] else coords
            coords_shapely = [(coord[0], coord[1]) for coord in coords_list]
            shapely_poly = ShapelyPolygon(coords_shapely)
            
            if not shapely_poly.is_valid:
                shapely_poly = shapely_poly.buffer(0)
            
            if shapely_poly.is_empty:
                return 0
            
            return abs(shapely_poly.area)
        except Exception as e:
            print(f"Ошибка при вычислении площади: {e}")
            return 0
    
    def _split_large_polygon_3857(self, coords, num_parts=20):
        """Разбивает большой полигон на несколько частей"""
        if not SHAPELY_AVAILABLE:
            return [coords]
        
        try:
            coords_list = coords[:-1] if len(coords) > 1 and coords[0] == coords[-1] else coords
            coords_shapely = [(coord[0], coord[1]) for coord in coords_list]
            shapely_poly = ShapelyPolygon(coords_shapely)
            
            if not shapely_poly.is_valid:
                shapely_poly = shapely_poly.buffer(0)
            
            if shapely_poly.is_empty:
                return [coords]
            
            bounds = shapely_poly.bounds
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            
            if width == 0 or height == 0:
                return [coords]
            
            aspect_ratio = width / height
            grid_rows = max(1, int(math.sqrt(num_parts / aspect_ratio)))
            grid_cols = max(1, int(math.ceil(num_parts / grid_rows)))
            
            while grid_cols * grid_rows < num_parts:
                if width > height:
                    grid_cols += 1
                else:
                    grid_rows += 1
            
            cell_width = width / grid_cols
            cell_height = height / grid_rows
            min_cell_area_threshold = (cell_width * cell_height) * 0.001
            
            parts = []
            for row in range(grid_rows):
                for col in range(grid_cols):
                    minx = bounds[0] + col * cell_width
                    maxx = bounds[0] + (col + 1) * cell_width
                    miny = bounds[1] + row * cell_height
                    maxy = bounds[1] + (row + 1) * cell_height
                    
                    cell_poly = ShapelyPolygon([
                        (minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy), (minx, miny)
                    ])
                    
                    try:
                        intersection = shapely_poly.intersection(cell_poly)
                        
                        if not intersection.is_empty and intersection.area > min_cell_area_threshold:
                            if intersection.geom_type == 'Polygon':
                                if intersection.is_valid and len(intersection.exterior.coords) >= 4:
                                    part_coords = list(intersection.exterior.coords)
                                    part_coords_formatted = [[coord[0], coord[1]] for coord in part_coords]
                                    if len(part_coords_formatted) >= 3:
                                        if part_coords_formatted[0] != part_coords_formatted[-1]:
                                            part_coords_formatted.append(part_coords_formatted[0])
                                        parts.append(part_coords_formatted)
                            elif intersection.geom_type == 'MultiPolygon':
                                for poly in intersection.geoms:
                                    if poly.is_valid and len(poly.exterior.coords) >= 4 and poly.area > min_cell_area_threshold:
                                        part_coords = list(poly.exterior.coords)
                                        part_coords_formatted = [[coord[0], coord[1]] for coord in part_coords]
                                        if len(part_coords_formatted) >= 3:
                                            if part_coords_formatted[0] != part_coords_formatted[-1]:
                                                part_coords_formatted.append(part_coords_formatted[0])
                                            parts.append(part_coords_formatted)
                    except Exception:
                        continue
            
            if not parts:
                return [coords]
            return parts
        except Exception as e:
            print(f"Ошибка при разбиении полигона: {e}")
            return [coords]
    
    def _split_polygons_by_area_3857(self, polygons, target_count):
        """Разбивает все полигоны так, чтобы получить примерно target_count полигонов"""
        if not SHAPELY_AVAILABLE:
            return polygons
        
        polygons_with_area = []
        total_area = 0
        for p in polygons:
            area = self._calculate_polygon_area_3857(p['coords'])
            polygons_with_area.append((area, p))
            total_area += area
        
        if total_area == 0:
            return polygons
        
        target_area = total_area / target_count
        result_polygons = []
        max_part_area = target_area * 1.2
        
        for area, polygon_data in polygons_with_area:
            if area <= max_part_area:
                result_polygons.append(polygon_data)
            else:
                num_parts = int(math.ceil(area / max_part_area))
                num_parts = max(2, num_parts)
                
                split_parts = self._split_large_polygon_3857(polygon_data['coords'], num_parts=num_parts)
                
                for part_idx, part_coords in enumerate(split_parts):
                    part_area = self._calculate_polygon_area_3857(part_coords)
                    if part_area > 0:
                        if part_area > max_part_area * 1.5:
                            num_sub_parts = int(math.ceil(part_area / max_part_area))
                            sub_parts = self._split_large_polygon_3857(part_coords, num_parts=num_sub_parts)
                            for sub_idx, sub_coords in enumerate(sub_parts):
                                sub_area = self._calculate_polygon_area_3857(sub_coords)
                                if sub_area > 0:
                                    result_polygons.append({
                                        'coords': sub_coords,
                                        'properties': polygon_data['properties'],
                                        'id': f"{polygon_data['id']}_part{part_idx+1}_sub{sub_idx+1}"
                                    })
                        else:
                            result_polygons.append({
                                'coords': part_coords,
                                'properties': polygon_data['properties'],
                                'id': f"{polygon_data['id']}_part{part_idx+1}"
                            })
        
        return result_polygons
    
    def _make_grid_request(self, polygon_coords, category_id=36368):
        """Делает запрос в grid используя полигон"""
        url = "https://nspd.gov.ru/api/geoportal/v1/intersects?typeIntersect=fullObject"
        headers = {
            "referer": "https://nspd.gov.ru/map?zoom=14&coordinate_x=4184142&coordinate_y=7513154&baseLayerId=235&theme_id=1",
            "Content-Type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }
        
        payload = {
            "geom": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "crs": {
                                "properties": {"name": "EPSG:3857"},
                                "type": "name"
                            },
                            "type": "Polygon",
                            "coordinates": [polygon_coords]
                        },
                        "properties": {}
                    }
                ]
            },
            "categories": [{"id": category_id}]
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, verify=False, timeout=120)
                response.raise_for_status()
                data = response.json()
                
                if 'features' in data:
                    return data['features']
                return []
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  Ошибка: {e}, повтор через 10 сек... (попытка {attempt + 1}/{max_retries})")
                    time.sleep(10)
                else:
                    print(f"  Ошибка после {max_retries} попыток: {e}")
                    return []
    
    def get_grid_data(self, lat, lon, boundary_type='kr', category_id=36368, verbose=False):
        """
        Удобная функция для получения данных из grid используя координаты и тип границы.
        
        Args:
            lat (float): Широта в градусах (WGS84)
            lon (float): Долгота в градусах (WGS84)
            boundary_type (str): Тип границы - 'kr' (район), 'kk' (квартал), или 'ko' (округ)
            category_id (int): ID категории для запроса в grid (по умолчанию 36368 - ЗУ)
            verbose (bool): Выводить ли подробную информацию о процессе
        
        Returns:
            dict: FeatureCollection с результатами запросов или None в случае ошибки
        """
        test_size = 1
        
        if verbose:
            print(f"Используется тип границы: {boundary_type}")
            print(f"Координаты: {lat}, {lon}, размер: {test_size}м")
        
        # Выбираем нужную функцию
        if boundary_type == 'kr':
            json_data = self.get_cadastral_regions(lat, lon, test_size)
        elif boundary_type == 'kk':
            json_data = self.get_cadastral_quarters(lat, lon, test_size)
        elif boundary_type == 'ko':
            json_data = self.get_cadastral_districts(lat, lon, test_size)
        else:
            raise ValueError(f"Неизвестный тип границы: {boundary_type}. Используйте 'kr', 'kk' или 'ko'")
        
        if not json_data:
            if verbose:
                print("Не удалось получить данные из функции")
            return None
        
        # Извлекаем полигоны из features
        if verbose:
            print(f"\nИзвлечение полигонов из features...")
        polygons = self._extract_polygons_from_features(json_data)
        if verbose:
            print(f"Извлечено полигонов: {len(polygons)}")
        
        if not polygons:
            if verbose:
                print("Не найдено полигонов для обработки")
            return None
        
        # Определяем target_count на основе cnt_land_geom и cnt_oks_geom
        target_count = 30
        if polygons:
            props = polygons[0].get('properties', {})
            options = props.get('options', {})
            cnt_land_geom = options.get('cnt_land_geom', 0)
            cnt_oks_geom = options.get('cnt_oks_geom', 0)
            
            if verbose:
                print(f"cnt_land_geom: {cnt_land_geom}, cnt_oks_geom: {cnt_oks_geom}")
            
            max_value = max(cnt_land_geom, cnt_oks_geom)
            
            if max_value > 0:
                max_str = str(max_value)
                num_digits = len(max_str)
                
                if num_digits < 5:
                    target_count = 1
                    if verbose:
                        print(f"Максимальное значение: {max_value} (< 5 цифр), используем 1 полигон")
                else:
                    remaining_digits = max_str[:-4]
                    if remaining_digits:
                        first_digits = int(remaining_digits)
                        target_count = ((first_digits + 9) // 10) * 10
                        target_count = max(10, target_count)
                        if verbose:
                            print(f"Максимальное значение: {max_value}, убрали последние 4 цифры: {remaining_digits} ({first_digits}), округлено вверх: {target_count}")
                    else:
                        target_count = 1
                        if verbose:
                            print(f"Максимальное значение: {max_value}, после удаления последних 4 цифр ничего не осталось, используем 1 полигон")
            else:
                if verbose:
                    print("Не найдены cnt_land_geom и cnt_oks_geom, используем значение по умолчанию: 30")
        
        # Разбиваем полигоны по площади
        if verbose:
            print(f"\nРазбиваем полигоны так, чтобы получить примерно {target_count} полигонов одинаковой площади...")
        processed_polygons = self._split_polygons_by_area_3857(polygons, target_count)
        if verbose:
            print(f"После разбиения: {len(processed_polygons)} полигонов")
        
        # Делаем запросы в grid для каждого полигона
        if verbose:
            print(f"\nВыполнение запросов в grid...")
        all_features = []
        seen_ids = set()
        
        for i, polygon_data in enumerate(processed_polygons):
            polygon_coords = polygon_data['coords']
            if verbose:
                print(f"Запрос {i+1}/{len(processed_polygons)}: полигон с {len(polygon_coords)} точками (ID: {polygon_data.get('id', 'N/A')})")
            
            features = self._make_grid_request(polygon_coords, category_id=category_id)
            
            if features:
                new_count = 0
                for feature in features:
                    fid = feature.get('id')
                    if fid and fid not in seen_ids:
                        seen_ids.add(fid)
                        all_features.append(feature)
                        new_count += 1
                if verbose:
                    print(f"  Получено: {len(features)}, новых: {new_count}, всего: {len(all_features)}")
            else:
                if verbose:
                    print(f"  Нет features в ответе")
            
            time.sleep(0.5)
        
        if verbose:
            print(f"\n=== Результаты ===")
            print(f"Всего получено features (до фильтрации): {len(all_features)}")
        
        # Фильтруем по уникальным id
        if verbose:
            print(f"\nФильтрация по уникальным id...")
        unique_features_by_id = []
        seen_ids = set()
        skipped_by_id = 0
        
        for feature in all_features:
            fid = feature.get('id')
            if fid:
                if fid in seen_ids:
                    skipped_by_id += 1
                    continue
                seen_ids.add(fid)
            unique_features_by_id.append(feature)
        
        if verbose:
            print(f"Удалено дубликатов по id: {skipped_by_id}")
            print(f"Уникальных features (после фильтрации по id): {len(unique_features_by_id)}")
        
        # Дополнительная фильтрация по уникальным cad_num
        if verbose:
            print(f"\nФильтрация по уникальным cad_num...")
        unique_features = []
        seen_cad_nums = set()
        skipped_by_cad_num = 0
        
        for feature in unique_features_by_id:
            cad_num = None
            try:
                properties = feature.get('properties', {})
                options = properties.get('options', {})
                cad_num = options.get('cad_num')
            except (AttributeError, KeyError, TypeError):
                pass
            
            if cad_num:
                if cad_num in seen_cad_nums:
                    skipped_by_cad_num += 1
                    continue
                seen_cad_nums.add(cad_num)
            
            unique_features.append(feature)
        
        if verbose:
            print(f"Удалено дубликатов по cad_num: {skipped_by_cad_num}")
            print(f"Уникальных features (после фильтрации по id и cad_num): {len(unique_features)}")
        
        # Формируем результат
        result = {
            "type": "FeatureCollection",
            "features": unique_features
        }
        
        if verbose:
            print(f"Получено {len(unique_features)} уникальных features")
        
        return result

