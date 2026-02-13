# NSPD Request

[![Version](https://img.shields.io/badge/version-v2.0.1-blue.svg)](https://github.com/Logar1t/NSPD-request)
[![GitHub](https://img.shields.io/badge/GitHub-Logar1t%2FNSPD--request-green.svg)](https://github.com/Logar1t/NSPD-request)

Python-библиотека для работы с НСПД (Национальная система пространственных данных). Предоставляет упрощенные функции для получения данных по кадастровым номерам и геометриям объектов недвижимости.

⚠️ **Важно**

Данная библиотека является неофициальным проектом и создана исключительно в образовательных целях

## Установка

```bash
pip install nspd-request
```

Или из исходников:
```bash
git clone https://github.com/Logar1t/NSPD-request.git
cd NSPD-request
pip install -r requirements.txt
```

## Список функций

### Инициализация
- **`NSPD(timeout=30)`** - Создание экземпляра класса с настройкой таймаута запросов  
  📖 [Подробная документация](DOCUMENTATION.md#инициализация)

### Получение кадастровых данных по координатам
- **`get_cadastral_districts(lat, lon, size_meters=100)`** - Получает данные о кадастровых округах по координатам  
  📖 [Подробная документация](DOCUMENTATION.md#получение-кадастровых-данных-по-координатам)
- **`get_cadastral_quarters(lat, lon, size_meters=100)`** - Получает данные о кадастровых кварталах по координатам  
  📖 [Подробная документация](DOCUMENTATION.md#получение-кадастровых-данных-по-координатам)
- **`get_cadastral_regions(lat, lon, size_meters=1)`** - Получает данные о кадастровых районах по координатам  
  📖 [Подробная документация](DOCUMENTATION.md#получение-кадастровых-данных-по-координатам)

### Работа с кадастровыми номерами
- **`search_by_cadastral_number(kad_number)`** - Получает полные данные из НСПД по кадастровому номеру  
  📖 [Подробная документация](DOCUMENTATION.md#работа-с-кадастровыми-номерами)
- **`get_object_info(kad_number, include_geom_id=False, include_object_type=False, include_related=False)`** - Универсальная функция для получения информации об объекте с дополнительными полями  
  📖 [Подробная документация](DOCUMENTATION.md#работа-с-кадастровыми-номерами)
- **`get_geom_id(kad_number)`** - Получает только geom_id (уникальный идентификатор геометрии) по кадастровому номеру  
  📖 [Подробная документация](DOCUMENTATION.md#работа-с-кадастровыми-номерами)
- **`get_object_type(kad_number)`** - Определяет точный тип объекта (ЗУ, Здание, Сооружение, ОНС) по кадастровому номеру  
  📖 [Подробная документация](DOCUMENTATION.md#работа-с-кадастровыми-номерами)

### Получение связанных объектов
- **`get_land_plots_by_oks(geom_id, debug=False)`** - Получает список ЗУ по geomId ОКС (работает для всех типов ОКС: Здание, Сооружение, ОНС)  
  📖 [Подробная документация](DOCUMENTATION.md#получение-связанных-объектов)
- **`get_oks_by_land_plot(geom_id, debug=False)`** - Получает список ОКС по geomId ЗУ (возвращает все типы ОКС)  
  📖 [Подробная документация](DOCUMENTATION.md#получение-связанных-объектов)
- **`get_related_objects(kad_number, debug=False)`** - Получает связанные объекты по кадастровому номеру (автоматически определяет тип объекта)  
  📖 [Подробная документация](DOCUMENTATION.md#получение-связанных-объектов)

### Получение объектов по координатам
- **`get_by_coordinates(latitude, longitude, object_type='land_plot', bbox_size=0.05)`** - Универсальная функция для получения кадастрового номера по координатам  
  📖 [Подробная документация](DOCUMENTATION.md#получение-объектов-по-координатам)
- **`get_land_plot_by_coordinates(latitude, longitude, bbox_size=0.05)`** - Получает кадастровый номер ЗУ по координатам  
  📖 [Подробная документация](DOCUMENTATION.md#получение-объектов-по-координатам)
- **`get_oks_by_coordinates(latitude, longitude, bbox_size=0.05)`** - Получает кадастровый номер ОКС по координатам  
  📖 [Подробная документация](DOCUMENTATION.md#получение-объектов-по-координатам)

### Grid (массовая выгрузка)
- **`get_grid_data(lat, lon, boundary_type='kr', category_id=36368, verbose=False)`** - Выгружает список объектов выбранной категории в границах, определенных по координатам  
  📖 [Подробная документация](DOCUMENTATION.md#grid)

**Параметры `boundary_type`:**
- `'kr'` - Кадастровый район
- `'kk'` - Кадастровый квартал
- `'ko'` - Кадастровый округ

**Параметры `category_id`:**
- `36368` - ЗУ (Земельный участок)
- `36369` - Здание (ОКС)
- `36383` - Сооружение (ОКС)
- `36384` - Объект незавершенного строительства (ОКС)

---

## Примеры использования

### Быстрый старт

```python
from nspd_request import NSPD

# Создаем экземпляр
api = NSPD()

# Получение geom_id
geom_id = api.get_geom_id("77:03:0002007:7190")
print(f"geom_id: {geom_id}")  # Выводит: 426710013

# Определение типа объекта
obj_type = api.get_object_type("77:03:0002007:7190")
print(f"Тип: {obj_type}")  # Выводит: ЗУ

# Получение связанных объектов
related = api.get_related_objects("77:03:0002007:7190")
if not related.get("error"):
    print(f"Тип объекта: {related['type']}")  # ЗУ
    print(f"Связанных объектов: {len(related['related'])}")  # 4
    for obj in related['related']:
        print(f"  - {obj}")  # Кадастровые номера связанных ОКС
```

### Получение информации об объекте

```python
from nspd_request import NSPD

api = NSPD()

# Получение полных данных по кадастровому номеру
data = api.search_by_cadastral_number("77:03:0002007:7190")
if "error" not in data:
    print(f"Geom ID: {data.get('geom_id')}")
    print(f"Кадастровый номер: {data.get('kad_number')}")

# Универсальная функция с дополнительными полями
data = api.get_object_info("77:03:0002007:7190", 
                          include_geom_id=True, 
                          include_object_type=True)
if "error" not in data:
    print(f"Geom ID: {data.get('geom_id')}")
    print(f"Тип объекта: {data.get('object_type')}")
```

### Получение связанных объектов

```python
from nspd_request import NSPD

api = NSPD()

# Автоматическое получение связанных объектов
result = api.get_related_objects("77:03:0002007:7190")
if not result.get("error"):
    print(f"Тип объекта: {result['type']}")
    print(f"Geom ID: {result['geom_id']}")
    print(f"Связанных объектов: {len(result['related'])}")
    for obj in result['related']:
        print(f"  - {obj}")

# Или пошагово
geom_id = api.get_geom_id("77:03:0002007:7190")
obj_type = api.get_object_type("77:03:0002007:7190")

if obj_type == "ЗУ":
    # Получаем ОКС на этом ЗУ
    oks_list = api.get_oks_by_land_plot(geom_id)
    print(f"Найдено ОКС: {len(oks_list) if oks_list else 0}")
elif obj_type in ["Здание", "Сооружение", "Объект незавершенного строительства"]:
    # Получаем ЗУ для этого ОКС
    zu_list = api.get_land_plots_by_oks(geom_id)
    print(f"Найдено ЗУ: {len(zu_list) if zu_list else 0}")
```

### Поиск объектов по координатам

```python
from nspd_request import NSPD

api = NSPD()

# Поиск ЗУ по координатам
kad_number = api.get_land_plot_by_coordinates(55.811978, 37.498339)
if kad_number:
    print(f"Найден ЗУ: {kad_number}")
    
    # Получение информации о найденном ЗУ
    info = api.get_object_info(kad_number, include_geom_id=True, include_object_type=True)
    print(f"Тип: {info.get('object_type')}")

# Поиск ОКС по координатам
oks_number = api.get_oks_by_coordinates(55.756126, 37.615042)
if oks_number:
    print(f"Найден ОКС: {oks_number}")

# Универсальная функция
zu_number = api.get_by_coordinates(55.811978, 37.498339, object_type='land_plot')
oks_number = api.get_by_coordinates(55.756126, 37.615042, object_type='oks')
```

### Массовая выгрузка через Grid

```python
from nspd_request import NSPD
from nspd_request import save_json_to_file

api = NSPD()

# Выгрузка всех ЗУ в кадастровом районе
result = api.get_grid_data(
    lat=55.770783,
    lon=37.73718,
    boundary_type='kr',      # Используем границы кадастрового района
    category_id=36368,        # Выгружаем только ЗУ
    verbose=True              # Показывать прогресс
)

if result:
    features = result.get('features', [])
    print(f"Найдено ЗУ в районе: {len(features)}")
    
    # Обработка каждого объекта
    for feature in features[:10]:  # Первые 10
        properties = feature.get('properties', {})
        options = properties.get('options', {})
        cad_num = options.get('cad_num', 'N/A')
        print(f"  - {cad_num}")
    
    # Сохранение в файл (если нужно)
    save_json_to_file(result, 'all_zu_in_region.json')
```

### Получение кадастровых данных по координатам

```python
from nspd_request import NSPD

api = NSPD()

# Получение данных о кадастровом районе
region_data = api.get_cadastral_regions(55.7558, 37.6173, size_meters=1)
if region_data:
    features = region_data.get('features', [])
    if features:
        first = features[0]
        props = first.get('properties', {})
        options = props.get('options', {})
        print(f"Кадастровый номер района: {props.get('descr', 'N/A')}")
        print(f"ЗУ в районе: {options.get('cnt_land_geom', 0)}")
        print(f"ОКС в районе: {options.get('cnt_oks_geom', 0)}")
```

### Обработка ошибок

```python
from nspd_request import NSPD

api = NSPD()

# Проверка ошибок для методов, возвращающих None
geom_id = api.get_geom_id("неверный_номер")
if geom_id is None:
    print("Ошибка: не удалось получить geom_id")

# Проверка ошибок для методов, возвращающих dict
result = api.search_by_cadastral_number("неверный_номер")
if "error" in result:
    print(f"Ошибка: {result['error']}")

# Проверка ошибок для get_related_objects
related = api.get_related_objects("неверный_номер")
if related.get("error"):
    print(f"Ошибка: {related['error']}")
```

---

## Демонстрация

Запустите файл для просмотра всех примеров:

```bash
python demo.py
```

Демонстрация включает:
1. Получение geom_id по кадастровому номеру
2. Определение типа объекта (ЗУ/ОКС)
3. Получение связанных объектов
4. Универсальная функция get_object_info() с настройками
5. Сравнение способов получения данных
6. Поиск объектов по координатам
7. Массовая выгрузка через Grid
8. Обработка ошибок

---

## Подробная документация

Для получения подробной информации о каждой функции, параметрах, возвращаемых значениях и дополнительных примерах см. [DOCUMENTATION.md](DOCUMENTATION.md)

---

## Требования

- Python 3.12+
- requests
- pyproj (для работы с координатами)
- shapely (опционально, для работы с Grid)

## Поддержка проекта

Самый простой способ - это оставить ⭐ проекту на [GitHub](https://github.com/Logar1t/NSPD-request) и отправить его своим коллегам.

## Лицензия

Библиотека создана для работы с открытым НСПД.
