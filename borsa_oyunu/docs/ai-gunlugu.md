## 📓 AI Geliştirme Günlüğü (AI Pair Programming Log)

Bu günlük, **Borsa Simülasyonu Oyunu** projesinin Antigravity üzerinde AI Pair Programming ("Vibe Coding") metodolojisiyle gerçekleştirilen geliştirme oturumlarını kronolojik olarak belgelemektedir. Her oturumda alınan mimari kararlar, ajana yapılan müdahaleler, karşılaşılan hatalar ve teknik kazanımlar rubrik kurallarına uygun olarak işlenmiştir.

---

## 📅 Oturum 1 [15 Mayıs 2026] [19:00 - 20:30]
### 🎯 Hedef
Proje fikrinin kararlaştırılması ve veritabanı temel şemasının tasarlanması.
### 💻 Kullandığım Mod ve Model
* **Mod:** Plan Modu (Zorunlu karmaşık mimari adımı)
* **Model:** Gemini 3 Pro (Antigravity entegre)
* **Görünüm:** Manager View
### 💬 Verdiğim Promptlar
1. "İnternet Programcılığı dersi için Flask 3.x tabanlı bir stock market tycoon (borsa simülasyonu) oyunu yapmak istiyorum. Kullanıcıların kayıt olabileceği, başlangıç bakiyesiyle hisse alıp satabileceği bir altyapı kuracağız. Plan modunda ilerleyelim."
### 📋 Ajanın Önerdiği Plan
* Proje kök dizininde monolitik bir `app.py` oluşturulması.
* SQLite veritabanı bağlantısının kurulması ve `User`, `Stock`, `Portfolio` modellerinin klasik `db.Column` (SQLAlchemy 1.x stili) ile yazılması.
### 🧐 Plan'da Sorguladıklarım & İtirazlarım
* Ajanın ilk başta getirdiği veritabanı şemasında modern SQLAlchemy 2.x stili yerine eski `db.Column` yapısı vardı. Dönem ödevi yönergesini dikkate alarak ajana itiraz ettim ve: *"SQLAlchemy 2.x stili Mapped ve mapped_column yapılarını kullan"* direktifini vererek planı revize ettirdim.
### 🛠️ Üretilen Kodda Düzelttiklerim
* `models.py` içerisinde `db.relationship` yapılarında kullanılan `order_by` argümanının SQLAlchemy 2.x şemalarında çökme oluşturduğunu fark ettim. İlişkisel `order_by` parametrelerini tamamen temizletip, kronolojik sıralama işlemlerini doğrudan rotalardaki veritabanı sorgularına aktararak kararlı bir yapı kurdum.
### 🧠 Bu Oturumdan Öğrendiğim
* Yapay zeka ajanları bazen eski dokümantasyon dillerini (SQLAlchemy 1.x gibi) kullanma eğilimindedir. Mimar olarak bizim yönergelerdeki modern standartları sıkı sıkıya dikte etmemiz gerekmektedir.

---

## 📅 Oturum 2 [18 Mayıs 2026] [14:00 - 15:30]
### 🎯 Hedef
Kullanıcı kayıt (Register), giriş (Login) ekranlarının ve temel Borsa Alım-Satım mekanizmasının kurulması.
### 💻 Kullandığım Mod ve Model
* **Mod:** Fast Modu
* **Model:** Gemini 3 Pro
* **Görünüm:** Editor View
### 💬 Verdiğim Promptlar
1. "Kullanıcı kayıt ve giriş HTML arayüzlerini şık, karanlık bir fintech temasıyla oluştur. Kullanıcı giriş yaptığında borsa ana ekranına (dashboard) yönlendirilsin."
### 📋 Ajanın Önerdiği Plan
* `login.html` ve `register.html` sayfalarının Bootstrap 5 ile oluşturulması.
* `app.py` içerisine login_required dekoratörlerinin eklenmesi.
### 🛠️ Üretilen Kodda Düzelttiklerim
* Giriş yapan kullanıcının zaten oturumu açıkken tekrar `/login` sayfasına gitmesini engellemek için `current_user.is_authenticated` kontrolünü rotanın başına manuel olarak ekledim. Ajanın gözden kaçırdığı bu edge-case (uç durum) oturum güvenliğini sağladı.
### 🧠 Bu Oturumdan Öğrendiğim
* Flask-Login entegrasyonunda session (oturum) güvenliği ve kullanıcı yönlendirmelerinin mantıksal kontrollerini yazılımcının bizzat denetlemesi kritik önem taşır.

