# Proje Dersleri ve Kuralları (oftek)

## 1. Mimari Prensipler
- **Sıfır Dış Bağımlılık (Portable/Flash Bellek Uyumu)**: Python standart kütüphaneleri (`http.server`, `sqlite3`, `json`) korunmalıdır. Harici pip paketlerine bağımlı olunmamalıdır.
- **Sade "oftek" İsimlendirmesi & "Muhasebe" Adı Yasağı**: Uygulamanın adı tek başına yalın olarak **"oftek"**tir. Tarayıcı sekme başlığında (`<title>oftek</title>`), header ana logosunda, konsol ekranında ve arayüz başlıklarında "muhasebe" veya "oftek muhasebe" ibareleri KESİNLİKLE KULLANILMAYACAKTIR. Yalın ve sade "oftek" adı korunacaktır.
- **Entegrasyon (Ön Operasyonlar + Defter Kayıtları)**: Ön operasyonlar (tahsilat, tediye, tahakkuk) gün kapatıldığında çift taraflı (Borç=Alacak) Yevmiye Fişine dönüştürülmelidir.
- **Veri Güvenliği ve Kilit Mekanizması**: Kapatılan günlerin hareketleri kilitlenmeli, geriye dönük veri bütünlüğü bozulmamalıdır.
- **Türkçe Karakter ve Dil Desteği**: Tüm UI, log ve veritabanı metinleri eksiksiz Türkçe olmalıdır.
- **KESİN İSİMLENDİRME KURALI**: Eski muhasebe planı kod adı ve benzeri terimler dosya adlarında, değişkenlerde, veritabanında, UI metinlerinde ve kod açıklamalarında KESİNLİKLE KULLANILMAYACAKTIR. Yalnızca "Genel Hesap Planı", "Yevmiye Fişi" veya "oftek" kullanılacaktır.

## 2. Kullanıcı Kesin Kararları & İş Mantığı Dersleri
- **Tahsilat Dağıtımında Çift Mod (FIFO Otomatik + Seçimli Manuel)**:
  Tahsilatlar açık alacaklara dağıtılırken kullanıcı hem tek tıkla otomatik **FIFO** dağıtımı yapabilmeli hem de açık faturaları görerek **seçimli (manuel tutar tahsisli)** dağıtım yapabilmelidir.
- **Yıl ve Ay (Dönemsellik) Esası**:
  Alacak, borç, personel hakedişleri ve tüm finansal işlemlerde **Yıl ve Ay** (`donem_yil`, `donem_ay`) mutlak surette tutulmalı ve filtrelenebilmelidir. Özellikle personel maaş tahakkuklarında hangi yıl ve aya ait olduğu açıkça belirtilmeli ve mükerrer tahakkuk engellenmelidir.
- **KESİN DROPDOWN YASAĞI (Arama ve Otomatik Tamamlama Zorunluluğu)**:
  Tüm sistemde standart dropdown (`<select>`) kullanımı kesinlikle yasaktır. Liste seçimlerinde her zaman yazdıkça filtreleyen akıllı otomatik tamamlama (Autocomplete / Combobox) veya tıklanabilir buton segmentleri kullanılmalıdır. Çoklu seçim alanlarında da mutlaka anlık filtreleme yapan arama kutusu bulunmalıdır.
- **Fiş Girişi Pop-up Değil Tam Sayfa (Desktop-Class) Olmalıdır**:
  Muhasebe ve yevmiye fiş girişleri dar modal pencereler yerine ekranı geniş olarak kullanan, sidebar daraltılabilen tam sayfa sekmeler olarak açılmalıdır.
- **Fiş Ekranı Klavye Kısayolları Standartları**:
  Hızlı veri girişi için `Tab` (son alandan sonra otomatik yeni satır), `Ctrl+K` (kasa ile kalan farkı otomatik kapatıp dengeleme), `Ctrl+D` veya `Ctrl+'` (üst satırı kopyalama), `F2` (yeni satır) ve `Ctrl+S` (kaydetme) kısayolları standart olarak sunulmalıdır.
- **Kırmızı Alan (Danger Zone) ve Güvenli Sıfırlama Mekanizması**:
  Operasyonel verileri tek tuşla sıfırlama imkanı sunulurken kazaen veri kaybını önlemek için zorlaştırılmış koruma (onay kutusuna büyük harflerle tam olarak "SIFIRLA" yazma zorunluluğu) mutlak surette uygulanmalıdır. Hesap planı korunarak operasyonel hareketler temizlenmelidir.
