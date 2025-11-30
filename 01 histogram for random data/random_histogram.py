# random_histogram.py

# Создай гистограмму для случайных данных,
# сгенерированных с помощью функции `numpy.random.normal`.

import matplotlib.pyplot as plt
import numpy as np

mean = 0       # Среднее значение
std_dev = 1    # Стандартное отклонение
num_samples = 1000  # Количество образцов

data = np.random.normal(mean, std_dev, num_samples)

#  Создаём гистограмму с интервалом 50 из 1000 значений.
plt.hist(data, bins=50, edgecolor="black", alpha=0.7)

# Подписываем график
plt.xlabel("Значение")
plt.ylabel("Частота")
plt.title("Тестовая гистограмма")

# Делаем сетку на фоне графика:
plt.grid(True, linestyle="--", alpha=0.6)

# Выводим график
plt.show()





