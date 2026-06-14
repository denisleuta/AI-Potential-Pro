import pandas as pd
import numpy as np
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
import shap
import joblib
import warnings

warnings.filterwarnings("ignore")

# ----------------------------
# 1. ЗАГРУЗКА И ПОДГОТОВКА ДАННЫХ
# ----------------------------

df = pd.read_excel("new.xlsx")


print("Исходные данные (long format):")
print(df.head(5))
print(f"\nВсего строк: {len(df)}")

# ----------------------------
# 2. ПРЕОБРАЗОВАНИЕ В WIDE FORMAT
# ----------------------------

# Шаг 1: pivot — один матч = одна строка
df_wide = df.pivot_table(
    index=[
        "Турнир",
        "ИгрокФИО",
        "Амплуа",
        "Команда",
        "Матч",
        "ИндексНаМатч_90",
        "ИгровоеВремя",
    ],
    columns="Данные",
    values="КоличествоДействий",
    fill_value=0,
    aggfunc="sum",  # на случай дублей
).reset_index()

print("\nПосле pivot (wide format):")
print(df_wide.shape)
print(df_wide.columns.tolist()[:10], "...")

# ----------------------------
# 3. FEATURE ENGINEERING
# ----------------------------

# Извлекаем дату из 'Матч'
def extract_date(match_str):
    try:
        return pd.to_datetime(match_str.split("(")[-1].rstrip(")"), format="%d.%m.%Y")
    except:
        return pd.NaT


df_wide["Дата"] = df_wide["Матч"].apply(extract_date)
df_wide = df_wide.sort_values(["ИгрокФИО", "Дата"]).reset_index(drop=True)

# Удаляем строки без даты
df_wide = df_wide.dropna(subset=["Дата"])

# --- Нормализация действий на 90 минут ---
action_cols = [
    col
    for col in df_wide.columns
    if col
    not in [
        "Турнир",
        "ИгрокФИО",
        "Амплуа",
        "Команда",
        "Матч",
        "ИндексНаМатч_90",
        "ИгровоеВремя",
        "Дата",
    ]
]

for col in action_cols:
    df_wide[f"{col}_90"] = df_wide[col] * 90.0 / df_wide["ИгровоеВремя"]

# --- Скользящие средние (за последние 3 матча игрока) ---
df_wide = df_wide.sort_values(["ИгрокФИО", "Дата"])

# Выбираем все действия для прогноза
all_actions = df["Данные"].dropna().unique()
top_actions = sorted(all_actions)

# Создадим список колонок для прогноза (нормализованные + индекс)
target_actions_90 = [f"{act}_90" for act in top_actions]
y_cols = ["ИндексНаМатч_90"] + target_actions_90

# Добавляем скользящие средние
for col in y_cols:
    df_wide[f"{col}_last3_mean"] = df_wide.groupby("ИгрокФИО")[col].transform(
        lambda x: x.shift(1).rolling(window=3, min_periods=1).mean()
    )
    df_wide[f"{col}_last1"] = df_wide.groupby("ИгрокФИО")[col].shift(1)

# Заполняем NaN (первые матчи игроков)
df_wide = df_wide.fillna(0)

# --- Категориальные признаки ---
le_tour = LabelEncoder()
le_pos = LabelEncoder()
le_team = LabelEncoder()

df_wide["Турнир_enc"] = le_tour.fit_transform(df_wide["Турнир"])
df_wide["Амплуа_enc"] = le_pos.fit_transform(df_wide["Амплуа"])
df_wide["Команда_enc"] = le_team.fit_transform(df_wide["Команда"])

# --- Временные фичи ---
df_wide["День_недели"] = df_wide["Дата"].dt.dayofweek
df_wide["Месяц"] = df_wide["Дата"].dt.month

# --- Дома/Выезд (простая эвристика) ---
def is_home(match_str, team):
    # "Урал-М 1 : 0 Локомотив Москва-М" — если команда после ":", то выезд
    parts = match_str.split(" : ")
    if len(parts) < 2:
        return 0.5  # unknown
    left_team = parts[0].split()[-1]  # "Урал-М"
    right_team = parts[1].split()[0]  # "Локомотив"
    return 1 if team in right_team or team in parts[0] else 0


df_wide["Дома"] = df_wide.apply(
    lambda row: is_home(row["Матч"], row["Команда"]), axis=1
)

# --- Признаки усталости ---
df_wide["Дней_с_прошлого"] = (
    df_wide.groupby("ИгрокФИО")["Дата"].diff().dt.days.fillna(7).clip(0, 14)
)

# ----------------------------
# 4. ФОРМИРОВАНИЕ X И Y
# ----------------------------

# Фичи: всё, кроме мета-полей и целевых
meta_cols = [
    "Турнир",
    "ИгрокФИО",
    "Амплуа",
    "Команда",
    "Матч",
    "ИндексНаМатч_90",
    "Дата",
]
feature_cols = [col for col in df_wide.columns if col not in meta_cols + y_cols]

X = df_wide[feature_cols].copy()
y = df_wide[y_cols].copy()

print(f"\nФичи: {len(feature_cols)}")
print(f"Целевые переменные: {len(y_cols)} → {y_cols}")

# ----------------------------
# 5. РАЗБИЕНИЕ (по игрокам + времени)
# ----------------------------

