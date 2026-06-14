import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler


@st.cache_data
def load_and_preprocess():
    skater_stats = pd.read_csv("game_skater_stats.csv")

    # Группировка и агрегация по игроку
    grouped = (
        skater_stats.groupby(["player_id"], as_index=False)
        .agg(
            {
                "goals": "sum",
                "assists": "sum",
                "shots": "sum",
                "hits": "sum",
                "blocked": "sum",
                "powerPlayGoals": "sum",
                "shortHandedGoals": "sum",
                "plusMinus": "sum",
                "powerPlayTimeOnIce": "sum",
                "game_id": "nunique",
            }
        )
        .rename(columns={"game_id": "games_played"})
    )

    # Фильтрация: только игроки с ≥ 20 матчами
    grouped = grouped[grouped["games_played"] >= 20]

    # Новые метрики
    grouped["shot_accuracy"] = (
        grouped["goals"] / grouped["shots"].replace(0, np.nan) * 100
    )
    grouped["pp_time_per_game"] = (
        grouped["powerPlayTimeOnIce"] / grouped["games_played"]
    )
    grouped.fillna(0, inplace=True)

    return grouped


def create_hockey_radar(player_values, avg_values, labels, title):
    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=player_values,
            theta=labels,
            fill="toself",
            name="Овечкин",
            line=dict(color="rgb(200, 50, 50)", width=2),
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=avg_values,
            theta=labels,
            fill="toself",
            name="Среднее по лиге",
            line=dict(color="rgb(50, 150, 50)", width=2),
        )
    )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title=title,
        height=500,
    )

    return fig


def main():
    try:
        df = load_and_preprocess()

        st.title("🏒 Сравнительный анализ Александра Овечкина")

        # Добавим фото
        st.image(
            "https://img.gazeta.ru/files3/807/16141807/2023-01-20T031423Z_2062327915_MT1USATODAY19821818_RTRMADP_3_NHL-WASHINGTON-CAPITALS-AT-ARIZONA-COYOTES-pic4_zoom-1500x1500-80304.jpg",
            caption="Александр Овечкин",
            width=350,
        )

        ovechkin_id = 8471214
        player_df = df[df["player_id"] == ovechkin_id]

        if player_df.empty:
            st.error("Данные по Овечкину не найдены.")
            return

        # Категории и метрики
        categories = {
            "📊 Основные показатели": ["goals", "assists", "shots", "hits"],
            "⚡ Показатели при игре в большинстве": [
                "powerPlayGoals",
                "shortHandedGoals",
                "pp_time_per_game",
            ],
            "🎯 Эффективность": ["shot_accuracy", "plusMinus", "blocked"],
        }

        scaler = MinMaxScaler()

        for title, metrics in categories.items():
            labels = [m.replace("_", " ").title() for m in metrics]

            normalized = df.copy()
            normalized[metrics] = scaler.fit_transform(df[metrics])

            player_values = (
                normalized[normalized["player_id"] == ovechkin_id][metrics]
                .values.flatten()
                .tolist()
            )
            avg_values = normalized[metrics].mean().values.tolist()

            fig = create_hockey_radar(player_values, avg_values, labels, title)
            st.plotly_chart(fig, use_container_width=True)

        # Блок с карьерной статистикой
        st.subheader("Ключевые показатели за карьеру")
        cols = st.columns(5)
        cols[0].metric("Игры", 1487)
        cols[1].metric("Голы", 895)
        cols[2].metric("Передачи", 724)
        cols[3].metric("Очки", 1619)
        cols[4].metric("Коэффициент полезности", "+62")

    except Exception as e:
        st.error(f"Ошибка: {str(e)}")


if __name__ == "__main__":
    main()
