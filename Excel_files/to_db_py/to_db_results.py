import psycopg2
import pandas as pd


df = pd.read_excel("academy_data_sport_results.xlsx")

# Настройки подключения
conn = psycopg2.connect(
    dbname="ZenitRadar", user="postgres", password="masha25", host="localhost"
)

cur = conn.cursor()

# Создание таблицы с учетом всех необходимых колонок
cur.execute(
    """
CREATE TABLE IF NOT EXISTS academy_results (
    id SERIAL PRIMARY KEY,
    tournament VARCHAR(100),
    team VARCHAR(100),
    player VARCHAR(200),
    role VARCHAR(10),
    time_to_game integer,
    index integer

)
"""
)
conn.commit()

# Вставка данных в таблицу
for index, row in df.iterrows():
    cur.execute(
        """
        INSERT INTO academy_results (tournament, team, player, role, time_to_game, index)
        VALUES (%s, %s, %s, %s, %s, %s)
    """,
        (
            row["Турнир"],
            row["Команда"],
            row["Игрок"],
            row["Амплуа"],
            row["Время на поле"],
            row["Индекс ТТД"],
        ),
    )

conn.commit()

cur.close()
conn.close()


# Читаем Excel-файл
df = pd.read_excel("files_from_bd/academy_results_zenit.xlsx")

# Подключаемся к базе данных
conn = psycopg2.connect(
    dbname="ZenitRadar", user="postgres", password="masha25", host="localhost"
)

# Создаем курсор
cur = conn.cursor()

# Импортируем данные в таблицу
for index, row in df.iterrows():
    cur.execute(
        "INSERT INTO your_table (id, name, email) VALUES (%s, %s, %s)",
        (row["id"], row["name"], row["email"]),
    )

# Сохраняем изменения
conn.commit()

# Закрываем соединение
cur.close()
conn.close()
