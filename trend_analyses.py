import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


@st.cache_data
def load_data():
    """Загрузка и предварительная обработка данных"""
    try:
        df = pd.read_excel("julydatasets2025/full_data.xlsx")
        df.columns = [
            "Турнир",
            "Игрок",
            "Амплуа",
            "Команда",
            "Матч",
            "Данные",
            "КоличествоДействий",
        ]

        # Преобразуем количество действий в числовой формат
        df["КоличествоДействий"] = pd.to_numeric(
            df["КоличествоДействий"], errors="coerce"
        )

        # Извлекаем дату из названия матча и преобразуем в datetime
        df["Дата"] = df["Матч"].str.extract(r"\((\d{2}\.\d{2}\.\d{4})\)")
        df["Дата"] = pd.to_datetime(df["Дата"], format="%d.%m.%Y", errors="coerce")

        # Удаляем строки с некорректными датами
        df = df.dropna(subset=["Дата"])

        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {str(e)}")
        return None


def prepare_player_data(df, player_name, metrics):
    """Подготовка данных для выбранного игрока и метрик"""
    try:
        player_df = df[df["Игрок"] == player_name].copy()

        if player_df.empty:
            return None, None

        # Группируем по матчам и датам
        pivot_df = player_df.pivot_table(
            index=["Матч", "Дата"],
            columns="Данные",
            values="КоличествоДействий",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()

        # Оставляем только выбранные метрики
        available_metrics = [m for m in metrics if m in pivot_df.columns]
        pivot_df = pivot_df[["Матч", "Дата"] + available_metrics]

        # Сортируем по дате (убедимся, что даты в правильном формате)
        pivot_df.sort_values("Дата", inplace=True)

        return pivot_df, available_metrics
    except Exception as e:
        st.error(f"Ошибка подготовки данных: {str(e)}")
        return None, None


def plot_metrics_trend(df, metrics, player_name):
    """Построение графиков динамики показателей"""
    try:
        fig = go.Figure()
        colors = px.colors.qualitative.Plotly

        for i, metric in enumerate(metrics):
            # Убедимся, что данные числовые
            if pd.api.types.is_numeric_dtype(df[metric]):
                fig.add_trace(
                    go.Scatter(
                        x=df["Дата"],
                        y=df[metric],
                        name=metric,
                        mode="lines+markers",
                        line=dict(color=colors[i % len(colors)], width=2),
                        marker=dict(size=8),
                        hovertemplate=f"<b>{metric}</b><br>Дата: %{{x|%d.%m.%Y}}<br>Значение: %{{y}}<extra></extra>",
                    )
                )

        fig.update_layout(
            title=f"Динамика показателей игрока {player_name}",
            xaxis_title="Дата матча",
            yaxis_title="Количество действий",
            hovermode="x unified",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            height=600,
            margin=dict(l=50, r=50, t=80, b=50),
        )

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Ошибка построения графиков: {str(e)}")


def main():
    st.title("📈 Динамика показателей футболиста по матчам")

    # Загрузка данных
    df = load_data()
    if df is None:
        st.warning("Не удалось загрузить данные. Проверьте путь к файлу.")
        return

    # Выбор игрока
    players = sorted(df["Игрок"].unique())
    selected_player = st.selectbox("Выберите игрока", players)

    # Получаем информацию об игроке
    player_info = (
        df[df["Игрок"] == selected_player].iloc[0]
        if not df[df["Игрок"] == selected_player].empty
        else None
    )
    if player_info is not None:
        st.markdown(
            f"**Амплуа:** {player_info['Амплуа']} | **Команда:** {player_info['Команда']}"
        )

    # Выбор показателей для анализа
    all_metrics = sorted(df["Данные"].unique())
    selected_metrics = st.multiselect(
        "Выберите показатели для анализа",
        all_metrics,
        default=all_metrics[:3] if len(all_metrics) > 3 else all_metrics,
    )

    if not selected_metrics:
        st.warning("Пожалуйста, выберите хотя бы один показатель")
        return

    # Подготовка данных
    player_data, available_metrics = prepare_player_data(
        df, selected_player, selected_metrics
    )

    if player_data is None or player_data.empty:
        st.warning("Нет данных для выбранного игрока")
        return

    # Визуализация
    plot_metrics_trend(player_data, available_metrics, selected_player)

    # Детализированные данные
    with st.expander("Показать детальные данные по матчам"):
        st.dataframe(
            player_data.assign(Дата=player_data["Дата"].dt.strftime("%d.%m.%Y")),
            hide_index=True,
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
