# random_scatter.py
# Построй диаграмму рассеяния для двух наборов случайных данных,
# сгенерированных с помощью функции `numpy.random.rand'.
import numpy as np
import matplotlib.pyplot as plt

# Создаём 2 массива
x = np.random.random(200) # 200 случайных чисел для оси X
y = np.random.random(200) # 200 случайных чисел для оси Y

# Создаём диаграмму рассеяния
plt.scatter(x,y, alpha=0.7, color="blue", edgecolors="black")

# Настраиваем график: название и подписи осей (сетка по оси Y будет пунктирной и слегка прозрачной (непрозрачность 60%)
plt.xlabel("ось X")
plt.ylabel("ось Y")
plt.title("Тестовая диаграмма рассеяния двух списков случайных чисел")
plt.grid(True, linestyle="--", alpha=0.6)

#Выводим график рассеяния
plt.show()



