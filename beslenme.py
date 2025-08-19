import streamlit as st
import pandas as pd
import os
import datetime
import matplotlib.pyplot as plt

# ===================== 📂 Veri Dosyası =====================
CSV_FILE = "yiyecekler.csv"
LOG_FILE = "gunluk_kayitlar.csv"

# Eğer yiyecekler.csv yoksa örnek dosya oluştur
if not os.path.exists(CSV_FILE):
    sample_data = """isim,kalori,protein,karbonhidrat,yag
Armut,57,0.4,15,0.2
Ayva,57,0.4,15,0.1
Badem,579,21,22,50
Bal,304,0.3,82,0
Balık (somon),208,20,0,13
Tavuk Göğsü,165,31,0,3.6
Pirinç,130,2.7,28,0.3
Ekmek,265,9,49,3.2
"""
    with open(CSV_FILE, "w", encoding="utf-8") as f:
        f.write(sample_data)

# ===================== 📊 Veriyi Oku =====================
foods = pd.read_csv(CSV_FILE)
for col in ["kalori", "protein", "karbonhidrat", "yag"]:
    foods[col] = pd.to_numeric(foods[col], errors="coerce")

# ===================== 🖥️ Streamlit =====================
st.set_page_config(page_title="🥗 Beslenme Asistanı", page_icon="🥑", layout="centered")

# Arka plan beyaz
st.markdown(
    """
    <style>
        .stApp { background-color: white; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🥗 Akıllı Beslenme Asistanı")
st.write("Öğününü seç, yiyeceğini seç, gramını gir 👇")

# Kullanıcı oturumu
if "meals" not in st.session_state:
    st.session_state.meals = {"Sabah": [], "Öğle": [], "Akşam": [], "Ara Öğün": []}

# ===================== 🍽️ Öğün Seçimi =====================
meal = st.selectbox("🍽 Öğün Seç", ["Sabah", "Öğle", "Akşam", "Ara Öğün"])

# ===================== 🥑 Yiyecek Seçimi =====================
food_name = st.selectbox("🥑 Yiyecek Seç", foods["isim"].tolist())

# ===================== ⚖️ Gramaj =====================
amount = st.number_input("⚖️ Miktar (gram)", min_value=1, value=100, step=10)

# ===================== ➕ Ekle Butonu =====================
if st.button("➕ Ekle"):
    selected_food = foods[foods["isim"] == food_name].iloc[0]
    factor = amount / 100

    cal = selected_food["kalori"] * factor
    prot = selected_food["protein"] * factor
    carb = selected_food["karbonhidrat"] * factor
    fat = selected_food["yag"] * factor

    st.session_state.meals[meal].append({
        "isim": food_name,
        "gram": amount,
        "kalori": round(cal, 2),
        "protein": round(prot, 2),
        "karbonhidrat": round(carb, 2),
        "yag": round(fat, 2)
    })

    st.success(f"✅ {meal} öğününe {amount} g {food_name} eklendi!")
    st.balloons()  # 🎉 Konfeti yerine balon animasyonu

# ===================== 📋 Öğünleri Göster =====================
st.header("📋 Günlük Öğünler")

total_kcal, total_prot, total_carb, total_fat = 0, 0, 0, 0

for m, items in st.session_state.meals.items():
    if items:
        st.subheader(f"🍽 {m} Öğünü")
        df = pd.DataFrame(items)
        st.table(df)

        total_kcal += df["kalori"].sum()
        total_prot += df["protein"].sum()
        total_carb += df["karbonhidrat"].sum()
        total_fat += df["yag"].sum()

# ===================== 🔢 Günlük Toplam =====================
st.header("📊 Günlük Toplam Değerler")

totals = pd.DataFrame([{
    "Kalori": round(total_kcal, 2),
    "Protein": round(total_prot, 2),
    "Karbonhidrat": round(total_carb, 2),
    "Yağ": round(total_fat, 2)
}])
st.table(totals)

# ❤️ Kalp atışı animasyonu
st.markdown(
    """
    <div style="text-align:center; font-size:40px; animation: pulse 1s infinite;">
        ❤️
    </div>
    <style>
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.3); }
            100% { transform: scale(1); }
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ===================== 🎯 Günlük Hedef =====================
DAILY_KCAL_TARGET = 2000
progress = min(total_kcal / DAILY_KCAL_TARGET, 1.0)
st.subheader("🎯 Günlük Kalori Hedefi")
st.progress(progress)

# ===================== 📊 Grafik =====================
if total_kcal > 0:
    labels = ["Protein", "Karbonhidrat", "Yağ"]
    values = [total_prot, total_carb, total_fat]

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title("Makro Dağılımı")
    st.pyplot(fig)

# ===================== 💾 Günlük Kayıtları CSV'ye Kaydet =====================
today = datetime.date.today().isoformat()

if total_kcal > 0:
    log_df = pd.DataFrame([{
        "Tarih": today,
        "Kalori": round(total_kcal, 2),
        "Protein": round(total_prot, 2),
        "Karbonhidrat": round(total_carb, 2),
        "Yağ": round(total_fat, 2)
    }])
    if os.path.exists(LOG_FILE):
        old = pd.read_csv(LOG_FILE)
        log_df = pd.concat([old, log_df]).drop_duplicates(subset=["Tarih"], keep="last")
    log_df.to_csv(LOG_FILE, index=False)

    st.success("📅 Günlük kayıt kaydedildi!")

# ===================== 🚪 Çıkış / Reset =====================
if st.button("🗑️ Günlük Verileri Sıfırla"):
    st.session_state.meals = {"Sabah": [], "Öğle": [], "Akşam": [], "Ara Öğün": []}
    st.rerun()
