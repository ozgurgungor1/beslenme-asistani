# beslenme.py
import os
import json
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- Opsiyonel bağımlılıklar (zarifçe devre dışı bırak) ----------
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    HAS_PDF = True
except Exception:
    HAS_PDF = False

try:
    from openai import OpenAI
    OPENAI_KEY = os.getenv("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")
    client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
except Exception:
    client = None
    OPENAI_KEY = None

# ---------- Dosyalar ----------
FOODS_CSV = "yiyecekler.csv"  # 100 g bazlı besin değerleri
TODAY = datetime.now().strftime("%Y-%m-%d")
DAILY_CSV = f"gunluk_kayit_{TODAY}.csv"  # tarih bazlı günlük log

# ---------- Yiyecek CSV yoksa küçük bir örnek üret ----------
if not os.path.exists(FOODS_CSV):
    sample = """isim,kalori,protein,karbonhidrat,yag
Armut,57,0.4,15,0.2
Ayva,57,0.4,15,0.1
Badem,579,21,22,50
Bal,304,0.3,82,0
Somon,208,20,0,13
Tavuk Göğsü,165,31,0,3.6
Pirinç (pişmiş),130,2.7,28,0.3
Ekmek (beyaz),265,9,49,3.2
Yumurta,155,13,1.1,11
Yoğurt (light),59,10,3.6,0.4
"""
    with open(FOODS_CSV, "w", encoding="utf-8") as f:
        f.write(sample)

# ---------- Veri yükleme ----------
foods = pd.read_csv(FOODS_CSV)
foods_columns = ["kalori", "protein", "karbonhidrat", "yag"]
for c in foods_columns:
    foods[c] = pd.to_numeric(foods[c], errors="coerce")

# ---------- Streamlit ayarları ----------
st.set_page_config(page_title="🥗 Akıllı Beslenme Asistanı", page_icon="🥗", layout="wide")

# ---------- Session state ----------
if "meals" not in st.session_state:
    # Eğer günlük CSV varsa ordan yükle
    if os.path.exists(DAILY_CSV):
        tmp = pd.read_csv(DAILY_CSV)
        meals = {"Sabah": [], "Öğle": [], "Akşam": [], "Ara Öğün": []}
        for _, r in tmp.iterrows():
            meals[str(r["Öğün"])].append({
                "isim": r["isim"],
                "gram": float(r["gram"]),
                "kalori": float(r["kalori"]),
                "protein": float(r["protein"]),
                "karbonhidrat": float(r["karbonhidrat"]),
                "yag": float(r["yag"]),
            })
        st.session_state.meals = meals
    else:
        st.session_state.meals = {"Sabah": [], "Öğle": [], "Akşam": [], "Ara Öğün": []}

if "profile" not in st.session_state:
    st.session_state.profile = {
        "boy_cm": 175,
        "kilo_kg": 80,
        "yas": 28,
        "cinsiyet": "Erkek",
        "aktivite": "Orta (1.55)",
        "hedef": "Kilo Ver (-500 kcal/gün)",
    }

