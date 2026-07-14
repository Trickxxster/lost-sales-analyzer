import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np
import re

st.set_page_config(page_title="РђРЅР°Р»РёР· РЅРµСѓРґРѕРІР»РµС‚РІРѕСЂС‘РЅРЅРѕРіРѕ СЃРїСЂРѕСЃР°", layout="wide")

st.title("рџ“Љ РђРЅР°Р»РёР· РЅРµСѓРґРѕРІР»РµС‚РІРѕСЂС‘РЅРЅРѕРіРѕ СЃРїСЂРѕСЃР°")

# --------------------- Р¦РµРЅС‹ (СЃРѕРїРѕСЃС‚Р°РІР»РµРЅРёРµ) ---------------------
def get_price(product_name):
    """
    Р’РѕР·РІСЂР°С‰Р°РµС‚ С†РµРЅСѓ С‚РѕРІР°СЂР° РЅР° РѕСЃРЅРѕРІРµ РµРіРѕ РЅР°Р·РІР°РЅРёСЏ.
    РСЃРїРѕР»СЊР·СѓРµС‚ РєР»СЋС‡РµРІС‹Рµ СЃР»РѕРІР° Рё СЂРµРіСѓР»СЏСЂРЅС‹Рµ РІС‹СЂР°Р¶РµРЅРёСЏ.
    """
    product_lower = product_name.lower()
    
    # РЎРЅР°С‡Р°Р»Р° РёС‰РµРј С‚РѕС‡РЅС‹Рµ СЃРѕРІРїР°РґРµРЅРёСЏ РґР»СЏ С‡РµС…Р»РѕРІ
    if 'eligant' in product_lower:
        return 2490
    if 'urban' in product_lower:  # Urban, Urban+
        return 2990
    if 'clair' in product_lower:
        return 2990
    
    # Р—Р°СЂСЏРґРЅС‹Рµ СѓСЃС‚СЂРѕР№СЃС‚РІР°
    if 'balance' in product_lower:
        return 3490
    if 'pulse' in product_lower:
        return 4490
    
    # Powerbank
    if 'powerbank' in product_lower:
        # РћРїСЂРµРґРµР»СЏРµРј С‘РјРєРѕСЃС‚СЊ
        if '10 000' in product_lower or '10000' in product_lower:
            return 5990
        elif '5 000' in product_lower or '5000' in product_lower:
            return 4490
        else:
            # Р•СЃР»Рё С‘РјРєРѕСЃС‚СЊ РЅРµ СѓРєР°Р·Р°РЅР°, РІРѕР·РІСЂР°С‰Р°РµРј СЃСЂРµРґРЅСЋСЋ С†РµРЅСѓ
            return 5490
    
    # Р•СЃР»Рё РЅРёС‡РµРіРѕ РЅРµ РїРѕРґРѕС€Р»Рѕ вЂ“ С†РµРЅР° 0 (Р±СѓРґРµС‚ РІРёРґРЅРѕ, С‡С‚Рѕ РЅРµ Р·Р°РґР°РЅР°)
    return 0

# --------------------- РџР°СЂСЃРёРЅРі С„Р°Р№Р»Р° ---------------------
def parse_excel(file):
    df_raw = pd.read_excel(file, header=None, dtype=str)
    df_raw = df_raw.fillna('')
    start_indices = df_raw[df_raw[0].str.contains('РќРѕРјРµРЅРєР»Р°С‚СѓСЂР°', na=False)].index.tolist()
    if not start_indices:
        st.error("РќРµ РЅР°Р№РґРµРЅС‹ Р±Р»РѕРєРё СЃ 'РќРѕРјРµРЅРєР»Р°С‚СѓСЂР°'. РџСЂРѕРІРµСЂСЊС‚Рµ СЃС‚СЂСѓРєС‚СѓСЂСѓ С„Р°Р№Р»Р°.")
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
        data_rows = data_rows[~data_rows[0].str.contains('РС‚РѕРіРѕ', na=False)]
        for _, row in data_rows.iterrows():
            product_name = str(row[0]).strip()
            product_char = str(row[1]).strip()
            product = f"{product_name} | {product_char}" if product_char else product_name
            # РћРїСЂРµРґРµР»СЏРµРј С†РµРЅСѓ РґР»СЏ С‚РѕРІР°СЂР°
            price = get_price(product)
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
                    'stock': stock,
                    'price': price
                })
    if not records:
        st.error("РќРµ СѓРґР°Р»РѕСЃСЊ РёР·РІР»РµС‡СЊ РґР°РЅРЅС‹Рµ. РџСЂРѕРІРµСЂСЊС‚Рµ СЃС‚СЂСѓРєС‚СѓСЂСѓ С„Р°Р№Р»Р°.")
        return None
    df = pd.DataFrame(records)
    df['sales'] = df['sales'].astype(float)
    df['stock'] = df['stock'].astype(float)
    df['price'] = df['price'].astype(float)
    return df

