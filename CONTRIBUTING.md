# oftek Katkı ve Geliştirme Rehberi (CONTRIBUTING)

**oftek** açık kaynak projesine katkıda bulunmak istediğiniz için teşekkür ederiz!

Bu proje; işletmeler, dernekler, vakıflar, kooperatifler, KOBİ'ler ve eğitim kurumları için tasarlanmış bağımsız, taşınabilir ve sıfır kurulumlu bir operasyonel takip ve yevmiye fişi sistemidir.

Projenin yüksek kalitesini, taşınabilirliğini ve masaüstü ergonomisini korumak adına tüm katkılarda aşağıdaki temel kurallara eksiksiz uyulması zorunludur.

---

## 🏛️ Temel Mimari ve Tasarım Prensipleri

### 1. Kesinlikle Sıfır Dropdown Kuralı (0 `<select>`)
- Kullanıcı arayüzünde standart HTML `<select>` (açılır liste) kullanımı **KESİNLİKLE YASAKTIR**.
- Seçim işlemleri daima şu iki yöntemle yapılır:
  1. **Yazdıkça Filtreleyen Canlı Arama (Autocomplete / Combobox):** Hesap kodları, cariler, personeller ve geçmiş açıklamalar gibi çoklu seçeneklerde.
  2. **Tıklanabilir Buton Segmentleri:** Kurum türü, para birimi, personel bilgi tipleri gibi 2 ila 6 seçenekli tercihlerde.
- Autocomplete bileşenlerinde **`Tab` veya `Enter`** tuşu ile ilk sıradaki seçeneğin otomatik seçilip bir sonraki hücreye odaklanması masaüstü klavye ergonomisi için şarttır.

### 2. Modüler Mimari & Maksimum 300 Satır Kuralı (SRP)
- Kod dosyaları (backend handler'lar, motorlar, veritabanı modülleri) **300 satır sınırını aşmamalıdır**.
- Bir modül büyüdüğünde mantıksal alt parçalara (yeni handler veya yardımcı motor) ayrılmalıdır.
- Dosya uzunlukları ve sorumluluk alanları tek bir amaca odaklanmalıdır.

### 3. Sıfır Harici Paket Bağımlılığı (Zero External Dependencies)
- Backend tarafında yalnızca **Python standart kütüphaneleri** (`http.server`, `sqlite3`, `json`, `datetime`, `urllib` vb.) kullanılır.
- Projeye `pip install` gerektirecek herhangi bir harici kütüphane (Flask, Django, FastAPI, SQLAlchemy vb.) eklenemez.
- Bu kural, uygulamanın USB bellekten veya tek bir klasörden hiçbir kurulum yapmadan doğrudan çalışabilmesi (taşınabilirlik) için hayati öneme sahiptir.

### 4. Kurum ve Şahıs Bağımsızlığı & Sade "oftek" Marka Kimliği
- Uygulama herhangi bir şahıs veya belirli bir tek kuruma özel kodlanamaz.
- Kodda, logolarda, başlıklarda veya dokümantasyonda şahıs isimleri veya "oftek muhasebe" gibi tamlamalar yer alamaz. Projenin adı tek başına yalın **"oftek"**tir.
- Kurum kimliği, unvanı, türü ve para birimi `sistem_ayarlari` tablosu üzerinden dinamik yönetilir.

### 5. Yasaklı Terim Kuralı
- Kod tabanında, değişken isimlerinde, veritabanı sütunlarında veya dokümantasyonda eski sistem çağrışımı yapan terimler ("tekdüzen" vb.) kesinlikle kullanılmaz.
- Bunun yerine **"Genel Hesap Planı"** veya **"oftek Hesap Planı"** terimi kullanılır.

### 6. Veri Bütünlüğü ve Kırmızı Alan Güvenliği
- Silme ve sıfırlama gibi tehlikeli operasyonlar ana ekranda yer alamaz; mutlaka "Sistem & Ayarlar" altında, onay kutusuna büyük harflerle **"SIFIRLA"** yazma şartı içeren çift korumalı mekanizmayla sınırlandırılmalıdır.
- Borç = Alacak çift taraflı denklik kuralı çiğnenemez.

---

## 🧪 Test Zorunluluğu

- Yapılan her değişiklik ve eklenen her API rotası için `tests/` dizini altına kapsamlı birim ve entegrasyon testleri eklenmelidir.
- Mevcut testler bozulmamalıdır. Pull Request göndermeden önce tüm testlerin geçtiğinden emin olunmalıdır:

```bash
# Proje kök dizininde testleri çalıştırma
python -m unittest discover tests
```

---

## 🚀 Geliştirme Süreci (Nasıl Katkı Sağlanır?)

1. Bu depoyu GitHub üzerinde **Fork** edin.
2. Anlaşılır bir dal (branch) açın: `git checkout -b ozellik/yeni-raporlama`.
3. Kodlarınızı yukarıdaki kurallara uygun olarak yazın.
4. Testleri çalıştırın ve yeni özellik için test ekleyin: `python -m unittest discover tests`.
5. Değişikliklerinizi açık bir mesajla commitleyin: `git commit -m "feat: yeni kasa ekstresi raporlama desteği"`.
6. Dalınızı gönderin: `git push origin ozellik/yeni-raporlama`.
7. Ana depoya bir **Pull Request (PR)** oluşturun.
