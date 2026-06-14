import psycopg2
import pandas as pd


df = pd.read_excel("stats_data_sport_preprocessed_results.xlsx")

# Настройки подключения
conn = psycopg2.connect(
    dbname="ZenitRadar", user="postgres", password="masha25", host="localhost"
)

cur = conn.cursor()

# Создание таблицы с учетом всех необходимых колонок
cur.execute(
    """
CREATE TABLE IF NOT EXISTS index_ttd (
    id SERIAL PRIMARY KEY,
    tournament VARCHAR(100),
    player VARCHAR(200),
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
        INSERT INTO index_ttd (tournament, player, time_to_game, index)
        VALUES (%s, %s, %s, %s)
    """,
        (
            row["Турнир"],
            row["Игрок"],
            row["Минут на поле"],
            row["Index"],
        ),
    )

conn.commit()

cur.close()
conn.close()