# GroupKFold по игрокам
groups = df_wide["ИгрокФИО"]
gkf = GroupKFold(n_splits=3)  # 3 фолда — мало данных, иначе 5

# Сохраним результаты
results = []
models = []

# ----------------------------
# 6. ОБУЧЕНИЕ И ВАЛИДАЦИЯ
# ----------------------------

for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups)):
    print(f"\n=== FOLD {fold + 1} ===")

    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
    players_val = df_wide.iloc[val_idx]["ИгрокФИО"].unique()

    print(
        f"Train: {len(X_train)} матчей, {len(df_wide.iloc[train_idx]['ИгрокФИО'].unique())} игроков"
    )
    print(f"Val: {len(X_val)} матчей, {len(players_val)} игроков → {players_val}")

    # Модель: MultiOutput XGBoost
    base_model = XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42,
        tree_method="hist",  # быстрее
        enable_categorical=False,  # мы уже закодировали
    )

    model = MultiOutputRegressor(estimator=base_model, n_jobs=-1)

    print("Обучение...")
    model.fit(X_train, y_train)

    # Прогноз
    y_pred = model.predict(X_val)
    y_pred = pd.DataFrame(y_pred, columns=y_cols, index=y_val.index)

    # Метрики
    metrics = {}
    for i, col in enumerate(y_cols):
        mae = mean_absolute_error(y_val[col], y_pred[col])
        rmse = np.sqrt(mean_squared_error(y_val[col], y_pred[col]))
        r2 = r2_score(y_val[col], y_pred[col])
        metrics[col] = {"MAE": mae, "RMSE": rmse, "R2": r2}
        print(f"{col:30} → MAE: {mae:.3f}, RMSE: {rmse:.3f}, R2: {r2:.3f}")

    results.append(metrics)
    models.append(model)

# Средние метрики
print("\n=== СРЕДНИЕ МЕТРИКИ ПО ФОЛДАМ ===")
avg_metrics = {}
for col in y_cols:
    maes = [res[col]["MAE"] for res in results]
    rmses = [res[col]["RMSE"] for res in results]
    r2s = [res[col]["R2"] for res in results]
    avg_metrics[col] = {
        "MAE": np.mean(maes),
        "RMSE": np.mean(rmses),
        "R2": np.mean(r2s),
    }
    print(
        f"{col:30} → MAE: {np.mean(maes):.3f}, RMSE: {np.mean(rmses):.3f}, R2: {np.mean(r2s):.3f}"
    )

# ----------------------------
# 7. ИНТЕРПРЕТАЦИЯ (SHAP) — на лучшей модели
# ----------------------------

print("\n=== SHAP — ВАЖНОСТЬ ПРИЗНАКОВ (для ИНДЕКС) ===")
best_model = models[0]  # можно выбрать по R2

# Берём базовую модель для первого выхода (ИндексНаМатч_90)
explainer = shap.TreeExplainer(best_model.estimators_[0])
shap_values = explainer.shap_values(X_train)

# Важность признаков
shap_df = pd.DataFrame(
    {"feature": feature_cols, "importance": np.abs(shap_values).mean(axis=0)}
).sort_values("importance", ascending=False)

print(shap_df.head(10))

# (Опционально) сохранить график:
shap.summary_plot(shap_values, X_train, feature_names=feature_cols, show=False)
import matplotlib.pyplot as plt

plt.savefig("shap_summary.png", bbox_inches="tight")

# ----------------------------
# 8. СОХРАНЕНИЕ МОДЕЛИ
# ----------------------------

# Сохраняем лучшую модель и энкодеры
joblib.dump(best_model, "xgb_multioutput_player_forecast.pkl")
joblib.dump(
    {
        "label_encoders": {"tour": le_tour, "pos": le_pos, "team": le_team},
        "feature_cols": feature_cols,
        "y_cols": y_cols,
        "top_actions": top_actions,
    },
    "model_metadata.pkl",
)

print("\n✅ Модель и метаданные сохранены.")

# ----------------------------
# 9. ПРИМЕР ПРОГНОЗА НОВОГО МАТЧА
# ----------------------------

print("\n=== ПРИМЕР ПРОГНОЗА ===")

# Возьмём последний матч Морозова как "новый"
example_row = (
    df_wide[df_wide["ИгрокФИО"] == "Шилов Вадим Александрович"].iloc[-1:].copy()
)

# Подготовим X для прогноза
X_example = example_row[feature_cols]

# Прогноз
pred = best_model.predict(X_example)[0]
forecast = dict(zip(y_cols, pred))

print("Прогноз на следующий матч для игрока:")
print(
    f"Игрок: {example_row['ИгрокФИО'].values[0]} | Команда: {example_row['Команда'].values[0]}"
)
print(f"Амплуа: {example_row['Амплуа'].values[0]}")
print("-" * 40)
for k, v in forecast.items():
    if k == "ИндексНаМатч_90":
        print(f"🎯 {k:25}: {v:.2f}")
    elif "_90" in k:
        act_name = k.replace("_90", "")
        print(f"⚽ {act_name:25}: {v:.2f} (на 90 мин)")

df_wide.to_pickle("df_wide_for_inference.pkl")
print("✅ df_wide сохранён для инференса.")
