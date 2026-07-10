import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np

# ---------- НАСТРОЙКА СТРАНИЦЫ ----------
st.set_page_config(page_title="Анализ неудовлетворённого спроса", layout="wide")

# ---------- ПРИНУДИТЕЛЬНЫЙ CSS (с !important) ----------
st.markdown("""
<style>
    /* Переопределяем фон с !important */
    .stApp, html, body, .main {
        background: linear-gradient(-45deg, #0a0e1a, #1a1f3a, #2d1b3d, #0a2a4a) !important;
        background-size: 400% 400% !important;
        animation: gradientFlow 20s ease infinite !important;
        min-height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
        color: #e6edf3 !important;
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
    }

    /* Анимированные фигуры (фон) */
    .bg-shapes {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        pointer-events: none !important;
        z-index: -1 !important;
        overflow: hidden !important;
    }
    .bg-shapes div {
        position: absolute !important;
        border-radius: 50% !important;
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        animation: floatShape 35s infinite alternate ease-in-out !important;
    }
    .bg-shapes div:nth-child(1) {
        width: 400px !important; height: 400px !important; top: -10% !important; left: -10% !important;
        animation-duration: 40s !important;
        background: radial-gradient(circle, rgba(100, 150, 255, 0.08), transparent) !important;
    }
    .bg-shapes div:nth-child(2) {
        width: 250px !important; height: 250px !important; bottom: 5% !important; right: 5% !important;
        animation-duration: 30s !important; animation-delay: -5s !important;
        border-radius: 30% 70% 50% 50% / 50% 40% 60% 50% !important;
        background: radial-gradient(circle, rgba(255, 100, 200, 0.06), transparent) !important;
    }
    .bg-shapes div:nth-child(3) {
        width: 180px !important; height: 180px !important; top: 40% !important; left: 70% !important;
        animation-duration: 45s !important; animation-delay: -10s !important;
        border-radius: 40% 60% 30% 70% / 50% 40% 60% 50% !important;
        background: radial-gradient(circle, rgba(255, 200, 50, 0.05), transparent) !important;
    }
    .bg-shapes div:nth-child(4) {
        width: 120px !important; height: 120px !important; bottom: 30% !important; left: 15% !important;
        animation-duration: 25s !important; animation-delay: -2s !important;
        border-radius: 60% 40% 50% 50% / 30% 60% 40% 70% !important;
        background: radial-gradient(circle, rgba(0, 255, 200, 0.05), transparent) !important;
    }
    .bg-shapes div:nth-child(5) {
        width: 300px !important; height: 300px !important; top: 70% !important; left: 60% !important;
        animation-duration: 50s !important; animation-delay: -8s !important;
        border-radius: 30% 70% 60% 40% / 50% 40% 60% 50% !important;
        background: radial-gradient(circle, rgba(150, 100, 255, 0.06), transparent) !important;
    }
    @keyframes floatShape {
        0% { transform: translate(0, 0) rotate(0deg) scale(1); opacity: 0.5; }
        100% { transform: translate(80px, -60px) rotate(360deg) scale(1.3); opacity: 1; }
    }

    /* Контейнеры данных */
    .main > div {
        background: rgba(0, 0, 0, 0.25) !important;
        border-radius: 24px !important;
        padding: 20px 28px !important;
        margin: 16px 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(6px) !important;
        -webkit-backdrop-filter: blur(6px) !important;
    }

    /* Заголовки и текст */
    h1, h2, h3, .stMarkdown, .stDataFrame, .stMetric, .stSelectbox label, .stSlider label {
        color: #f0f6fc !important;
    }
    .stMetric label {
        color: #58a6ff !important;
        font-weight: 500;
    }
    .stMetric .stMetricValue {
        color: #ffffff !important;
        font-size: 2.4rem !important;
        font-weight: 700;
    }

    /* Виджеты */
    .stButton button, .stSelectbox div, .stSlider div, .stFileUploader div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f0f6fc !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        transition: all 0.2s ease !important;
        backdrop-filter: blur(4px) !important;
    }
    .stButton button:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
        transform: scale(1.02);
    }
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
        background: rgba(10, 14, 26, 0.85) !important;
        backdrop-filter: blur(10px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Таблицы */
    .stDataFrame {
        background: rgba(0, 0, 0, 0.2) !important;
        border-radius: 16px !important;
        padding: 8px !important;
        border: none !important;
    }
    .stDataFrame table {
        color: #e6edf3 !important;
    }
    .stDataFrame thead tr th {
        background: rgba(255, 255, 255, 0.04) !important;
        color: #58a6ff !important;
    }

    /* Скроллбар */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.3); }

    /* Анимированный заголовок */
    .title-glow {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        background: linear-gradient(45deg, #58a6ff, #f0883e, #ff6b9d) !important;
        background-size: 300% 300% !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        animation: glowPulse 4s ease infinite alternate !important;
        text-shadow: 0 0 30px rgba(88, 166, 255, 0.2) !important;
        display: inline-block;
        padding: 0 10px;
    }
    @keyframes glowPulse {
        0% { background-position: 0% 50%; text-shadow: 0 0 20px rgba(88, 166, 255, 0.2); }
        50% { text-shadow: 0 0 40px rgba(240, 136, 62, 0.4), 0 0 80px rgba(255, 107, 157, 0.2); }
        100% { background-position: 100% 50%; text-shadow: 0 0 20px rgba(88, 166, 255, 0.2); }
    }
</style>
""", unsafe_allow_html=True)

