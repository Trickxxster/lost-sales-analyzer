import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np

# ---------- НАСТРОЙКА СТРАНИЦЫ ----------
st.set_page_config(page_title="Анализ неудовлетворённого спроса", layout="wide")

# ---------- КАСТОМНЫЙ CSS (НОВЫЙ ДИЗАЙН) ----------
st.markdown("""
<style>
    /* Основной фон – тёмный градиент с анимацией */
    .stApp {
        background: linear-gradient(135deg, #0d1117, #161b22, #0d1117);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        color: #e6edf3;
        font-family: 'Segoe UI', sans-serif;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Анимированные геометрические фигуры на фоне */
    .bg-shapes {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
        overflow: hidden;
    }
    .bg-shapes div {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.03);
        animation: floatShape 30s infinite alternate ease-in-out;
    }
    .bg-shapes div:nth-child(1) {
        width: 300px; height: 300px; top: 5%; left: -5%;
        animation-duration: 35s;
    }
    .bg-shapes div:nth-child(2) {
        width: 200px; height: 200px; bottom: 10%; right: 5%;
        animation-duration: 28s;
        animation-delay: -5s;
        border-radius: 30% 70% 50% 50% / 50% 40% 60% 50%;
    }
    .bg-shapes div:nth-child(3) {
        width: 150px; height: 150px; top: 40%; left: 60%;
        animation-duration: 40s;
        animation-delay: -10s;
        border-radius: 40% 60% 30% 70% / 50% 40% 60% 50%;
    }
    .bg-shapes div:nth-child(4) {
        width: 100px; height: 100px; bottom: 30%; left: 20%;
        animation-duration: 25s;
        animation-delay: -2s;
        border-radius: 60% 40% 50% 50% / 30% 60% 40% 70%;
    }
    .bg-shapes div:nth-child(5) {
        width: 250px; height: 250px; top: 70%; left: 70%;
        animation-duration: 45s;
        animation-delay: -8s;
        border-radius: 30% 70% 60% 40% / 50% 40% 60% 50%;
    }
    @keyframes floatShape {
        0% { transform: translate(0, 0) rotate(0deg) scale(1); }
        100% { transform: translate(80px, -60px) rotate(360deg) scale(1.2); }
    }

    /* Контейнеры – без рамок, с лёгкой тенью и закруглением */
    .main > div {
        background: rgba(255, 255, 255, 0.04);
        border-radius: 20px;
        padding: 20px 25px;
        margin: 16px 0;
        border: 1px solid rgba(255, 255, 255, 0.06);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(4px);
    }

    /* Текст и заголовки – светлые */
    h1, h2, h3, .stMarkdown, .stDataFrame, .stMetric, .stSelectbox label, .stSlider label {
        color: #f0f6fc !important;
    }
    .stMetric label {
        color: #58a6ff !important;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    .stMetric .stMetricValue {
        color: #ffffff !important;
        font-size: 2.2rem !important;
        font-weight: 700;
    }

    /* Виджеты – без лишних рамок, на прозрачном фоне */
    .stButton button, .stSelectbox div, .stSlider div, .stFileUploader div {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f0f6fc !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        transform: scale(1.02);
    }
    /* Убираем рамки вокруг слайдера */
    .stSlider div[data-baseweb="slider"] {
        background: transparent !important;
        border: none !important;
    }
    .stSlider div[data-baseweb="slider"] div {
        background: transparent !important;
        border: none !important;
    }

    /* Боковая панель – полупрозрачная, с затемнением */
    .css-1d391kg {
        background: rgba(13, 17, 23, 0.8) !important;
        backdrop-filter: blur(8px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Таблицы */
    .stDataFrame {
        background: rgba(0, 0, 0, 0.2) !important;
        border-radius: 16px;
        padding: 8px;
        border: none;
    }
    .stDataFrame table {
        color: #e6edf3 !important;
    }
    .stDataFrame thead tr th {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #58a6ff !important;
    }

    /* Скроллбар */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.3); }

    /* Анимированный заголовок */
    .title-glow {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(45deg, #58a6ff, #f0883e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: pulseGlow 3s infinite alternate;
    }
    @keyframes pulseGlow {
        0% { text-shadow: 0 0 10px rgba(88, 166, 255, 0.2); }
        100% { text-shadow: 0 0 30px rgba(88, 166, 255, 0.6), 0 0 60px rgba(240, 136, 62, 0.3); }
    }
</style>
""", unsafe_allow_html=True)

# Добавляем HTML с фигурами
st.markdown("""
<div class="bg-shapes">
    <div></div>
    <div></div>
    <div></div>
    <div></div>
    <div></div>
</div>
""", unsafe_allow_html=True)

# ---------- ЗАГОЛОВОК С АНИМАЦИЕЙ ----------
st.markdown('<div class="title-glow">📊 Анализ неудовлетворённого спроса</div>', unsafe_allow_html=True)

# ---------- ОСТАЛЬНОЙ КОД (без изменений) ----------
# ... (весь код функций parse_excel, calculate_deficit и интерфейса)
# Обратите внимание: везде заменяем use_container_width=True на width='stretch'

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

# ---------- ИНТЕРФЕЙС С ЗАМЕНОЙ use_container_width ----------
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

            # Фильтры
            st.sidebar.header("🔍 Фильтры")
            cities = sorted(df_deficit['city'].unique())
            products = sorted(df_deficit['product'].unique())

            selected_city = st.sidebar.selectbox("Город для детального анализа", ["Все"] + cities)
            selected_product = st.sidebar.selectbox("Товар для детального графика", ["Все"] + products)
            top_n_heat = st.sidebar.slider("Количество товаров на тепловой карте", min_value=5, max_value=50, value=15)

            # Метрики
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

            # Графики (заменяем use_container_width=True на width='stretch')
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
                        st.dataframe(non_zero[['product', 'day', 'deficit']].sort_values(['product', 'day']),
                                     width='stretch')
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
                    st.dataframe(daily, width='stretch')
                else:
                    st.warning("Нет данных для выбранного товара и города.")

            st.subheader("📋 Детальная таблица дефицита по дням")
            detail = df_deficit.groupby(['city', 'product', 'day']).agg({
                'sales': 'sum',
                'stock': 'sum',
                'avg_demand': 'first',
                'deficit': 'sum'
            }).reset_index()
            st.dataframe(detail, width='stretch')

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