---

## 📅 Oturum 3 [20 Mayıs 2026] [21:30 - 23:00]
### 🎯 Hedef
Borsa mekanizmasına zaman odaklı canlı simülasyon (Time-driven Simulation) ve dinamik haber akışı eklemek.
### 💻 Kullandığım Mod ve Model
* **Mod:** Plan Modu
* **Model:** Gemini 3 Pro
* **Görünüm:** Manager View
### 💬 Verdiğim Promptlar
1. "Borsa fiyatlarının ve haberlerin sadece sayfa yenilenince değil, kullanıcı ekranı izlerken her 5 saniyede bir arka planda kendi kendine değişmesini istiyorum. Sayfa yenilenmeden veriler güncellenmeli."
### 📋 Ajanın Önerdiği Plan
* `app.py` içinde bir `/api/market-tick` JSON endpoint'i tasarlamak.
* `dashboard.html` içinde JavaScript `setInterval` kullanarak her 5000ms'de bir bu endpoint'e Fetch API ile istek atmak.
### 🧐 Plan'da Sorguladıklarım & İtirazlarım
* Ajan ilk planda tüm haberleri her saniye basmayı önerdi. Çok hızlı haber spami olacağı için itiraz ettim ve her tetiklenmede %30 ihtimalle yeni haber düşmesi kısıtını koydurttum. Ayrıca veri tabanı yükünü hafifletmek adına 30 kayıttan eski fiyat geçmişlerini silen döngüsel temizlik motoru entegre ettirdim.
### ❌ Karşılaştığım Hatalar ve Çözümler
* **Hata:** Grafik çizgileri (Sparklines) anlık güncellenirken JavaScript DOM elementleri çakıştı ve ekran dondu.
* **Çözüm:** `Chart.js` ve SVG çizgilerinin güncellenme mantığını, eski veriyi silip yenisini ekleyecek şekilde JavaScript tarafında refaktör ettik. (Kanıt: `docs/img/oturum-3-js-tick.png`)

---

## 📅 Oturum 4 [22 Mayıs 2026] [16:00 - 17:30]
### 🎯 Hedef
Yapay Zeka Finansal Danışman (AI Broker) entegrasyonu.
### 💻 Kullandığım Mod ve Model
* **Mod:** Plan Modu
* **Model:** Gemini 3 Pro
* **Görünüm:** Editor View
### 💬 Verdiğim Promptlar
1. "Oyuna bir Yapay Zeka Danışmanı eklemek istiyorum. Kullanıcının nakit parasını, portföyünü ve son gelen haberleri okuyup akıllıca bir yatırım stratejisi üretsin."
### ❌ Karşılaştığım Hatalar ve Çözümler
* **Ajanın Hatası:** Ajan çok fazla kod satırı arasında boğulduğu için ilk kod çıktısında AI yönlendirmesini (`/api/ai-advice`) ve "Broker Kerem" chatbox arayüzünü tamamen eklemeyi unuttu! Kod kesildi.
* **Çözüm:** Ajana sert bir hatırlatma promptu ("You forgot to include the AI Advisor integration!") göndererek, mevcut canlı simülasyon kodlarını bozmadan bu özelliği ek parçalar halinde entegre etmesini sağladım. (Kanıt: `docs/img/oturum-4-ai-prompt.png`)

---

