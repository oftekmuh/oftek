# oftek

<p align="center">
  <img src="logo.png" alt="oftek Logo" width="220" />
</p>

<p align="center">
  <strong>Her Kurum ve İşletme İçin Bağımsız, Taşınabilir Operasyonel Takip & Gün Sonu Otomatik Fiş Sistemi</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/Lisans-MIT-blue.svg" alt="Lisans: MIT" /></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Testler-30%20Geçti-brightgreen.svg" alt="Test Durumu: 30 Başarılı" />
  <img src="https://img.shields.io/badge/Dış%20Bağımlılık-Sıfır-orange.svg" alt="Sıfır Harici Bağımlılık" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg" alt="Platform Desteği" />
</p>

---

## 🌟 oftek Nedir?

**oftek**, herhangi bir kişi, unvan veya tek bir kurum yapısına bağlı olmayan; **her isteyen kurumun, şirketin veya sivil toplum kuruluşunun** indirip kendi bünyesinde bağımsızca çalıştırabileceği açık kaynaklı bir operasyonel takip ve yevmiye fişi çözümüdür.

Günlük kasa hareketleri, cari firma borçları, müşteri alacakları (FIFO veya Seçimli Fatura tahsisli), personel hakedişleri ve çift taraflı (Borç = Alacak) resmi yevmiye fişleri tek bir çatı altında toplanır. Gün kapatıldığında tüm ön operasyonlar otomatik olarak resmi defter kayıtlarına dönüştürülür.

---

> ### ⚠️ ÇOK ÖNEMLİ: Dosyalar ZIP Arşivindeyse MUTLAKA ZİPTEN ÇIKARINIZ!
> Projeyi internetten, GitHub'dan veya başka bir ortamdan **.zip (sıkıştırılmış arşiv)** olarak indirdiyseniz, **kesinlikle zip penceresinin içindeyken `baslat.bat` çalıştırmayınız!**  
> Windows zip içindeki dosyaları geçici salt-okunur bellekte çalıştırdığından veritabanı kaydedilemez ve sunucu açılmaz.  
> 
> **Ne Yapmalısınız?**
> 1. İndirdiğiniz `.zip` arşivine sağ tıklayın.
> 2. **"Tümünü Ayıkla..."** (veya *Klasöre Çıkar*) seçeneğine tıklayın.
> 3. Dosyaları dilediğiniz bir klasöre veya USB flash belleğe çıkartın.
> 4. Çıkarttığınız klasördeki **`baslat.bat`** dosyasına çift tıklayarak sistemi başlatın.

---

## 🏢 Hangi Kurumlar İçin Uygundur?

oftek, mimari olarak tamamen kurum bağımsızdır. **Sistem & Ayarlar** ekranından kurum adı, türü ve para birimi (`₺`, `$`, `€`, `£`) tek tıkla belirlenebilir:

| Kurum Türü | Kullanım Alanı ve Senaryolar |
| :--- | :--- |
| **KOBİ & Şirketler** | Müşteri cari takibi, açık faturalara tahsilat dağıtımı, tedarikçi borçları, personel avans/maaş tahakkukları ve resmi muhasebe yevmiye fişleri. |
| **Dernekler & Vakıflar** | Bağış/aidat tahsilatları, faaliyet giderleri, dönemsel personel ödemeleri, şeffaf kasa ve defter kayıtları. |
| **Kooperatifler & Birlikler** | Ortakların cari hesapları, dönemsel aidat/masraf tahakkukları, faturalı alacak takipleri ve gün sonu kapanış fişleri. |
| **Eğitim & Spor Kulüpleri** | Kurs/üyelik takipleri, eğitmen/antrenör hak edişleri, malzeme tedarik borçları ve günlük kasa denetimi. |
| **Bireysel & Serbest Meslek** | Kendi adına bağımsız gelir/gider takibi yapmak, cari borç/alacakları yönetmek ve Excel'den hesap planı aktarmak isteyen profesyoneller. |

---

## ✨ Öne Çıkan Özellikler

