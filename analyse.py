import pandas as pd

# --- 1. Загрузка и подготовка ---
df = pd.read_excel("last.xlsx")  # или другой разделитель / Excel

# Приведение индекса к float
df["Индекс_на_матч"] = (
    df["Индекс_на_матч"].astype(str).str.replace(",", ".").astype(float)
)

# 1. Считаем матчей НЕ по игроку, а по (Турнир, Амплуа, Игрок)
matches_per_role = (
    df.groupby(["Турнир", "Амплуа", "Игрок"])["Матч"].nunique().rename("Матчей_в_роли")
)

df = df.merge(matches_per_role, on=["Турнир", "Амплуа", "Игрок"])

# 2. Фильтр: только если сыграл >10 матчей В ЭТОЙ РОЛИ
df_filtered = df[df["Матчей_в_роли"] > 10]

# 3. Уникальные матчи в рамках роли
df_unique = df_filtered.drop_duplicates(["Турнир", "Амплуа", "Игрок", "Матч"])

# 4. Агрегация — как раньше, но только для тех, кто реально отыграл роль
ratings_by_role = (
    df_unique.groupby(["Турнир", "Амплуа", "Игрок"])
    .apply(
        lambda g: pd.Series(
            {
                "Средний_индекс": g["Индекс_на_матч"].mean(),
                "Команда": g["Команда"].mode().iloc[0]
                if not g["Команда"].mode().empty
                else g["Команда"].iloc[0],
                "Матчей": g["Матчей_в_роли"].iloc[0],
            }
        )
    )
    .reset_index()
)
# --- 3. Формирование топов ---
# Словарь: {турнир: список (амплуа, топ-25 DataFrame)}
tournament_tops = {}

for tournament in ratings_by_role["Турнир"].unique():
    tourney_data = ratings_by_role[ratings_by_role["Турнир"] == tournament]
    tops_by_role = {}
    for role in tourney_data["Амплуа"].unique():
        role_data = tourney_data[tourney_data["Амплуа"] == role]
        top25 = role_data.nlargest(25, "Средний_индекс").reset_index(drop=True)
        tops_by_role[role] = top25
    tournament_tops[tournament] = tops_by_role

# --- 4. Запись в Excel ---
with pd.ExcelWriter("Рейтинги_по_турнирам_и_амплуа.xlsx", engine="openpyxl") as writer:
    for tournament, role_tops in tournament_tops.items():
        # Создаём один лист на турнир
        sheet_name = tournament[:31].replace(":", "").replace("/", "_")  # Excel-safe
        # Начинаем с первой строки
        start_row = 0
        for role, df_top in role_tops.items():
            if df_top.empty:
                continue
            # Заголовок амплуа
            header = pd.DataFrame([f"🔹 Амплуа: {role} (Топ-{len(df_top)})"])
            header.to_excel(
                writer,
                sheet_name=sheet_name,
                startrow=start_row,
                index=False,
                header=False,
            )
            start_row += 1

            # Таблица: Игрок | Команда | Средний_индекс | Матчей
            output_df = df_top[["Игрок", "Команда", "Средний_индекс", "Матчей"]].copy()
            output_df.to_excel(
                writer, sheet_name=sheet_name, startrow=start_row, index=False
            )
            start_row += len(output_df) + 3  # +3 для отступа между блоками

print("✅ Готово! Файл сохранён: 'Рейтинги_по_турнирам_и_амплуа.xlsx'")
