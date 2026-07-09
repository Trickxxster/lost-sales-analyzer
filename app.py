import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np

st.set_page_config(page_title="Анализ неудовлетворённого спроса", layout="wide")
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
    # Читаем все строки без заголовков
    df_raw = pd.read_excel(file, header=None, dtype=str)
    # Заполняем NaN пустой строкой
    df_raw = df_raw.fillna('')

    # Находим индексы строк, где в первой колонке "Номенклатура"
    start_indices = df_raw[df_raw[0].str.contains('Номенклатура', na=False)].index.tolist()
    if not start_indices:
        st.error("Не найдены блоки с 'Номенклатура'. Проверьте структуру файла.")
        return None

    # Определяем конец последнего блока
    end_indices = start_indices[1:] + [len(df_raw)]

    records = []

    for day_idx, (start, end) in enumerate(zip(start_indices, end_indices), start=1):
        # Строка с городами (первая строка блока)
        header_row = df_raw.iloc[start]
        # Строка с подзаголовками (вторая строка блока)
        subheader_row = df_raw.iloc[start + 1] if start + 1 < len(df_raw) else None

        # Ищем города: ячейки, содержащие "LikeStore" или "Like"
        cities = {}
        for col_idx, val in header_row.items():
            val_str = str(val).strip()
            if 'LikeStore' in val_str or 'Like' in val_str:
                # Запоминаем начальную колонку для этого города
                cities[val_str] = col_idx

        if not cities:
            st.warning(f"День {day_idx}: города не найдены в заголовке. Пропускаем блок.")
            continue

        # Данные товаров: строки начиная с start+2 до end-1 (исключая строку "Итого"?)
        # Строка "Итого" может быть последней в блоке, её тоже можно пропустить
        data_rows = df_raw.iloc[start+2:end]
        # Удаляем строки, где первый столбец пустой или содержит "Итого"
        data_rows = data_rows[~data_rows[0].str.contains('Итого', na=False)]

        for _, row in data_rows.iterrows():
            product_name = str(row[0]).strip()
            product_char = str(row[1]).strip()
            product = f"{product_name} | {product_char}" if product_char else product_name

            for city, col_start in cities.items():
                # Проверяем, что есть достаточно колонок
                if col_start + 9 >= len(row):
                    continue
                # Извлекаем значения по смещениям
                sales_val = row[col_start + 1]  # "Количество"
                stock_val = row[col_start + 5]  # "Итоговый остаток, шт"

                # Преобразуем в числа
                try:
                    sales = float(sales_val) if sales_val not in ['', None] else 0.0
                except:
                    sales = 0.0
                try:
                    stock = float(stock_val) if stock_val not in ['', None] else 0.0
                except:
                    stock = 0.0

                # Сохраняем запись
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
    # Приводим типы
    df['sales'] = df['sales'].astype(float)
    df['stock'] = df['stock'].astype(float)
    return df

# --------------------- Расчёт дефицита ---------------------
def calculate_deficit(df):
    """
    Для каждого города и товара:
    - Оцениваем средний дневной спрос по дням, где stock > 0 (товар был в наличии).
    - Для дней, где stock == 0, считаем дефицит = спрос - 0 (т.е. спрос).
    Возвращает DataFrame с дефицитом по дням и итоговые метрики.
    """
    # Группируем по городу и товару
    results = []
    for (city, product), group in df.groupby(['city', 'product']):
        # Дни с наличием (stock > 0)
        available = group[group['stock'] > 0]
        if len(available) == 0:
            # Если никогда не было товара, спрос оценить нельзя – пропускаем
            continue

        # Средний спрос = средние продажи в дни наличия
        avg_demand = available['sales'].mean()
        if avg_demand <= 0:
            continue

        # Для каждого дня в группе
        for _, row in group.iterrows():
            day = row['day']
            stock = row['stock']
            sales = row['sales']
            if stock == 0:
                deficit = avg_demand  # весь спрос не удовлетворён
            else:
                deficit = 0.0
            results.append({
                'city': city,
                'product': product,
                'day': day,
                'sales': sales,
                'stock': stock,
                'avg_demand': avg_demand,
                'deficit': deficit
            })

    df_result = pd.DataFrame(results)
    if df_result.empty:
        return None, None

    # Итоговые метрики
    total_deficit_by_product = df_result.groupby('product')['deficit'].sum().reset_index()
    total_deficit_by_city = df_result.groupby('city')['deficit'].sum().reset_index()
    total_deficit = df_result['deficit'].sum()

    return df_result, {
        'total_deficit': total_deficit,
        'by_product': total_deficit_by_product,
        'by_city': total_deficit_by_city
    }

