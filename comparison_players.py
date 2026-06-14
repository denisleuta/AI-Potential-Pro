import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# Конфигурация доступных сезонов
SEASON_DATA = {
    "2024/2025": "julydatasets2025/full_data.xlsx",
    "2023/2024": "datasets2024/games2024.xlsx",
}


@st.cache_data
def load_data(season):
    """Загрузка данных для выбранного сезона"""
    file_path = SEASON_DATA.get(season)
    if not file_path or not os.path.exists(file_path):
        st.error(f"Файл данных для сезона {season} не найден!")
        return None

    df = pd.read_excel(file_path)

    df.columns = df.columns.str.strip()

    df.columns = [
        "tournament",
        "player",
        "position",
        "team",
        "match",
        "data",
        "actions",
    ]

    # Преобразуем действия в числовой формат
    df["actions"] = pd.to_numeric(df["actions"], errors="coerce")

    # Удалим строки, где actions не удалось преобразовать (NaN)
    df = df.dropna(subset=["actions"])

    # Агрегируем данные: суммируем количество действий по игроку, позиции, команде, матчу и типу действия
    agg_df = df.groupby(
        ["player", "position", "team", "match", "data"], as_index=False
    )["actions"].sum()

    # Преобразуем агрегированные данные в сводную таблицу:
    pivot_df = agg_df.pivot_table(
        index=["player", "position", "team", "match"],
        columns="data",
        values="actions",
        fill_value=0,
    )
    pivot_df = pivot_df.reset_index()

    return pivot_df


def create_radar_chart(
    player_values,
    position_values,
    team_values,
    metrics,
    player_name,
    title_suffix,
    position=None,
):
    fig = go.Figure()

    if position:
        player_name = f"{player_name} ({position})"

    max_val = np.max([player_values, position_values, team_values]) * 1.1
    min_val = np.min([player_values, position_values, team_values]) * 0.9

    colors = {
        "player": "rgba(255, 80, 80, 0.9)",
        "position": "rgba(50, 200, 50, 0.7)",
        "team": "rgba(0, 100, 255, 0.6)",
    }

    fig.add_trace(
        go.Scatterpolar(
            r=team_values + [team_values[0]],
            theta=metrics + [metrics[0]],
            name="Команда",
            fill="toself",
            line=dict(color=colors["team"], width=2),
            hoverinfo="text+name+theta+r",
            hovertemplate="<b>%{theta}</b><br>Значение: %{r:.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=position_values + [position_values[0]],
            theta=metrics + [metrics[0]],
            name="Позиция",
            fill="toself",
            line=dict(color=colors["position"], width=2),
            hoverinfo="text+name+theta+r",
            hovertemplate="<b>%{theta}</b><br>Значение: %{r:.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=player_values + [player_values[0]],
            theta=metrics + [metrics[0]],
            name=player_name,
            fill="toself",
            line=dict(color=colors["player"], width=3),
            hoverinfo="text+name+theta+r",
            hovertemplate="<b>%{theta}</b><br>Значение: %{r:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showticklabels=False,
                range=[min_val, max_val],
                gridcolor="#E0E0E0",
                linecolor="#B0B0B0",
            ),
            angularaxis=dict(
                rotation=90,
                direction="counterclockwise",
                gridcolor="#E0E0E0",
                linecolor="#B0B0B0",
            ),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.15,
            xanchor="center",
            x=0.5,
            font=dict(size=14),
        ),
        height=700,
        margin=dict(l=100, r=100, t=100, b=100),
        paper_bgcolor="rgba(245, 245, 245, 1)",
        plot_bgcolor="rgba(255, 255, 255, 1)",
        annotations=[
            dict(
                text=f"{title_suffix}: {player_name}",
                x=0.5,
                y=1.15,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=18, color="#303030"),
            )
        ],
    )
    return fig


