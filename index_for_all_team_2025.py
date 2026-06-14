import streamlit as st
import pandas as pd
import numpy as np
import glob
from io import BytesIO

# Группировка показателей по категориям
categories_def = {
    "атака": [
        "Голевой момент создал",
        "Удар в створ",
        "Удар мимо",
        "Голевой момент не реализовал",
        "Участие в голевой атаке",
        "Голевой момент реализовал",
        "Передача голевая",
    ],
    "защита": [
        "Единоборство вверху в атаке неудачное",
        "Единоборство вверху в атаке удачное",
        "Перехват передачи",
        "Борьба за нейтральный мяч удачная",
        "Блокировка передачи",
        "Борьба за нейтральный мяч неудачная",
        "Грубая голевая ошибка",
        "Отбор удачный",
        "Гол пропущенный",  #
        "Единоборство вверху в обороне неудачное",
        "Единоборство вверху в обороне удачное",
    ],
    "пас": [
        "Передача в борьбу -",
        "Передача в борьбу рукой +" "Передача ключевая неточная",
        "Навес точный",
        "Передача прогрессивная неточная",
        "Передача прогрессивная точная",
        "Навес неточный",
        "Передача ключевая точная",
        "Передача без развития",  #
        "Передача ногой длинная неточная",  #
        "Передача ногой короткая/средняя точная",
        "Передача ногой длинная точная",
        "Передача рукой короткая/средняя точная",
        "Передача рукой длинная точная",
        "Передача рукой длинная неточная",  #
        "Передача рукой короткая/средняя неточная",  #
    ],
    "дриблинг": [
        "Обводка в зоне завершения удачная",
        "Обводка до зоны завершения удачная",
        'Эффективность "+" Продвижения мяча вперед за счет дриблинга',
        'Эффективность "+" Обводки в зоне завершения',
        'Эффективность "-" Продвижения мяча вперед за счет дриблинга',
        'Эффективность "-" Обводки в зоне завершения',
    ],
    "другое": [
        "Выносы мяча",
        "Фол",
        "Грубая ошибка",
        "Прием мяча неудачный",
        "Красная карточка",  #
        "Потеря мяча",
        'Эффективность "+" Подбора мяча',
    ],
}

negative_impact_metrics = {
    "Атака": ["Удар мимо", "Голевой момент не реализовал"],
    "Защита": [
        "Единоборство вверху в атаке неудачное",
        "Единоборство вверху в обороне неудачное",
        "Борьба за нейтральный мяч неудачная",
        "Грубая голевая ошибка",
    ],
    "Пас": [
        "Передача без развития",
        "Передача прогрессивная неточная",
        "Передача в борьбу -",
        "Навес неточный",
        "Передача ногой длинная неточная",  #
        "Передача рукой длинная неточная",  #
        "Передача рукой короткая/средняя неточная",  #
    ],
    "Другое": [
        "Фол",
        "Грубая ошибка",
        "Прием мяча неудачный",
        "Потеря мяча",
        "Красная карточка",
    ],
}


def min_max_normalize(series):
    return (series - series.min()) / (series.max() - series.min())


# Вычисление баллов по категориям для каждого игрока
def compute_category_scores(
    df, metric_columns, categories_def, negative_impact_metrics
):
    df_scores = df.copy()
    # Расчет сырых баллов без нормализации
    for cat, metrics in categories_def.items():
        present_metrics = [m for m in metrics if m in metric_columns]
        positive_metrics = [
            m for m in present_metrics if m not in negative_impact_metrics.get(cat, [])
        ]
        negative_metrics = [
            m for m in present_metrics if m in negative_impact_metrics.get(cat, [])
        ]

        positive_score = df[positive_metrics].sum(axis=1) if positive_metrics else 0
        negative_score = df[negative_metrics].sum(axis=1) if negative_metrics else 0

        df_scores[cat] = positive_score - negative_score

    # Нормализуем итоговые категориальные баллы
    for cat in categories_def.keys():
        if cat in df_scores.columns:
            df_scores[cat] = min_max_normalize(df_scores[cat])

    return df_scores


# Агрегирование данных по игроку (суммирование результатов за все матчи)
def aggregate_player_data(df):
    # Группируем по игроку, позиции, команде и турниру, суммируя показатели по каждому типу действия
    agg_df = df.groupby(
        ["tournament", "player", "position", "team", "data"], as_index=False
    )["actions"].sum()
    # Преобразуем в формат pivot: строки – турнир, игрок, позиция, команда; столбцы – типы действий
    pivot_df = agg_df.pivot_table(
        index=["tournament", "player", "position", "team"],
        columns="data",
        values="actions",
        fill_value=0,
    )
    pivot_df = pivot_df.reset_index()
    return pivot_df


# Получение списка метрик (то, что не является служебными колонками)
def get_metric_columns(df):
    non_metric = {"tournament", "player", "position", "team"}
    return [col for col in df.columns if col not in non_metric]


# Расчёт общего индекса полезности
def compute_overall_index(df, category_list):
    def calculate_overall(row):
        pos = str(row["position"]).lower()
        if pos in ["вратарь", "gk"]:
            return row.get("Вратарская игра", np.nan)
        return row[[cat for cat in category_list if cat in row]].mean()

    df["overall_rating"] = df.apply(calculate_overall, axis=1)
    return df


# Функция для получения топ-N по выбранной колонке
def get_rankings(df, by, top_n=50):
    df_ranked = df.sort_values(by=by, ascending=False).reset_index(drop=True)
    # Выбираем только нужные колонки
    return df_ranked[["player", "position", "team", by]].head(top_n)