# Добавляем HTML-контейнер с фигурами (он будет виден всегда)
st.markdown("""
<div class="bg-shapes">
    <div></div>
    <div></div>
    <div></div>
    <div></div>
    <div></div>
</div>
""", unsafe_allow_html=True)

# ---------- ЗАГОЛОВОК ----------
st.markdown('<div class="title-glow">📊 Анализ неудовлетворённого спроса</div>', unsafe_allow_html=True)

# ---------- ВСПОМОГАТЕЛЬНАЯ ПРОВЕРКА (чтобы убедиться, что CSS применился) ----------
st.markdown('<p style="color: #58a6ff; font-size: 0.8rem; opacity:0.6;">✨ Дизайн с анимацией активен</p>', unsafe_allow_html=True)

# ---------- ФУНКЦИИ ПАРСИНГА И РАСЧЁТА (без изменений) ----------
def parse_excel(file):
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
            deficit = avg_demand if stock == 0 else 0.0
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
    total_deficit = df_result['deficit'].sum()
    by_product = df_result.groupby('product')['deficit'].sum().reset_index()
    by_city = df_result.groupby('city')['deficit'].sum().reset_index()
    days_with_deficit = df_result[df_result['deficit'] > 0].groupby('product')['day'].nunique().reset_index()
    days_with_deficit.columns = ['product', 'days_with_deficit']
    metrics = {
        'total_deficit': total_deficit,
        'by_product': by_product,
        'by_city': by_city,
        'days_with_deficit': days_with_deficit
    }
    return df_result, metrics

