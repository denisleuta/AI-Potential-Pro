import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


def create_radar_chart(
    player_values, position_values, team_values, metrics, player_name, title_suffix
):
    fig = go.Figure()

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


@st.cache_data
def load_and_preprocess():
    df = pd.read_excel("julydatasets2025/full_data.xlsx")

    # Удаляем лишние пробелы в названиях столбцов
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

    # Преобразуем actions в числовой тип на случай, если там строки
    df["actions"] = pd.to_numeric(df["actions"], errors="coerce").fillna(0)

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
    "Атакующие позиции": [
        "Гол",
        "Участие в голевой атаке",
        "Удар в створ",
        "Передача ключевая",
        "Передача голевая",
        "Обводка до зоны завершения удачная",
        "Обводка в зоне завершения удачная",
        "Навес точный",
    ],
    "Обороняющие позиции": [
        "Блокировка навеса",
        "Передача в борьбу +",
        "Отбор удачный",
        "Единоборство вверху в обороне удачное",
        "Блокировка удара",
        "Блокировка передачи",
        "Навес точный",
        "Передача ключевая",
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


def main():
    try:
        df = load_and_preprocess()

        # Преобразуем все числовые столбцы к float (кроме категориальных)
        numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
        df[numeric_cols] = df[numeric_cols].astype("float64")

        st.title("⚽ Расширенный анализ показателей футболистов")

        # Выбор команды
        teams = sorted(df["team"].unique())
        selected_team = st.selectbox("Выберите команду", teams)
        df_team = df[df["team"] == selected_team]

        # Выбор игрока
        players = sorted(df_team["player"].unique())
        selected_player = st.selectbox("Выберите игрока", players)
        df_player = df_team[df_team["player"] == selected_player]

        # Выбор позиции
        positions = sorted(df_player["position"].unique())
        selected_position = st.selectbox("Выберите позицию", positions)
        df_position = df_player[df_player["position"] == selected_position]

        # Режим анализа
        analysis_mode = st.radio(
            "Режим анализа", ["Отдельный матч", "Все матчи"], horizontal=True
        )

        if analysis_mode == "Отдельный матч":
            matches = sorted(df_position["match"].unique())
            if len(matches) > 1:
                selected_match = st.selectbox("Выберите матч", matches)
            else:
                selected_match = matches[0]

            player_data = df_position[df_position["match"] == selected_match].iloc[0]
            position_data = df_team[
                (df_team["position"] == selected_position)
                & (df_team["match"] == selected_match)
            ]
            team_data = df_team[df_team["match"] == selected_match]
            title_suffix = f"Показатели за матч: {selected_match}"
        else:
            # Для средних значений сначала убедимся, что работаем только с числовыми столбцами
            numeric_cols = df_position.select_dtypes(include=["float64"]).columns
            player_data = df_position[numeric_cols].mean().to_dict()

            # Добавляем категориальные данные
            player_data.update(
                {
                    "player": selected_player,
                    "position": selected_position,
                    "team": selected_team,
                }
            )

            position_data = df_team[df_team["position"] == selected_position]
            team_data = df_team.copy()
            title_suffix = "Средние показатели за все матчи"

        # Получаем список доступных метрик (только числовые)
        available_metrics = df.select_dtypes(include=["float64"]).columns.tolist()

        # Создаем вкладки
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "Атака",
                "Защита",
                "Пас",
                "Атакующие позиции",
                "Обороняющие позиции",
                "Произвольные показатели",
            ]
        )

        def create_tab(tab, category_name, metrics_list):
            with tab:
                metrics = [m for m in metrics_list if m in available_metrics]
                if not metrics:
                    st.warning(
                        f"Нет данных для показателей категории '{category_name}'"
                    )
                    return

                player_values = [player_data.get(m, 0) for m in metrics]

                pos_values = [safe_mean(position_data, m) for m in metrics]
                team_values = [safe_mean(team_data, m) for m in metrics]

                fig = create_radar_chart(
                    player_values,
                    pos_values,
                    team_values,
                    metrics,
                    selected_player,
                    f"{category_name}<br>{title_suffix}",
                )
                st.plotly_chart(fig, use_container_width=True)

        create_tab(tab1, "Атакующие показатели", categories_def["Атака"])
        create_tab(tab2, "Защитные показатели", categories_def["Защита"])
        create_tab(tab3, "Показатели паса", categories_def["Пас"])
        create_tab(
            tab4,
            "Радар для игроков атакующего плана",
            categories_def["Атакующие позиции"],
        )
        create_tab(
            tab5,
            "Радар для игроков оборонительного плана",
            categories_def["Обороняющие позиции"],
        )

        with tab6:
            selected_metrics = st.multiselect(
                "Выберите показатели для анализа",
                available_metrics,
                default=available_metrics[:5]
                if len(available_metrics) > 5
                else available_metrics,
            )
            if selected_metrics:
                player_values = [player_data.get(m, 0) for m in selected_metrics]
                pos_values = [safe_mean(position_data, m) for m in selected_metrics]
                team_values = [safe_mean(team_data, m) for m in selected_metrics]

                fig = create_radar_chart(
                    player_values,
                    pos_values,
                    team_values,
                    selected_metrics,
                    selected_player,
                    f"Произвольные показатели<br>{title_suffix}",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы один показатель.")

    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        st.info("Проверьте данные и настройки приложения")


if __name__ == "__main__":
    main()
