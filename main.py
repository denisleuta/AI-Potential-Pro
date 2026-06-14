import pandas as pd
import streamlit as st

# Начало страницы
st.set_page_config(page_title="Радар и статистика", page_icon="📊")

# Импорт функций для страниц
from first_page import show as first_page_show
from rating_for_all_team_2024 import main as rating_for_all_team_2024
from comparison_players import main as comparison_players
from rating_for_all_team_2025 import main as rating_for_all_team_2025
from trend_analyses import main as trend_analyses
from forecast_model.app import main as forecast_indicator
from price_forecast_model import main as forecast_price
from radars_for_all_team_2024 import main as radars_2024
from radars_for_all_team_2025 import main as radars_2025
from index_for_all_team_2025 import main as index_2025
from coef_index import main as index_with_coef
from coef_rating import main as rating_with_coef

# Определение страниц
pages = {
    "Главная страница": first_page_show,
    "Топ 10 среди всех футболистов за 2024 год": rating_for_all_team_2024,
    "Топ 10 среди всех футболистов за 2025 год": rating_for_all_team_2025,
    "Индексы футболистов за 2025 год": index_2025,
    "Топ 10 с использованием коэффициенов среди всех футболистов за 2025 год": rating_with_coef,
    "Индексы с использованием коэффициентов футболистов за 2025 год": index_with_coef,
    "Радары игроков за сезон 23/24": radars_2024,
    "Радары игроков за сезон 24/25": radars_2025,
    "Сравнение радарных графиков двух футболистов": comparison_players,
    "Динамика показателей футболиста по матчам": trend_analyses,
    "Модель предсказывающая значение показателей в следующем матче": forecast_indicator,
    "Модель предсказывающая трансферную стоимость": forecast_price,
    "Радары игроков за сезон 23/24": radars_2024,
    "Радары игроков за сезон 24/25": radars_2025,
}

# Выбор страницы
selected_page = st.sidebar.selectbox("Выберите страницу", list(pages.keys()))

# Запуск выбранной страницы
pages[selected_page]()
