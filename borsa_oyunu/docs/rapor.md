# 📊 Borsa Simülasyonu Oyunu Dönem Projesi Raporu

## 1. Projenin Amacı ve Ne İşe Yaradığı
Bu projenin amacı, dinamik piyasa hareketlerini simüle eden, modern web mimarisi standartlarına uygun ve yapay zeka destekli bir finansal borsa "tycoon" platformu geliştirmektir. Uygulama, kullanıcıların sanal bir başlangıç bakiyesiyle gerçek zamanlı olarak değişen hisse senedi ve yüksek volatiliteye sahip kripto para piyasalarında alım-satım işlemleri yapmalarına, portföylerini anlık olarak optimize etmelerine ve toplam servet sıralamasına göre küresel bir liderlik tablosunda rekabet etmelerine olanak tanır. Arka planda çalışan zaman odaklı otomatik simülasyon motoru sayesinde fiyatlar ve makroekonomik haber akışları dinamik olarak güncellenirken, entegre edilen "Broker Kerem" yapay zeka danışman modülü kullanıcının anlık finansal durumunu ve portföy konsantrasyonunu analiz ederek kişiselleştirilmiş stratejik yatırım tavsiyeleri üretmektedir.

---

## 2. Mimari Özet
Proje, monolitik bir yapıdan arındırılarak ölçeklenebilir, güvenli ve modüler bir yazılım tasarımı sunan **Application Factory Pattern** ve **Blueprint** mimarisi üzerine kurulmuştur.

### A. Klasör Yapısı (Workspace Hierarchy)
Uygulamanın dizin ağacı, sorumlulukların ayrılması (Separation of Concerns) prensibine göre şu şekilde yapılandırılmıştır[cite: 1]:

