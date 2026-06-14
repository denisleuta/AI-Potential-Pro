import pandas as pd

# Предположим, что ваши данные находятся в файле 'player_stats.csv'
# Если разделитель не запятая, укажите его, например, sep=';'
df = pd.read_excel("123.xlsx")

# Если данные уже загружены в DataFrame, например, как в вашем примере, начинаем сюда
# Применяем фильтр по турниру, если указан
tournament_filter = "ЮФЛ-1"
if tournament_filter:
    # Фильтруем данные по выбранному турниру
    filtered_df = df[df["Турнир"] == tournament_filter]
    if filtered_df.empty:
        print(
            f"Внимание: Турнир '{tournament_filter}' не найден в данных. Будет создан отчет по всем турнирам."
        )
        filtered_df = df
else:
    filtered_df = df
    tournament_filter = "Все турниры"

# 1. Группируем по амплуа и по типу показателя, суммируем количество действий
grouped_data = (
    filtered_df.groupby(["Амплуа", "Данные"])["КоличествоДействий"].sum().reset_index()
)

# 2. Сортируем данные внутри каждой группы 'Амплуа' по убыванию количества действий
sorted_data = grouped_data.sort_values(
    ["Амплуа", "КоличествоДействий"], ascending=[True, False]
)

# 3. Создаем ExcelWriter объект для записи в один файл с несколькими листами
with pd.ExcelWriter("top_metrics_by_position.xlsx", engine="openpyxl") as writer:

    # 4. Получаем список всех уникальных амплуа
    positions = sorted_data["Амплуа"].unique()

    # 5. Для каждой позиции создаем отдельный лист в файле
    for position in positions:
        # Фильтруем данные для текущей позиции
        position_data = sorted_data[sorted_data["Амплуа"] == position]

        # Берем топ-10 показателей для этой позиции
        top_10_for_position = position_data.head(120)

        # Записываем датафрейм на отдельный лист, названный по амплуа
        # Обрезаем название листа, если оно слишком длинное (ограничение Excel - 31 символ)
        sheet_name = str(position)[:31]
        top_10_for_position.to_excel(writer, sheet_name=sheet_name, index=False)

        # (Опционально) Можно записать все показатели для позиции, а не только топ-10
        # position_data.to_excel(writer, sheet_name=sheet_name, index=False)

print("Отчет успешно сохранен в файл 'top_metrics_by_position.xlsx'")
