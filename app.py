import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np

st.set_page_config(page_title="Анализ неудовлетворённого спроса", layout="wide")

# ---------- КАСТОМНЫЙ CSS С АНИМАЦИЕЙ И ТЁМНЫМ ФОНОМ ----------
st.markdown("""
<style>
    /* Принудительно устанавливаем тёмный фон для всей страницы */
    body, .stApp, .stAppViewContainer, .main, .block-container {
        background-color: #0a0e1a !important;
        background-image: linear-gradient(135deg, #0a0e1a 0%, #1a1f35 50%, #16213e 100%) !important;
        background-attachment: fixed !important;
        color: #f0f0f0 !important;
    }
    /* Анимация градиента через псевдоэлемент */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(-45deg, #0a0e1a, #1a1f35, #16213e, #0f3460);
        background-size: 400% 400%;
        animation: gradientFlow 20s ease infinite;
        z-index: -1;
        pointer-events: none;
    }
    @keyframes gradientFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Контейнеры данных – прозрачные, без лишних рамок */
    .stMarkdown, .stDataFrame, .stMetric, .stSelectbox, .stSlider, .stFileUploader, .stButton {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Блоки с данными (все div внутри main) делаем полупрозрачными с тенью */
    .main > div {
        background: rgba(0, 0, 0, 0.3) !important;
        border-radius: 16px !important;
        padding: 20px 25px !important;
        margin: 10px 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: none !important;
    }

    /* Заголовки, текст, метрики – светлые */
    h1, h2, h3, h4, .stMarkdown, .stDataFrame, .stMetric, label, .stSelectbox label, .stSlider label {
        color: #e8e8e8 !important;
    }
    .stMetric label {
        color: #90caf9 !important;
        font-weight: 600;
    }
    .stMetric .stMetricValue {
        color: #ffffff !important;
        font-size: 2.2rem !important;
        font-weight: 700;
    }

    /* Виджеты – без фона и рамок, только текст */
    .stSelectbox div, .stSlider div, .stFileUploader div, .stButton button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        transform: scale(1.02);
    }
    /* Убираем лишние рамки вокруг слайдера */
    .stSlider div[data-baseweb="slider"] {
        background: transparent !important;
        border: none !important;
    }
    .stSlider div[data-baseweb="slider"] div {
        background: transparent !important;
        border: none !important;
    }
    /* Боковая панель */
    .css-1d391kg {
        background: rgba(0, 0, 0, 0.6) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    /* Таблицы */
    .stDataFrame {
        background: rgba(0, 0, 0, 0.2) !important;
        border-radius: 12px;
        padding: 8px;
        border: none;
    }
    .stDataFrame table {
        color: #e0e0e0 !important;
    }
    .stDataFrame thead tr th {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #90caf9 !important;
    }

    /* Стили для анимированных "пузырьков" (лава) */
    .bubbles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
        overflow: hidden;
    }
    .bubble {
        position: absolute;
        bottom: -150px;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 50%;
        border: 1px solid rgba(255, 255, 255, 0.03);
        animation: rise 20s infinite ease-in-out;
    }
    .bubble:nth-child(1) { width: 80px; height: 80px; left: 10%; animation-duration: 22s; animation-delay: 0s; }
    .bubble:nth-child(2) { width: 120px; height: 120px; left: 30%; animation-duration: 26s; animation-delay: 2s; }
    .bubble:nth-child(3) { width: 60px; height: 60px; left: 50%; animation-duration: 18s; animation-delay: 4s; }
    .bubble:nth-child(4) { width: 150px; height: 150px; left: 70%; animation-duration: 30s; animation-delay: 1s; }
    .bubble:nth-child(5) { width: 90px; height: 90px; left: 85%; animation-duration: 24s; animation-delay: 3s; }
    .bubble:nth-child(6) { width: 100px; height: 100px; left: 20%; animation-duration: 28s; animation-delay: 5s; }

    @keyframes rise {
        0% { transform: translateY(0) scale(1) rotate(0deg); opacity: 0.2; }
        20% { opacity: 0.6; }
        80% { opacity: 0.6; }
        100% { transform: translateY(-110vh) scale(1.5) rotate(720deg); opacity: 0; }
    }
</style>
<div class="bubbles">
    <div class="bubble"></div>
    <div class="bubble"></div>
    <div class="bubble"></div>
    <div class="bubble"></div>
    <div class="bubble"></div>
    <div class="bubble"></div>
</div>
""", unsafe_allow_html=True)