# ---------- Yardımcı fonksiyonlar ----------
def save_daily_csv():
    rows = []
    for meal, items in st.session_state.meals.items():
        for it in items:
            rows.append({
                "Tarih": TODAY,
                "Öğün": meal,
                "isim": it["isim"],
                "gram": float(it["gram"]),
                "kalori": float(it["kalori"]),
                "protein": float(it["protein"]),
                "karbonhidrat": float(it["karbonhidrat"]),
                "yag": float(it["yag"]),
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df.to_csv(DAILY_CSV, index=False)

def totals():
    t = {"kalori": 0.0, "protein": 0.0, "karbonhidrat": 0.0, "yag": 0.0}
    for items in st.session_state.meals.values():
        for it in items:
            t["kalori"] += float(it["kalori"])
            t["protein"] += float(it["protein"])
            t["karbonhidrat"] += float(it["karbonhidrat"])
            t["yag"] += float(it["yag"])
    return t

def mifflin_st_jeor(cm, kg, yas, cinsiyet):
    # cinsiyet: Erkek +5, Kadın -161
    s = 5 if cinsiyet == "Erkek" else -161
    return 10 * kg + 6.25 * cm - 5 * yas + s

def aktivite_carpani(label):
    return {
        "Düşük (1.2)": 1.2,
        "Hafif (1.375)": 1.375,
        "Orta (1.55)": 1.55,
        "Yüksek (1.725)": 1.725,
        "Atletik (1.9)": 1.9,
    }.get(label, 1.55)

def hedef_ayari_label_to_delta(label):
    return {
        "Kilo Ver (-500 kcal/gün)": -500,
        "Koru (0 kcal/gün)": 0,
        "Kilo Al (+300 kcal/gün)": +300,
    }.get(label, -500)

def add_food_to_meal(meal_name, food_name, gram):
    row = foods.loc[foods["isim"] == food_name].iloc[0]
    factor = float(gram) / 100.0
    item = {
        "isim": food_name,
        "gram": float(gram),
        "kalori": round(float(row["kalori"]) * factor, 2),
        "protein": round(float(row["protein"]) * factor, 2),
        "karbonhidrat": round(float(row["karbonhidrat"]) * factor, 2),
        "yag": round(float(row["yag"]) * factor, 2),
    }
    st.session_state.meals[meal_name].append(item)
    save_daily_csv()

def build_meals_dataframe():
    rows = []
    for meal, items in st.session_state.meals.items():
        for idx, it in enumerate(items):
            r = it.copy()
            r["Öğün"] = meal
            r["_row_id"] = f"{meal}|{idx}"
            rows.append(r)
    df = pd.DataFrame(rows, columns=["_row_id","Öğün","isim","gram","kalori","protein","karbonhidrat","yag"])
    return df

def update_meals_from_dataframe(df_edited):
    # df_edited: gram değişmişse yeniden hesapla
    # Önce tüm öğünleri temizle sonra yeniden doldur
    new_state = {"Sabah": [], "Öğle": [], "Akşam": [], "Ara Öğün": []}
    for _, r in df_edited.iterrows():
        meal = str(r["Öğün"])
        food = str(r["isim"])
        gram = float(r["gram"])
        row = foods.loc[foods["isim"] == food]
        if row.empty:
            # listede yoksa direct değerleri kullan
            item = {
                "isim": food,
                "gram": gram,
                "kalori": float(r["kalori"]),
                "protein": float(r["protein"]),
                "karbonhidrat": float(r["karbonhidrat"]),
                "yag": float(r["yag"]),
            }
        else:
            base = row.iloc[0]
            factor = gram / 100.0
            item = {
                "isim": food,
                "gram": gram,
                "kalori": round(float(base["kalori"]) * factor, 2),
                "protein": round(float(base["protein"]) * factor, 2),
                "karbonhidrat": round(float(base["karbonhidrat"]) * factor, 2),
                "yag": round(float(base["yag"]) * factor, 2),
            }
        if meal not in new_state:
            meal = "Ara Öğün"
        new_state[meal].append(item)
    st.session_state.meals = new_state
    save_daily_csv()

def generate_pdf(path, profile, total_dict, df_all):
    if not HAS_PDF:
        return None
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Günlük Beslenme Raporu", styles["Title"]))
    story.append(Spacer(1, 12))
    ptxt = (
        f"Tarih: {TODAY}<br/>"
        f"Boy: {profile['boy_cm']} cm, Kilo: {profile['kilo_kg']} kg, Yaş: {profile['yas']}<br/>"
        f"Cinsiyet: {profile['cinsiyet']}, Aktivite: {profile['aktivite']}, Hedef: {profile['hedef']}"
    )
    story.append(Paragraph(ptxt, styles["Normal"]))
    story.append(Spacer(1, 12))

    # Toplamlar
    tt = [
        ["Kalori (kcal)", "Protein (g)", "Karbonhidrat (g)", "Yağ (g)"],
        [
            f"{total_dict['kalori']:.2f}",
            f"{total_dict['protein']:.2f}",
            f"{total_dict['karbonhidrat']:.2f}",
            f"{total_dict['yag']:.2f}",
        ],
    ]
    t1 = Table(tt)
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ALIGN", (0,0), (-1,-1), "CENTER")
    ]))
    story.append(t1)
    story.append(Spacer(1, 12))

    # Detay tablo
    if not df_all.empty:
        headers = ["Öğün","Yiyecek","Gram","Kalori","Protein","Karbonhidrat","Yağ"]
        data = [headers]
        for _, r in df_all.iterrows():
            data.append([
                str(r["Öğün"]), str(r["isim"]), f"{float(r['gram']):.0f}",
                f"{float(r['kalori']):.2f}", f"{float(r['protein']):.2f}",
                f"{float(r['karbonhidrat']):.2f}", f"{float(r['yag']):.2f}",
            ])
        t2 = Table(data, repeatRows=1)
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("ALIGN", (2,1), (-1,-1), "RIGHT"),
        ]))
        story.append(t2)

    doc.build(story)
    return path

