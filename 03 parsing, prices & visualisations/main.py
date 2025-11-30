# main.py
from myproject.scraper import scrape_all_pages
import pandas as pd

if __name__ == "__main__":
    print("Начинаем парсинг...")
    data = scrape_all_pages("https://www.divan.ru/category/svet?sort=0", headless=True)
    print(f"Получено товаров: {len(data)}")

    if not data:
        print("Внимание: Данные не получены! Проверьте подключение к интернету и доступность сайта.")
    else:
        # Сохраняем в XLSX
        df = pd.DataFrame(data)
        df.to_excel("lamps.xlsx", index=False, engine="openpyxl")
        print("Данные сохранены в lamps.xlsx")