- **Personel Türleri ve Sınırsız Dinamik Ek Bilgi Alanları**:
  Personel kartları tek tip olmamalı; kullanıcı dilediği personel türünü (Beyaz Yaka, Saha vb.) tanımlayabilmeli ve her personele sınırsız sayıda [Başlık + Bilgi Türü (Metin/Sayı/Tarih) + Değer] ekleyebilmelidir. Bilgi türü seçiminde dropdown kesinlikle kullanılmamalı, 3'lü buton segmentleri tercih edilmelidir.
- **Tam Ekran Enlemesine Kullanım (%100 Layout Genişliği)**:
  Sistem masaüstü ve geniş ekranlarda daraltıcı (`max-w-7xl`, dar `container`) sınırlara hapsedilmemelidir. Header, sidebar, tablolar, fiş girişleri ve rapor alanları ekranın tüm yatay genişliğini (%100) uçtan uca ferahça kullanmalıdır.
- **Genel Amaçlı, Kişisel Verisiz ve Sektör Bağımsız SEO & GEO Standardı**:
  GitHub ve genel açık kaynak dağıtımında; hiçbir kişisel veri (isim, soyisim, e-posta, kişisel adres vb.) barındırmadan, tek bir iş koluna (dernek, vakıf vb.) indirgemeksizin ve yasaklı terimlerden ('tekdüzen') kesinlikle arındırılmış biçimde genel ön muhasebe, cari takip, kasa yönetimi ve yevmiye fişi anahtar kelimeleriyle arama motoru (SEO), Open Graph, Twitter Cards, Schema.org ve ülke düzeyinde (TR / Türkiye) GEO meta etiketleri kullanılmalıdır. Tarayıcı sekme başlığı ise daima yalın ve sade `<title>oftek</title>` olarak korunmalıdır.
- **Yevmiye Fiş Girişinde Minimal Alan & Geniş Çalışma Alanı**:
  Fiş giriş sayfasında üst başlık ve form alanları ile alt toplam panelleri ultra-kompakt toolbar formatında tutulmalıdır. Dikeyde gereksiz boşluk bırakılmamalı, ekranın asıl odak noktası olan yevmiye satırları tablosuna maksimum çalışma alanı (`min-h-[460px]`, `overflow-y-auto`) tahsis edilmelidir. Başlangıçta kullanıcıyı boğmamak adına tek (1) boş satırla açılmalı, kullanıcı `Tab` veya `F2` ile ihtiyaç duydukça yeni satırları açmalıdır.
- **Kırmızı Alanın (Danger Zone) Konumu & Özel Ayarlar Sayfası**:
  Kullanıcının yanlışlıkla dokunması felakete yol açabilecek tüm kritik veritabanı sıfırlama veya tehlike aksiyonları ana sayfa (Dashboard) veya günlük çalışma alanlarında asla yer almamalıdır. Bu aksiyonlar bağımsız bir "Sistem & Ayarlar" sayfasına taşınmalı, açık ve kırmızı ikaz kutusu içine alınmalı ve her daim çift doğrulamalı ("SIFIRLA" yazma şartı) onay pencereleri ile korunmalıdır. Ayarlar sayfası aynı zamanda personel türleri, borç çeşitleri, veri aktarım araçları ve sistem teknik bilgilerini merkezi olarak barındırmalıdır.
- **Otomatik Tamamlamada Tab ile İlk Seçeneği Seçme & Akıcı Hücre Geçişi**:
  Kullanıcı fiş veya form veri girişi yaparken bir hesabı, açıklamayı, personeli veya cariyi aradığı anda açılan listede en üstteki (ilk) seçenek varsayılan olarak seçili ve görsel `Tab ⇥` ipucuyla hazırda beklemelidir. Kullanıcı `Tab` (veya `Enter`) tuşuna bastığı anda en üstteki seçenek anında hücreye yerleştirilmeli, liste kapatılmalı ve odaklanma doğrudan bir sonraki hücreye (Hesap -> Açıklama -> Borç -> Alacak -> Yeni Satır) kaymalıdır. Böylece fareye hiç dokunmadan seri, kesintisiz masaüstü muhasebe veri girişi sağlanmalıdır.
