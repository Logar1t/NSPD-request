"""
Демонстрация библиотеки NSPD API
Показывает все возможности библиотеки с реальными данными
"""

from nspd_request import NSPD
import time

def demo_basic_functions():
    """
    Демонстрация основных функций
    """
    print("🚀 ДЕМОНСТРАЦИЯ ОСНОВНЫХ ФУНКЦИЙ")
    print("=" * 60)
    
    api = NSPD()
    
    # Тестовые данные
    zu_number = "77:03:0002007:7190"  # ЗУ
    oks_number = "77:03:0002007:9137"  # ОКС
    
    print(f"\n📋 Анализируем ЗУ: {zu_number}")
    print("-" * 40)
    
    # 1. Получаем geom_id
    geom_id = api.get_geom_id(zu_number)
    print(f"✅ geom_id: {geom_id}")
    
    # 2. Определяем тип объекта
    obj_type = api.get_object_type(zu_number)
    print(f"✅ Тип объекта: {obj_type}")
    
    # 3. Получаем связанные объекты
    related = api.get_related(zu_number)
    if related.get("error"):
        print(f"❌ Ошибка: {related['error']}")
    else:
        print(f"✅ Связанных объектов: {len(related['related'])}")
        for i, obj in enumerate(related['related'][:3], 1):
            print(f"   {i}. {obj}")
        if len(related['related']) > 3:
            print(f"   ... и еще {len(related['related']) - 3}")
    
    print(f"\n📋 Анализируем ОКС: {oks_number}")
    print("-" * 40)
    
    # 1. Получаем geom_id
    geom_id = api.get_geom_id(oks_number)
    print(f"✅ geom_id: {geom_id}")
    
    # 2. Определяем тип объекта
    obj_type = api.get_object_type(oks_number)
    print(f"✅ Тип объекта: {obj_type}")
    
    # 3. Получаем связанные объекты
    related = api.get_related(oks_number)
    if related.get("error"):
        print(f"❌ Ошибка: {related['error']}")
    else:
        print(f"✅ Связанных объектов: {len(related['related'])}")
        for i, obj in enumerate(related['related'], 1):
            print(f"   {i}. {obj}")

def demo_get_info_function():
    """
    Демонстрация универсальной функции get_info()
    """
    print(f"\n{'='*60}")
    print("⚡ ДЕМОНСТРАЦИЯ ФУНКЦИИ get_info()")
    print("=" * 60)
    
    api = NSPD()
    kad_number = "77:03:0002007:7190"
    
    print(f"📋 Анализируем объект: {kad_number}")
    print("=" * 60)
    
    # 1. Только базовые данные (по умолчанию)
    print("\n1️⃣ Только базовые данные:")
    print("-" * 40)
    
    data = api.get_info(kad_number)
    if "error" in data:
        print(f"❌ Ошибка: {data['error']}")
    else:
        print(f"✅ Получены базовые данные")
        print(f"   Ключи: {list(data.keys())}")
        print(f"   Кадастровый номер: {data.get('kad_number')}")
    
    # 2. С дополнительным geom_id
    print("\n2️⃣ С дополнительным geom_id:")
    print("-" * 40)
    
    data = api.get_info(kad_number, include_geom_id=True)
    if "error" in data:
        print(f"❌ Ошибка: {data['error']}")
    else:
        print(f"✅ Получены данные с geom_id")
        print(f"   Ключи: {list(data.keys())}")
        print(f"   geom_id: {data.get('geom_id')}")
    
    # 3. С дополнительным object_type
    print("\n3️⃣ С дополнительным object_type:")
    print("-" * 40)
    
    data = api.get_info(kad_number, include_object_type=True)
    if "error" in data:
        print(f"❌ Ошибка: {data['error']}")
    else:
        print(f"✅ Получены данные с object_type")
        print(f"   Ключи: {list(data.keys())}")
        print(f"   object_type: {data.get('object_type')}")
    
    # 4. С обоими дополнительными полями
    print("\n4️⃣ С обоими дополнительными полями:")
    print("-" * 40)
    
    data = api.get_info(kad_number, include_geom_id=True, include_object_type=True)
    if "error" in data:
        print(f"❌ Ошибка: {data['error']}")
    else:
        print(f"✅ Получены данные с geom_id и object_type")
        print(f"   Ключи: {list(data.keys())}")
        print(f"   geom_id: {data.get('geom_id')}")
        print(f"   object_type: {data.get('object_type')}")
        print(f"   Кадастровый номер: {data.get('kad_number')}")

