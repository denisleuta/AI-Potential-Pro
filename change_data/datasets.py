import pandas as pd
import os

# Загрузка данных (если еще не загружены)
df = pd.read_excel("julydatasets2025/full_data.xlsx")

# Основное разделение
position_dfs = {
    position: group.reset_index(drop=True) for position, group in df.groupby("Амплуа")
}

# Сохранение с проверкой директории
output_dir = "."  # Текущая директория
for position, data in position_dfs.items():
    # Создаем безопасное имя файла
    filename = f"{position.replace('/', '_')}_players.xlsx"  # Заменяем слэши

    # Полный путь для сохранения
    filepath = os.path.join(output_dir, filename)

    data.to_csv(filepath, index=False)

    print(f"Сохранено: {filepath} ({len(data)} записей)")