- **API Rota Yönlendirme Emniyeti ve Süreç Yönetimi**:
  Router modüllerinde (`api_handlers.py`) rota eşleşme kontrolü `if res is not None:` şeklinde değil, `if status is not None:` şeklinde yapılmalıdır. Böylece boş sonuç dönen başarılı HTTP 200 istekleri (örneğin henüz açık gün oturumu yokken dönen `{}`) router tarafından "rotanın bulunamadığı" yanılgısına düşerek 404 üretmez. Ayrıca sunucu güncellemelerinde arka plandaki eski port dinleyen süreçler (Zombie PID) tamamen temizlenmeli, yeni rotalar canlıda test edilerek doğrulanmalıdır.
- **Taşınabilir (USB / Flash Bellek) Ortamında Python Konumlandırma Standardı**:
  Kullanıcı uygulamayı USB veya harici sürücüde çalıştırdığında `baslat.bat` (`F:\oftek\baslat.bat`) ile taşınabilir Python (`F:\python\python.exe`) genellikle yan dizinde veya sürücü kökünde yer alır. `baslat.bat` öncelikle `%~dp0python\python.exe` (dahili gömülü Python), ardından `%~dp0..\python\python.exe` (üst/yan dizin), `%~d0\python\python.exe` (sürücü kökü) ve sistem PATH'ini tarayarak Python'ı otomatik tespit etmelidir.
- **Kurum ve Şahıs Bağımsızlığı & Genel Amaçlı Açık Kaynak Kimliği**:
  oftek, herhangi bir tek kuruluşa veya kişiye özel olmayıp, tüm tüzel veya kâr amacı gütmeyen kuruluşların (KOBİ, Şirket, Dernek, Vakıf, Kooperatif, Eğitim Kurumu) kendi bünyelerinde bağımsız çalıştırabilecekleri açık kaynak bir standart olarak korunmalıdır. Kurum kimliği, unvanı, türü ve para birimi (`sistem_ayarlari`) dinamik olmalı, kod tabanında veya arayüzde asla şahıs isimleri veya dar kurumsal kısıtlamalar bulunmamalıdır.
- **GitHub Açık Kaynak & Veri Güvenliği Standardı**:
  Kullanıcının kendi yerel `muhasebe.db` veritabanı asla GitHub deposuna itilmemelidir (`.gitignore`). Repoyu klonlayan herkes sıfır kurulumda `init_database()` ile temiz fabrika ayarlarına sahip veritabanını otomatik üretmelidir. Gömülü Python klasörü (`python/`) repo boyutunu şişirmemesi adına depoya dahil edilmez; Windows taşınabilir paketleri GitHub Releases üzerinden dağıtılır.
- **SQLite B-Tree İndeksleri & Yüksek Sorgu Performansı**:
  Operasyonel hızın yüksek kalması için fiş satırları, hesap kodları, cari durumlar, gün oturumları ve personel tahakkukları gibi kritik sorgu alanlarında SQLite B-Tree indeksleri (`idx_*`) daima devrede tutulmalıdır.
- **Python Embedded (Gömülü Python) `._pth` ve `sys.path` Standartları**:
  Windows gömülü Python (`python-embed`) sürümlerinde güvenlik nedeniyle çalışma dizini varsayılan olarak `sys.path`'e dahil edilmez. Bu sebeple:
  1. `python/python311._pth` dosyasına mutlaka `..` satırı ve `import site` eklenmelidir.
  2. `app.py` ve `server.py` gibi giriş noktalarının en başında `BASE_DIR` hesaplanıp `if BASE_DIR not in sys.path: sys.path.insert(0, BASE_DIR)` koruması mutlak surette uygulanmalıdır. Bu sayede gömülü Python ister doğrudan ister bat ile çağrılsın tüm modüller (`db_manager`, `api_handlers` vb.) eksiksiz çözümlenir.
- **Frontend Modüler Mimarisi & SRP Ayrıştırması**:
  Tek ve devasa bir monolitik HTML içinde binlerce satır JavaScript tutmak yerine, iş mantıkları sorumluluklarına göre ayrıştırılmalıdır (`web/js/api.js`, `session.js`, `dashboard.js`, `debts.js`, `receivables.js`, `employees.js`, `vouchers.js`, `accruals.js`, `accounts.js`, `settings.js`, `reports.js`, `app.js`). Özel CSS kuralları `web/css/style.css`'e taşınmalıdır. Bu sayede kod okunabilirliği, bakım kolaylığı ve hata ayıklama hızı en üst düzeye çıkarılır; HTML şablonu %60'tan fazla hafifler.
