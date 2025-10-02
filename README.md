# NSPD Request

[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com/Logar1t/NSPD-request)
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

## Быстрый старт

```python
from nspd_request import NSPD

# Создаем экземпляр API
api = NSPD()

# Получение geom_id
geom_id = api.get_geom_id("77:03:0002007:7190")
print(f"geom_id: {geom_id}")

# Определение типа объекта
obj_type = api.get_object_type("77:03:0002007:7190")
print(f"Тип: {obj_type}")

# Получение связанных объектов
related = api.get_related("77:03:0002007:7190")
print(f"Связанных объектов: {len(related['related'])}")
```

## Основные функции

### 1. Получение geom_id

```python
from nspd_request import NSPD

api = NSPD()

# Получение geom_id по кадастровому номеру
geom_id = api.get_geom_id("77:03:0002007:7190")
print(f"geom_id: {geom_id}")  # 426710013
```

**Параметры:**
- `kad_number` (str): Кадастровый номер

**Возвращает:**
- `str` или `None`: geom_id или None в случае ошибки

### 2. Определение типа объекта

```python
from nspd_request import NSPD

api = NSPD()

# Определение типа объекта (ЗУ или ОКС)
obj_type = api.get_object_type("77:03:0002007:7190")
print(f"Тип: {obj_type}")  # ЗУ
```

**Параметры:**
- `kad_number` (str): Кадастровый номер

**Возвращает:**
- `str` или `None`: "ЗУ", "ОКС" или None в случае ошибки

**Принцип работы:**
- Сначала определяет по `categoryId` из `meta` (36368 = ЗУ, 36369 = ОКС)
- Если не удалось, анализирует связи с другими объектами

### 3. Получение связанных объектов

```python
from nspd_request import NSPD

api = NSPD()

# Получение связанных объектов
related = api.get_related("77:03:0002007:7190")
print(f"Тип: {related['type']}")  # ЗУ
print(f"Связанных: {len(related['related'])}")  # 4
```

**Параметры:**
- `kad_number` (str): Кадастровый номер
- `debug` (bool): Включить отладочную информацию (по умолчанию False)

**Возвращает:**
- `dict`: Словарь с информацией:
  - `data`: Полные данные объекта из НСПД
  - `geom_id`: Извлеченный ID геометрии
  - `type`: Определенный тип объекта ("ЗУ" или "ОКС")
  - `related`: Список связанных объектов
  - `error`: Сообщение об ошибке (если есть)

### 4. Получение списка ЗУ по geomId ОКС

```python
from nspd_request import NSPD

api = NSPD()

# Получение списка ЗУ по geomId ОКС
zu_list = api.get_zu_by_oks("108123297")
print(f"Найдено ЗУ: {len(zu_list)}")  # 1
```

**Параметры:**
- `geom_id` (str): ID геометрии ОКС
- `debug` (bool): Включить отладочную информацию (по умолчанию False)

**Возвращает:**
- `list` или `None`: Список ЗУ или None в случае ошибки

### 5. Получение списка ОКС по geomId ЗУ

```python
from nspd_request import NSPD

api = NSPD()

# Получение списка ОКС по geomId ЗУ
oks_list = api.get_oks_by_zu("426710013")
print(f"Найдено ОКС: {len(oks_list)}")  # 4
```

**Параметры:**
- `geom_id` (str): ID геометрии ЗУ
- `debug` (bool): Включить отладочную информацию (по умолчанию False)

**Возвращает:**
- `list` или `None`: Список ОКС или None в случае ошибки

### 6. Универсальная функция get_info()

```python
from nspd_request import NSPD

api = NSPD()

# Только базовые данные
data = api.get_info("77:03:0002007:7190")

# С дополнительным geom_id
data = api.get_info("77:03:0002007:7190", include_geom_id=True)

# С дополнительным object_type
data = api.get_info("77:03:0002007:7190", include_object_type=True)

# С обоими дополнительными полями
data = api.get_info("77:03:0002007:7190", include_geom_id=True, include_object_type=True)
```

**Параметры:**
- `kad_number` (str): Кадастровый номер
- `include_geom_id` (bool): Дополнительно включить geom_id в результат
- `include_object_type` (bool): Дополнительно включить object_type в результат

