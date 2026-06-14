import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
import plotly.express as px
import plotly.graph_objects as go
from itertools import cycle


# Загрузка данных
@st.cache_data
def load_data():
    df = pd.read_excel("julydatasets2025/short_2025_july.xlsx")
    df.columns = [
        "Турнир",
        "Игрок",
        "Амплуа",
        "Команда",
        "Матч",
        "Данные",
        "КоличествоДействий",
    ]
    return df


# Подготовка данных для моделирования
def prepare_data(df, tournament, position, known_players):
    filtered_df = df[(df["Турнир"] == tournament) & (df["Амплуа"] == position)].copy()

    stats = filtered_df.pivot_table(
        index=["Игрок", "Команда", "Турнир"],
        columns="Данные",
        values="КоличествоДействий",
        aggfunc="mean",
        fill_value=0,
    ).reset_index()

    stats["ТрансфернаяСтоимость"] = stats["Игрок"].apply(
        lambda x: known_players.get(x, np.nan)
    )

    return stats


# Выбор модели в зависимости от количества данных
def select_model(num_samples):
    if num_samples < 5:
        return LinearRegression(), "Линейная регрессия (мало данных)"
    elif num_samples < 15:
        return (
            RandomForestRegressor(n_estimators=50, random_state=42),
            "Случайный лес (50 деревьев)",
        )
    else:
        return (
            GradientBoostingRegressor(n_estimators=100, random_state=42),
            "Градиентный бустинг (100 деревьев)",
        )


# Обучение модели с кросс-валидацией
def train_model(X, y):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    num_samples = len(y)
    model, model_name = select_model(num_samples)

    # Кросс-валидация для оценки R²
    cv_scores = cross_val_score(
        model, X_scaled, y, cv=min(5, num_samples), scoring="r2"
    )
    mean_r2 = np.mean(cv_scores)

    # Если R² nan (возможно при малом количестве данных), используем MAE
    if np.isnan(mean_r2):
        cv_scores_mae = -cross_val_score(
            model,
            X_scaled,
            y,
            cv=min(5, num_samples),
            scoring="neg_mean_absolute_error",
        )
        mean_mae = np.mean(cv_scores_mae)
        mean_r2 = None
    else:
        mean_mae = None

    # Финальное обучение на всех данных
    model.fit(X_scaled, y)

    return model, scaler, mean_mae, mean_r2, model_name


