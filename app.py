import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from io import BytesIO

# Заголовок приложения
st.set_page_config(page_title="Анализ неудовлетворённого спроса", layout="wide")
st.title("📊 Анализ неудовлетворённого спроса")

# Загрузка файла
uploaded_file = st.file_uploader("Загрузите Excel-файл с данными", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Читаем Excel
        df_raw = pd.read_excel(uploaded_file, parse_dates=["Дата"])
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
        st.stop()

    # Проверка наличия обязательных колонок
    required_cols = ["Дата", "Продано штук", "Остаток на конец периода, шт", "Стоимость 1 шт в рублях"]
    missing = [col for col in required_cols if col not in df_raw.columns]
    if missing:
        st.error(f"В файле отсутствуют обязательные колонки: {', '.join(missing)}")
        st.stop()

    # Приводим данные к нужному формату
    df = df_raw.copy()
    df["Продано штук"] = df["Продано штук"].fillna(0).astype(int)
    df["Остаток на конец периода, шт"] = df["Остаток на конец периода, шт"].astype(int)
    df["Стоимость 1 шт в рублях"] = df["Стоимость 1 шт в рублях"].astype(float)
    df = df.sort_values("Дата").reset_index(drop=True)

    # Проверка, что данные не пустые
    if df.empty:
        st.error("Таблица пуста")
        st.stop()

    # ---- Расчёт остатка на начало и поступлений ----
    df["Остаток_нач"] = 0
    df["Поступления"] = 0

    # Первая строка: начальный остаток = остаток на конец (если нет предыдущего дня)
    df.loc[0, "Остаток_нач"] = df.loc[0, "Остаток на конец периода, шт"]

    for i in range(1, len(df)):
        prev_end = df.loc[i-1, "Остаток на конец периода, шт"]
        df.loc[i, "Остаток_нач"] = prev_end

        # Поступления = остаток_кон - остаток_нач + продажи
        post = df.loc[i, "Остаток на конец периода, шт"] - df.loc[i, "Остаток_нач"] + df.loc[i, "Продано штук"]
        if post < 0:
            post = 0
            st.warning(f"В строке {i+1} (дата {df.loc[i, 'Дата'].strftime('%d.%m.%Y')}) "
                       f"получилось отрицательное поступление, установлено 0.")
        df.loc[i, "Поступления"] = post

    # ---- Оценка спроса ----
    # Дни без дефицита: остаток на конец > 0
    days_without_deficit = df[df["Остаток на конец периода, шт"] > 0]

    if days_without_deficit.empty:
        st.error("Нет ни одного дня без дефицита, невозможно оценить спрос.")
        st.stop()

    # Выбор метода оценки спроса
    st.sidebar.header("Параметры расчёта")
    method = st.sidebar.selectbox(
        "Метод оценки спроса",
        ["Среднее арифметическое", "Медиана", "Скользящее среднее (по всем дням)"]
    )

    if method == "Скользящее среднее (по всем дням)":
        window = st.sidebar.slider("Окно скользящего среднего (дней)", min_value=2, max_value=30, value=7)
        # Вычисляем скользящее среднее по фактическим продажам (включая дни с дефицитом)
        df["Спрос_оценка"] = df["Продано штук"].rolling(window=window, min_periods=1).mean()
        # Для первых дней, где нет достаточного окна, берём среднее по всем дням без дефицита
        avg_no_deficit = days_without_deficit["Продано штук"].mean()
        df["Спрос_оценка"] = df["Спрос_оценка"].fillna(avg_no_deficit)
    else:
        if method == "Среднее арифметическое":
            demand_est = days_without_deficit["Продано штук"].mean()
        else:  # Медиана
            demand_est = days_without_deficit["Продано штук"].median()
        df["Спрос_оценка"] = demand_est

    # ---- Расчёт дефицита и упущенной выгоды ----
    df["Дефицит_шт"] = df.apply(
        lambda r: max(0, r["Спрос_оценка"] - r["Остаток_нач"]),
        axis=1
    )
    df["Упущенная_выгода"] = df["Дефицит_шт"] * df["Стоимость 1 шт в рублях"]

    # ---- Итоговые метрики ----
    total_loss = df["Упущенная_выгода"].sum()
    total_deficit = df["Дефицит_шт"].sum()
    days_with_deficit = (df["Дефицит_шт"] > 0).sum()
    avg_deficit_per_day = total_deficit / len(df) if len(df) > 0 else 0

    # ---- Интерфейс ----
    st.subheader("📈 Итоговые показатели за период")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Общая упущенная выгода", f"{total_loss:,.2f} руб.")
    col2.metric("Общий дефицит (шт)", f"{total_deficit:,.0f}")
    col3.metric("Дней с дефицитом", f"{days_with_deficit}")
    col4.metric("Средний дефицит в день (шт)", f"{avg_deficit_per_day:.1f}")

    # ---- Графики ----
    st.subheader("📉 Графики")

    # 1. Остаток, продажи и оценка спроса
    fig1 = px.line(
        df,
        x="Дата",
        y=["Остаток_нач", "Продано штук", "Спрос_оценка"],
        title="Остаток на начало дня, фактические продажи и оценка спроса",
        labels={"value": "Количество (шт)", "variable": "Показатель"},
        color_discrete_map={
            "Остаток_нач": "blue",
            "Продано штук": "green",
            "Спрос_оценка": "red"
        }
    )
    st.plotly_chart(fig1, use_container_width=True)

    # 2. Дефицит по дням
    fig2 = px.bar(
        df,
        x="Дата",
        y="Дефицит_шт",
        title="Дефицит по дням (шт)",
        labels={"Дефицит_шт": "Дефицит (шт)"},
        color_discrete_sequence=["orange"]
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 3. Упущенная выгода по дням
    fig3 = px.bar(
        df,
        x="Дата",
        y="Упущенная_выгода",
        title="Упущенная выгода по дням (руб.)",
        labels={"Упущенная_выгода": "Упущенная выгода (руб.)"},
        color_discrete_sequence=["red"]
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ---- Таблица с расчётами ----
    st.subheader("📋 Детальная таблица")
    display_cols = [
        "Дата", "Остаток_нач", "Поступления", "Продано штук",
        "Остаток на конец периода, шт", "Спрос_оценка", "Дефицит_шт", "Упущенная_выгода"
    ]
    # Форматируем дату для красоты
    df_display = df[display_cols].copy()
    df_display["Дата"] = df_display["Дата"].dt.strftime("%d.%m.%Y")
    st.dataframe(df_display, use_container_width=True)

    # ---- Кнопка скачать результат ----
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Результат", index=False)
        return output.getvalue()

    excel_data = to_excel(df_display)
    st.download_button(
        label="📥 Скачать результат (Excel)",
        data=excel_data,
        file_name="результат_анализа.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---- Дополнительная информация ----
    st.sidebar.header("О программе")
    st.sidebar.info(
        "Приложение оценивает неудовлетворённый спрос на основе данных о продажах и остатках.\n\n"
        "**Метод оценки:**\n"
        "- Среднее / Медиана – по дням без дефицита (остаток > 0).\n"
        "- Скользящее среднее – по фактическим продажам (может быть неточным).\n\n"
        "Дефицит считается как (оценка спроса – остаток на начало дня), если остаток меньше спроса."
    )

else:
    st.info("👈 Загрузите Excel-файл с данными, чтобы начать анализ.")