# ========================= ÜST KISIM: AI ÖNERİ & PROFİL =========================
st.title("🥗 Akıllı Beslenme Asistanı")

with st.expander("🤖 Yapay Zeka Diyet Önerisi (GPT)", expanded=True):
    col_ai1, col_ai2 = st.columns([3, 1])
    with col_ai1:
        st.caption("Güncel öğünlerine, boy-kilo ve hedef bilgilerine göre öneri üretir.")
    with col_ai2:
        if client:
            st.success("API hazır ✅")
        else:
            st.info("OPENAI_API_KEY bulunamadı. Ortama ekleyin veya Streamlit Secrets kullanın.")

    if st.button("✨ Öneri Al"):
        df_all = build_meals_dataframe()
        t = totals()
        if client is None:
            st.warning("Öneri için API anahtarı gerekli.")
        elif df_all.empty:
            st.warning("Önce öğün ekle!")
        else:
            profile = st.session_state.profile
            yemekler = [f"{r['Öğün']}: {r['isim']} {float(r['gram']):.0f} g" for _, r in df_all.iterrows()]
            yemek_listesi = "\n".join(yemekler)

            prompt = f"""
Sen profesyonel bir diyetisyensin.
Kullanıcı profili:
- Boy: {profile['boy_cm']} cm
- Kilo: {profile['kilo_kg']} kg
- Yaş: {profile['yas']}
- Cinsiyet: {profile['cinsiyet']}
- Aktivite: {profile['aktivite']}
- Hedef: {profile['hedef']}

Bugünkü öğünleri:
{yemek_listesi}

Toplam makrolar (bugüne kadar):
- Kalori: {t['kalori']:.0f} kcal
- Protein: {t['protein']:.1f} g
- Karbonhidrat: {t['karbonhidrat']:.1f} g
- Yağ: {t['yag']:.1f} g

İstediğim:
1) Hangi yiyeceklerden yaklaşık ne kadar eklenmeli/azaltılmalı (pratik öneri).
2) Günlük hedef kaloriye göre gün sonu öneri makro dağılımı.
3) Bu planla 1 ayda tahmini kilo değişimi (makul aralıkla).
4) 3 kısa madde halinde sürdürülebilirlik ipucu.
"""
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Kısa, net ve uygulanabilir yaz."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.5,
                )
                st.success("📌 Öneri")
                st.write(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"API hatası: {e}")

# Profil & hedef (sidebar)
with st.sidebar:
    st.header("👤 Profil & Hedef")
    p = st.session_state.profile
    p["boy_cm"] = st.number_input("Boy (cm)", 100, 230, value=int(p["boy_cm"]), step=1)
    p["kilo_kg"] = st.number_input("Kilo (kg)", 30, 250, value=int(p["kilo_kg"]), step=1)
    p["yas"] = st.number_input("Yaş", 10, 100, value=int(p["yas"]), step=1)
    p["cinsiyet"] = st.selectbox("Cinsiyet", ["Erkek", "Kadın"], index=0 if p["cinsiyet"]=="Erkek" else 1)
    p["aktivite"] = st.selectbox("Aktivite Seviyesi",
                                 ["Düşük (1.2)", "Hafif (1.375)", "Orta (1.55)", "Yüksek (1.725)", "Atletik (1.9)"],
                                 index=["Düşük (1.2)","Hafif (1.375)","Orta (1.55)","Yüksek (1.725)","Atletik (1.9)"].index(p["aktivite"]))
    p["hedef"] = st.selectbox("Hedef", ["Kilo Ver (-500 kcal/gün)", "Koru (0 kcal/gün)", "Kilo Al (+300 kcal/gün)"],
                              index=["Kilo Ver (-500 kcal/gün)","Koru (0 kcal/gün)","Kilo Al (+300 kcal/gün)"].index(p["hedef"]))
    st.session_state.profile = p

# Hedef kalori hesap
BMR = mifflin_st_jeor(st.session_state.profile["boy_cm"], st.session_state.profile["kilo_kg"],
                      st.session_state.profile["yas"], st.session_state.profile["cinsiyet"])
TDEE = BMR * aktivite_carpani(st.session_state.profile["aktivite"])
daily_target = max(1200, TDEE + hedef_ayari_label_to_delta(st.session_state.profile["hedef"]))  # minimum güvenlik

# ========================= ORTA KISIM: ÖĞÜN YÖNETİMİ =========================
st.subheader("🍽️ Öğün Ekle")
col1, col2, col3, col4 = st.columns([1.1, 2.4, 1.1, 0.8])
with col1:
    meal = st.selectbox("Öğün", ["Sabah", "Öğle", "Akşam", "Ara Öğün"])