def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    processed_data = output.getvalue()
    return processed_data


# Функция загрузки исходных данных
@st.cache_data
def load_data():
    # df = pd.read_excel("julydatasets2025/short_2025_july.xlsx") #2025 год
    df = pd.read_excel("julydatasets2025/full_data.xlsx")  # 2024 год
    df.columns = df.columns.str.strip()

    # Если в файле заголовки заданы неверно, задаём их вручную:
    df.columns = [
        "tournament",
        "player",
        "position",
        "team",
        "match",
        "data",
        "actions",
    ]
    return df


def main():
    st.title("Рейтинги футболистов по позициям и категориям")

    # Загрузка данных
    df_raw = load_data()

    # Выбор турнира
    tournaments = sorted(df_raw["tournament"].unique())
    selected_tournament = st.selectbox("Выберите турнир", tournaments)

    # Фильтрация данных по выбранному турниру
    df_tournament = df_raw[df_raw["tournament"] == selected_tournament]

    # Выбор команды
    teams = sorted(df_tournament["team"].unique().tolist())
    teams.insert(0, "Все команды")
    selected_team = st.selectbox("Выберите команду", teams)

    # Фильтрация по команде, если выбрана конкретная
    if selected_team != "Все команды":
        df_tournament = df_tournament[df_tournament["team"] == selected_team]

    # Агрегируем данные по игрокам (суммируем по всем матчам)
    pivot_df = aggregate_player_data(df_tournament)
    metric_cols = get_metric_columns(pivot_df)

    # Вычисляем баллы по категориям (нормализация метрик и расчёт групповых баллов)
    df_scores = compute_category_scores(
        df=pivot_df,
        metric_columns=metric_cols,
        categories_def=categories_def,
        negative_impact_metrics=negative_impact_metrics,
    )

    # Список категорий, по которым будет рассчитываться общий индекс
    score_categories = list(categories_def.keys())
    df_scores = compute_overall_index(df_scores, score_categories)

    # Разбиваем игроков на вратарей и полевых
    df_goalkeepers = df_scores[
        df_scores["position"].str.lower().isin(["вратарь", "gk"])
    ]
    df_field = df_scores[~df_scores["position"].str.lower().isin(["вратарь", "gk"])]

    # Общий рейтинг топ-10 игроков (все позиции)
    st.header("Общий рейтинг топ-10 игроков")

    # Получаем список всех команд в данных
    all_teams = sorted(df_scores["team"].unique())

    # Мультиселект для исключения команд
    excluded_teams = st.multiselect(
        "Исключить команды из общего рейтинга",
        options=all_teams,
        default=[],
        help="Выберите команды, которые не должны отображаться в общем рейтинге",
    )

    # Фильтруем данные, исключая выбранные команды
    if excluded_teams:
        filtered_scores = df_scores[~df_scores["team"].isin(excluded_teams)]
    else:
        filtered_scores = df_scores.copy()

    # Получаем топ-10 из отфильтрованных данных
    overall_top_10 = get_rankings(filtered_scores, "overall_rating", top_n=200)

    # Показываем таблицу
    st.dataframe(overall_top_10)

    # Кнопка для скачивания общего рейтинга
    st.download_button(
        label="Скачать общий рейтинг в Excel",
        data=to_excel(overall_top_10),
        file_name=f"Общий_рейтинг_{selected_tournament}_{selected_team}.xlsx",
        mime="application/vnd.ms-excel",
    )

    # Рейтинг полевых игроков по позициям
    st.header("Рейтинг полевых игроков по позициям")
    positions = sorted(df_field["position"].unique())
    for pos in positions:
        st.subheader(f"Топ 10 игроков на позиции: {pos}")
        df_pos = df_field[df_field["position"] == pos]
        ranking = get_rankings(df_pos, "overall_rating", top_n=10)
        st.dataframe(ranking)

        # Кнопка для скачивания рейтинга по позиции
        st.download_button(
            label=f"Скачать рейтинг {pos} в Excel",
            data=to_excel(ranking),
            file_name=f"Рейтинг_{pos}_{selected_tournament}_{selected_team}.xlsx",
            mime="application/vnd.ms-excel",
        )

    # Рейтинг по категориям
    st.header("Рейтинг по категориям (для всех игроков)")
    for cat in categories_def.keys():
        if cat in df_scores.columns:
            st.markdown(f"**Топ 10 по категории: {cat}**")
            ranking_cat = get_rankings(df_scores, cat, top_n=10)
            st.dataframe(ranking_cat)

            # Кнопка для скачивания рейтинга по категории
            st.download_button(
                label=f"Скачать рейтинг {cat} в Excel",
                data=to_excel(ranking_cat),
                file_name=f"Рейтинг_{cat}_{selected_tournament}_{selected_team}.xlsx",
                mime="application/vnd.ms-excel",
            )

    # Рейтинг вратарей
    st.header("Рейтинг вратарей")
    if not df_goalkeepers.empty:
        ranking_gk = get_rankings(df_goalkeepers, "overall_rating", top_n=10)
        st.dataframe(ranking_gk)

        # Кнопка для скачивания рейтинга вратарей
        st.download_button(
            label="Скачать рейтинг вратарей в Excel",
            data=to_excel(ranking_gk),
            file_name=f"Рейтинг_вратарей_{selected_tournament}_{selected_team}.xlsx",
            mime="application/vnd.ms-excel",
        )
    else:
        st.info("Данные по вратарям отсутствуют.")


if __name__ == "__main__":
    main()