def create_comparison_radar_chart(
    players_values,  # Теперь это список списков значений для каждого игрока
    metrics,
    players_names,  # Список имен игроков
    title_suffix,
    players_positions=None,  # Список позиций
    players_seasons=None,  # Список сезонов
):
    fig = go.Figure()

    # Генерация цветов для каждого игрока
    colors = [
        "rgba(255, 80, 80, 0.9)",  # Красный
        "rgba(80, 80, 255, 0.9)",  # Синий
        "rgba(80, 255, 80, 0.9)",  # Зеленый
        "rgba(255, 255, 80, 0.9)",  # Желтый
        "rgba(255, 80, 255, 0.9)",  # Фиолетовый
        "rgba(80, 255, 255, 0.9)",  # Голубой
    ]

    # Находим максимальное и минимальное значения для масштабирования графика
    max_val = np.max([np.max(vals) for vals in players_values]) * 1.1
    min_val = np.min([np.min(vals) for vals in players_values]) * 0.9

    # Добавляем данные для каждого игрока
    for i, (values, name) in enumerate(zip(players_values, players_names)):
        # Формируем имя для легенды
        legend_name = name
        if players_positions and i < len(players_positions):
            legend_name += f" ({players_positions[i]})"
        if players_seasons and i < len(players_seasons):
            legend_name += f" [{players_seasons[i]}]"

        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],  # Замыкаем график
                theta=metrics + [metrics[0]],
                name=legend_name,
                fill="toself",
                line=dict(color=colors[i % len(colors)], width=3),
                hoverinfo="text+name+theta+r",
                hovertemplate="<b>%{theta}</b><br>Значение: %{r:.2f}<extra></extra>",
            )
        )

    # Формируем заголовок
    title = f"{title_suffix}: " + " vs ".join(
        [
            f"{name}"
            + (f" ({pos})" if players_positions and i < len(players_positions) else "")
            + (f" [{sea}]" if players_seasons and i < len(players_seasons) else "")
            for i, (name, pos, sea) in enumerate(
                zip(players_names, players_positions or [], players_seasons or [])
            )
        ]
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showticklabels=False,
                range=[min_val, max_val],
                gridcolor="#E0E0E0",
                linecolor="#B0B0B0",
            ),
            angularaxis=dict(
                rotation=90,
                direction="counterclockwise",
                gridcolor="#E0E0E0",
                linecolor="#B0B0B0",
            ),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.15,
            xanchor="center",
            x=0.5,
            font=dict(size=14),
        ),
        height=700,
        margin=dict(l=100, r=100, t=100, b=100),
        paper_bgcolor="rgba(245, 245, 245, 1)",
        plot_bgcolor="rgba(255, 255, 255, 1)",
        annotations=[
            dict(
                text=title,
                x=0.5,
                y=1.15,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=18, color="#303030"),
            )
        ],
    )
    return fig


def generate_comparison_analysis(
    player1_data, player2_data, metrics, player1_name, player2_name
):
    analysis = []

    for i, metric in enumerate(metrics):
        val1 = player1_data.get(metric, 0)
        val2 = player2_data.get(metric, 0)

        if val1 == 0 and val2 == 0:
            continue

        diff = val1 - val2
        abs_diff = abs(diff)

        if diff > 0:
            leader = player1_name
            advantage = f"{abs_diff:.2f} выше"
        elif diff < 0:
            leader = player2_name
            advantage = f"{abs_diff:.2f} выше"
        else:
            leader = "Одинаково"
            advantage = "Нет разницы"

        # Определяем значимость различия
        if abs_diff > 0:
            if (
                abs_diff > max(val1, val2) * 0.5
            ):  # Большая разница (>50% от максимального значения)
                significance = "значительно превосходит"
            elif abs_diff > max(val1, val2) * 0.2:  # Средняя разница (>20%)
                significance = "превосходит"
            else:  # Малая разница
                significance = "немного лучше"
        else:
            significance = "одинаковы"

        analysis.append(
            {
                "Показатель": metric,
                player1_name: f"{val1:.2f}",
                player2_name: f"{val2:.2f}",
                "Разница": advantage,
                "Анализ": f"{leader} {significance} по показателю '{metric}'"
                if leader != "Одинаково"
                else f"Оба игрока одинаковы по показателю '{metric}'",
            }
        )

    return pd.DataFrame(analysis)


def get_player_data(df, team, player, position, analysis_mode, match=None):
    df_team = df[df["team"] == team]
    df_player = df_team[df_team["player"] == player]

    if df_player.empty:
        return {}, pd.DataFrame(), pd.DataFrame(), "Нет данных"

    # Если позиция не задана, используем первую доступную
    if not position and not df_player.empty:
        position = df_player.iloc[0]["position"]

    df_position = df_team[df_team["position"] == position]

    if analysis_mode == "Отдельный матч":
        if match is None:
            matches = sorted(df_position["match"].unique())
            if len(matches) > 0:
                match = matches[0]  # Выбираем первый матч
            else:
                return {}, pd.DataFrame(), pd.DataFrame(), "Нет доступных матчей"

        # Фильтруем данные по матчу
        player_data_row = (
            df_player[df_player["match"] == match].iloc[0]
            if not df_player[df_player["match"] == match].empty
            else {}
        )
        position_data = df_position[df_position["match"] == match]
        team_data = df_team[df_team["match"] == match]
        title_suffix = f"Показатели за матч: {match}"
    else:
        numeric_cols = df_player.select_dtypes(include=["float64"]).columns
        player_data = df_player[numeric_cols].mean().to_dict()
        player_data.update(
            {
                "player": player,
                "position": position,
                "team": team,
            }
        )
        position_data = df_position
        team_data = df_team
        title_suffix = "Средние показатели за все матчи"

    return (
        player_data_row if analysis_mode == "Отдельный матч" else player_data,
        position_data,
        team_data,
        title_suffix,
    )