with col2:
    food_name = st.selectbox("Yiyecek", foods["isim"].tolist())
with col3:
    gram = st.number_input("Gram", min_value=1, value=100, step=10)
with col4:
    if st.button("➕ Ekle", use_container_width=True):
        add_food_to_meal(meal, food_name, gram)
        st.success(f"{meal} → {food_name} ({gram} g) eklendi.")

# Tüm öğünleri tek tabloda göster + düzenleme / silme
st.subheader("📋 Günlük Öğünler")
df_all = build_meals_dataframe()
if df_all.empty:
    st.info("Henüz öğün eklemedin.")
else:
    # Düzenleme: gram, öğün değiştirilebilir
    edited = st.data_editor(
        df_all[["Öğün","isim","gram","kalori","protein","karbonhidrat","yag"]],
        use_container_width=True,
        num_rows="dynamic",
        disabled=["kalori","protein","karbonhidrat","yag","isim"],  # ismi kilitli; gram/öğün serbest
        column_config={
            "gram": st.column_config.NumberColumn("Gram", step=10, min_value=1),
        },
        key="editor",
    )

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("💾 Güncelle (yeniden hesapla)"):
            # edited DataFrame'e _row_id yok; orijinalden isim/öğün/gram alıp güncelle
            # Burada edited zaten ÖĞÜN & GRAM değerleri içeriyor; isim sabit.
            # Recompute by merging isim-öğün-gram
            edited2 = edited.copy()
            update_meals_from_dataframe(edited2)
            st.success("Güncellendi.")
    with c2:
        # Silme: seçili satırları silmek için çok basit bir yol
        del_idx = st.multiselect("Silmek için satır seç", edited.index.tolist(), [])
        if st.button("🗑️ Seçilenleri Sil"):
            keep = edited.loc[~edited.index.isin(del_idx)].copy()
            update_meals_from_dataframe(keep)
            st.success("Seçilenler silindi.")

# ========================= SAĞ TARAF: ÖZET & GRAFİK =========================
t = totals()
right_col1, right_col2, right_col3, right_col4 = st.columns(4)
right_col1.metric("Toplam Kalori", f"{t['kalori']:.2f} kcal")
right_col2.metric("Protein", f"{t['protein']:.2f} g")
right_col3.metric("Karbonhidrat", f"{t['karbonhidrat']:.2f} g")
right_col4.metric("Yağ", f"{t['yag']:.2f} g")

# Hedef ilerleme barı
st.subheader("🎯 Günlük Hedef")
pct = int(min(100, max(0, round(100 * (t["kalori"] / daily_target)))))
st.progress(pct)
st.caption(f"Hedef kcal ≈ {daily_target:.0f} • Tamamlanan %{pct}")

# Küçük pasta grafik
st.subheader("📊 Makro Dağılımı (küçük)")
if (t["protein"] + t["karbonhidrat"] + t["yag"]) > 0:
    fig, ax = plt.subplots(figsize=(3,3))
    ax.pie([t["protein"], t["karbonhidrat"], t["yag"]],
           labels=["Protein","Karbonhidrat","Yağ"], autopct="%1.1f%%")
    ax.set_aspect('equal')
    st.pyplot(fig, use_container_width=False)
else:
    st.info("Makro grafiği için en az bir öğün ekleyin.")

# ========================= PDF RAPOR =========================
st.subheader("🧾 PDF Raporu")
if HAS_PDF:
    if st.button("📥 PDF indir"):
        out_path = f"gunluk_rapor_{TODAY}.pdf"
        df_all = build_meals_dataframe()
        path = generate_pdf(out_path, st.session_state.profile, t, df_all)
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                st.download_button("📄 Günlük Raporu İndir", data=f, file_name=os.path.basename(path), mime="application/pdf")
        else:
            st.error("PDF oluşturulamadı.")
else:
    st.info("PDF için: `pip install reportlab`")

# ========================= ALTA BİLGİ =========================
with st.expander("ℹ️ Notlar"):
    st.markdown(
        "- Besin değerleri **100 g** bazlıdır. Gram değiştikçe otomatik yeniden hesaplanır.\n"
        "- Günlük kayıtlar otomatik olarak **tarihli CSV** dosyasına kaydedilir.\n"
        "- Hedef kalori, **Mifflin–St Jeor** + aktivite katsayısı + hedef ayarı ile hesaplanır.\n"
        "- AI öneri için `OPENAI_API_KEY` ortam değişkeni gereklidir."
    )

# Sayfa sonunda güvenlik için kaydet
save_daily_csv()
