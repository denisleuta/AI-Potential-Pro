import psycopg2
import pandas as pd

# Чтение данных из Excel
df = pd.read_excel("physical_2007.xlsx")

# Преобразование числовых столбцов
numeric_columns = df.columns[1:]
for col in numeric_columns:
    df[col] = df[col].astype(str).str.replace(",", ".").astype(float)

# Замена пустых значений на 0
df = df.fillna(0)
# Настройки подключения
conn = psycopg2.connect(
    dbname="ZenitRadar", user="postgres", password="masha25", host="localhost"
)

cur = conn.cursor()

# Создание таблицы
cur.execute(
    """
CREATE TABLE IF NOT EXISTS player_physics (
    id SERIAL PRIMARY KEY,
    player VARCHAR(200),
    player_0_15 NUMERIC,
    player_15_30 NUMERIC,
    player_0_30 NUMERIC,
    jump NUMERIC
    )
"""
)
conn.commit()

# Вставка данных в таблицу
for index, row in df.iterrows():
    cur.execute(
        """
        INSERT INTO player_physics (
            player, player_0_15, player_15_30, player_0_30, jump
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            row["Игрок "],
            row["0-15 м (с)"],
            row["15-30 м (с)"],
            row["0-30 м (с)"],
            row["Прыжок в длинну"],
        ),
    )

conn.commit()

cur.close()
conn.close()