def demo_comparison():
    """
    Сравнение различных способов получения данных
    """
    print(f"\n{'='*60}")
    print("📊 СРАВНЕНИЕ СПОСОБОВ ПОЛУЧЕНИЯ ДАННЫХ")
    print("=" * 60)
    
    api = NSPD()
    kad_number = "77:03:0002007:7190"
    
    print(f"\n🔍 Объект: {kad_number}")
    print("-" * 40)
    
    # Способ 1: Отдельные функции
    print("1️⃣ Отдельные функции:")
    
    geom_id = api.get_geom_id(kad_number)
    obj_type = api.get_object_type(kad_number)
    
    print(f"   geom_id: {geom_id}")
    print(f"   object_type: {obj_type}")
    print(f"   Количество запросов: 3 (get_data + get_geom_id + get_object_type)")
    
    # Способ 2: Универсальная функция
    print("\n2️⃣ Универсальная функция get_info():")
    
    data = api.get_info(kad_number, include_geom_id=True, include_object_type=True)
    if "error" not in data:
        print(f"   geom_id: {data.get('geom_id')}")
        print(f"   object_type: {data.get('object_type')}")
        print(f"   Количество запросов: 1 (get_info с параметрами)")
    
    print(f"\n💡 Вывод: get_info() эффективнее для получения нескольких полей!")

def demo_optimization():
    """
    Демонстрация оптимизации
    """
    print(f"\n{'='*60}")
    print("🚀 ДЕМОНСТРАЦИЯ ОПТИМИЗАЦИИ")
    print("=" * 60)
    
    api = NSPD()
    kad_number = "77:03:0002007:7190"
    
    print(f"📋 Тестируем объект: {kad_number}")
    print("=" * 60)
    
    # Тест оптимизированной функции get_info()
    print("\n⚡ Оптимизированная функция get_info():")
    print("-" * 40)
    
    start_time = time.time()
    
    # Получаем все данные одним запросом
    data = api.get_info(kad_number, include_geom_id=True, include_object_type=True)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    if "error" in data:
        print(f"❌ Ошибка: {data['error']}")
    else:
        print(f"✅ Данные получены за {execution_time:.2f} секунд")
        print(f"   geom_id: {data.get('geom_id')}")
        print(f"   object_type: {data.get('object_type')}")
        print(f"   Кадастровый номер: {data.get('kad_number')}")
        print(f"   Ключи в ответе: {list(data.keys())}")

def demo_error_handling():
    """
    Демонстрация обработки ошибок
    """
    print(f"\n{'='*60}")
    print("⚠️  ДЕМОНСТРАЦИЯ ОБРАБОТКИ ОШИБОК")
    print("=" * 60)
    
    api = NSPD()
    
    error_cases = [
        "99:99:9999999:9999",  # Неверный номер
        "",                    # Пустой номер
        "77:03:0002007:9999"   # Номер не существует
    ]
    
    for case in error_cases:
        print(f"\n🔍 Тестируем: '{case}'")
        
        # Тест get_geom_id
        geom_id = api.get_geom_id(case)
        if geom_id is None:
            print(f"✅ get_geom_id: Корректно обработана ошибка")
        else:
            print(f"❌ get_geom_id: Неожиданный результат")
        
        # Тест get_object_type
        obj_type = api.get_object_type(case)
        if obj_type is None:
            print(f"✅ get_object_type: Корректно обработана ошибка")
        else:
            print(f"❌ get_object_type: Неожиданный результат")
        
        # Тест get_related
        related = api.get_related(case)
        if related.get("error"):
            print(f"✅ get_related: Корректно обработана ошибка")
        else:
            print(f"❌ get_related: Неожиданный результат")

