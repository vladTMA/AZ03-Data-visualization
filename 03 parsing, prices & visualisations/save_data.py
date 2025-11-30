# Скрипт для сохранения данных вручную
# Используйте этот скрипт, если нужно сохранить данные отдельно

from myproject import saver, scraper

def save_current_data():
    """Сохраняет данные, собранные на данный момент."""
    print("Сбор данных...")
    
    # Собираем данные (можно уменьшить max_pages для быстрого теста)
    data = scraper.scrape_all_pages(
        "https://www.divan.ru/category/svet?sort=0",
        headless=False,
        max_pages=1,  # Только первая страница для быстрого сохранения
        delay_between_pages=5
    )
    
    if not data:
        print("Данные не получены!")
        return
    
    print(f"Найдено товаров: {len(data)}")
    
    # Сохраняем в XLSX
    filepath = saver.save_xlsx(data, filename="results.xlsx")
    print(f"\nДанные сохранены в: {filepath}")
    
    # Выводим примеры
    print("\nПервые 5 товаров:")
    for i, item in enumerate(data[:5], 1):
        name = item.get('name', 'Нет названия')[:50]
        price = item.get('price', 'Нет цены')
        currency = item.get('currency', '')
        print(f"  {i}. {name} - {price} {currency}")

if __name__ == "__main__":
    save_current_data()