- **Header Ay Seçicisinin Kaldırılması & Süreç Odaklı Tarih Mantığı**:
  Genel sistem başlığında (Header) yer alan global ay seçici, kullanıcılar için kafa karışıklığı yaratmakta ("geçmiş veya gelecek aya fiş kesersem ne olur?", "ara günlerde ne yapmalıyım?") ve gereksiz bir filtre baskısı oluşturmaktadır. Bu sebeple Header sadece genel çalışma Mali Yılını (`2026`, `2025`) barındırmalı; operasyonel işlemler tamamen serbest işlem tarihiyle çalışmalı, ay bazlı filtreler ise yalnızca ait oldukları yer olan Raporlama ve Personel Tahakkuk ekranlarında yerel filtre olarak sunulmalıdır.
- **İstemci Taraflı SheetJS ile Sıfır Yükle Excel (.xlsx) İndirme**:
  Sistem taşınabilir ve sıfır dış bağımlılık prensibini korurken, kullanıcıya Excel raporları sunmak için backend'e ağır kütüphaneler (openpyxl, pandas vb.) eklenmemelidir. Bunun yerine frontend'de CDN üzerinden veya yerel önbellekten çalışan SheetJS kütüphanesi (`xlsx.full.min.js`) kullanılarak `XLSX.utils.json_to_sheet()` ve `XLSX.writeFile()` ile doğrudan istemci tarafında saniyeler içinde zengin `.xlsx` dosyaları oluşturulmalı ve indirilmelidir.
- **Dışa Aktarma Değil, Ekran İçi Canlı & Filtrelenebilir Raporlama Önceliği**:
  Finansal verileri sürekli CSV veya Excel dosyası olarak dışarı aktarıp harici araçlarda incelemek hem veri gizliliği/güvenliği açısından risklidir hem de kullanıcıyı sürekli dosya yönetimiyle uğraştırır. Bunun yerine sistem içi raporlama;
  1. Hızlı dönem butonları (`[Bugün]`, `[Bu Hafta]`, `[Bu Ay]`, `[Bu Yıl]`, `[Tümü]`) ve serbest tarih aralığı sunmalı (0 dropdown),
  2. Kullanıcı klavyeden yazdıkça tabloyu gecikmesiz süzmeli (Instant Search) ve özet kartlarını filtreye göre dinamik olarak anlık yeniden toplamalı,
  3. Muavin Defteri (Hesap Ekstresi) ile herhangi bir hesabın yürüyen bakiyesini ve hareketlerini anında ekrana getirmeli,
  4. Satırdaki herhangi bir fişe tıklandığında sayfadan hiç çıkmadan çift taraflı (Borç=Alacak) yevmiye fişi detayını pop-up modal içinde denetletmelidir. Böylece kullanıcı harici hiçbir dosyaya veya programa ihtiyaç duymadan tüm denetim ve analizini sistem içinde en yüksek hızla yapabilmelidir.
- **Kurumsal Logo Varlıklarının Ayrımı & Responsive Ölçeklendirme**:
  Uygulama genelinde iki farklı logo türü amaca göre kullanılmalıdır:
  1. **Sade Logo (`logo-sade.png` / Amblem):** Yanında zaten kurum/sistem başlığı metin olarak yer alan kompakt alanlarda (Header sol amblem, Favicon, Ayarlar profil kutusu, Kılavuz üst barı) kullanılmalıdır. Böylece metin + amblem çakışması veya kalabalık görünüm engellenir, yükseklik `h-9` / `h-10` (`max-w-[42px]`) ile orantılanmalıdır.
  2. **İsimli Logo (`logo-isim.png` / Amblem + OFTEK):** Geniş ve bağımsız vitrin alanlarında (Dashboard karşılama banner'ı, Ayarlar Sistem Bilgisi kartı, Kılavuz Giriş bölümü, Open Graph ve Twitter Cards) kullanılmalıdır. Yükseklik `h-14` / `h-16` aralığında tutularak marka kimliği güçlü ve net biçimde öne çıkarılmalıdır.
