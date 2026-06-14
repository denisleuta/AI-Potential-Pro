import streamlit as st
import pandas as pd
import joblib
import numpy as np
from datetime import datetime, timedelta
import os


def main():
    st.title("🔮 Прогноз показателей на следующий матч")

    # ----------------------------
    # ЗАГРУЗКА АРТЕФАКТОВ
    # ----------------------------

    @st.cache_resource
    def load_artifacts():
        # Получаем путь к папке, где находится app.py
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Формируем полные пути к файлам
        model_path = os.path.join(current_dir, "xgb_multioutput_player_forecast.pkl")
        meta_path = os.path.join(current_dir, "model_metadata.pkl")
        df_path = os.path.join(current_dir, "df_wide_for_inference.pkl")

        model = joblib.load(model_path)
        meta = joblib.load(meta_path)
        df_wide = pd.read_pickle(df_path)
        # Убедимся, что 'Дата' — datetime
        df_wide["Дата"] = pd.to_datetime(df_wide["Дата"])
        return model, meta, df_wide

    try:
        model, meta, df_wide = load_artifacts()
        feature_cols = meta["feature_cols"]
        y_cols = meta["y_cols"]
        le_tour = meta["label_encoders"]["tour"]
        le_pos = meta["label_encoders"]["pos"]
        le_team = meta["label_encoders"]["team"]
    except Exception as e:
        st.error(f"❌ Ошибка загрузки артефактов: {e}")
        st.stop()

    # Уникальные игроки
    players = sorted(df_wide["ИгрокФИО"].unique())

    # ----------------------------
    # ИНТЕРФЕЙС
    # ----------------------------

    st.markdown(
        """
    Выберите игрока и укажите параметры **следующего матча** — приложение предскажет его показатели на 90 минут.
    """
    )

    selected_players = st.multiselect("👤 Выберите игроков", players)

    # Общие параметры будущего матча (можно сделать индивидуальными, но пока общие)
    st.subheader("🗓️ Параметры следующего матча")
    col1, col2 = st.columns(2)
    with col1:
        next_match_date = st.date_input(
            "Дата матча", value=datetime.today() + timedelta(days=3)
        )
    with col2:
        home_away = st.selectbox("Место проведения", ["Дома", "На выезде"])

    if st.button("🎯 Сделать прогноз и сохранить отчёт"):
        if not selected_players:
            st.warning("Пожалуйста, выберите хотя бы одного игрока.")
        else:
            report_rows = []

            for player in selected_players:
                player_data = df_wide[df_wide["ИгрокФИО"] == player].copy()
                if player_data.empty:
                    st.warning(f"Игрок {player} не найден в данных.")
                    continue

                # Сортируем по дате и берём последний матч
                player_data = player_data.sort_values("Дата")
                last_match_row = player_data.iloc[-1]
                last_match_date = last_match_row["Дата"]

                # Рассчитываем "дней с прошлого матча"
                days_since_last = (next_match_date - last_match_date.date()).days
                if days_since_last < 0:
                    days_since_last = 0  # на всякий случай

                # Определяем "дома"
                home_flag = 1 if home_away == "Дома" else 0

                # Извлекаем базовые признаки из последнего матча (last1, last3_mean и т.д.)
                base_features = last_match_row[feature_cols].copy()

                # ОБНОВЛЯЕМ контекстные признаки на будущий матч
                base_features["Дома"] = home_flag
                base_features["Дней_с_прошлого"] = days_since_last
                base_features["День_недели"] = next_match_date.weekday()
                base_features["Месяц"] = next_match_date.month

                # Кодируем категориальные (должны быть уже в base_features, но на всякий)
                try:
                    base_features["Турнир_enc"] = le_tour.transform(
                        [last_match_row["Турнир"]]
                    )[0]
                except:
                    base_features["Турнир_enc"] = 0
                try:
                    base_features["Амплуа_enc"] = le_pos.transform(
                        [last_match_row["Амплуа"]]
                    )[0]
                except:
                    base_features["Амплуа_enc"] = 0
                try:
                    base_features["Команда_enc"] = le_team.transform(
                        [last_match_row["Команда"]]
                    )[0]
                except:
                    base_features["Команда_enc"] = 0

                # Формируем X
                X_input = base_features.to_frame().T
                X_input = X_input.apply(pd.to_numeric, errors="coerce").fillna(0.0)
                X_input = X_input.astype(np.float64)

                # Прогноз + обрезка отрицательных
                pred = model.predict(X_input)[0]
                pred = np.clip(pred, 0, None)
                result = dict(zip(y_cols, pred))

                # Собираем отчёт
                row = {
                    "Игрок": player,
                    "Команда": last_match_row["Команда"],
                    "Амплуа": last_match_row["Амплуа"],
                    "Последний матч": last_match_row["Матч"],
                    "Дата последнего матча": last_match_row["Дата"].strftime(
                        "%d.%m.%Y"
                    ),
                    "Дата следующего матча": next_match_date.strftime("%d.%m.%Y"),
                    "Место": home_away,
                    "Дней отдыха": days_since_last,
                }
                for key, val in result.items():
                    if key == "ИндексНаМатч_90":
                        row["Индекс на матч"] = round(val, 2)
                    else:
                        act_name = key.replace("_90", "")
                        row[act_name] = round(val, 2)
                report_rows.append(row)

            if report_rows:
                report_df = pd.DataFrame(report_rows)
                st.success(f"✅ Прогнозы готовы для {len(report_rows)} игроков")
                st.dataframe(report_df)

                # Экспорт в Excel
                from io import BytesIO

                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    report_df.to_excel(writer, index=False, sheet_name="Прогнозы")
                    worksheet = writer.sheets["Прогнозы"]
                    for idx, col in enumerate(report_df.columns):
                        max_len = (
                            max(report_df[col].astype(str).map(len).max(), len(col)) + 2
                        )
                        worksheet.set_column(idx, idx, min(max_len, 50))

                st.download_button(
                    label="📥 Скачать отчёт в Excel",
                    data=output.getvalue(),
                    file_name="прогноз_на_будущий_матч.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.error("Не удалось сформировать отчёт.")


if __name__ == "__main__":
    main()
