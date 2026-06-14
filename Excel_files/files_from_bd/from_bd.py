import psycopg2
import pandas as pd
import os

# Устанавливаем соединение с базой данных
conn = psycopg2.connect(
    host="localhost",
    database="ZenitRadar",
    user="postgres",
    password="masha25",
    options="-c client_encoding=UTF8",
)

# Создаем курсор
cursor = conn.cursor()

# Выполняем SQL-запрос
cursor.execute("SELECT * FROM combined_footballerss")
rows = cursor.fetchall()


# Получаем названия столбцов
columns = [desc[0] for desc in cursor.description]

# Создаем DataFrame из данных
df = pd.DataFrame(rows, columns=columns)

# Создаем директорию, если она не существует
output_directory = "files_from_bd"

# Путь к выходному файлу
output_file_path = os.path.join(output_directory, "combined_footballerss.xlsx")

# Записываем данные в Excel-файл
df.to_excel(output_file_path, index=False, engine="openpyxl")


# Выполняем SQL-запрос
cursor.execute("SELECT * FROM academy_results_zenit")
rows = cursor.fetchall()


# Получаем названия столбцов
columns = [desc[0] for desc in cursor.description]

# Создаем DataFrame из данных
df = pd.DataFrame(rows, columns=columns)

# Путь к выходному файлу
output_file_path = os.path.join(output_directory, "academy_results_zenit.xlsx")

# Записываем данные в Excel-файл
df.to_excel(output_file_path, index=False, engine="openpyxl")


# Закрываем соединение
cursor.close()
conn.close()