st.title("📊 Анализ неудовлетворённого спроса")
# --------------------- Парсинг файла ---------------------
def parse_excel(file):
    """
    Парсит Excel-файл со структурой:
    - Каждый день – отдельный блок, начинающийся со строки, где в первом столбце 'Номенклатура'.
    - В блоке: первая строка – города, вторая – подзаголовки (Класс шт, Количество, ...),
      далее строки товаров.
    Возвращает DataFrame с колонками:
    day, city, product, sales, stock
    """
    df_raw = pd.read_excel(file, header=None, dtype=str)
    df_raw = df_raw.fillna('')

    start_indices = df_raw[df_raw[0].str.contains('Номенклатура', na=False)].index.tolist()
    if not start_indices:
        st.error("Не найдены блоки с 'Номенклатура'. Проверьте структуру файла.")
        return None

    end_indices = start_indices[1:] + [len(df_raw)]
    records = []

    for day_idx, (start, end) in enumerate(zip(start_indices, end_indices), start=1):
        header_row = df_raw.iloc[start]
        subheader_row = df_raw.iloc[start + 1] if start + 1 < len(df_raw) else None

        cities = {}
        for col_idx, val in header_row.items():
            val_str = str(val).strip()
            if 'LikeStore' in val_str or 'Like' in val_str:
                cities[val_str] = col_idx

        if not cities:
            continue

        data_rows = df_raw.iloc[start+2:end]
        data_rows = data_rows[~data_rows[0].str.contains('Итого', na=False)]

        for _, row in data_rows.iterrows():
            product_name = str(row[0]).strip()
            product_char = str(row[1]).strip()
            product = f"{product_name} | {product_char}" if product_char else product_name

            for city, col_start in cities.items():
                if col_start + 9 >= len(row):
                    continue
                sales_val = row[col_start + 1]
                stock_val = row[col_start + 5]

                try:
                    sales = float(sales_val) if sales_val not in ['', None] else 0.0
                except:
                    sales = 0.0
                try:
                    stock = float(stock_val) if stock_val not in ['', None] else 0.0
                except:
                    stock = 0.0

                records.append({
                    'day': day_idx,
                    'city': city,
                    'product': product,
                    'sales': sales,
                    'stock': stock
                })

    if not records:
        st.error("Не удалось извлечь данные. Проверьте структуру файла.")
        return None

    df = pd.DataFrame(records)
    df['sales'] = df['sales'].astype(float)
    df['stock'] = df['stock'].astype(float)
    return df

# --------------------- Расчёт дефицита ---------------------
def calculate_deficit(df):
    results = []
    for (city, product), group in df.groupby(['city', 'product']):
        available = group[group['stock'] > 0]
        if len(available) == 0:
            continue
        avg_demand = available['sales'].mean()
        if avg_demand <= 0:
            continue

        for _, row in group.iterrows():
            day = row['day']
            stock = row['stock']
            if stock == 0:
                deficit = avg_demand
            else:
                deficit = 0.0
            results.append({
                'city': city,
                'product': product,
                'day': day,
                'sales': row['sales'],
                'stock': stock,
                'avg_demand': avg_demand,
                'deficit': deficit
            })

    df_result = pd.DataFrame(results)
    if df_result.empty:
        return None, None

    # Агрегированные метрики
    total_deficit = df_result['deficit'].sum()
    by_product = df_result.groupby('product')['deficit'].sum().reset_index()
    by_city = df_result.groupby('city')['deficit'].sum().reset_index()
    # Количество дней с дефицитом по товару
    days_with_deficit = df_result[df_result['deficit'] > 0].groupby('product')['day'].nunique().reset_index()
    days_with_deficit.columns = ['product', 'days_with_deficit']

    metrics = {
        'total_deficit': total_deficit,
        'by_product': by_product,
        'by_city': by_city,
        'days_with_deficit': days_with_deficit
    }
    return df_result, metrics

# --------------------- Интерфейс Streamlit ---------------------
uploaded_file = st.file_uploader("📂 Загрузите Excel-файл", type=["xlsx"])

