import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np

# ---------- НАСТРОЙКА СТРАНИЦЫ ----------
st.set_page_config(page_title="Анализ неудовлетворённого спроса", layout="wide")

# ---------- ЗАГОЛОВОК ----------
st.markdown('<div class="title-glow">📊 Анализ неудовлетворённого спроса</div>', unsafe_allow_html=True)

st.components.v1.html("""
<div id="bg-animation" style="position:fixed; top:0; left:0; width:100%; height:100%; z-index:-1; overflow:hidden; pointer-events:none;">
    <canvas id="canvas" style="width:100%; height:100%;"></canvas>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
        window.addEventListener('resize', resize);
        resize();
        const circles = [];
        for (let i = 0; i < 15; i++) {
            circles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                r: 30 + Math.random() * 120,
                dx: (Math.random() - 0.5) * 0.3,
                dy: (Math.random() - 0.5) * 0.3,
                color: `hsla(${Math.random() * 360}, 80%, 70%, 0.04)`
            });
        }
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            circles.forEach(c => {
                c.x += c.dx;
                c.y += c.dy;
                if (c.x < 0 || c.x > canvas.width) c.dx *= -1;
                if (c.y < 0 || c.y > canvas.height) c.dy *= -1;
                ctx.beginPath();
                ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
                ctx.fillStyle = c.color;
                ctx.fill();
                ctx.strokeStyle = 'rgba(255,255,255,0.02)';
                ctx.lineWidth = 1;
                ctx.stroke();
            });
            requestAnimationFrame(animate);
        }
        animate();
    </script>
</div>
""", height=0)

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