# ---------- ИНТЕРФЕЙС (с width='stretch' для графиков) ----------
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

            selected_city = st.sidebar.selectbox("Город для детального анализа", ["Все"] + cities)
            selected_product = st.sidebar.selectbox("Товар для детального графика", ["Все"] + products)
            top_n_heat = st.sidebar.slider("Количество товаров на тепловой карте", min_value=5, max_value=50, value=15)

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

            # ---- ГРАФИКИ ----
            st.subheader("🏙️ Дефицит по городам")
            fig_city = px.bar(metrics['by_city'], x='city', y='deficit',
                              title="Суммарный дефицит по городам (шт)",
                              labels={'city': 'Город', 'deficit': 'Дефицит (шт)'},
                              color='deficit', color_continuous_scale='Reds')
            st.plotly_chart(fig_city, width='stretch')

            st.subheader("📦 Дефицит по товарам (топ-10)")
            top_products = metrics['by_product'].nlargest(10, 'deficit')
            fig_prod = px.bar(top_products, x='deficit', y='product',
                              orientation='h',
                              title="Топ-10 товаров по дефициту (шт)",
                              labels={'deficit': 'Дефицит (шт)', 'product': 'Товар'},
                              color='deficit', color_continuous_scale='Reds')
            fig_prod.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_prod, width='stretch')

            st.subheader("📅 Количество дней с дефицитом по товарам")
            days_def = metrics['days_with_deficit'].nlargest(15, 'days_with_deficit')
            fig_days = px.bar(days_def, x='days_with_deficit', y='product',
                              orientation='h',
                              title="Топ-15 товаров по количеству дней с дефицитом",
                              labels={'days_with_deficit': 'Дней с дефицитом', 'product': 'Товар'},
                              color='days_with_deficit', color_continuous_scale='Oranges')
            fig_days.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_days, width='stretch')

            st.subheader("🔥 Тепловая карта дефицита (товары × города)")
            heat_data = df_deficit.groupby(['product', 'city'])['deficit'].sum().reset_index()
            top_products_heat = heat_data.groupby('product')['deficit'].sum().nlargest(top_n_heat).index
            heat_data_filtered = heat_data[heat_data['product'].isin(top_products_heat)]
            if not heat_data_filtered.empty:
                pivot = heat_data_filtered.pivot(index='product', columns='city', values='deficit').fillna(0)
                fig_heat = px.imshow(pivot, text_auto=True, aspect="auto",
                                     color_continuous_scale='Reds',
                                     title=f"Дефицит по товарам (топ-{top_n_heat}) и городам (шт)")
                fig_heat.update_layout(height=600)
                st.plotly_chart(fig_heat, width='stretch')
            else:
                st.info("Недостаточно данных для тепловой карты.")

            st.subheader("📆 Дефицит по товарам в выбранном городе (по дням)")
            city_for_daily = st.selectbox("Выберите город для отображения дефицита по дням", cities)
            df_city = df_deficit[df_deficit['city'] == city_for_daily]
            if not df_city.empty:
                pivot_daily = df_city.pivot(index='product', columns='day', values='deficit').fillna(0)
                products_with_deficit = pivot_daily.sum(axis=1)
                products_with_deficit = products_with_deficit[products_with_deficit > 0]
                if len(products_with_deficit) > 0:
                    top_products_daily = products_with_deficit.nlargest(min(30, len(products_with_deficit))).index
                    pivot_daily = pivot_daily.loc[top_products_daily]
                else:
                    st.warning(f"В городе {city_for_daily} нет дефицита ни по одному товару.")
                    pivot_daily = pd.DataFrame()
                if not pivot_daily.empty:
                    pivot_daily['total'] = pivot_daily.sum(axis=1)
                    pivot_daily = pivot_daily.sort_values('total', ascending=False).drop(columns='total')
                    fig_daily_heat = px.imshow(pivot_daily, text_auto=True, aspect="auto",
                                               color_continuous_scale='Reds',
                                               title=f"Дефицит (шт) по дням – город {city_for_daily}",
                                               labels={'product': 'Товар', 'day': 'День месяца', 'color': 'Дефицит (шт)'})
                    fig_daily_heat.update_layout(height=max(400, 30*len(pivot_daily)))
                    st.plotly_chart(fig_daily_heat, width='stretch')
                    non_zero = df_city[df_city['deficit'] > 0]
                    if not non_zero.empty:
                        st.subheader(f"📋 Дни с дефицитом в городе {city_for_daily}")
                        st.dataframe(non_zero[['product', 'day', 'deficit']].sort_values(['product', 'day']))
                else:
                    st.info("Нет данных для отображения тепловой карты по дням.")
            else:
                st.warning(f"Нет данных для города {city_for_daily}.")

            if selected_product != "Все":
                st.subheader(f"📉 Детальный график: {selected_product}")
                filtered = df_deficit[df_deficit['product'] == selected_product]
                if selected_city != "Все":
                    filtered = filtered[filtered['city'] == selected_city]
                    city_label = f" в городе {selected_city}"
                else:
                    city_label = " (все города)"
                if not filtered.empty:
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
                    st.plotly_chart(fig_det, width='stretch')
                    st.dataframe(daily)
                else:
                    st.warning("Нет данных для выбранного товара и города.")

            st.subheader("📋 Детальная таблица дефицита по дням")
            detail = df_deficit.groupby(['city', 'product', 'day']).agg({
                'sales': 'sum',
                'stock': 'sum',
                'avg_demand': 'first',
                'deficit': 'sum'
            }).reset_index()
            st.dataframe(detail)

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