if uploaded_file:
    with st.spinner("Парсинг файла..."):
        df_data = parse_excel(uploaded_file)

    if df_data is not None:
        st.success(f"✅ Данные загружены. {len(df_data)} записей, дни: {df_data['day'].min()} – {df_data['day'].max()}")

        with st.expander("📋 Предпросмотр данных"):
            st.dataframe(df_data.head(100))

        with st.spinner("Расчёт дефицита..."):
            df_deficit, metrics = calculate_deficit(df_data)

        if df_deficit is None:
            st.error("Не удалось рассчитать дефицит: нет дней с наличием товара.")
        else:
            st.success("✅ Расчёт выполнен.")

            # ---- Фильтры ----
            st.sidebar.header("🔍 Фильтры")
            cities = sorted(df_deficit['city'].unique())
            products = sorted(df_deficit['product'].unique())

            selected_city = st.sidebar.selectbox("Город для детального графика", ["Все"] + cities)
            selected_product = st.sidebar.selectbox("Товар для детального графика", ["Все"] + products)

            # Топ-N для тепловой карты
            top_n = st.sidebar.slider("Количество товаров на тепловой карте", min_value=5, max_value=50, value=15)

            # ---- Общие метрики ----
            total_def = metrics['total_deficit']
            total_days = df_deficit['day'].nunique()
            days_with_def = df_deficit[df_deficit['deficit'] > 0]['day'].nunique()
            n_products = df_deficit['product'].nunique()
            n_cities = df_deficit['city'].nunique()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Общий дефицит (шт)", f"{total_def:,.0f}")
            col2.metric("Дней с дефицитом", f"{days_with_def} из {total_days}")
            col3.metric("Товаров с дефицитом", f"{n_products}")
            col4.metric("Городов", f"{n_cities}")

            # ---- ГРАФИК 1: Дефицит по городам ----
            st.subheader("🏙️ Дефицит по городам")
            fig_city = px.bar(metrics['by_city'], x='city', y='deficit',
                              title="Суммарный дефицит по городам (шт)",
                              labels={'city': 'Город', 'deficit': 'Дефицит (шт)'},
                              color='deficit', color_continuous_scale='Reds')
            st.plotly_chart(fig_city, use_container_width=True)

            # ---- ГРАФИК 2: Дефицит по товарам (топ-10) ----
            st.subheader("📦 Дефицит по товарам (топ-10)")
            top_products = metrics['by_product'].nlargest(10, 'deficit')
            fig_prod = px.bar(top_products, x='deficit', y='product',
                              orientation='h',
                              title="Топ-10 товаров по дефициту (шт)",
                              labels={'deficit': 'Дефицит (шт)', 'product': 'Товар'},
                              color='deficit', color_continuous_scale='Reds')
            fig_prod.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_prod, use_container_width=True)

            # ---- ГРАФИК 3: Количество дней с дефицитом по товарам ----
            st.subheader("📅 Количество дней с дефицитом по товарам")
            days_def = metrics['days_with_deficit'].nlargest(15, 'days_with_deficit')
            fig_days = px.bar(days_def, x='days_with_deficit', y='product',
                              orientation='h',
                              title="Топ-15 товаров по количеству дней с дефицитом",
                              labels={'days_with_deficit': 'Дней с дефицитом', 'product': 'Товар'},
                              color='days_with_deficit', color_continuous_scale='Oranges')
            fig_days.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_days, use_container_width=True)

            # ---- ГРАФИК 4: Тепловая карта дефицита (товары vs города) ----
            st.subheader("🔥 Тепловая карта дефицита (товары × города)")
            heat_data = df_deficit.groupby(['product', 'city'])['deficit'].sum().reset_index()
            # Оставляем топ-N товаров по общему дефициту
            top_products_heat = heat_data.groupby('product')['deficit'].sum().nlargest(top_n).index
            heat_data_filtered = heat_data[heat_data['product'].isin(top_products_heat)]

            if not heat_data_filtered.empty:
                pivot = heat_data_filtered.pivot(index='product', columns='city', values='deficit').fillna(0)
                fig_heat = px.imshow(pivot,
                                     text_auto=True,
                                     aspect="auto",
                                     color_continuous_scale='Reds',
                                     title=f"Дефицит по товарам (топ-{top_n}) и городам (шт)")
                fig_heat.update_layout(height=600)
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.info("Недостаточно данных для тепловой карты.")

            # ---- ГРАФИК 5: Детальный график для выбранного товара (и города, если выбран) ----
            if selected_product != "Все":
                st.subheader(f"📉 Детальный график: {selected_product}")
                filtered = df_deficit[df_deficit['product'] == selected_product]
                if selected_city != "Все":
                    filtered = filtered[filtered['city'] == selected_city]
                    city_label = f" в городе {selected_city}"
                else:
                    city_label = " (все города)"

                if not filtered.empty:
                    # Агрегируем по дням
                    daily = filtered.groupby('day').agg({
                        'stock': 'sum',
                        'deficit': 'sum',
                        'sales': 'sum'
                    }).reset_index()

                    fig_det = go.Figure()
                    fig_det.add_trace(go.Scatter(x=daily['day'], y=daily['stock'],
                                                 mode='lines+markers', name='Остаток'))
                    fig_det.add_trace(go.Scatter(x=daily['day'], y=daily['sales'],
                                                 mode='lines+markers', name='Продажи'))
                    fig_det.add_trace(go.Bar(x=daily['day'], y=daily['deficit'],
                                             name='Дефицит', marker_color='red'))
                    fig_det.update_layout(title=f"Остатки, продажи и дефицит – {selected_product}{city_label}",
                                          xaxis_title='День месяца', yaxis_title='Количество (шт)')
                    st.plotly_chart(fig_det, use_container_width=True)

                    # Также таблица по дням для этого товара
                    st.dataframe(daily, use_container_width=True)
                else:
                    st.warning("Нет данных для выбранного товара и города.")

            # ---- Таблица детализации ----
            st.subheader("📋 Детальная таблица дефицита по дням")
            # Группируем для удобства
            detail = df_deficit.groupby(['city', 'product', 'day']).agg({
                'sales': 'sum',
                'stock': 'sum',
                'avg_demand': 'first',
                'deficit': 'sum'
            }).reset_index()
            st.dataframe(detail, use_container_width=True)

            # ---- Скачивание результата ----
            def to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Результат', index=False)
                return output.getvalue()

            excel_data = to_excel(detail)
            st.download_button(
                label="📥 Скачать результат (Excel)",
                data=excel_data,
                file_name="результат_анализа.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.error("Не удалось обработать файл. Проверьте формат.")
else:
    st.info("👈 Загрузите Excel-файл для начала анализа.")