**Возвращает:**
- `dict`: Словарь с данными и дополнительными полями (если запрошены)

**Преимущества:**
- По умолчанию возвращает все данные из НСПД
- Можно настроить дополнительные поля через параметры
- Эффективнее чем несколько отдельных запросов

### 7. Получение ЗУ по координатам

```python
from nspd_request import NSPD

api = NSPD()

# Получение ЗУ по координатам (широта, долгота)
kad_number = api.get_zu_by_coordinates(55.811978, 37.498339)
print(f"Найден ЗУ: {kad_number}")  # 77:09:0004001:8

# С настройкой размера области поиска
kad_number = api.get_zu_by_coordinates(55.7558, 37.6176, bbox_size=0.1)
print(f"Найден ЗУ: {kad_number}")
```

**Параметры:**
- `latitude` (float): Широта в градусах (WGS84)
- `longitude` (float): Долгота в градусах (WGS84)
- `bbox_size` (float): Размер области поиска в метрах (по умолчанию 0.05)

**Возвращает:**
- `str` или `None`: Кадастровый номер ЗУ или None в случае ошибки

**Особенности:**
- Автоматически преобразует координаты из WGS84 в EPSG:3857
- Создает BBOX для поиска в указанной области
- Возвращает первый найденный ЗУ в области
- Можно настроить размер области поиска через `bbox_size`

## Полный рабочий процесс

### Простой способ (рекомендуется)

```python
from nspd_request import NSPD

api = NSPD()

# Одна функция делает все автоматически!
result = api.get_related("77:03:0002007:7190")

if result["error"]:
    print(f"Ошибка: {result['error']}")
else:
    print(f"Тип объекта: {result['type']}")
    print(f"geomId: {result['geom_id']}")
    print(f"Связанные объекты ({len(result['related'])}):")
    
    for i, obj in enumerate(result['related'], 1):
        print(f"  {i}. {obj}")
```

### Пошаговый способ

```python
from nspd_request import NSPD

api = NSPD()
kad_number = "77:03:0002007:7190"

# 1. Получаем geom_id
geom_id = api.get_geom_id(kad_number)
print(f"geom_id: {geom_id}")

# 2. Определяем тип объекта
obj_type = api.get_object_type(kad_number)
print(f"Тип: {obj_type}")

# 3. Получаем связанные объекты
if obj_type == "ЗУ":
    oks_list = api.get_oks_by_zu(geom_id)
    print(f"Найдено ОКС: {len(oks_list) if oks_list else 0}")
elif obj_type == "ОКС":
    zu_list = api.get_zu_by_oks(geom_id)
    print(f"Найдено ЗУ: {len(zu_list) if zu_list else 0}")
```

## Обработка ошибок

Все функции возвращают понятные сообщения об ошибках:

```python
from nspd_request import NSPD

api = NSPD()

# Проверка ошибок для получения geom_id
geom_id = api.get_geom_id("неверный_номер")
if geom_id is None:
    print("Ошибка при получении geom_id")

# Проверка ошибок для определения типа объекта
obj_type = api.get_object_type("неверный_номер")
if obj_type is None:
    print("Ошибка при определении типа объекта")

# Проверка ошибок для получения связанных объектов
related = api.get_related("неверный_номер")
if related.get("error"):
    print(f"Ошибка: {related['error']}")

# Проверка ошибок для получения списков
zu_list = api.get_zu_by_oks("неверный_id")
if zu_list is None:
    print("Ошибка при получении списка ЗУ")
```

## Примеры использования

Запустите файл для просмотра всех примеров:

```bash
python demo.py
```

Демонстрация включает:
1. Получение geom_id по кадастровому номеру
2. Определение типа объекта (ЗУ/ОКС)
3. Получение связанных объектов
4. Универсальная функция get_info() с настройками
5. Сравнение способов получения данных
6. Демонстрация оптимизации
7. Обработка ошибок
8. **Поиск ЗУ по координатам**
9. Тестирование производительности

## Требования

- Python 3.12+
- requests
- pyproj (для работы с координатами)

## Поддержка проекта

Самый простой способ - это оставить ⭐ проекту на [GitHub](https://github.com/Logar1t/NSPD-request) и отправить его своим коллегам.

## Лицензия

Библиотека создана для работы с открытым API НСПД.