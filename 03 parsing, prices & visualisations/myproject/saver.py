# saver.py
import os
from openpyxl import Workbook

# Директория для сохранения файлов
OUTPUT_DIR = "output"

FIELDS = ["name", "price", "currency", "url"]
HEADER_NAMES = {
    "name": "Название",
    "price": "Цена",
    "currency": "Валюта",
    "url": "Ссылка"
}

def save_xlsx(data, filename="data.xlsx"):
    """Сохраняет список словарей в XLSX с корректными типами данных."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    wb = Workbook()
    ws = wb.active
    ws.title = "Data"

    # Заголовки
    ws.append([HEADER_NAMES[f] for f in FIELDS])

    # Данные
    for item in data:
        row = [item.get(f, "") for f in FIELDS]
        ws.append(row)

    wb.save(filepath)
    return filepath