import pandas as pd

df = pd.read_excel("top_for_zenit_index/data_zenit.xlsx")


def get_top_players(df, team_name, min_matches=1, top_n=10):
    # Фильтруем по выбранной команде
    team_df = df[df["Команда"] == team_name].copy()

    # Преобразуем числовые колонки
    # Проверяем, является ли столбец строковым, прежде чем применять str.replace
    if team_df["ИндексНаМатч_90"].dtype == object:
        team_df["ИндексНаМатч_90"] = pd.to_numeric(
            team_df["ИндексНаМатч_90"].astype(str).str.replace(",", "."),
            errors="coerce",
        )
    else:
        team_df["ИндексНаМатч_90"] = pd.to_numeric(
            team_df["ИндексНаМатч_90"], errors="coerce"
        )

    team_df["РейтингЧисло"] = pd.to_numeric(team_df["РейтингЧисло"], errors="coerce")

    # Группируем по игроку, амплуа и матчу (усредняем дубликаты для одного матча)
    match_stats = (
        team_df.groupby(["ИгрокФИО", "Амплуа", "Матч"])
        .agg({"ИндексНаМатч_90": "mean", "РейтингЧисло": "mean"})
        .reset_index()
    )

    # Теперь группируем по игроку и амплуа для расчета средних по всем матчам
    player_stats = (
        match_stats.groupby(["ИгрокФИО", "Амплуа"])
        .agg({"ИндексНаМатч_90": "mean", "РейтингЧисло": "mean", "Матч": "count"})
        .rename(columns={"Матч": "КоличествоМатчей"})
        .reset_index()
    )

    # Фильтруем по минимальному количеству матчей
    player_stats = player_stats[player_stats["КоличествоМатчей"] >= min_matches]

    # Сортируем по ИндексуНаМатч_90 и получаем топ-N
    top_by_index = player_stats.sort_values("ИндексНаМатч_90", ascending=False).head(
        top_n
    )

    # Сортируем по РейтингЧисло и получаем топ-N
    top_by_rating = player_stats.sort_values("РейтингЧисло", ascending=False).head(
        top_n
    )

    return top_by_index, top_by_rating


def save_to_excel(top_index, top_rating, filename):
    # Создаем Excel writer
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        # Записываем первую таблицу в A1
        top_index.to_excel(
            writer, sheet_name="Топ игроков", index=False, startrow=0, startcol=0
        )

        # Записываем вторую таблицу с отступом (на 2 столбца правее конца первой таблицы)
        start_col = len(top_index.columns) + 2
        top_rating.to_excel(
            writer,
            sheet_name="Топ игроков",
            index=False,
            startrow=0,
            startcol=start_col,
        )

        # Добавляем заголовки для таблиц
        worksheet = writer.sheets["Топ игроков"]
        worksheet.cell(row=1, column=1, value="Топ по Индексу на матч")
        worksheet.cell(row=1, column=start_col + 1, value="Топ по Рейтингу")


top_index, top_rating = get_top_players(df, "Зенит-М", min_matches=3)
print("Топ по Индексу на матч:")
print(top_index)
print("\nТоп по Рейтингу:")
print(top_rating)
save_to_excel(top_index, top_rating, "top_players.xlsx")
