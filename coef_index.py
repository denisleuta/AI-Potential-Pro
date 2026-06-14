import streamlit as st
import pandas as pd
import numpy as np
import glob
from io import BytesIO

from coefficient import coefficients

# Группировка показателей по категориям
categories_def = {
    "Атака": [
        "Голевой момент создал",
        "Удар мимо",
        "Удар в створ",
        "Единоборство вверху в атаке удачное",
        "Участие в голевой атаке",
        "Голевой момент не реализовал",
        "Голевой момент реализовал",
        "Передача голевая",
        "Единоборство вверху в атаке неудачное",
    ],
    "Защита": [
        "Перехват передачи",
        "Блокировка передачи",
        "Выносы мяча",
        "Отбор удачный",
        "Единоборство вверху в обороне удачное",
        "Единоборство вверху в обороне неудачное",
    ],
    "Пас": [
        "Передача ключевая неточная",
        "Навес точный",
        "Передача прогрессивная неточная",
        "Передача прогрессивная точная",
        "Передача в борьбу -",
        "Навес неточный",
        "Передача ключевая точная",
        "Передача без развития",
        "Передача рукой длинная точная",
        "Передача рукой короткая/средняя точная",
        "Передача ногой длинная точная",
        "Передача ногой короткая/средняя точная",
        "Передача ногой длинная неточная",
        "Передача рукой длинная неточная",
        "Передача рукой короткая/средняя неточная",
        "Передача в борьбу рукой +",
    ],
    "Дриблинг": [
        "Обводка до зоны завершения удачная",
        "Эффективность '-' Продвижения мяча вперед за счет дриблинга",
        "Эффективность '-' Обводки в зоне завершения",
        "Обводка в зоне завершения удачная",
        "Эффективность '+' Обводки в зоне завершения",
        "Эффективность '+' Продвижения мяча вперед за счет дриблинга",
        "Потеря мяча",
    ],
    "Вратарская игра": [
        "Удар от ворот длинный точный",
        "Удар от ворот длинный неточный",
        "Удар от ворот короткий/средний точный",
        "Удар от ворот короткий/средний неточный",
        "Перехват передачи (GK)",
        "Удар зафиксированный",
        "Гол пропущенный",
        "Сейв",
        "Игра на выходе при навесах удачная",
        "Пенальти отбитый",
    ],
    "Другое": [
        "Грубая голевая ошибка",
        "Грубая ошибка",
        "Красная карточка",
        "Фол",
        "Прием мяча неудачный",
        "Эффективность '+' Подбора мяча",
        "Борьба за нейтральный мяч удачная",
        "Борьба за нейтральный мяч неудачная",
    ],
}

negative_impact_metrics = {
    "Атака": [
        "Удар мимо",
        "Голевой момент не реализовал",
        "Единоборство вверху в атаке неудачное",
    ],
    "Защита": [
        "Единоборство вверху в обороне неудачное",
    ],
    "Пас": [
        "Передача ключевая неточная",
        "Передача прогрессивная неточная",
        "Передача в борьбу -",
        "Навес неточный",
        "Передача без развития",
        "Передача ногой длинная неточная",
        "Передача рукой длинная неточная",
        "Передача рукой короткая/средняя неточная",
    ],
    "Дриблинг": [
        "Эффективность '-' Продвижения мяча вперед за счет дриблинга",
        "Эффективность '-' Обводки в зоне завершения",
        "Потеря мяча",
    ],
    "Вратарская игра": [
        "Удар от ворот длинный неточный",
        "Удар от ворот короткий/средний неточный",
        "Гол пропущенный",
    ],
    "Другое": [
        "Грубая голевая ошибка",
        "Грубая ошибка",
        "Красная карточка",
        "Фол",
        "Прием мяча неудачный",
        "Борьба за нейтральный мяч неудачная",
    ],
}