- 🚀 **Sıfır Harici Bağımlılık (Zero External Dependencies):** Sadece Python standart kütüphaneleri (`sqlite3`, `http.server`, `json`). `pip install` yapmanıza gerek yoktur.
- ⚡ **SQLite B-Tree İndeksleri:** Bütün tablolar ilişkisel indekslerle güçlendirilmiştir; yüz binlerce satırda dahi sorgular milisaniyeler içinde tamamlanır.
- 🎯 **Kesinlikle Sıfır Dropdown (0 `<select>`):** Sistemde hantal açılır kutu yoktur. Tüm seçimler yazdıkça süzen akıllı arama (Autocomplete) veya tıklanabilir buton segmentleri ile yapılır.
- 📊 **Ekran İçi Canlı Raporlama & Muavin Defteri:** Harici dosya indirmeye gerek kalmadan 5 alt sekme (Kasa/Banka, Cari Bakiyeler, Personel Bordro, Genel Mizan, Muavin Defteri), hızlı dönem filtreleri ([Bugün], [Bu Hafta], [Bu Ay], [Bu Yıl], [Tümü]), anlık arama (klavyeden yazdıkça filtrelenip özet kartları anında yeniden toplanır) ve çift taraflı kayıt denetim modalı.
- ⌨️ **Masaüstü Sınıfı Fiş Girişi & Seri Klavye Ergonomisi:**
  - Tam sayfa ferah çalışma alanı (%100 ekran yayılımı).
  - Canlı Borç / Alacak ve Fark dengeleme motoru.
  - <kbd>Tab</kbd>: İlk arama sonucunu anında seçer ve sonraki alana odaklanır / son hücrede yeni satır açar.
  - <kbd>Ctrl + K</kbd>: Kalan farkı Kasa (100) hesabıyla otomatik kapatır ve fişi dengeler.
  - <kbd>Ctrl + D</kbd> / <kbd>Ctrl + '</kbd>: Üst satırı kopyalar.
  - <kbd>F2</kbd>: Yeni satır ekler.
  - <kbd>Ctrl + S</kbd>: Fişi kaydeder.
- 📱 **Aynı Yerel Ağdaki Diğer Cihazlardan (Telefon, Tablet, PC) Erişim:** Python'ın dahili web sunucusu `0.0.0.0:8080` üzerinde tüm yerel ağ arayüzlerini dinler. Programı tek bir bilgisayarda başlattığınızda, aynı Wi-Fi veya ofis ağına bağlı cep telefonu, tablet veya diğer bilgisayarlardan yerel IP adresiyle (Örn: `http://192.168.1.45:8080`) hiçbir kurulum yapmadan anında bağlanabilir, kasayı ve tahsilatları mobil cihazınızdan özgürce yönetebilirsiniz.
- 🔄 **Çift Modlu Tahsilat Dağıtımı:** Müşteri ödemelerini ister tek tıkla otomatik **FIFO** ile dağıtın, ister açık faturaları görerek **Seçimli** tutar tahsis edin.
- 👥 **Personel Yönetimi & Dinamik Ek Bilgiler:** Sınırsız dinamik ek bilgi alanı (Metin, Sayı, Tarih), personel türleri, borç çeşitleri yönetimi, dönemlik maaş tahakkukları ve parçalı avans yönetimi.
- 📑 **Genel Hesap Planı & Mizan:** Excel şablonundan tek tıkla toplu hesap aktarımı ve geçici mizan raporu.
- 🛡️ **Kırmızı Alan (Danger Zone) Emniyeti:** Operasyonel verileri sıfırlarken kazaen kayıpları engellemek için büyük harfle **"SIFIRLA"** yazma şartı içeren çift korumalı onay mekanizması.

---

## 🚀 Hızlı Başlangıç

