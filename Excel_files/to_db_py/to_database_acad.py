import psycopg2
import pandas as pd


df = pd.read_excel("tt_2007.xlsx")
numeric_columns = df.columns[4:]
for col in numeric_columns:
    df[col] = df[col].astype(str).str.replace(",", ".").astype(float)
df = df.fillna(0)
# Настройки подключения
conn = psycopg2.connect(
    dbname="ZenitRadar", user="postgres", password="masha25", host="localhost"
)

cur = conn.cursor()

# Создание таблицы
cur.execute(
    """
CREATE TABLE IF NOT EXISTS player_stats (
    id SERIAL PRIMARY KEY,
    player VARCHAR(200),
    match VARCHAR(200),
    tournament VARCHAR(100),
    position VARCHAR(50),
    time_on_field INTEGER,
    goal_scoring_efficiency NUMERIC,
    shot_accuracy NUMERIC,
    ball_receiving NUMERIC,
    contested_passes NUMERIC,
    key_passes NUMERIC,
    progressive_passes NUMERIC,
    crosses NUMERIC,
    dribbles_to_final_third NUMERIC,
    dribbles_in_final_third NUMERIC,
    tackles NUMERIC,
    neutral_zone_duels NUMERIC,
    attacking_aerial_duels NUMERIC,
    defensive_aerial_duels NUMERIC,
    effective_dribbles_in_final_third NUMERIC,
    effective_ball_progression NUMERIC,
    effective_ball_recovery NUMERIC,
    gross_goal_error_per_90 NUMERIC,
    gross_error_per_90 NUMERIC,
    goal_creating_actions_per_90 NUMERIC,
    goal_participation_per_90 NUMERIC,
    opening_per_90 NUMERIC,
    goal_assists_per_90 NUMERIC,
    ball_progression_dribbles_per_90 NUMERIC,
    blocks_per_90 NUMERIC,
    interceptions_per_90 NUMERIC,
    ball_recoveries_per_90 NUMERIC,
    fouls_drawn_per_90 NUMERIC,
    offsides_per_90 NUMERIC
)
"""
)
conn.commit()

# Вставка данных в таблицу
for index, row in df.iterrows():
    cur.execute(
        """
        INSERT INTO player_stats (
            player, match, tournament, position, time_on_field, goal_scoring_efficiency,
            shot_accuracy, ball_receiving, contested_passes, key_passes, progressive_passes,
            crosses, dribbles_to_final_third, dribbles_in_final_third, tackles,
            neutral_zone_duels, attacking_aerial_duels, defensive_aerial_duels,
            effective_dribbles_in_final_third, effective_ball_progression, effective_ball_recovery,
            gross_goal_error_per_90, gross_error_per_90, goal_creating_actions_per_90,
            goal_participation_per_90, opening_per_90, goal_assists_per_90,
            ball_progression_dribbles_per_90, blocks_per_90, interceptions_per_90,
            ball_recoveries_per_90, fouls_drawn_per_90, offsides_per_90
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            row[" Игрок"],
            row[" Матч"],
            row[" Турнир"],
            row[" Позиция"],
            row[" Время на поле"],
            row["Реализация голевых моментов"],
            row["Точность ударов"],
            row["Прием мяча"],
            row["Передача в борьбу"],
            row["Передача ключевая"],
            row["Передача прогрессивная"],
            row["Навесы"],
            row["Обводка до зоны завершения"],
            row["Обводка в зоне завершения"],
            row["Отборы"],
            row["Борьба за нейтральный мяч"],
            row["Единоборство вверху в атаке"],
            row["Единоборство вверху в обороне"],
            row["Эфф. обводки в зоне завершения"],
            row["Эфф. продвижения мяча вперед (дриблинг)"],
            row["Эфф. подбора мяча"],
            row["Грубая голевая ошибка / 90 мин."],
            row["Грубая ошибка / 90 мин."],
            row["Голевой момент создал / 90 мин."],
            row["Участие в голевой атаке / 90 мин."],
            row["Открывание / 90 мин."],
            row["Голевые передачи / 90 мин."],
            row["Продвижение мяча вперед за счет дриблинга / 90 мин."],
            row["Блокировка / 90 мин."],
            row["Перехваты / 90 мин."],
            row["Подборы мяча / 90 мин."],
            row["Фол на игроке / 90 мин."],
            row["Офсайд / 90 мин."],
        ),
    )

conn.commit()

cur.close()
conn.close()