position_categories = {
    "GK": ["Вратарская игра"],
    "CD": ["Атака", "Защита", "Пас", "Другое"],
    "FB": ["Атака", "Защита", "Пас", "Дриблинг", "Другое"],
    "DM": ["Атака", "Защита", "Пас", "Дриблинг", "Другое"],
    "AM": ["Пас", "Дриблинг", "Атака", "Другое"],
    "W": ["Атака", "Пас", "Дриблинг", "Другое"],
    "ST": ["Атака", "Пас", "Дриблинг", "Другое"],
    "default": ["Атака", "Защита", "Пас", "Дриблинг", "Вратарская игра"],
}


def min_max_normalize(series):
    return (series - series.min()) / (series.max() - series.min())


# Преобразование словаря коэффициентов в DataFrame
def flatten_coefficients_dict(coefficients_dict):
    rows = []
    for pos, metrics in coefficients_dict.items():
        for metric, coef in metrics.items():
            rows.append({"position": pos, "metric": metric, "coefficient": coef})
    return pd.DataFrame(rows)


coeff_df = flatten_coefficients_dict(coefficients)


def apply_position_weights(df, coeff_df):
    df_weighted = df.copy()
    metric_cols = get_metric_columns(df)

    for metric in metric_cols:
        # Объединяем данные с коэффициентами по позиции и названию метрики
        merged = df_weighted.merge(
            coeff_df[coeff_df["metric"] == metric][["position", "coefficient"]],
            on="position",
            how="left",
        )
        # Умножаем метрику на коэффициент (по умолчанию 1.0 если коэффициент не найден)
        df_weighted[metric] = df_weighted[metric] * merged["coefficient"].fillna(1.0)

    return df_weighted


# Вычисление баллов по категориям для каждого игрока
def compute_category_scores(
    df, metric_columns, categories_def, negative_impact_metrics
):
    df_scores = df.copy()

    # Нормализация
    for cat in categories_def.keys():
        if cat in df_scores.columns:
            df_scores[cat] = min_max_normalize(df_scores[cat])

    # Расчет сырых баллов по категориям
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

    # Нормализация
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


def compute_overall_index(df, position_categories):
    def calculate_overall(row):
        pos = str(row["position"]).strip()

        # Получаем категории для данной позиции
        categories = position_categories.get(pos, position_categories["default"])

        # Оставляем только те категории, которые есть в данных
        available_cats = [cat for cat in categories if cat in row.index]
        if not available_cats:
            return 0

        # Вычисляем среднее по выбранным категориям (игнорируя нули)
        return row[available_cats].replace(0, np.nan).mean()

    df["overall_index"] = df.apply(calculate_overall, axis=1)
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
    # df = pd.read_excel("julydatasets2025/short_2025_july.xlsx") #2025
    df = pd.read_excel("datasets2024/short_data_2024.xlsx")  # 2024 год
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
    pivot_df = apply_position_weights(pivot_df, coeff_df)
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
    df_scores = compute_overall_index(df_scores, position_categories)

    # Разбиваем игроков на вратарей и полевых
    df_goalkeepers = df_scores[
        df_scores["position"].str.lower().isin(["вратарь", "gk"])
    ]
    df_field = df_scores[~df_scores["position"].str.lower().isin(["вратарь", "gk"])]

    st.header("Общий рейтинг топ-10 игроков (без вратарей)")

    # Исключаем вратарей из общего рейтинга
    field_players = df_scores[
        ~df_scores["position"].str.lower().isin(["вратарь", "gk"])
    ]

    # Получаем список всех команд в данных (только полевые игроки)
    all_teams = sorted(field_players["team"].unique())

    # Мультиселект для исключения команд
    excluded_teams = st.multiselect(
        "Исключить команды из общего рейтинга",
        options=all_teams,
        default=[],
        help="Выберите команды, которые не должны отображаться в общем рейтинге",
    )

    # Фильтруем данные, исключая выбранные команды
    if excluded_teams:
        filtered_scores = field_players[~field_players["team"].isin(excluded_teams)]
    else:
        filtered_scores = field_players.copy()

    # Получаем топ-10 из отфильтрованных данных
    overall_top_10 = get_rankings(filtered_scores, "overall_index", top_n=10)

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
        ranking = get_rankings(df_pos, "overall_index", top_n=10)
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
        ranking_gk = get_rankings(df_goalkeepers, "overall_index", top_n=10)
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
