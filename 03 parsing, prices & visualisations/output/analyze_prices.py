# analyze_prices.py
import pandas as pd
import matplotlib.pyplot as plt

def main():
    # Загружаем данные из Excel
    df = pd.read_excel("results.xlsx")

    # Преобразуем колонку "Цена" в число, ошибки заменяем на NaN
    df["Цена"] = pd.to_numeric(df["Цена"], errors="coerce")

    # Фильтруем только строки, где цена > 0
    df = df[df["Цена"] > 0]

    # Вычисляем среднюю цену
    avg_price = df["Цена"].mean()
    print(f"Средняя цена светильников: {avg_price:.2f} руб.")

    # --- Гистограмма ---
    plt.figure(figsize=(10, 6))
    plt.hist(df["Цена"], bins=15, edgecolor="black")
    plt.title("Распределение цен на светильники")
    plt.xlabel("Цена (руб.)")
    plt.ylabel("Количество товаров")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.show()

    # --- Boxplot ---
    plt.figure(figsize=(8, 6))
    plt.boxplot(df["Цена"], vert=True, patch_artist=True)
    plt.title("Boxplot цен на светильники")
    plt.ylabel("Цена (руб.)")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.show()

if __name__ == "__main__":
    main()