```text
borsa_oyunu/
│
├── app/                        # Ana uygulama paketi
│   ├── __init__.py             # Application Factory (create_app) & Uzantı konfigürasyonları
│   ├── models.py               # SQLAlchemy 2.x Mapped veri modelleri & ilişkileri
│   │
│   ├── auth/                   # Kimlik Doğrulama Modülü (Blueprint)
│   │   ├── forms.py            # Flask-WTF login/register formları & validatörler
│   │   └── routes.py           # Kayıt, giriş ve çıkış rotaları
│   │
│   └── main/                   # Ana Oyun ve Finansal Operasyonlar Modülü (Blueprint)
│       └── routes.py           # Dashboard, ticaret emirleri, API uç noktaları & AI Broker rotaları
│
├── templates/                  # Jinja2 HTML şablonları
│   ├── base.html               # Master şablon (Template Inheritance ana kalıbı)
│   ├── dashboard.html          # Canlı borsa takip ve işlem paneli
│   ├── stock_detail.html       # Hisse/Kripto detay ve işlem geçmişi sayfası
│   └── auth/                   # Giriş/Kayıt alt şablonları
│
├── instance/                   # SQLite veritabanı dizini (borsa.db)
├── migrations/                 # Flask-Migrate veritabanı göç geçmişi dosyaları
├── docs/                       # AI Günlüğü ve Rapor dokümantasyon dizini
│   └── img/                    # Teknik kanıt ekran görüntüleri (SS)
│
├── Dockerfile                  # Üretim ortamı konteyner tarifi
├── docker-compose.yml          # Sandbox ortamı orkestrasyon dosyası
├── requirements.txt            # Bağımlı Python kütüphaneleri listesi
└── run.py                      # Uygulama giriş noktası (Entry Point)
### B. Ana İşleyiş ve Veri Akışları (Core Flows)

1. **Oturum ve Güvenlik Akışı:** Kullanıcı istekleri öncelikle `auth` blueprint'i üzerinden karşılanır. Giriş ve kayıt işlemleri **Flask-WTF** formları üzerinden doğrulanır, formlara gömülen `csrf_token` ile CSRF saldırıları engellenir ve şifreler veritabanına `werkzeug.security` ile hash'lenerek güvenli bir şekilde kaydedilir[cite: 1].
2. **Gerçek Zamanlı Piyasa Simülasyon Akışı:** Kullanıcı `dashboard` sayfasını izlerken, JavaScript tabanlı bir poller her 5 saniyede bir arka planda `/api/market-tick` uç noktasına AJAX istekleri atar. Sunucu tarafında tetiklenen döngüsel motor, hisse ve kripto fiyatlarını günceller, rastlantısal finansal haberler üretir ve bu güncel verileri sayfa yenilenmeden dinamik SVG/Canvas grafiklerine ve piyasa tablolarına pürüzsüzce yansıtır.
3. **Yapay Zeka ve Danışmanlık Akışı:** Kullanıcı "Broker Kerem" panelinden tavsiye talep ettiğinde, `/api/ai-advice` rotası kullanıcının mevcut nakit durumunu, portföyündeki varlık dağılımlarını ve en son yayınlanan piyasa haberlerini veritabanından çekerek bir bağlam (context) oluşturur ve kullanıcıya dinamik yatırımlar öneren kural tabanlı bir finansal zekayı tetikler.
4. **Veritabanı ve Sürüm Kontrol Akışı:** Modeller üzerinde yapılan tüm yapısal değişiklikler **Flask-Migrate** eklentisiyle `flask db migrate` ve `flask db upgrade` komut zinciriyle yönetilerek `migrations/` klasörü altında kayıt altına alınır ve SQLite şemasıyla kararlı şekilde eşleştirilir[cite: 1].

---
### Vibe coding deneyiminiz: ne işe yaradı, nerede zorlandınız?
Ne işe yaradı kısmından çok neler öğrettiği kısmı benim için daha etkili bir tabir olur çünkü bu proje yaparken yapay zekayı nerde nasıl kullanmam gerektiğini ayrıca bir projeye başlarken nelere dikkat etmem gerektiğini ve dosyalama işlemnine önem vermezsem işimin nasıl allak bullak bi hale geldiğini öğrenmiş oldum.
En çok zorlandığım kısım ise gerçekten gemini ve antigravity yapay zekasına aynı anda laf anlatmaya çalışmak oldu çünkü gerçekten çoğu zaman işi kendim yapmak zorunda kaldım o kadar laftan anlamıyor ki insan gerçekten bir yerde çıldırıyor.

Antigravity'de en faydalı bulduğunuz 2 özellik ve neden:
Antigravity en başında çok hızlı çalışmasıyla aklımı aldı her ne kadar çoğu zaman laf anlamasa bile anladığı zaman yaptığı işler ve hızı cidden insanı şoka sokuyor. Ayrıca bunun yanında verdiğiniz komutlar (promptlar) dahilinde yönlendirdiğiniz zaman bütün işi eline alıp çok seri şekilde yapabilliyor ve bu gerçekten çok etkileyici 

Ajanın yakalayıp düzelttiğiniz en kritik 3 hata:
-En başında Register (kayıt ol) ve  login (giriş) ekranında gerçekten tam bir yarım akıllının yapacağı türden hatalar yaptı ve projenin genel akışını bozdu ayrıca benim hevesimi de iyice kırdı diyebilirim.
-Ai entegrasyonunu ısrarla yapmayı unuttu ve sitemin bütün şemasını bozdu bir şey eklicem derken.
-Hisseler gerçekçi ve rastgele olarak değil tamamen arz talep durumunun tersine hareket ediyordu ve bunu ısrarla düzeltmedi.

Eğer projeyi sıfırdan AI olmadan yapsaydınız ne kadar sürerdi tahmininiz?
yani yapılan iş muazzam derecede uzun yapay zeka olmasaydı günlük 8 9 saatlik sıkıcı bir mesai ile en az 4 5 ay gibi bir sürede biterdi en az.

Bu projeyi sürdürürseniz bir sonraki adım ne olur?
Kesinlikle bunu geliştirip aslında çok oyunculu bi tycoon oyununa çevirmek olurdu ki insanların buna tepkisini görebileyim ki neden olmasın daha ilerisi  :D