def demo_coordinates():
    """
    Демонстрация получения ЗУ по координатам
    """
    print(f"\n{'='*60}")
    print("🗺️  ДЕМОНСТРАЦИЯ ПОЛУЧЕНИЯ ЗУ ПО КООРДИНАТАМ")
    print("=" * 60)
    
    api = NSPD()
    
    # Тестовые координаты
    test_coordinates = [
        (55.811978, 37.498339, "Москва, ожидаемый результат: 77:09:0004001:8")
    ]
    
    for lat, lon, description in test_coordinates:
        print(f"\n📍 Координаты: {lat}, {lon}")
        print(f"   Описание: {description}")
        print("-" * 40)
        
        start_time = time.time()
        kad_number = api.get_zu_by_coordinates(lat, lon)
        end_time = time.time()
        
        request_time = end_time - start_time
        
        if kad_number:
            print(f"✅ Найден ЗУ: {kad_number}")
            print(f"   Время поиска: {request_time:.2f} сек")
            
            # Дополнительно получаем информацию о найденном ЗУ
            print(f"   📋 Дополнительная информация:")
            obj_type = api.get_object_type(kad_number)
            if obj_type:
                print(f"      Тип объекта: {obj_type}")
            
            geom_id = api.get_geom_id(kad_number)
            if geom_id:
                print(f"      geom_id: {geom_id}")
        else:
            print(f"❌ ЗУ не найден за {request_time:.2f} сек")
            print(f"   Возможно, в этой области нет ЗУ или нужен больший bbox_size")

def demo_performance():
    """
    Демонстрация производительности
    """
    print(f"\n{'='*60}")
    print("⚡ ДЕМОНСТРАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 60)
    
    api = NSPD()
    
    test_numbers = [
        "77:03:0002007:7190",
        "77:03:0002007:9137"
    ]
    
    total_time = 0
    successful_requests = 0
    
    for kad_number in test_numbers:
        print(f"\n⏱️  Тестируем: {kad_number}")
        
        start_time = time.time()
        result = api.get_related(kad_number)
        end_time = time.time()
        
        request_time = end_time - start_time
        total_time += request_time
        
        if not result.get("error"):
            successful_requests += 1
            print(f"✅ Успешно за {request_time:.2f} сек")
            print(f"   Найдено связанных объектов: {len(result['related'])}")
        else:
            print(f"❌ Ошибка за {request_time:.2f} сек: {result['error']}")
    
    print(f"\n📊 ИТОГИ ПРОИЗВОДИТЕЛЬНОСТИ:")
    print(f"   Успешных запросов: {successful_requests}/{len(test_numbers)}")
    print(f"   Общее время: {total_time:.2f} сек")
    print(f"   Среднее время на запрос: {total_time/len(test_numbers):.2f} сек")

def main():
    """
    Главная функция демонстрации
    """
    print("🎯 ДЕМОНСТРАЦИЯ БИБЛИОТЕКИ NSPD API")
    print("=" * 60)
    print("Библиотека для работы с API НСПД")
    print("Автоматическое получение данных и связей между объектами")
    print("=" * 60)
    
    try:
        demo_basic_functions()
        demo_get_info_function()
        demo_comparison()
        demo_optimization()
        demo_error_handling()
        demo_coordinates()
        demo_performance()
        
        print(f"\n{'='*60}")
        print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print("=" * 60)
        print("📚 Для получения дополнительной информации читайте README.md")
        
    except Exception as e:
        print(f"\n❌ Ошибка при демонстрации: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