# --------------------- Интерфейс Streamlit ---------------------
uploaded_file = st.file_uploader("📂 Загрузите Excel-файл", type=["xlsx"])

if uploaded_file:
    with st.spinner("Парсинг файла..."):
        df_data = parse_excel(uploaded_file)

    if df_data is not None:
        st.success(f"✅ Данные загружены. {len(df_data)} записей, дни: {df_data['day'].min()} – {df_data['day'].max()}")

        # Показываем сырые данные (опционально)
        with st.expander("📋 Предпросмотр данных"):
            st.dataframe(df_data.head(100))

        # Расчёт дефицита
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

            selected_city = st.sidebar.selectbox("Город", ["Все"] + cities)
            selected_product = st.sidebar.selectbox("Товар", ["Все"] + products)

            df_filtered = df_deficit.copy()
            if selected_city != "Все":
                df_filtered = df_filtered[df_filtered['city'] == selected_city]
            if selected_product != "Все":
                df_filtered = df_filtered[df_filtered['product'] == selected_product]

            # ---- Метрики ----
            total_def = df_filtered['deficit'].sum()
            avg_def_per_day = df_filtered.groupby('day')['deficit'].sum().mean()
            days_with_deficit = df_filtered[df_filtered['deficit'] > 0]['day'].nunique()
            total_days = df_filtered['day'].nunique()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Общий дефицит (шт)", f"{total_def:,.0f}")
            col2.metric("Средний дефицит в день", f"{avg_def_per_day:.1f}")
            col3.metric("Дней с дефицитом", f"{days_with_deficit} из {total_days}")
            col4.metric("Количество товаров", f"{df_filtered['product'].nunique()}")

            # ---- Графики ----
            st.subheader("📈 Динамика дефицита по дням")

            # Суммарный дефицит по дням
            daily_deficit = df_filtered.groupby('day')['deficit'].sum().reset_index()
            fig1 = px.bar(daily_deficit, x='day', y='deficit',
                          title="Дефицит по дням (все товары, шт)",
                          labels={'day': 'День месяца', 'deficit': 'Дефицит (шт)'},
                          color_discrete_sequence=['orange'])
            st.plotly_chart(fig1, use_container_width=True)

            # Динамика остатков и дефицита для выбранного товара (если выбран)
            if selected_product != "Все":
                st.subheader(f"📉 Детали по товару: {selected_product}")
                prod_data = df_filtered[df_filtered['product'] == selected_product]
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=prod_data['day'], y=prod_data['stock'],
                                          mode='lines+markers', name='Остаток на конец дня'))
                fig2.add_trace(go.Bar(x=prod_data['day'], y=prod_data['deficit'],
                                      name='Дефицит', marker_color='red'))
                fig2.update_layout(title=f"Остатки и дефицит – {selected_product}",
                                   xaxis_title='День', yaxis_title='Количество (шт)')
                st.plotly_chart(fig2, use_container_width=True)

            # Тепловая карта дефицита по городам и товарам (топ-10)
            st.subheader("🔥 Тепловая карта дефицита (топ товаров)")
            # Агрегируем дефицит по товарам и городам
            heat_data = df_deficit.groupby(['city', 'product'])['deficit'].sum().reset_index()
            # Оставляем топ-10 товаров по общему дефициту
            top_products = heat_data.groupby('product')['deficit'].sum().nlargest(10).index
            heat_data = heat_data[heat_data['product'].isin(top_products)]

            if not heat_data.empty:
                pivot = heat_data.pivot(index='product', columns='city', values='deficit').fillna(0)
                fig3 = px.imshow(pivot,
                                 text_auto=True,
                                 aspect="auto",
                                 color_continuous_scale='Reds',
                                 title="Дефицит по товарам (топ-10) и городам (шт)")
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Недостаточно данных для тепловой карты.")

            # ---- Таблица с результатами ----
            st.subheader("📋 Детальная таблица")
            # Группируем для удобства
            table_data = df_deficit.groupby(['city', 'product', 'day']).agg({
                'sales': 'sum',
                'stock': 'sum',
                'avg_demand': 'first',
                'deficit': 'sum'
            }).reset_index()
            st.dataframe(table_data, use_container_width=True)

            # ---- Скачивание результата ----
            def to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Результат', index=False)
                return output.getvalue()

            excel_data = to_excel(table_data)
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