def main():
    st.title("💰 Прогнозирование трансферной стоимости футболистов")
    st.markdown(
        """
    **Как использовать:**
    1. Выберите турнир и позицию
    2. Укажите известные стоимости для игроков (чем больше, тем точнее)
    3. Система автоматически подберет оптимальный алгоритм

    Адаптивный выбор модели:

    * Для 3-4 игроков: линейная регрессия (простая, устойчивая к малым данным)

    * Для 5-14 игроков: случайный лес (баланс точности и устойчивости)

    * Для 15+ игроков: градиентный бустинг (максимальная точность)
    """
    )

    df = load_data()

    # Выбор турнира и позиции
    col1, col2 = st.columns(2)
    with col1:
        tournament = st.selectbox("Выберите турнир", df["Турнир"].unique())
    with col2:
        position = st.selectbox("Выберите позицию", df["Амплуа"].unique())

    players_in_tournament = df[
        (df["Турнир"] == tournament) & (df["Амплуа"] == position)
    ]["Игрок"].unique()

    if len(players_in_tournament) == 0:
        st.warning("Нет данных для выбранных турнира и позиции")
        return

    # Настройки в боковой панели
    st.sidebar.header("Настройки модели")
    num_known_players = st.sidebar.slider(
        "Количество игроков с известной стоимостью",
        min_value=3,
        max_value=min(20, len(players_in_tournament)),
        value=min(5, len(players_in_tournament)),
        step=1,
    )

    # Секция ввода известных стоимостей
    st.sidebar.header("Известные стоимости")
    known_players = {}

    for i in range(num_known_players):
        player = st.sidebar.selectbox(
            f"Игрок {i+1}", players_in_tournament, key=f"player_{i}"
        )
        cost = st.sidebar.number_input(
            f"Стоимость (млн RUB)",
            min_value=0.1,
            max_value=100.0,
            value=1.0,
            key=f"cost_{i}",
        )
        known_players[player] = cost

    # Подготовка данных
    stats = prepare_data(df, tournament, position, known_players)
    known_stats = stats.dropna(subset=["ТрансфернаяСтоимость"])
    predict_stats = stats[stats["ТрансфернаяСтоимость"].isna()]

    if len(known_stats) < 3:
        st.warning("Необходимо указать стоимости минимум для 3 игроков")
        return

    # Обучение модели
    X = known_stats.drop(["Игрок", "Команда", "Турнир", "ТрансфернаяСтоимость"], axis=1)
    y = known_stats["ТрансфернаяСтоимость"]

    try:
        model, scaler, mae, r2, model_name = train_model(X, y)

        st.sidebar.markdown("---")
        st.sidebar.subheader("Используемая модель")
        st.sidebar.info(model_name)

        if r2 is not None:
            st.sidebar.metric("Точность модели (R²)", f"{r2:.2f}")
        if mae is not None:
            st.sidebar.metric("Средняя ошибка (MAE)", f"{mae:.2f} млн RUB")

    except Exception as e:
        st.error(f"Ошибка обучения модели: {str(e)}")
        return

    # Прогнозирование
    if not predict_stats.empty:
        X_predict = predict_stats.drop(
            ["Игрок", "Команда", "Турнир", "ТрансфернаяСтоимость"], axis=1
        )
        X_predict_scaled = scaler.transform(X_predict)
        predictions = model.predict(X_predict_scaled)

        # Формируем результаты
        results = predict_stats[["Игрок", "Команда"]].copy()
        results["Прогнозируемая стоимость (млн RUB)"] = np.round(predictions, 2)
        results = results.sort_values(
            "Прогнозируемая стоимость (млн RUB)", ascending=False
        )

        # Отображаем результаты
        st.header(f"Прогноз трансферной стоимости ({position}, {tournament})")

        # Информация о модели
        st.info(f"**Используемая модель:** {model_name}")
        if r2 is not None:
            st.info(f"**Точность модели (R²):** {r2:.2f} (чем ближе к 1, тем лучше)")
        if mae is not None:
            st.info(f"**Средняя ошибка (MAE):** ±{mae:.2f} млн RUB")

        # Таблица с результатами
        st.dataframe(
            results,
            column_config={
                "Игрок": "Игрок",
                "Команда": "Команда",
                "Прогнозируемая стоимость (млн RUB)": st.column_config.NumberColumn(
                    "Стоимость (млн RUB)", format="%.2f"
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

        # Визуализация
        st.subheader("Сравнение игроков")

        known_for_plot = known_stats[
            ["Игрок", "Команда", "ТрансфернаяСтоимость"]
        ].copy()
        known_for_plot["Тип"] = "Известная стоимость"
        results_for_plot = results.copy()
        results_for_plot = results_for_plot.rename(
            columns={"Прогнозируемая стоимость (млн RUB)": "ТрансфернаяСтоимость"}
        )
        results_for_plot["Тип"] = "Прогнозируемая стоимость"

        plot_data = pd.concat([known_for_plot, results_for_plot])

        fig = px.bar(
            plot_data,
            x="Игрок",
            y="ТрансфернаяСтоимость",
            color="Тип",
            barmode="group",
            hover_data=["Команда"],
            color_discrete_map={
                "Известная стоимость": "#636EFA",
                "Прогнозируемая стоимость": "#EF553B",
            },
        )

        fig.update_layout(
            yaxis_title="Трансферная стоимость (млн RUB)",
            hovermode="x unified",
            height=600,
        )

        st.plotly_chart(fig, use_container_width=True)

        # Советы по интерпретации
        with st.expander("🔍 Как интерпретировать результаты"):
            st.markdown(
                f"""
            **Качество прогноза зависит от количества данных:**
            - Использовано игроков с известной стоимостью: **{len(known_stats)}**
            - Алгоритм: **{model_name}**

            **Рекомендации:**
            1. Для более точных прогнозов добавьте больше игроков с известной стоимостью
            2. Учитывайте диапазон: прогноз ± {mae:.2f} млн RUB
            3. Сравнивайте только игроков одного турнира и позиции

            **Точность модели:**
            - Чем ближе R² к 1, тем лучше модель объясняет данные
            - При R² < 0 модель работает хуже простого среднего
            - При малом количестве данных используйте MAE как основной критерий
            """
            )


if __name__ == "__main__":
    main()