### Seçenek 1: Windows Taşınabilir (Dahili Python 3.11 Dahildir - Sıfır Kurulum)
Proje içerisinde hazır taşınabilir **`python/`** motoru yer alır (~20 MB). Bilgisayarınıza Python veya harici paketler yüklemenize gerek yoktur.
1. İndirdiğiniz zip arşivini klasöre çıkartın (Zip içinden doğrudan çalıştırmayınız).
2. **`baslat.bat`** dosyasına çift tıklayın.
3. Dahili Python motoru otomatik devreye girer, yerel sunucu başlatılır ve tarayıcınız otomatik açılır:  
   👉 **[http://localhost:8080](http://localhost:8080)**

### Seçenek 2: Kendi Bilgisayarınızdaki Python ile Çalıştırma (Windows / Linux / macOS)
Sisteminizde Python 3.10, 3.11 veya 3.12 yüklüyse:
```bash
# Proje dizinine girin ve başlatın (harici pip paketi gerekmez)
python app.py
```
Tarayıcınızda açın: **[http://localhost:8080](http://localhost:8080)**

> **Python'ı Sıfırdan Kurmak İsterseniz:** [python.org/downloads](https://www.python.org/downloads/) adresinden Python indirin. Kuruluma başlarken alttaki **"Add Python to PATH"** kutusunu mutlaka işaretleyin.

### 📱 Aynı Ağdaki Diğer Cihazlardan (Telefon / Tablet) Nasıl Girilir?
1. Programı ana bilgisayarda başlattığınızda açılan siyah konsol ekranında yerel IP adresiniz otomatik listelenir:  
   `* Mobilden Giriş (Aynı WiFi): http://192.168.1.X:8080`
2. Telefonunuzu veya tabletinizi ana bilgisayarla **aynı Wi-Fi veya ofis ağına** bağlayın.
3. Mobil cihazınızın tarayıcısına (Safari, Chrome vb.) konsolda yazan IP adresini (Örn: `http://192.168.1.45:8080`) yazıp Enter'a basın.
4. oftek'in dokunmatik ve tam uyumlu mobil arayüzü karşınıza gelecektir; sahada veya dükkanda kasayı telefonunuzdan yönetebilirsiniz.

### 🛠️ Olası Hatalar ve Hızlı Çözümler (Sorun Giderme)
- **`baslat.bat` açılıp hemen kapanıyor veya "Python bulunamadı" diyor:**
  - *Sebep:* Dosyaları ZIP arşivinden çıkarmadan doğrudan zip içinde çalıştırmış olabilirsiniz. Windows zip içini geçici bellekte açar ve `python` klasörünü göremez.
  - *Çözüm:* `.zip` dosyasına sağ tıklayıp **"Tümünü Ayıkla"** deyin ve çıkarttığınız klasördeki `baslat.bat`'ı çalıştırın.
- **Port 8080 kullanımda hatası:**
  - *Sebep:* Önceki bir oturum veya başka bir yerel yazılım portu tutuyor olabilir.
  - *Çözüm:* `Ctrl+Shift+Esc` ile Görev Yöneticisi'ni açıp arka plandaki `python.exe` sürecini sonlandırın veya bilgisayarı yeniden başlatın.
- **Telefondan bağlanılamıyor:**
  - *Çözüm:* Telefonun mobil verisini (4.5G) kapatıp bilgisayarla aynı Wi-Fi ağına bağlandığından ve Windows Güvenlik Duvarı'nda "Özel Ağlara İzin Ver" seçildiğinden emin olun.
- Daha ayrıntılı hata senaryoları için **[`kullanim_kilavuzu.html`](kullanim_kilavuzu.html)** sayfasındaki 13. Bölümü inceleyebilirsiniz.

---

## 🌐 Web & Kılavuz Bağlantıları

- **Uygulama Ana Ekranı:** [http://localhost:8080](http://localhost:8080) veya [http://127.0.0.1:8080](http://127.0.0.1:8080)
- **Görsel Kullanım Kılavuzu:** [http://localhost:8080/kilavuz](http://localhost:8080/kilavuz)
- **Çevrimdışı Kılavuz Dosyası:** [`kullanim_kilavuzu.html`](kullanim_kilavuzu.html)

---

## 🧪 Birim ve Entegrasyon Testleri

oftek, 30 adet kapsamlı otomatik test ile korunmaktadır. Testleri çalıştırmak için:

```bash
# Dahili Python ile (Windows):
.\python\python.exe -m unittest discover tests

# Sistem Python'ı ile (Tüm Platformlar):
python -m unittest discover tests
```

---

## 📁 Mimari & Dosya Düzeni

```text
oftek/
├── app.py                      # Ana başlatıcı (sys.path ve otomatik tarayıcı açıcı)
├── server.py                   # Yerel HTTP sunucusu ve REST yönlendirici
├── baslat.bat                  # Taşınabilir akıllı Windows başlatıcı (ayrıntılı teşhis & geri bildirim)
├── python/                     # Windows için dahili gömülü Python 3.11 motoru (~20 MB)
├── db_manager.py               # SQLite bağlantı, şema ve indeks yöneticisi (< 300 satır)
├── db_seed.py                  # Standart hesap planı ve tohum veriler (< 300 satır)
├── accounting_engine.py        # FIFO ve finansal hesaplama motoru
├── accounting_voucher.py       # Çift taraflı yevmiye fiş üretim motoru
├── api_handlers.py             # REST API modüler yönlendiricisi
├── handlers_*.py               # Modüler API servis işleyicileri (ayarlar, cariler, personel vb.)
├── web/
│   ├── index.html              # Modern, %100 genişlikte, sıfır dropdown kullanıcı arayüzü
│   ├── js/                     # Modüler istemci iş mantıkları (dashboard, debts vb.)
│   ├── css/                    # Özel stiller
│   └── img/                    # Kurumsal logo ve ikon varlıkları
├── tests/                      # 30/30 Tam kapsamlı otomatik test paketi
├── .github/workflows/          # GitHub Actions CI/CD otomatik test iş akışı
├── CONTRIBUTING.md             # Katkı sağlama ve kodlama standartları rehberi
├── SECURITY.md                 # Güvenlik politikası ve yerel veri emniyeti
├── LICENSE                     # MIT Açık Kaynak Lisansı
└── README.md                   # Proje tanıtım ve dokümantasyon vitrini
```

---

## 🤝 Katkıda Bulunma

oftek topluluk katkılarına açıktır. Katkı kuralları, sıfır dropdown standardı ve modüler kodlama prensipleri için lütfen [CONTRIBUTING.md](CONTRIBUTING.md) belgesini inceleyiniz.

---

## 📄 Lisans

Bu proje **[MIT Lisansı](LICENSE)** ile lisanslanmıştır. Ticari veya kişisel amaçlarla özgürce kullanılabilir, değiştirilebilir ve dağıtılabilir.
