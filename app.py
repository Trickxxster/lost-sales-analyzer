import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Анализ неудовлетворённого спроса", layout="wide")
st.title("📊 Анализ неудовлетворённого спроса")

uploaded_file = st.file_uploader("Загрузите Excel-файл с данными", type=["xlsx"])

def find_header_row(df_raw, keywords, max_rows=5):
    """Ищет строку с заголовками среди первых max_rows строк."""
    for i in range(min(max_rows, len(df_raw))):
        row = df_raw.iloc[i].astype(str).str.lower()
        for kw in keywords:
            if row.str.contains(kw).any():
                return i
    return None

def find_column(df, keywords):
    """Ищет колонку по ключевым словам в названии."""
    for col in df.columns:
        col_lower = col.lower().strip()
        for kw in keywords:
            if kw in col_lower:
                return col
    return None

if uploaded_file is not None:
    try:
        # Читаем все строки без заголовка
        df_raw_all = pd.read_excel(uploaded_file, header=None, dtype=str)
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
        st.stop()

    if df_raw_all.empty:
        st.error("Файл пуст")
        st.stop()

    # Ищем строку с заголовками
    header_row = find_header_row(df_raw_all, ["дата", "продано", "остаток", "цена"])
    if header_row is None:
        st.error("Не удалось найти строку с заголовками. Убедитесь, что есть колонки: Дата, Продано штук, Остаток на конец периода, шт, Стоимость 1 шт в рублях.")
        st.stop()

    # Перечитываем с найденным заголовком
    try:
        df_raw = pd.read_excel(uploaded_file, header=header_row)
    except Exception as e:
        st.error(f"Ошибка при чтении с заголовком: {e}")
        st.stop()

    # Определяем колонки
    date_col = find_column(df_raw, ["дата", "date", "день", "период", "dt"])
    if date_col is None:
        st.error("Не найдена колонка с датой.")
        st.stop()
    df_raw.rename(columns={date_col: "Дата"}, inplace=True)

    sales_col = find_column(df_raw, ["продано", "продажи", "sales", "прод"])
    if sales_col is None:
        st.error("Не найдена колонка с продажами.")
        st.stop()
    df_raw.rename(columns={sales_col: "Продано штук"}, inplace=True)

    stock_col = find_column(df_raw, ["остаток", "stock", "наличие", "конец"])
    if stock_col is None:
        st.error("Не найдена колонка с остатком.")
        st.stop()
    df_raw.rename(columns={stock_col: "Остаток на конец периода, шт"}, inplace=True)

    price_col = find_column(df_raw, ["цена", "стоимость", "price", "cost"])
    if price_col is None:
        st.error("Не найдена колонка с ценой.")
        st.stop()
    df_raw.rename(columns={price_col: "Стоимость 1 шт в рублях"}, inplace=True)

    # Берём нужные колонки
    df = df_raw[["Дата", "Продано штук", "Остаток на конец периода, шт", "Стоимость 1 шт в рублях"]].copy()

    # ---- Преобразование дат ----
    # Пробуем несколько форматов
    def parse_dates_robust(series):
        for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return pd.to_datetime(series, format=fmt, errors="coerce")
            except:
                continue
        # Если ни один не подошёл, используем стандартный парсер с dayfirst=True
        return pd.to_datetime(series, dayfirst=True, errors="coerce")

    df["Дата"] = parse_dates_robust(df["Дата"])

    # Удаляем строки с нераспознанной датой
    invalid_dates = df["Дата"].isna()
    if invalid_dates.any():
        st.warning(f"Найдено {invalid_dates.sum()} строк с нераспознанной датой. Они будут удалены.")
        df = df[~invalid_dates].copy()

    if df.empty:
        st.error("После удаления нераспознанных дат таблица пуста. Проверьте формат дат.")
        st.stop()

    # Приводим числа
    df["Продано штук"] = pd.to_numeric(df["Продано штук"], errors="coerce").fillna(0).astype(int)
    df["Остаток на конец периода, шт"] = pd.to_numeric(df["Остаток на конец периода, шт"], errors="coerce").astype(int)
    df["Стоимость 1 шт в рублях"] = pd.to_numeric(df["Стоимость 1 шт в рублях"], errors="coerce").astype(float)

    # Сортируем по дате
    df = df.sort_values("Дата").reset_index(drop=True)

    # Проверяем последнюю дату
    first_date = df["Дата"].min().strftime("%d.%m.%Y")
    last_date = df["Дата"].max().strftime("%d.%m.%Y")
    st.info(f"📅 Период данных: с {first_date} по {last_date} (всего {len(df)} дней)")

    # ---- Расчёт остатка на начало и поступлений ----
    df["Остаток_нач"] = 0
    df["Поступления"] = 0
    df.loc[0, "Остаток_нач"] = df.loc[0, "Остаток на конец периода, шт"]
    for i in range(1, len(df)):
        prev_end = df.loc[i-1, "Остаток на конец периода, шт"]
        df.loc[i, "Остаток_нач"] = prev_end
        post = df.loc[i, "Остаток на конец периода, шт"] - df.loc[i, "Остаток_нач"] + df.loc[i, "Продано штук"]
        if post < 0:
            post = 0
            st.warning(f"В строке {i+1} (дата {df.loc[i, 'Дата'].strftime('%d.%m.%Y')}) "
                       f"получилось отрицательное поступление, установлено 0.")
        df.loc[i, "Поступления"] = post

    # ---- Оценка спроса ----
    days_without_deficit = df[df["Остаток на конец периода, шт"] > 0]
    if days_without_deficit.empty:
        st.error("Нет ни одного дня без дефицита, невозможно оценить спрос.")
        st.stop()

    st.sidebar.header("Параметры расчёта")
    method = st.sidebar.selectbox(
        "Метод оценки спроса",
        ["Среднее арифметическое", "Медиана", "Скользящее среднее (по всем дням)"]
    )

    if method == "Скользящее среднее (по всем дням)":
        window = st.sidebar.slider("Окно скользящего среднего (дней)", min_value=2, max_value=30, value=7)
        df["Спрос_оценка"] = df["Продано штук"].rolling(window=window, min_periods=1).mean()
        avg_no_deficit = days_without_deficit["Продано штук"].mean()
        df["Спрос_оценка"] = df["Спрос_оценка"].fillna(avg_no_deficit)
    else:
        if method == "Среднее арифметическое":
            demand_est = days_without_deficit["Продано штук"].mean()
        else:
            demand_est = days_without_deficit["Продано штук"].median()
        df["Спрос_оценка"] = demand_est

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

    st.subheader("📈 Итоговые показатели за период")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Общая упущенная выгода", f"{total_loss:,.2f} руб.")
    col2.metric("Общий дефицит (шт)", f"{total_deficit:,.0f}")
    col3.metric("Дней с дефицитом", f"{days_with_deficit}")
    col4.metric("Средний дефицит в день (шт)", f"{avg_deficit_per_day:.1f}")

    # ---- Графики ----
    st.subheader("📉 Графики")
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

    fig2 = px.bar(
        df,
        x="Дата",
        y="Дефицит_шт",
        title="Дефицит по дням (шт)",
        labels={"Дефицит_шт": "Дефицит (шт)"},
        color_discrete_sequence=["orange"]
    )
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.bar(
        df,
        x="Дата",
        y="Упущенная_выгода",
        title="Упущенная выгода по дням (руб.)",
        labels={"Упущенная_выгода": "Упущенная выгода (руб.)"},
        color_discrete_sequence=["red"]
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ---- Таблица ----
    st.subheader("📋 Детальная таблица")
    display_cols = [
        "Дата", "Остаток_нач", "Поступления", "Продано штук",
        "Остаток на конец периода, шт", "Спрос_оценка", "Дефицит_шт", "Упущенная_выгода"
    ]
    df_display = df[display_cols].copy()
    df_display["Дата"] = df_display["Дата"].dt.strftime("%d.%m.%Y")
    st.dataframe(df_display, use_container_width=True)

    # ---- Скачивание ----
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
