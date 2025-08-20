import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------ ÖRNEK VERİ ------------------
data = {
    "Tarih": ["2025-08-19"],
    "İsim": ["Armut"],
    "Öğün": ["Kahvaltı"],
    "Miktar (g)": [100],
    "Kalori": [57],
    "Protein (g)": [0.4],
    "Karbonhidrat (g)": [15],
    "Yağ (g)": [0.2]
}
df = pd.DataFrame(data)

# ------------------ SAYFA AYARLARI ------------------
st.set_page_config(page_title="Beslenme Takibi", layout="wide")
st.title("🍽️ Seçilen Besin Değerleri")

# ------------------ KART GÖRÜNÜMÜ ------------------
st.subheader("📋 Besin Özeti")
col1, col2, col3, col4 = st.columns(4)

col1.metric("🗓️ Tarih", df["Tarih"].iloc[0])
col2.metric("🍎 Besin", df["İsim"].iloc[0])
col3.metric("🍽️ Öğün", df["Öğün"].iloc[0])
col4.metric("⚖️ Miktar", f"{df['Miktar (g)'].iloc[0]} g")

# ------------------ DETAY TABLO ------------------
st.subheader("📑 Detaylı Besin Bilgisi")
st.dataframe(df.style.format(precision=2), use_container_width=True)

# ------------------ MAKRO GRAFİKLER ------------------
st.subheader("📊 Makro Dağılımı")

makro_df = pd.DataFrame({
    "Makro": ["Protein", "Karbonhidrat", "Yağ"],
    "Miktar (g)": [
        df["Protein (g)"].iloc[0],
        df["Karbonhidrat (g)"].iloc[0],
        df["Yağ (g)"].iloc[0]
    ]
})

col_a, col_b = st.columns(2)

# Bar chart
with col_a:
    bar_fig = px.bar(
        makro_df,
        x="Makro",
        y="Miktar (g)",
        text="Miktar (g)",
        color="Makro",
        title="Makro Dağılımı (g)",
    )
    bar_fig.update_traces(textposition="outside")
    st.plotly_chart(bar_fig, use_container_width=True)

# Pie chart
with col_b:
    pie_fig = px.pie(
        makro_df,
        names="Makro",
        values="Miktar (g)",
        title="Makro Yüzdesi",
        hole=0.4  # donut görünümü
    )
    st.plotly_chart(pie_fig, use_container_width=True)