# --------------------- Р Р°СЃС‡С‘С‚ РґРµС„РёС†РёС‚Р° ---------------------
def calculate_deficit(df):
    results = []
    for (city, product), group in df.groupby(['city', 'product']):
        available = group[group['stock'] > 0]
        if len(available) == 0:
            continue
        avg_demand = available['sales'].mean()
        if avg_demand <= 0:
            continue
        # Р‘РµСЂС‘Рј С†РµРЅСѓ РёР· РїРµСЂРІРѕР№ Р·Р°РїРёСЃРё (РѕРЅР° РґРѕР»Р¶РЅР° Р±С‹С‚СЊ РѕРґРёРЅР°РєРѕРІРѕР№ РґР»СЏ С‚РѕРІР°СЂР°)
        price = group.iloc[0]['price']
        for _, row in group.iterrows():
            day = row['day']
            stock = row['stock']
            deficit = avg_demand if stock == 0 else 0.0
            lost_revenue = deficit * price
            results.append({
                'city': city,
                'product': product,
                'day': day,
                'sales': row['sales'],
                'stock': stock,
                'avg_demand': avg_demand,
                'deficit': deficit,
                'price': price,
                'lost_revenue': lost_revenue
            })
    df_result = pd.DataFrame(results)
    if df_result.empty:
        return None, None
    total_deficit = df_result['deficit'].sum()
    total_lost_revenue = df_result['lost_revenue'].sum()
    by_product = df_result.groupby('product')['deficit'].sum().reset_index()
    by_city = df_result.groupby('city')['deficit'].sum().reset_index()
    # Р”РѕР±Р°РІРёРј СѓРїСѓС‰РµРЅРЅСѓСЋ РїСЂРёР±С‹Р»СЊ РїРѕ С‚РѕРІР°СЂР°Рј Рё РіРѕСЂРѕРґР°Рј РґР»СЏ РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹С… РіСЂР°С„РёРєРѕРІ
    lost_by_product = df_result.groupby('product')['lost_revenue'].sum().reset_index()
    lost_by_city = df_result.groupby('city')['lost_revenue'].sum().reset_index()
    days_with_deficit = df_result[df_result['deficit'] > 0].groupby('product')['day'].nunique().reset_index()
    days_with_deficit.columns = ['product', 'days_with_deficit']
    metrics = {
        'total_deficit': total_deficit,
        'total_lost_revenue': total_lost_revenue,
        'by_product': by_product,
        'by_city': by_city,
        'lost_by_product': lost_by_product,
        'lost_by_city': lost_by_city,
        'days_with_deficit': days_with_deficit
    }
    return df_result, metrics

# --------------------- РРЅС‚РµСЂС„РµР№СЃ ---------------------
uploaded_file = st.file_uploader("рџ“‚ Р—Р°РіСЂСѓР·РёС‚Рµ Excel-С„Р°Р№Р»", type=["xlsx"])