def main():
    try:
        st.title("⚽ Расширенный анализ показателей футболистов")

        analysis_type = st.radio(
            "Тип анализа",
            ["Сравнение нескольких игроков"],
            horizontal=True,
        )

        analysis_mode = st.radio(
            "Режим анализа", ["Отдельный матч", "Все матчи"], horizontal=True
        )

        # Выбор количества игроков для сравнения
        num_players = st.slider("Количество игроков для сравнения", 2, 6, 2)

        # Создаем колонки для каждого игрока
        cols = st.columns(num_players)

        players_data = []
        players_names = []
        players_positions = []
        players_seasons = []
        title_suffixes = []

        for i in range(num_players):
            with cols[i]:
                st.subheader(f"Игрок {i+1}")

                # Выбор сезона
                selected_season = st.selectbox(
                    f"Сезон {i+1}", list(SEASON_DATA.keys()), key=f"season_{i}"
                )
                df = load_data(selected_season)
                if df is None:
                    return

                # Выбор команды
                teams = sorted(df["team"].unique())
                selected_team = st.selectbox(f"Команда {i+1}", teams, key=f"team_{i}")
                df_team = df[df["team"] == selected_team]

                # Выбор игрока
                players = sorted(df_team["player"].unique())
                selected_player = st.selectbox(
                    f"Игрок {i+1}", players, key=f"player_{i}"
                )
                df_player = df_team[df_team["player"] == selected_player]

                # Выбор позиции
                positions = sorted(df_player["position"].unique())
                selected_position = st.selectbox(
                    f"Позиция {i+1}", positions, key=f"position_{i}"
                )

                if analysis_mode == "Отдельный матч":
                    matches = sorted(
                        df_player[df_player["position"] == selected_position][
                            "match"
                        ].unique()
                    )
                    if len(matches) > 1:
                        selected_match = st.selectbox(
                            f"Матч {i+1}", matches, key=f"match_{i}"
                        )
                    else:
                        selected_match = matches[0] if matches else None
                else:
                    selected_match = None

                # Получаем данные игрока
                player_data, _, _, title_suffix = get_player_data(
                    df,
                    selected_team,
                    selected_player,
                    selected_position,
                    analysis_mode,
                    selected_match,
                )

                players_data.append(player_data)
                players_names.append(selected_player)
                players_positions.append(selected_position)
                players_seasons.append(selected_season)
                title_suffixes.append(title_suffix)

        # Получаем список доступных метрик (только числовые)
        available_metrics = list(
            set.intersection(
                *[
                    set(load_data(season).select_dtypes(include=["float64"]).columns)
                    for season in set(players_seasons)
                ]
            )
        )

        # Создаем вкладки для сравнения
        tab_names = ["Атака", "Защита", "Пас", "Ошибки", "Произвольные показатели"]
        tabs = st.tabs(tab_names)

        def create_comparison_tab(tab, category_name, metrics_list):
            with tab:
                metrics = [m for m in metrics_list if m in available_metrics]
                if not metrics:
                    st.warning(
                        f"Нет данных для показателей категории '{category_name}'"
                    )
                    return

                # Собираем значения для всех игроков
                all_players_values = [
                    [player_data.get(m, 0) for m in metrics]
                    for player_data in players_data
                ]

                fig = create_comparison_radar_chart(
                    all_players_values,
                    metrics,
                    players_names,
                    f"{category_name}",
                    players_positions,
                    players_seasons,
                )
                st.plotly_chart(fig, use_container_width=True)

                # Добавляем таблицу сравнения
                st.subheader("Детальный анализ сравнения")
                comparison_dfs = []

                for i in range(len(players_names)):
                    for j in range(i + 1, len(players_names)):
                        df = generate_comparison_analysis(
                            players_data[i],
                            players_data[j],
                            metrics,
                            f"{players_names[i]} ({players_positions[i]}) [{players_seasons[i]}]",
                            f"{players_names[j]} ({players_positions[j]}) [{players_seasons[j]}]",
                        )
                        comparison_dfs.append(df)

                if comparison_dfs:
                    comparison_df = pd.concat(comparison_dfs).drop_duplicates()
                    st.dataframe(
                        comparison_df,
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.warning("Нет данных для сравнения по выбранным показателям")

        # Создаем вкладки
        for tab, tab_name in zip(tabs, tab_names):
            if tab_name == "Произвольные показатели":
                with tab:
                    selected_metrics = st.multiselect(
                        "Выберите показатели для сравнения",
                        available_metrics,
                        default=available_metrics[:5]
                        if len(available_metrics) > 5
                        else available_metrics,
                        key="compare_metrics",
                    )
                    if selected_metrics:
                        all_players_values = [
                            [player_data.get(m, 0) for m in selected_metrics]
                            for player_data in players_data
                        ]

                        fig = create_comparison_radar_chart(
                            all_players_values,
                            selected_metrics,
                            players_names,
                            "Произвольные показатели",
                            players_positions,
                            players_seasons,
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # Добавляем таблицу сравнения
                        st.subheader("Детальный анализ сравнения")
                        comparison_dfs = []

                        for i in range(len(players_names)):
                            for j in range(i + 1, len(players_names)):
                                df = generate_comparison_analysis(
                                    players_data[i],
                                    players_data[j],
                                    selected_metrics,
                                    f"{players_names[i]} ({players_positions[i]}) [{players_seasons[i]}]",
                                    f"{players_names[j]} ({players_positions[j]}) [{players_seasons[j]}]",
                                )
                                comparison_dfs.append(df)

                        if comparison_dfs:
                            comparison_df = pd.concat(comparison_dfs).drop_duplicates()
                            st.dataframe(
                                comparison_df,
                                hide_index=True,
                                use_container_width=True,
                            )
                        else:
                            st.warning(
                                "Нет данных для сравнения по выбранным показателям"
                            )
                    else:
                        st.warning("Пожалуйста, выберите хотя бы один показатель.")
            else:
                create_comparison_tab(tab, tab_name, categories_def[tab_name])

    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        st.info("Проверьте данные и настройки приложения")


categories_def = {
    "Атака": [
        "Удар в створ",
        "Удар мимо",
        "Голевой момент создал",
        "Голевой момент реализовал",
        "Голевой момент не реализовал",
        "Единоборство вверху в атаке удачное",
        "Единоборство вверху в атаке неудачное",
        "Обводка до зоны завершения удачная",
        "Обводка до зоны завершения неудачная",
        "Обводка в зоне завершения удачная",
        "Обводка в зоне завершения неудачная",
        "Эффективность '+' Обводки в зоне завершения",
        "Эффективность '-' Обводки в зоне завершения",
        "Продвижение мяча вперед за счет дриблинга",
        "Эффективность '+' Продвижения мяча вперед за счет дриблинга",
        "Эффективность '-' Продвижения мяча вперед за счет дриблинга",
        "Передача голевая",
    ],
    "Защита": [
        "Фол",
        "Борьба за нейтральный мяч удачная",
        "Борьба за нейтральный мяч неудачная" "Единоборство вверху в обороне удачное",
        "Единоборство вверху в обороне неудачное",
        "Отбор удачный",
        "Блокировка передачи",
        "Перехват передачи",
    ],
    "Пас": [
        "Передача прогрессивная точная",
        "Передача прогрессивная неточная",
        "Передача без развития",
        "Передача ключевая точная",
        "Передача ключевая неточная",
        "Передача в борьбу -",
        "Навес точный",
        "Навес неточный",
        "Передача голевая",
    ],
    "Подбор и борьба за мяч": [
        "Подбор мяча",
        "Эффективность '+' Подбора мяча",
        "Эффективность '-' Подбора мяча",
        "Борьба за нейтральный мяч удачная",
        "Борьба за нейтральный мяч неудачная",
    ],
    "Вратарская игра": [
        "Сейв",
        "Игра ГК на выходе удачная",
        "Игра ГК на выходе неудачная",
        "Игра на выходе при навесах удачная",
        "Игра на выходе при навесах неудачная",
        "Удар от ворот короткий/средний точный",
        "Удар от ворот короткий/средний неточный",
        "Удар от ворот длинный точный",
        "Удар от ворот длинный неточный",
        "Передача рукой короткая/средняя точная",
        "Передача рукой длинная точная",
        "Передача рукой короткая/средняя неточная",
        "Передача рукой длинная неточная",
    ],
    "Ошибки": [
        "Потеря мяча",
        "Грубая ошибка",
        "Грубая голевая ошибка",
        "Желтая карточка",
        "Красная карточка",
        "Фол",
    ],
    "Другое": [
        "Открывание",
        "Стартовый состав",
        "Заменен",
        "Замена",
        "Офсайд",
        "Автогол",
    ],
}


def safe_mean(data, metric):
    """Безопасный расчет среднего значения для метрики"""
    if (
        isinstance(data, pd.DataFrame)
        and metric in data.select_dtypes(include=["float64"]).columns
    ):
        return data[metric].mean()
    return 0


if __name__ == "__main__":
    main()
