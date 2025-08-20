import streamlit as st
import pandas as pd
from openai import OpenAI

# OpenAI client (API anahtarını secrets'ten al)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Sayfa ayarları
st.set_page_config(page_title="🥗 Akıllı Beslenme Asistanı", page_icon="🍎")

st.title("🥗 Akıllı Beslenme Asistanı")
st.write("Öğününü seç, yiyeceğini seç, gramını gir 👇")

# Besin verilerini yükle
@st.cache_data
def load_foods():
    return pd.read_csv("foods.csv")

foods = load_foods()

# Öğün seç
meal = st.selectbox("🍽 Öğün Seç", ["Sabah", "Öğle", "Akşam", "Ara Öğün"])

# Yiyecek seç
food = st.selectbox("🥑 Yiyecek Seç", foods["isim"].tolist())

# Gram gir
amount = st.number_input("⚖️ Miktar (gram)", min_value=1, value=100)

# Seçilen yiyeceğin değerlerini getir
food_row = foods[foods["isim"] == food].iloc[0]
cal = food_row["kalori"] * amount / 100
prot = food_row["protein"] * amount / 100
carb = food_row["karbonhidrat"] * amount / 100
fat = food_row["yag"] * amount / 100

# Günlük öğünleri sakla
if "meals" not in st.session_state:
    st.session_state["meals"] = []

if st.button("➕ Ekle"):
    st.session_state["meals"].append({
        "Öğün": meal,
        "Yiyecek": food,
        "Gram": amount,
        "Kalori": cal,
        "Protein": prot,
        "Karbonhidrat": carb,
        "Yağ": fat
    })
    st.success(f"{meal} öğününe {amount}g {food} eklendi ✅")

# Günlük öğün tablosu
if st.session_state["meals"]:
    df = pd.DataFrame(st.session_state["meals"])
    st.subheader("📋 Günlük Öğünler")
    st.dataframe(df)

    st.subheader("📊 Günlük Toplam Değerler")
    totals = df[["Kalori", "Protein", "Karbonhidrat", "Yağ"]].sum()
    st.write(totals)

    # OpenAI'den öneri al
    if st.button("🤖 Yapay Zeka Önerisi Al"):
        with st.spinner("Öneriler hazırlanıyor..."):
            messages = [
                {"role": "system", "content": "Sen bir beslenme uzmanısın."},
                {"role": "user", "content": f"Bugünkü beslenme değerlerim: {totals.to_dict()}. Bana sağlıklı öneriler ver."}
            ]
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            advice = response.choices[0].message.content
            st.success(advice)