## 📅 Oturum 5 [25 Mayıs 2026] [13:00 - 15:00]
### 🎯 Hedef
Vizyoner Özellikler: Kripto Para Sekmesi, Global Liderlik Tablosu ve Yapay Zeka "Balina" Botların sisteme eklenmesi.
### 💻 Kullandığım Mod ve Model
* **Mod:** Plan Modu
* **Model:** Gemini 3 Pro
* **Görünüm:** Manager View
### 💬 Verdiğim Promptlar
1. "Sisteme yüksek volatiliteye sahip Kripto paraları ekle. Veritabanındaki tüm kullanıcıları servetine göre sıralayan bir Liderlik Tablosu kur. Arka planda kendi kendine büyük alım satımlar yapan sanal botlar (Whale Bots) yarat."
### 🧐 Plan'da Sorguladıklarım & İtirazlarım
* Kripto paraların dalgalanma oranını hisselerle aynı yapıyordu. Kriptonun doğası gereği volatilite sınırını `[-15%, +15%]` olarak ayarlattım. Botların hareketlerinin de "Son Balina Hareketleri" olarak ekrandan canlı bildirim olarak akmasını sağladım.

---

## 📅 Oturum 6 [28 Mayıs 2026] [10:00 - 12:00]
### 🎯 Hedef
Piyasa derinliğini artırmak (10 Yeni Hisse, 5 Yeni Kripto Para) ve ders yönergesine uygun olarak "Application Factory" mimarisine geçiş.
### 💻 Kullandığım Mod ve Model
* **Mod:** Plan Modu (Zorunlu teknik dönüşüm)
* **Model:** Gemini 3 Pro
* **Görünüm:** Manager View
### 💬 Verdiğim Promptlar
1. "Piyasaya AKBNK, FROTO gibi 10 yeni hisse ve AVAX, DOGE gibi 5 yeni kripto para ekle. Ardından projeyi tek bir `app.py` dosyasından kurtararak yönergede zorunlu olan Application Factory (`create_app`) ve Blueprint yapısına böl."
### 📋 Ajanın Önerdiği Plan
* Mimariyi `app/auth/` ve `app/main/` olarak iki temiz Blueprint'e ayırma planı.
* Formların `Flask-WTF` sınıflarına taşınarak Jinja2 şablon mirası (`base.html`) yapısına geçilmesi.
### 🛠️ Üretilen Kodda Düzelttiklerim
* Alım-satım formlarına hidden `csrf_token` input alanları eklettim ve global `CSRFProtect` aktif hale getirerek CSRF güvenlik açığını tamamen kapattım.

---

## 📅 Oturum 7 [01 Haziran 2026] [14:00 - 15:30]
### 🎯 Hedef
Flask-Migrate ile veritabanı göçü, Windows Çevre Hatalarının çözülmesi ve Docker entegrasyonu.
### 💻 Kullandığım Mod ve Model
* **Mod:** Fast Modu
* **Model:** Gemini 3 Pro
* **Görünüm:** Editor View
### ❌ Karşılaştığım Hatalar ve Çözümler
* **Hata 1:** Windows terminalinde `pip` ve `flask` komutları PATH hatasından dolayı tanınmadı (`'pip' is not recognized`).
* **Çözüm 1:** Komutları doğrudan Python çekirdeği üzerinden `python -m pip install` şeklinde çağırarak Windows çevre sınırlandırmasını aştık.
* **Hata 2:** `python -m flask db init` esnasında yerel bilgisayardaki Python 3.11 ve Python 3.12 sürümlerinin çakışmasından ötürü `ModuleNotFoundError: No module named 'flask_wtf'` hatası alındı.
* **Çözüm 2:** Paketleri doğrudan hatayı veren aktif Python 3.11 terminal motorunun içine (`python -m pip install`) yükleyerek sanal ortam bağımlılıklarını eşitledik. `flask db migrate` ve `flask db upgrade` komutlarını başarıyla yürüterek `migrations/` klasörünü ürettik. (Kanıt: `docs/img/oturum-7-windows-error.png`, `docs/img/oturum-7-success-build.png`)

---