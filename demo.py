"""
Демонстрация библиотеки NSPD
Показывает все возможности библиотеки с реальными данными
"""

from nspd_request import NSPD
import time

def print_section(title):
    """Выводит заголовок раздела"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

def print_subsection(title):
    """Выводит подзаголовок"""
    print(f"\n{'-'*70}")
    print(f"  {title}")
    print('-'*70)

def demo_basic_functions():
    """
    Демонстрация основных функций работы с кадастровыми номерами
    """
    print_section("🚀 ОСНОВНЫЕ ФУНКЦИИ")
    
    api = NSPD()
    
    # Тестовые данные
    zu_number = "77:03:0002007:7190"  # Земельный участок
    oks_number = "77:03:0002007:9137"  # Объект капитального строительства
    
    print(f"\n📋 Пример 1: Работа с Земельным участком (ЗУ)")
    print(f"   Кадастровый номер: {zu_number}")
    print_subsection("Получение информации о ЗУ")
    
    # 1. Получаем geom_id
    print("\n1. Получение geom_id (уникальный идентификатор геометрии):")
    geom_id = api.get_geom_id(zu_number)
    if geom_id:
        print(f"   ✅ geom_id: {geom_id}")
    else:
        print(f"   ❌ Не удалось получить geom_id")
        return
    
    # 2. Определяем тип объекта
    print("\n2. Определение типа объекта:")
    obj_type = api.get_object_type(zu_number)
    if obj_type:
        print(f"   ✅ Тип объекта: {obj_type}")
    else:
        print(f"   ❌ Не удалось определить тип")
    
    # 3. Получаем связанные объекты
    print("\n3. Получение связанных объектов:")
    related = api.get_related_objects(zu_number)
    if related.get("error"):
        print(f"   ❌ Ошибка: {related['error']}")
    else:
        print(f"   ✅ Найдено связанных объектов: {len(related['related'])}")
        if related['related']:
            print(f"   📝 Список связанных ОКС:")
            for i, obj in enumerate(related['related'][:5], 1):
                print(f"      {i}. {obj}")
            if len(related['related']) > 5:
                print(f"      ... и еще {len(related['related']) - 5} объектов")
    
    print(f"\n📋 Пример 2: Работа с Объектом капитального строительства (ОКС)")
    print(f"   Кадастровый номер: {oks_number}")
    print_subsection("Получение информации об ОКС")
    
    # 1. Получаем geom_id
    print("\n1. Получение geom_id:")
    geom_id = api.get_geom_id(oks_number)
    if geom_id:
        print(f"   ✅ geom_id: {geom_id}")
    else:
        print(f"   ❌ Не удалось получить geom_id")
        return
    
    # 2. Определяем тип объекта
    print("\n2. Определение типа объекта:")
    obj_type = api.get_object_type(oks_number)
    if obj_type:
        print(f"   ✅ Тип объекта: {obj_type}")
        print(f"   💡 ОКС может быть: Здание, Сооружение или Объект незавершенного строительства")
    else:
        print(f"   ❌ Не удалось определить тип")
    
    # 3. Получаем связанные объекты
    print("\n3. Получение связанных объектов:")
    related = api.get_related_objects(oks_number)
    if related.get("error"):
        print(f"   ❌ Ошибка: {related['error']}")
    else:
        print(f"   ✅ Найдено связанных объектов: {len(related['related'])}")
        if related['related']:
            print(f"   📝 Список связанных ЗУ:")
            for i, obj in enumerate(related['related'], 1):
                print(f"      {i}. {obj}")

def demo_get_info_function():
    """
    Демонстрация универсальной функции get_object_info()
    """
    print_section("⚡ УНИВЕРСАЛЬНАЯ ФУНКЦИЯ get_object_info()")
    
    api = NSPD()
    kad_number = "77:03:0002007:7190"
    
    print(f"\n📋 Кадастровый номер: {kad_number}")
    print("\n💡 Эта функция позволяет получить всю информацию об объекте одним запросом")
    print("   с возможностью выбора дополнительных полей через параметры.")
    
    # 1. Только базовые данные (по умолчанию)
    print_subsection("Вариант 1: Только базовые данные (по умолчанию)")
    data = api.get_object_info(kad_number)
    if "error" in data:
        print(f"❌ Ошибка: {data['error']}")
    else:
        print(f"✅ Получены базовые данные")
        print(f"   📦 Доступные ключи: {', '.join(list(data.keys())[:5])}...")
        print(f"   🔢 Кадастровый номер: {data.get('kad_number')}")
    
    # 2. С дополнительным geom_id
    print_subsection("Вариант 2: С дополнительным geom_id")
    data = api.get_object_info(kad_number, include_geom_id=True)
    if "error" in data:
        print(f"❌ Ошибка: {data['error']}")
    else:
        print(f"✅ Получены данные с geom_id")
        print(f"   🔑 geom_id: {data.get('geom_id')}")
        print(f"   💡 Используйте include_geom_id=True для получения идентификатора геометрии")
    
    # 3. С дополнительным object_type
    print_subsection("Вариант 3: С дополнительным object_type")
    data = api.get_object_info(kad_number, include_object_type=True)
    if "error" in data:
        print(f"❌ Ошибка: {data['error']}")
    else:
        print(f"✅ Получены данные с типом объекта")
        print(f"   🏷️  Тип объекта: {data.get('object_type')}")
        print(f"   💡 Используйте include_object_type=True для определения типа объекта")
    
    # 4. С обоими дополнительными полями
    print_subsection("Вариант 4: С обоими дополнительными полями")
    data = api.get_object_info(kad_number, include_geom_id=True, include_object_type=True)
    if "error" in data:
        print(f"❌ Ошибка: {data['error']}")
    else:
        print(f"✅ Получены полные данные")
        print(f"   🔑 geom_id: {data.get('geom_id')}")
        print(f"   🏷️  Тип объекта: {data.get('object_type')}")
        print(f"   🔢 Кадастровый номер: {data.get('kad_number')}")
        print(f"   💡 Комбинируйте параметры для получения нужных данных")

def demo_comparison():
    """
    Сравнение различных способов получения данных
    """
    print_section("📊 СРАВНЕНИЕ СПОСОБОВ ПОЛУЧЕНИЯ ДАННЫХ")
    
    api = NSPD()
    kad_number = "77:03:0002007:7190"
    
    print(f"\n📋 Объект: {kad_number}")
    print("\n💡 Сравним два подхода к получению данных:")
    
    # Способ 1: Отдельные функции
    print_subsection("Способ 1: Отдельные функции (несколько запросов)")
    start_time = time.time()
    geom_id = api.get_geom_id(kad_number)
    obj_type = api.get_object_type(kad_number)
    time1 = time.time() - start_time
    
    print(f"   🔑 geom_id: {geom_id}")
    print(f"   🏷️  object_type: {obj_type}")
    print(f"   ⏱️  Время выполнения: {time1:.2f} сек")
    print(f"   📡 Количество запросов: 2 (get_geom_id + get_object_type)")
    print(f"   ⚠️  Каждая функция делает отдельный запрос к НСПД")
    
    # Способ 2: Универсальная функция
    print_subsection("Способ 2: Универсальная функция (один запрос)")
    start_time = time.time()
    data = api.get_object_info(kad_number, include_geom_id=True, include_object_type=True)
    time2 = time.time() - start_time
    
    if "error" not in data:
        print(f"   🔑 geom_id: {data.get('geom_id')}")
        print(f"   🏷️  object_type: {data.get('object_type')}")
        print(f"   ⏱️  Время выполнения: {time2:.2f} сек")
        print(f"   📡 Количество запросов: 1 (get_object_info с параметрами)")
        print(f"   ✅ Один запрос вместо двух - быстрее и эффективнее!")
    
    print(f"\n💡 Вывод: Используйте get_object_info() для получения нескольких полей одновременно!")

def demo_coordinates():
    """
    Демонстрация получения объектов по координатам
    """
    print_section("🗺️  ПОЛУЧЕНИЕ ОБЪЕКТОВ ПО КООРДИНАТАМ")
    
    api = NSPD()
    
    # Тестовые координаты
    test_coordinates = [
        (55.811978, 37.498339, "Москва, центр", "ЗУ"),
        (55.756126, 37.615042, "Москва, центр", "ОКС")
    ]
    
    print("\n💡 Библиотека позволяет найти кадастровый номер объекта по его координатам")
    print("   Это полезно, когда у вас есть только географические координаты точки.")
    
    for lat, lon, description, obj_type in test_coordinates:
        print_subsection(f"Поиск {obj_type} по координатам")
        print(f"📍 Координаты: {lat}, {lon}")
        print(f"   Описание: {description}")
        
        start_time = time.time()
        
        if obj_type == "ЗУ":
            kad_number = api.get_land_plot_by_coordinates(lat, lon)
            obj_name = "Земельный участок"
        else:
            kad_number = api.get_oks_by_coordinates(lat, lon)
            obj_name = "Объект капитального строительства"
        
        end_time = time.time()
        request_time = end_time - start_time
        
        if kad_number:
            print(f"   ✅ Найден {obj_name}: {kad_number}")
            print(f"   ⏱️  Время поиска: {request_time:.2f} сек")
            
            # Дополнительно получаем информацию о найденном объекте
            print(f"\n   📋 Дополнительная информация о найденном объекте:")
            obj_type_found = api.get_object_type(kad_number)
            if obj_type_found:
                print(f"      🏷️  Тип объекта: {obj_type_found}")
            
            geom_id = api.get_geom_id(kad_number)
            if geom_id:
                print(f"      🔑 geom_id: {geom_id}")
        else:
            print(f"   ❌ {obj_name} не найден за {request_time:.2f} сек")
            print(f"   💡 Возможно, в этой точке нет объекта или нужен больший bbox_size")

def demo_grid():
    """
    Демонстрация работы с Grid (массовая выгрузка)
    """
    print_section("📦 МАССОВАЯ ВЫГРУЗКА ЧЕРЕЗ GRID")
    
    api = NSPD()
    
    print("\n💡 Grid позволяет получить все объекты определенного типа в границах")
    print("   кадастрового района, квартала или округа.")
    print("\n⚠️  Внимание: Это может занять некоторое время, так как обрабатывается")
    print("   большое количество объектов.")
    
    coords = (55.770783, 37.73718)
    print(f"\n📍 Координаты для определения границ: {coords[0]}, {coords[1]}")
    print(f"   Используем границы кадастрового района (boundary_type='kr')")
    print(f"   Выгружаем только Земельные участки (category_id=36368)")
    
    print("\n⏳ Начинаем выгрузку...")
    start_time = time.time()
    
    result = api.get_grid_data(
        coords[0], 
        coords[1], 
        boundary_type='kr', 
        category_id=36368,  # ЗУ
        verbose=False  # Устанавливаем False для более чистого вывода
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    if result:
        features = result.get('features', [])
        print(f"\n✅ Выгрузка завершена за {execution_time:.2f} сек")
        print(f"   📊 Найдено объектов: {len(features)}")
        if features:
            print(f"\n   📝 Примеры найденных объектов (первые 5):")
            for i, feature in enumerate(features[:5], 1):
                properties = feature.get('properties', {})
                options = properties.get('options', {})
                cad_num = options.get('cad_num', 'N/A')
                print(f"      {i}. {cad_num}")
            if len(features) > 5:
                print(f"      ... и еще {len(features) - 5} объектов")
    else:
        print(f"\n❌ Не удалось получить данные через Grid")
        print(f"   💡 Проверьте подключение к интернету и доступность НСПД")

def demo_error_handling():
    """
    Демонстрация обработки ошибок
    """
    print_section("⚠️  ОБРАБОТКА ОШИБОК")
    
    api = NSPD()
    
    print("\n💡 Библиотека корректно обрабатывает различные ошибочные ситуации:")
    print("   - Неверные кадастровые номера")
    print("   - Несуществующие объекты")
    print("   - Пустые значения")
    
    error_cases = [
        ("99:99:9999999:9999", "Неверный формат номера"),
        ("", "Пустой номер"),
        ("77:03:0002007:9999", "Номер не существует в базе")
    ]
    
    for case, description in error_cases:
        print_subsection(f"Тест: {description}")
        print(f"   Входные данные: '{case}'")
        
        # Тест get_geom_id
        geom_id = api.get_geom_id(case)
        if geom_id is None:
            print(f"   ✅ get_geom_id: Корректно вернул None")
        else:
            print(f"   ⚠️  get_geom_id: Вернул значение (может быть валидным)")
        
        # Тест get_object_type
        obj_type = api.get_object_type(case)
        if obj_type is None:
            print(f"   ✅ get_object_type: Корректно вернул None")
        else:
            print(f"   ⚠️  get_object_type: Вернул значение")
        
        # Тест get_related_objects
        related = api.get_related_objects(case)
        if related.get("error"):
            print(f"   ✅ get_related_objects: Корректно вернул ошибку")
        else:
            print(f"   ⚠️  get_related_objects: Не вернул ошибку")

def main():
    """
    Главная функция демонстрации
    """
    print("="*70)
    print("  🎯 ДЕМОНСТРАЦИЯ БИБЛИОТЕКИ NSPD")
    print("="*70)
    print("\n  Библиотека для работы с НСПД (Национальная система пространственных данных)")
    print("  Автоматическое получение данных и связей между объектами недвижимости")
    print("\n  Возможности:")
    print("  • Получение информации по кадастровому номеру")
    print("  • Определение типа объекта (ЗУ, Здание, Сооружение, ОНС)")
    print("  • Поиск связанных объектов")
    print("  • Поиск объектов по координатам")
    print("  • Массовая выгрузка объектов через Grid")
    
    try:
        demo_basic_functions()
        demo_get_info_function()
        demo_comparison()
        demo_coordinates()
        demo_grid()
        demo_error_handling()
        
        print_section("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print("\n  📚 Для получения дополнительной информации:")
        print("     • Читайте README.md - быстрый старт и примеры")
        print("     • Читайте DOCUMENTATION.md - полная документация")
        print("     • Изучайте исходный код в nspd_request/nspd_request.py")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n\n❌ Ошибка при демонстрации: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
