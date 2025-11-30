# run.py
from myproject import saver, scraper


def main():
    print("Начинаем парсинг всех страниц раздела...")
    # ВАЖНО: headless=False для обхода защиты сайта
    # Сайт блокирует headless режим, поэтому используем видимый браузер
    data = scraper.scrape_all_pages(
        "https://www.divan.ru/category/svet?sort=0",
        headless=False,  # False для обхода защиты (headless режим блокируется сайтом)
        max_pages=10,  # Уменьшено для теста (можно увеличить после проверки пагинации)
        delay_between_pages=10  # задержка между страницами
    )

    if not data:
        print("Внимание: данные не получены! Проверьте интернет и доступность сайта.")
        return

    print(f"Найдено товаров: {len(data)}")

    # Сохраняем в XLSX через saver
    saver.save_xlsx(data, filename="results.xlsx")

    # Выводим первые 3 товара
    print("\nПервые 3 товара:")
    for item in data[:3]:
        print(f"  - {item.get('name', 'Нет названия')}: {item.get('price', 'Нет цены')} {item.get('currency', '')}")

if __name__ == "__main__":
    main()
