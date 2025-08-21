<h1 align="center"> 🥗 Diyet Asistanı </h1>

<p align="center">
  <img src="logo.png" alt="Logo" width="120" />
</p>

<p align="center">
  📊 Kendi beslenme kayıtlarını tut, günlük toplam değerlerini gör ve <b>yapay zekâ</b> desteğiyle beslenmeni değerlendir!
</p>

---

## 📂 Proje Yapısı
DiyetAsistanı/
│── beslenme.py # Ana uygulama dosyası
│── yiyecekler.csv # Yiyecekler listesi
│── gunluk_kayit.csv # Günlük kayıtlar
│── requirements.txt # Gerekli kütüphaneler
│── README.md # Proje açıklaması
│── logo.png # Uygulama logosu
└── .streamlit/
└── secrets.toml # OpenAI API anahtarı



---

## ⚙️ Kurulum

```bash
# 1. Projeyi indir
git clone https://github.com/kullanici/DiyetAsistani.git
cd DiyetAsistani

# 2. Gerekli paketleri yükle
pip install -r requirements.txt

# 3. API anahtarını ekle
# .streamlit/secrets.toml
OPENAI_API_KEY = "BURAYA_API_KEYİNİ_YAZ"

# 4. Uygulamayı çalıştır
streamlit run beslenme.py




🚀 Özellikler

✅ Yiyecek ekle & gramaj gir

✅ Günlük kalori, protein, karbonhidrat ve yağ takibi

✅ Modern tablo görünümü (AgGrid desteği)

✅ Verilerin gunluk_kayit.csv dosyasında saklanır

✅ 🤖 Yapay zekâ ile “Beslenmeni Değerlendir”

✅ Telefon & bilgisayar uyumlu

✅ Kendi isim ve logonla masaüstüne eklenebilir


📌 Notlar

yiyecekler.csv içine yeni yiyecekler ekleyebilirsin.

gunluk_kayit.csv her çalıştırmada güncellenir, verilerin silinmez.

Telefonla kullanırken "Masaüstüne ekle" dediğinde kendi logon görünür.



<h3 align="center"> 🧑‍💻 Katkı Sağla </h3> <p align="center">Projeyi geliştirmek için pull request açabilir veya kendi ihtiyacına göre düzenleyebilirsin.</p> ```





