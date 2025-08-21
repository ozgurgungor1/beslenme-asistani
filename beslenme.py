import streamlit as st
import pandas as pd
from datetime import date
from openai import OpenAI
import os

# -----------------------------
# AYARLAR
# -----------------------------
st.set_page_config(page_title="🥗 Akıllı Beslenme Asistanı", page_icon="🥗", layout="centered")

FOODS_CSV = "yiyecekler.csv"
LOG_CSV   = "gunluk_kayit.csv"  # tarih bazlı kayıt

# OpenAI client (API anahtarı .streamlit/secrets.toml içinde)
# secrets.toml içeriği: OPENAI_API_KEY = "sk-xxxxx"
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# YARDIMCI FONKSİYONLAR
# -----------------------------
@st.cache_data
def load_foods(path: str) -> pd.DataFrame:
    """Yiyecek listesini yükle ve sayısal kolonları float'a çevir."""
    df = pd.read_csv(path)
    # Zorunlu kolon kontrolü
    needed = {"isim", "kalori", "protein", "karbonhidrat", "yag"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"'{path}' içinde eksik kolon(lar): {', '.join(missing)}")

    for col in ["kalori", "protein", "karbonhidrat", "yag"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # İsimleri stringle
    df["isim"] = df["isim"].astype(str)
    return df

def ensure_log_file(path: str):
    """gunluk_kayit.csv yoksa başlıklarla oluştur."""
    if not os.path.exists(path):
        cols = ["tarih", "ogun", "isim", "miktar", "kalori", "protein", "karbonhidrat", "yag"]
        pd.DataFrame(columns=cols).to_csv(path, index=False)

def load_log(path: str) -> pd.DataFrame:
    ensure_log_file(path)
    df = pd.read_csv(path)
    # Tipler
    if not df.empty:
        df["tarih"] = pd.to_datetime(df["tarih"]).dt.date
        for col in ["miktar", "kalori", "protein", "karbonhidrat", "yag"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        df["ogun"] = df["ogun"].astype(str)
        df["isim"] = df["isim"].astype(str)
    return df

def save_log(df: pd.DataFrame, path: str):
    df_out = df.copy()
    if not df_out.empty:
        # date obj -> iso
        df_out["tarih"] = pd.to_datetime(df_out["tarih"]).dt.strftime("%Y-%m-%d")
    df_out.to_csv(path, index=False)

def add_entry(df_log: pd.DataFrame, tarih: date, ogun: str, secilen: pd.Series, miktar: float) -> pd.DataFrame:
    """Yeni yemek kaydı ekle (miktar gram)."""
    row = {
        "tarih": tarih,
        "ogun": ogun,
        "isim": secilen["isim"],
        "miktar": miktar,
        "kalori": float(secilen["kalori"]) * (miktar / 100.0),
        "protein": float(secilen["protein"]) * (miktar / 100.0),
        "karbonhidrat": float(secilen["karbonhidrat"]) * (miktar / 100.0),
        "yag": float(secilen["yag"]) * (miktar / 100.0),
    }
    return pd.concat([df_log, pd.DataFrame([row])], ignore_index=True)

def day_slice(df_log: pd.DataFrame, tarih: date) -> pd.DataFrame:
    return df_log[df_log["tarih"] == tarih].reset_index(drop=True)

def render_meal_table(df_day: pd.DataFrame, ogun: str) -> pd.DataFrame:
    """Belirli öğünün tablosunu silme butonlarıyla göster; silinen satırları düşürüp df_day döndür."""
    sub = df_day[df_day["ogun"] == ogun].reset_index()
    if sub.empty:
        return df_day

    st.markdown(f"### 🍽️ {ogun}")
    # Silme butonu için sütunlar
    cols_to_show = ["isim", "miktar", "kalori", "protein", "karbonhidrat", "yag"]
    header = st.columns([3, 1, 1, 1, 1, 1, 1])  # +1 sil butonu
    header[0].markdown("**Yemek**")
    header[1].markdown("**Gram**")
    header[2].markdown("**Kalori**")
    header[3].markdown("**Protein**")
    header[4].markdown("**Karb.**")
    header[5].markdown("**Yağ**")
    header[6].markdown("**Sil**")

    to_drop_idx = []
    for _, row in sub.iterrows():
        c = st.columns([3, 1, 1, 1, 1, 1, 1])
        c[0].write(row["isim"])
        c[1].write(f"{row['miktar']:.0f} g")
        c[2].write(f"{row['kalori']:.1f}")
        c[3].write(f"{row['protein']:.1f}")
        c[4].write(f"{row['karbonhidrat']:.1f}")
        c[5].write(f"{row['yag']:.1f}")
        if c[6].button("🗑️", key=f"del-{ogun}-{row['index']}"):
            to_drop_idx.append(row["index"])

    if to_drop_idx:
        df_day = df_day.drop(index=to_drop_idx).reset_index(drop=True)
        st.info(f"{len(to_drop_idx)} kayıt silindi.")
    return df_day

def totals_block(df_day: pd.DataFrame):
    total = df_day[["kalori", "protein", "karbonhidrat", "yag"]].sum()
    st.subheader("📊 Günlük Toplam")
    c = st.columns(4)
    c[0].metric("Kalori (kcal)", f"{total['kalori']:.0f}")
    c[1].metric("Protein (g)", f"{total['protein']:.1f}")
    c[2].metric("Karb. (g)", f"{total['karbonhidrat']:.1f}")
    c[3].metric("Yağ (g)", f"{total['yag']:.1f}")
    return total

# -----------------------------
# VERİLERİ YÜKLE
# -----------------------------
try:
    foods = load_foods(FOODS_CSV)
except Exception as e:
    st.error(f"'{FOODS_CSV}' yüklenemedi: {e}")
    st.stop()

if "log_df" not in st.session_state:
    st.session_state.log_df = load_log(LOG_CSV)

# -----------------------------
# ARAYÜZ
# -----------------------------
st.title("🥗 Akıllı Beslenme Asistanı")

# Tarih seçimi
tarih = st.date_input("📅 Tarih", value=date.today())

# Öğün ve yemek ekleme
ogunler = ["Sabah", "Öğle", "Akşam", "Ara Öğün"]
st.markdown("### ➕ Öğüne Yemek Ekle")

left, right = st.columns([1, 2])

with left:
    secili_ogun = st.selectbox("Öğün", [""] + ogunler, index=0)

with right:
    secili_yemek = st.selectbox(
        "🍏 Yiyecek",
        [""] + sorted(foods["isim"].unique().tolist()),
        index=0
    )

miktar = st.number_input("⚖️ Miktar (gram)", min_value=0, step=10, value=0)

add_col1, add_col2 = st.columns([1, 3])
with add_col1:
    if st.button("Ekle", type="primary", use_container_width=True):
        if not secili_ogun or not secili_yemek or miktar <= 0:
            st.warning("Öğün, yiyecek ve miktar alanlarını doldur.")
        else:
            sec = foods.loc[foods["isim"] == secili_yemek].iloc[0]
            st.session_state.log_df = add_entry(st.session_state.log_df, tarih, secili_ogun, sec, miktar)
            save_log(st.session_state.log_df, LOG_CSV)
            st.success(f"{secili_ogun} öğününe {miktar} g {secili_yemek} eklendi.")

with add_col2:
    if st.button("Günü Temizle (Seçili Tarih)", use_container_width=True):
        before = len(st.session_state.log_df)
        st.session_state.log_df = st.session_state.log_df[st.session_state.log_df["tarih"] != tarih].reset_index(drop=True)
        save_log(st.session_state.log_df, LOG_CSV)
        st.info(f"{before - len(st.session_state.log_df)} kayıt temizlendi.")

st.divider()

# Seçili gün kayıtları
df_day = day_slice(st.session_state.log_df, tarih)

# Öğün tabloları (silme butonlarıyla)
for ogun in ogunler:
    df_day = render_meal_table(df_day, ogun)

# Eğer tabloda silme olduysa log’a yaz
if len(df_day) != len(day_slice(st.session_state.log_df, tarih)):
    # Diğer tarihler + güncellenen gün
    others = st.session_state.log_df[st.session_state.log_df["tarih"] != tarih]
    st.session_state.log_df = pd.concat([others, df_day], ignore_index=True)
    save_log(st.session_state.log_df, LOG_CSV)

# Toplamlar ve değerlendirme
total = totals_block(df_day)

st.markdown("### 🤖 Beslenmeni Değerlendir")
if st.button("Değerlendir"):
    if df_day.empty:
        st.warning("Bu tarihte kayıt yok.")
    else:
        prompt = (
            "Aşağıdaki günlük beslenmeyi kısaca değerlendir; eksik/fazla makroları, "
            "basit önerileri yaz. Net, pratik ve motive edici ol.\n\n"
            f"- Kalori: {total['kalori']:.0f} kcal\n"
            f"- Protein: {total['protein']:.1f} g\n"
            f"- Karbonhidrat: {total['karbonhidrat']:.1f} g\n"
            f"- Yağ: {total['yag']:.1f} g\n"
        )
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Uzman bir beslenme koçusun; kısa ve uygulanabilir öneriler ver."},
                    {"role": "user", "content": prompt},
                ],
            )
            st.success(resp.choices[0].message.content)
        except Exception as e:
            st.error(f"OpenAI isteği başarısız: {e}")

# Küçük notlar
with st.expander("ℹ️ İpuçları"):
    st.markdown(
        "SAĞLIKLI GÜNLER DİLERİZ :)"
    )
