"""
Библиотека для работы с API НСПД (Национальная система пространственных данных)
Предоставляет упрощенные функции для получения данных по кадастровым номерам и геометриям.
"""

import requests
import warnings
from pyproj import Transformer

# Отключаем предупреждения о SSL сертификатах
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class NSPD:
    """Основной класс для работы с НСПД API"""
    
    def __init__(self, timeout=15):
        """
        Инициализация API клиента
        
        :param timeout: Таймаут для запросов в секундах
        """
        self.timeout = timeout
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_data(self, kad_number):
        """
        Получает данные из НСПД по кадастровому номеру
        
        :param kad_number: Кадастровый номер
        :return: Данные из НСПД или словарь с ошибкой
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
                
                # Добавляем информацию о кадастровом номере
                response_data["kad_number"] = kad_number
                
                # Автоматически извлекаем geomId из ответа
                geom_id = self._extract_geom_id(response_data)
                if geom_id:
                    response_data["geom_id"] = geom_id
                
                return response_data
            else:
                return {"error": f"Ошибка HTTP {response.status_code} для кадастрового номера {kad_number}"}
                
        except requests.RequestException as e:
            return {"error": f"Исключение при запросе для кадастрового номера {kad_number}: {e}"}
    
    def _extract_geom_id(self, response_data):
        """
        Извлекает geomId из ответа НСПД
        
        :param response_data: Данные ответа от НСПД
        :return: geomId или None
        """
        try:
            # Ищем в структуре data.features[0].id
            if isinstance(response_data, dict) and 'data' in response_data:
                data = response_data['data']
                if isinstance(data, dict) and 'features' in data:
                    features = data['features']
                    if isinstance(features, list) and len(features) > 0:
                        first_feature = features[0]
                        if isinstance(first_feature, dict) and 'id' in first_feature:
                            return first_feature['id']
            
            # Альтернативные варианты поиска
            possible_paths = [
                ['data', 'id'],
                ['id'],
                ['geometry', 'id'],
                ['objectId'],
                ['featureId']
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
    
    def _determine_object_type_from_data(self, data):
        """
        Определяет тип объекта (ЗУ или ОКС) из уже полученных данных
        
        :param data: Данные ответа от НСПД
        :return: "ЗУ", "ОКС" или None
        """
        # Извлекаем categoryId из meta
        category_id = self._extract_category_id(data)
        
        # Определяем тип по categoryId
        if category_id == "36368":
            return "ЗУ"
        elif category_id == "36369":
            return "ОКС"
        
        # Если не удалось определить по categoryId, пробуем через связи
        geom_id = data.get("geom_id")
        if geom_id:
            # Пробуем получить ОКС (если это ЗУ)
            oks_list = self.get_oks_by_zu(geom_id)
            if oks_list and len(oks_list) > 0:
                return "ЗУ"
            
            # Пробуем получить ЗУ (если это ОКС)
            zu_list = self.get_zu_by_oks(geom_id)
            if zu_list and len(zu_list) > 0:
                return "ОКС"
        
        return None
    
    def get_geom_id(self, kad_number):
        """
        Получает только geom_id по кадастровому номеру
        
        :param kad_number: Кадастровый номер
        :return: geom_id или None в случае ошибки
        """
        data = self.get_data(kad_number)
        if "error" in data:
            return None
        return data.get("geom_id")
    
    def get_object_type(self, kad_number):
        """
        Определяет тип объекта (ЗУ или ОКС) по кадастровому номеру
        
        :param kad_number: Кадастровый номер
        :return: "ЗУ", "ОКС" или None в случае ошибки
        """
        data = self.get_data(kad_number)
        if "error" in data:
            return None
        
        return self._determine_object_type_from_data(data)
    
    def _extract_category_id(self, response_data):
        """
        Извлекает categoryId из ответа НСПД
        
        :param response_data: Данные ответа от НСПД
        :return: categoryId или None
        """
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
    
    def get_zu_by_oks(self, geom_id, debug=False):
        """
        Получает список ЗУ по geomId ОКС
        
        :param geom_id: ID геометрии ОКС
        :param debug: Включить отладочную информацию
        :return: Список ЗУ или None в случае ошибки
        """
        try:
            url = f"https://nspd.gov.ru/api/geoportal/v1/tab-values-data"
            
            # Список categoryId для попыток
            category_ids = ['36369']
            
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
                    
                    # Извлекаем список ЗУ из ответа
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
                    
                    return zu_list
                elif response.status_code == 500:
                    try:
                        error_data = response.json()
                        if error_data.get('code') == 1023:
                            if debug:
                                print(f"Получена ошибка 500 с кодом 1023 для categoryId: {category_id}, пробуем следующий...")
                            continue
                        else:
                            if debug:
                                print(f"Ошибка 500 с кодом {error_data.get('code')} для categoryId: {category_id}")
                            return None
                    except:
                        if debug:
                            print(f"Ошибка 500 для categoryId: {category_id}")
                        return None
                else:
                    if debug:
                        print(f"Ошибка запроса списка ЗУ: {response.status_code} для geomId: {geom_id} с categoryId: {category_id}")
                    return None
            
            if debug:
                print(f"Не удалось получить данные ЗУ ни с одним categoryId для geomId: {geom_id}")
            return None
                
        except Exception as e:
            if debug:
                print(f"Исключение при запросе списка ЗУ для geomId {geom_id}: {e}")
            return None
    
    def get_oks_by_zu(self, geom_id, debug=False):
        """
        Получает список ОКС по geomId ЗУ
        
        :param geom_id: ID геометрии ЗУ
        :param debug: Включить отладочную информацию
        :return: Список ОКС или None в случае ошибки
        """
        try:
            url = f"https://nspd.gov.ru/api/geoportal/v1/tab-group-data"
            
            params = {
                'tabClass': 'objectsList',
                'categoryId': '36368',
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
                
                # Извлекаем список ОКС из ответа
                oks_list = []
                
                if isinstance(data, dict) and 'object' in data and isinstance(data['object'], list):
                    for obj in data['object']:
                        if isinstance(obj, dict) and 'value' in obj and isinstance(obj['value'], list):
                            for value in obj['value']:
                                if value and value.strip():
                                    oks_list.append(value.strip())
                elif isinstance(data, dict):
                    # Альтернативные варианты структуры
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
                
                return oks_list
            else:
                if debug:
                    print(f"Ошибка запроса списка ОКС: {response.status_code} для geomId: {geom_id}")
                return None
                
        except Exception as e:
            if debug:
                print(f"Исключение при запросе списка ОКС для geomId {geom_id}: {e}")
            return None
    
    def get_related(self, kad_number, debug=False):
        """
        Получает связанные объекты по кадастровому номеру
        
        :param kad_number: Кадастровый номер
        :param debug: Включить отладочную информацию
        :return: Словарь с данными объекта и связанными объектами
        """
        result = {
            "data": None,
            "geom_id": None,
            "related": [],
            "type": None,
            "error": None
        }
        
        # Получаем данные по кадастровому номеру
        data = self.get_data(kad_number)
        
        if "error" in data:
            result["error"] = data["error"]
            return result
        
        result["data"] = data
        result["geom_id"] = data.get("geom_id")
        
        if not result["geom_id"]:
            result["error"] = "Не удалось извлечь geomId из ответа"
            return result
        
        if debug:
            print(f"Извлечен geomId: {result['geom_id']}")
        
        # Определяем тип объекта и получаем связанные
        object_type = self.get_object_type(kad_number)
        if not object_type:
            result["error"] = "Не удалось определить тип объекта"
            return result
        
        result["type"] = object_type
        
        if object_type == "ЗУ":
            # Получаем ОКС
            oks_list = self.get_oks_by_zu(result["geom_id"], debug)
            if oks_list:
                result["related"] = oks_list
                if debug:
                    print(f"Найдено связанных ОКС: {len(oks_list)}")
        elif object_type == "ОКС":
            # Получаем ЗУ
            zu_list = self.get_zu_by_oks(result["geom_id"], debug)
            if zu_list:
                result["related"] = zu_list
                if debug:
                    print(f"Найдено связанных ЗУ: {len(zu_list)}")
        
        return result
    
    def get_info(self, kad_number, include_geom_id=False, include_object_type=False):
        """
        Универсальная функция для получения информации об объекте
        
        :param kad_number: Кадастровый номер
        :param include_geom_id: Дополнительно включить geom_id в результат
        :param include_object_type: Дополнительно включить object_type в результат
        :return: Словарь с данными и дополнительными полями (если запрошены)
        """
        # Получаем базовые данные
        data = self.get_data(kad_number)
        
        if "error" in data:
            return data
        
        # Добавляем дополнительные поля если запрошены
        if include_geom_id:
            # Используем уже полученные данные вместо повторного запроса
            geom_id = data.get("geom_id")
            if not geom_id:
                geom_id = self._extract_geom_id(data)
            data["geom_id"] = geom_id
        
        if include_object_type:
            # Используем уже полученные данные вместо повторного запроса
            object_type = self._determine_object_type_from_data(data)
            data["object_type"] = object_type
        
        return data
    
    def _convert_wgs84_to_epsg3857(self, latitude, longitude):
        """
        Преобразует координаты из WGS84 (EPSG:4326) в EPSG:3857
        
        :param latitude: Широта в градусах
        :param longitude: Долгота в градусах
        :return: Координаты в EPSG:3857 (x, y)
        """
        # Создаем трансформер для преобразования координат
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        
        # Преобразование координат из WGS84 в EPSG:3857
        x, y = transformer.transform(longitude, latitude)

        return x, y
    
    def _create_bbox(self, latitude, longitude, bbox_size=0.05):
        """
        Создает BBOX для запроса к API НСПД
        
        :param latitude: Широта в градусах
        :param longitude: Долгота в градусах
        :param bbox_size: Размер BBOX в метрах
        :return: Строка BBOX в формате для URL
        """
        # Преобразование центральной точки в EPSG:3857
        x_center, y_center = self._convert_wgs84_to_epsg3857(latitude, longitude)

        # Расчет координат BBOX
        x_min = x_center - bbox_size / 2
        y_min = y_center - bbox_size / 2
        x_max = x_center + bbox_size / 2
        y_max = y_center + bbox_size / 2

        # Форматирование результата
        bbox_str = f"{x_min},{y_min},{x_max},{y_max}"
        
        return bbox_str
    
    def get_zu_by_coordinates(self, latitude, longitude, bbox_size=0.05):
        """
        Получает кадастровый номер ЗУ по координатам
        
        :param latitude: Широта в градусах (WGS84)
        :param longitude: Долгота в градусах (WGS84)
        :param bbox_size: Размер BBOX в метрах (по умолчанию 0.05)
        :return: Кадастровый номер ЗУ или None в случае ошибки
        """
        try:
            # Создаем BBOX
            bbox = self._create_bbox(latitude, longitude, bbox_size)
            
            # URL для ЗУ (слой 36048)
            url = f"https://nspd.gov.ru/api/aeggis/v3/36048/wms"
            
            # Параметры запроса
            params = {
                'REQUEST': 'GetFeatureInfo',
                'QUERY_LAYERS': '36048',
                'SERVICE': 'WMS',
                'VERSION': '1.3.0',
                'FORMAT': 'image/png',
                'STYLES': '',
                'TRANSPARENT': 'true',
                'LAYERS': '36048',
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
            
            # Заголовки
            headers = {
                **self.base_headers,
                'referer': 'https://nspd.gov.ru/map?thematic=PKK&zoom=17.690976575074885&coordinate_x=4191326.8832895053&coordinate_y=7501296.123874589&theme_id=1&baseLayerId=235&is_copy_url=true&active_layers=36049,36048'
            }
            
            # Выполняем запрос
            response = requests.get(url, params=params, headers=headers, verify=False, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'features' in data and data['features']:
                    # Извлекаем кадастровый номер из первого найденного ЗУ
                    feature = data['features'][0]
                    properties = feature.get('properties', {})
                    options = properties.get('options', {})
                    
                    # Получаем кадастровый номер
                    cad_num = options.get('cad_num', '')
                    return cad_num if cad_num else None
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            return None
