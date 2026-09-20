# Flash Disk Üzerinde Sıfır İz ile oftek Çalıştırma Rehberi

Bu rehber, **oftek** sistemini bilgisayara takılı bir USB flash disk veya taşınabilir harici sürücü üzerinde çalıştırmanızı ve **bilgisayarda hiçbir iz, çerez, geçmiş veya dosya kırıntısı bırakmamanızı** sağlar.

---

> ### ⚠️ ÇOK ÖNEMLİ: Dosyalar ZIP Arşivindeyse MUTLAKA ZİPTEN ÇIKARINIZ!
> Projeyi `.zip` (sıkıştırılmış arşiv) olarak taşıdıysanız veya indirdiyseniz, **kesinlikle zip penceresinin içindeyken `baslat.bat` dosyasını çalıştırmayınız!**  
> Windows zip içindeki dosyaları geçici salt-okunur bellekte açtığından veritabanı dosyası kaydedilemez ve başlatıcı hata verir.  
> 
> **Doğru Uygulama Adımları:**
> 1. `.zip` arşivine sağ tıklayın.
> 2. **"Tümünü Ayıkla..."** (veya *Klasöre Çıkar*) seçeneğine tıklayın.
> 3. Dosyaları flash diskinize veya bilgisayarınızda bir klasöre çıkartın.
> 4. Çıkarttığınız klasördeki **`baslat.bat`** dosyasına çift tıklayarak sistemi başlatın.

---

## 1. Bilgisayarda Neden Hiçbir Şey Kalmaz? (Sıfır İz Mimarisi)

1. **Taşınabilir Veritabanı (`muhasebe.db`):** 
   Program, veritabanı dosyasını bilgisayarın C: diskine, kullanıcı dizinine veya Temp klasörüne değil; doğrudan **flash diskin kendi klasörüne** yazar.
2. **Önbellek Koruması (`PYTHONDONTWRITEBYTECODE=1`):**
   Normalde Python çalışırken diske `.pyc` derleme dosyaları (`__pycache__`) yazar. `baslat.bat` başlatıcısı bu mekanizmayı devre dışı bırakır; bilgisayarın diskine hiçbir önbellek kırıntısı bırakılmaz.
3. **Dahili Gömülü Python (`oftek\python\`):**
   Sistem, içerisinde hazır bulunan bağımsız Python çalışma motoru ile çalışır. Takılan bilgisayarda Python kurulu olması gerekmez, bilgisayarın sistem kayıt defterine (Registry) veya ortam değişkenlerine (PATH) hiçbir kayıt eklenmez.
4. **Tarayıcı Geçmişi ve Çerez Koruması (Gizli Mod):**
   İsteğe bağlı olarak gizli pencere ile açıldığında, girilen fişler, cariler veya raporlar bilgisayarın tarayıcı geçmişine yazılmaz ve çerezler diskte tutulmaz.

---

## 2. Taşınabilir Klasör Yapısı

Sistemin flash disk üzerindeki eksiksiz yapısı aşağıdaki gibidir:

```text
USB FLASH DİSK (Örn: F:\oftek\)
│
├── app.py                      <-- Ana Başlatma Dosyası
├── server.py                   <-- HTTP & API Sunucu Motoru
├── baslat.bat                  <-- Çift tıklayıp çalıştıracağınız başlatıcı
├── kullanim_kilavuzu.html      <-- Çevrimdışı Kullanım Kılavuzu
├── muhasebe.db                 <-- Yerel SQLite Veritabanı
│
├── python\                     <-- Dahili Gömülü Python 3.11 Motoru
│   ├── python.exe              <-- Taşınabilir Python Çalıştırıcısı
│   ├── python311._pth          <-- Modül ve Yol Yapılandırması
│   └── sqlite3.dll             <-- Bağımsız Veritabanı Motoru
│
├── web\                        <-- Masaüstü Arayüz Dosyaları
│   └── index.html              <-- %100 Genişlikte, 0 Dropdown Arayüz
│
├── accounting_engine.py        <-- FIFO ve Tahakkuk Hesaplama Motoru
├── accounting_voucher.py       <-- Çift Taraflı Fiş Üretim Motoru
├── api_handlers.py             <-- API Rota Yönlendiricisi
├── db_manager.py               <-- Veritabanı Şema & Tablo Yöneticisi
└── handlers_*.py               <-- Modüler Servis İşleyicileri
```

---

## 3. Çalıştırma Talimatı

1. Zipten çıkardığınız veya flash diskinizdeki `oftek` klasörüne girin.
2. **`baslat.bat`** dosyasına çift tıklayın.
3. Başlatıcı otomatik olarak `python\python.exe` motorunu devreye alır ve tarayıcınızda açar.

### 🌐 Tıklanabilir Web Bağlantıları:
- **Ana Ekran:** [http://localhost:8080](http://localhost:8080) veya [http://127.0.0.1:8080](http://127.0.0.1:8080)
- **Kullanım Kılavuzu (Web):** [http://localhost:8080/kilavuz](http://localhost:8080/kilavuz)
- **Kullanım Kılavuzu (Dosya):** [`kullanim_kilavuzu.html`](kullanim_kilavuzu.html)

4. Çalışmanızı tamamladığınızda siyah komut penceresini kapatmanız yeterlidir; hiçbir arka plan süreci veya geçici dosya kalmaz.

---

## 4. Güvenlik ve Yedekleme Tavsiyeleri

- **Yedek Alma:** Flash diskiniz kaybolur veya donanımsal arıza yaşarsa verilerinizi korumak için periyodik olarak `oftek\muhasebe.db` dosyasını şifreli bir arşive veya güvenli bir ikinci diske kopyalayınız.
- **Güvenli Çıkart:** Flash diski bilgisayardan fiziksel olarak çıkarmadan önce komut penceresini kapatın ve Windows'un sağ alt köşesindeki *"Donanımı Güvenle Kaldır ve Medyayı Çıkar"* seçeneğini kullanın. Bu işlem, SQLite veritabanının yazma işlemlerinin eksiksiz ve güvenli şekilde diske kaydedilmesini temin eder.