if uploaded_file:
    with st.spinner("РџР°СЂСЃРёРЅРі С„Р°Р№Р»Р°..."):
        df_data = parse_excel(uploaded_file)

    if df_data is not None:
        st.success(f"вњ… Р”Р°РЅРЅС‹Рµ Р·Р°РіСЂСѓР¶РµРЅС‹. {len(df_data)} Р·Р°РїРёСЃРµР№, РґРЅРё: {df_data['day'].min()} вЂ“ {df_data['day'].max()}")

        with st.expander("рџ“‹ РџСЂРµРґРїСЂРѕСЃРјРѕС‚СЂ РґР°РЅРЅС‹С…"):
            st.dataframe(df_data.head(100))

        with st.spinner("Р Р°СЃС‡С‘С‚ РґРµС„РёС†РёС‚Р°..."):
            df_deficit, metrics = calculate_deficit(df_data)

        if df_deficit is None:
            st.error("РќРµ СѓРґР°Р»РѕСЃСЊ СЂР°СЃСЃС‡РёС‚Р°С‚СЊ РґРµС„РёС†РёС‚: РЅРµС‚ РґРЅРµР№ СЃ РЅР°Р»РёС‡РёРµРј С‚РѕРІР°СЂР°.")
        else:
            st.success("вњ… Р Р°СЃС‡С‘С‚ РІС‹РїРѕР»РЅРµРЅ.")

            # ---- Р¤РёР»СЊС‚СЂС‹ ----
            st.sidebar.header("рџ”Ќ Р¤РёР»СЊС‚СЂС‹")
            cities = sorted(df_deficit['city'].unique())
            products = sorted(df_deficit['product'].unique())

            selected_city = st.sidebar.selectbox("Р“РѕСЂРѕРґ РґР»СЏ РґРµС‚Р°Р»СЊРЅРѕРіРѕ Р°РЅР°Р»РёР·Р°", ["Р’СЃРµ"] + cities)
            selected_product = st.sidebar.selectbox("РўРѕРІР°СЂ РґР»СЏ РґРµС‚Р°Р»СЊРЅРѕРіРѕ РіСЂР°С„РёРєР°", ["Р’СЃРµ"] + products)
            top_n_heat = st.sidebar.slider("РљРѕР»РёС‡РµСЃС‚РІРѕ С‚РѕРІР°СЂРѕРІ РЅР° С‚РµРїР»РѕРІРѕР№ РєР°СЂС‚Рµ", min_value=5, max_value=50, value=15)

            # ---- РћР±С‰РёРµ РјРµС‚СЂРёРєРё (СЃ СѓРїСѓС‰РµРЅРЅРѕР№ РїСЂРёР±С‹Р»СЊСЋ) ----
            total_def = metrics['total_deficit']
            total_lost = metrics['total_lost_revenue']
            total_days = df_deficit['day'].nunique()
            days_with_def = df_deficit[df_deficit['deficit'] > 0]['day'].nunique()
            n_products = df_deficit['product'].nunique()
            n_cities = df_deficit['city'].nunique()

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("РћР±С‰РёР№ РґРµС„РёС†РёС‚ (С€С‚)", f"{total_def:,.0f}")
            col2.metric("РЈРїСѓС‰РµРЅРЅР°СЏ РїСЂРёР±С‹Р»СЊ (СЂСѓР±.)", f"{total_lost:,.2f}")
            col3.metric("Р”РЅРµР№ СЃ РґРµС„РёС†РёС‚РѕРј", f"{days_with_def} РёР· {total_days}")
            col4.metric("РўРѕРІР°СЂРѕРІ СЃ РґРµС„РёС†РёС‚РѕРј", f"{n_products}")
            col5.metric("Р“РѕСЂРѕРґРѕРІ", f"{n_cities}")

            # ---- Р“Р РђР¤РРљР (С‚РµРјР° simple_white) ----
            st.subheader("рџЏ™пёЏ Р”РµС„РёС†РёС‚ РїРѕ РіРѕСЂРѕРґР°Рј")
            fig_city = px.bar(metrics['by_city'], x='city', y='deficit',
                              title="РЎСѓРјРјР°СЂРЅС‹Р№ РґРµС„РёС†РёС‚ РїРѕ РіРѕСЂРѕРґР°Рј (С€С‚)",
                              labels={'city': 'Р“РѕСЂРѕРґ', 'deficit': 'Р”РµС„РёС†РёС‚ (С€С‚)'},
                              color='deficit', color_continuous_scale='Reds')
            fig_city.update_layout(template='simple_white')
            st.plotly_chart(fig_city, width='stretch')

            # ---- Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Р№ РіСЂР°С„РёРє: РЈРїСѓС‰РµРЅРЅР°СЏ РїСЂРёР±С‹Р»СЊ РїРѕ РіРѕСЂРѕРґР°Рј ----
            st.subheader("рџ’° РЈРїСѓС‰РµРЅРЅР°СЏ РїСЂРёР±С‹Р»СЊ РїРѕ РіРѕСЂРѕРґР°Рј")
            fig_lost_city = px.bar(metrics['lost_by_city'], x='city', y='lost_revenue',
                                   title="РЈРїСѓС‰РµРЅРЅР°СЏ РїСЂРёР±С‹Р»СЊ РїРѕ РіРѕСЂРѕРґР°Рј (СЂСѓР±.)",
                                   labels={'city': 'Р“РѕСЂРѕРґ', 'lost_revenue': 'РЈРїСѓС‰РµРЅРЅР°СЏ РїСЂРёР±С‹Р»СЊ (СЂСѓР±.)'},
                                   color='lost_revenue', color_continuous_scale='Reds')
            fig_lost_city.update_layout(template='simple_white')
            st.plotly_chart(fig_lost_city, width='stretch')

            st.subheader("рџ“¦ Р”РµС„РёС†РёС‚ РїРѕ С‚РѕРІР°СЂР°Рј (С‚РѕРї-10)")
            top_products = metrics['by_product'].nlargest(10, 'deficit')
            fig_prod = px.bar(top_products, x='deficit', y='product',
                              orientation='h',
                              title="РўРѕРї-10 С‚РѕРІР°СЂРѕРІ РїРѕ РґРµС„РёС†РёС‚Сѓ (С€С‚)",
                              labels={'deficit': 'Р”РµС„РёС†РёС‚ (С€С‚)', 'product': 'РўРѕРІР°СЂ'},
                              color='deficit', color_continuous_scale='Reds')
            fig_prod.update_layout(yaxis={'categoryorder': 'total ascending'}, template='simple_white')
            st.plotly_chart(fig_prod, width='stretch')

            st.subheader("рџ“… РљРѕР»РёС‡РµСЃС‚РІРѕ РґРЅРµР№ СЃ РґРµС„РёС†РёС‚РѕРј РїРѕ С‚РѕРІР°СЂР°Рј")
            days_def = metrics['days_with_deficit'].nlargest(15, 'days_with_deficit')
            fig_days = px.bar(days_def, x='days_with_deficit', y='product',
                              orientation='h',
                              title="РўРѕРї-15 С‚РѕРІР°СЂРѕРІ РїРѕ РєРѕР»РёС‡РµСЃС‚РІСѓ РґРЅРµР№ СЃ РґРµС„РёС†РёС‚РѕРј",
                              labels={'days_with_deficit': 'Р”РЅРµР№ СЃ РґРµС„РёС†РёС‚РѕРј', 'product': 'РўРѕРІР°СЂ'},
                              color='days_with_deficit', color_continuous_scale='Oranges')
            fig_days.update_layout(yaxis={'categoryorder': 'total ascending'}, template='simple_white')
            st.plotly_chart(fig_days, width='stretch')

            st.subheader("рџ”Ґ РўРµРїР»РѕРІР°СЏ РєР°СЂС‚Р° РґРµС„РёС†РёС‚Р° (С‚РѕРІР°СЂС‹ Г— РіРѕСЂРѕРґР°)")
            heat_data = df_deficit.groupby(['product', 'city'])['deficit'].sum().reset_index()
            top_products_heat = heat_data.groupby('product')['deficit'].sum().nlargest(top_n_heat).index
            heat_data_filtered = heat_data[heat_data['product'].isin(top_products_heat)]
            if not heat_data_filtered.empty:
                pivot = heat_data_filtered.pivot(index='product', columns='city', values='deficit').fillna(0)
                fig_heat = px.imshow(pivot, text_auto=True, aspect="auto",
                                     color_continuous_scale='Reds',
                                     title=f"Р”РµС„РёС†РёС‚ РїРѕ С‚РѕРІР°СЂР°Рј (С‚РѕРї-{top_n_heat}) Рё РіРѕСЂРѕРґР°Рј (С€С‚)")
                fig_heat.update_layout(height=600, template='simple_white')
                st.plotly_chart(fig_heat, width='stretch')
            else:
                st.info("РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РґР°РЅРЅС‹С… РґР»СЏ С‚РµРїР»РѕРІРѕР№ РєР°СЂС‚С‹.")

            st.subheader("рџ“† Р”РµС„РёС†РёС‚ РїРѕ С‚РѕРІР°СЂР°Рј РІ РІС‹Р±СЂР°РЅРЅРѕРј РіРѕСЂРѕРґРµ (РїРѕ РґРЅСЏРј)")
            city_for_daily = st.selectbox("Р’С‹Р±РµСЂРёС‚Рµ РіРѕСЂРѕРґ РґР»СЏ РѕС‚РѕР±СЂР°Р¶РµРЅРёСЏ РґРµС„РёС†РёС‚Р° РїРѕ РґРЅСЏРј", cities)
            df_city = df_deficit[df_deficit['city'] == city_for_daily]
            if not df_city.empty:
                pivot_daily = df_city.pivot(index='product', columns='day', values='deficit').fillna(0)
                products_with_deficit = pivot_daily.sum(axis=1)
                products_with_deficit = products_with_deficit[products_with_deficit > 0]
                if len(products_with_deficit) > 0:
                    top_products_daily = products_with_deficit.nlargest(min(30, len(products_with_deficit))).index
                    pivot_daily = pivot_daily.loc[top_products_daily]
                else:
                    st.warning(f"Р’ РіРѕСЂРѕРґРµ {city_for_daily} РЅРµС‚ РґРµС„РёС†РёС‚Р° РЅРё РїРѕ РѕРґРЅРѕРјСѓ С‚РѕРІР°СЂСѓ.")
                    pivot_daily = pd.DataFrame()
                if not pivot_daily.empty:
                    pivot_daily['total'] = pivot_daily.sum(axis=1)
                    pivot_daily = pivot_daily.sort_values('total', ascending=False).drop(columns='total')
                    fig_daily_heat = px.imshow(pivot_daily, text_auto=True, aspect="auto",
                                               color_continuous_scale='Reds',
                                               title=f"Р”РµС„РёС†РёС‚ (С€С‚) РїРѕ РґРЅСЏРј вЂ“ РіРѕСЂРѕРґ {city_for_daily}",
                                               labels={'product': 'РўРѕРІР°СЂ', 'day': 'Р”РµРЅСЊ РјРµСЃСЏС†Р°', 'color': 'Р”РµС„РёС†РёС‚ (С€С‚)'})
                    fig_daily_heat.update_layout(height=max(400, 30*len(pivot_daily)), template='simple_white')
                    st.plotly_chart(fig_daily_heat, width='stretch')
                    non_zero = df_city[df_city['deficit'] > 0]
                    if not non_zero.empty:
                        st.subheader(f"рџ“‹ Р”РЅРё СЃ РґРµС„РёС†РёС‚РѕРј РІ РіРѕСЂРѕРґРµ {city_for_daily}")
                        st.dataframe(non_zero[['product', 'day', 'deficit']].sort_values(['product', 'day']))
                else:
                    st.info("РќРµС‚ РґР°РЅРЅС‹С… РґР»СЏ РѕС‚РѕР±СЂР°Р¶РµРЅРёСЏ С‚РµРїР»РѕРІРѕР№ РєР°СЂС‚С‹ РїРѕ РґРЅСЏРј.")
            else:
                st.warning(f"РќРµС‚ РґР°РЅРЅС‹С… РґР»СЏ РіРѕСЂРѕРґР° {city_for_daily}.")

            if selected_product != "Р’СЃРµ":
                st.subheader(f"рџ“‰ Р”РµС‚Р°Р»СЊРЅС‹Р№ РіСЂР°С„РёРє: {selected_product}")
                filtered = df_deficit[df_deficit['product'] == selected_product]
                if selected_city != "Р’СЃРµ":
                    filtered = filtered[filtered['city'] == selected_city]
                    city_label = f" РІ РіРѕСЂРѕРґРµ {selected_city}"
                else:
                    city_label = " (РІСЃРµ РіРѕСЂРѕРґР°)"
                if not filtered.empty:
                    daily = filtered.groupby('day').agg({
                        'stock': 'sum',
                        'deficit': 'sum',
                        'sales': 'sum'
                    }).reset_index()
                    fig_det = go.Figure()
                    fig_det.add_trace(go.Scatter(x=daily['day'], y=daily['stock'],
                                                 mode='lines+markers', name='РћСЃС‚Р°С‚РѕРє'))
                    fig_det.add_trace(go.Scatter(x=daily['day'], y=daily['sales'],
                                                 mode='lines+markers', name='РџСЂРѕРґР°Р¶Рё'))
                    fig_det.add_trace(go.Bar(x=daily['day'], y=daily['deficit'],
                                             name='Р”РµС„РёС†РёС‚', marker_color='red'))
                    fig_det.update_layout(title=f"РћСЃС‚Р°С‚РєРё, РїСЂРѕРґР°Р¶Рё Рё РґРµС„РёС†РёС‚ вЂ“ {selected_product}{city_label}",
                                          xaxis_title='Р”РµРЅСЊ РјРµСЃСЏС†Р°', yaxis_title='РљРѕР»РёС‡РµСЃС‚РІРѕ (С€С‚)',
                                          template='simple_white')
                    st.plotly_chart(fig_det, width='stretch')
                    st.dataframe(daily)
                else:
                    st.warning("РќРµС‚ РґР°РЅРЅС‹С… РґР»СЏ РІС‹Р±СЂР°РЅРЅРѕРіРѕ С‚РѕРІР°СЂР° Рё РіРѕСЂРѕРґР°.")

            st.subheader("рџ“‹ Р”РµС‚Р°Р»СЊРЅР°СЏ С‚Р°Р±Р»РёС†Р° РґРµС„РёС†РёС‚Р° РїРѕ РґРЅСЏРј")
            detail = df_deficit.groupby(['city', 'product', 'day']).agg({
                'sales': 'sum',
                'stock': 'sum',
                'avg_demand': 'first',
                'deficit': 'sum',
                'price': 'first',
                'lost_revenue': 'sum'
            }).reset_index()
            st.dataframe(detail)

            def to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Р РµР·СѓР»СЊС‚Р°С‚', index=False)
                return output.getvalue()

            excel_data = to_excel(detail)
            st.download_button(
                label="рџ“Ґ РЎРєР°С‡Р°С‚СЊ СЂРµР·СѓР»СЊС‚Р°С‚ (Excel)",
                data=excel_data,
                file_name="СЂРµР·СѓР»СЊС‚Р°С‚_Р°РЅР°Р»РёР·Р°.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.error("РќРµ СѓРґР°Р»РѕСЃСЊ РѕР±СЂР°Р±РѕС‚Р°С‚СЊ С„Р°Р№Р». РџСЂРѕРІРµСЂСЊС‚Рµ С„РѕСЂРјР°С‚.")
else:
    st.info("рџ‘€ Р—Р°РіСЂСѓР·РёС‚Рµ Excel-С„Р°Р№Р» РґР»СЏ РЅР°С‡Р°Р»Р° Р°РЅР°Р»РёР·Р°.")
