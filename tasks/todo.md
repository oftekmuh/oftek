# oftek - Ön Muhasebe & Gün Sonu Fiş Entegrasyonu Yol Haritası

## Mevcut Durum & Analiz
- [x] Mevcut kod yapısının incelenmesi (Eski sunucu ve HTML yapısı)
- [x] Eksik modüllerin ve gereksinimlerin tespiti
- [x] Kullanıcının yeni isterlerinin (Seçimli Dağıtım + Yıl/Ay Dönemsellik) planlanması

## Faz 1: Veritabanı Şeması & Veri Modeli
- [x] Veritabanı Şemasının Temel Tasarımı (`db_manager.py`)
- [x] Şemaya `donem_yil` ve `donem_ay` kolonlarının eklenmesi (alacaklar, borclar, personel_tahakkuklari, gun_oturumlar, gunluk_islemler)
- [x] Personel Tahakkukları tablosuna mükerrer bordro önleme kısıtı (`UNIQUE(personel_id, donem_yil, donem_ay, tur)`) eklenmesi
- [x] Demo verilerin tamamen temizlenmesi (Fişler, cariler, personeller, alacak/borçlar sıfırlandı)

## Faz 2: Backend & Hesaplama Motoru
- [x] `accounting_engine.py` & `accounting_voucher.py`:
  - FIFO Otomatik Dağıtım motoru
  - Seçimli / Manuel Fatura Dağıtım motoru (`secimler: [{"alacak_id": 1, "tutar": 500}]`)
  - Yıl/Ay parametreli maaş ve prim tahakkuk motoru
  - Gün sonu yevmiye fişi motoru ve Borç = Alacak denkliği kontrolü
- [x] REST API Uç Noktalarının Modüler Tasarımı (Tüm modüller < 300 satır):
  - `api_handlers.py` (ana yönlendirici)
  - `handlers_session.py` (gün açma, gün kapatma, aktif oturum)
  - `handlers_debts.py` (cari firma borçları, fatura girişi, parçalı ödeme)
  - `handlers_employees.py` (personel kartları, dönemsel maaş tahakkuku, avans ödeme)
  - `handlers_receivables.py` (kategori bazlı alacaklar, FIFO ve Seçimli tahsilat dağıtımı)
  - `handlers_accounts.py` (Excel ile toplu hesap planı içe aktarımı `/api/accounts/bulk`)
- [x] Yerel HTTP Sunucusu & Otomatik Tarayıcı Açıcı (`server.py` ve `app.py`)

## Faz 3: Kullanıcı Arayüzü (Frontend)
- [x] Global Yıl & Ay Dönem Seçicisi (Header'da dinamik dönem filtresi)
- [x] Günlük Operasyon Çubuğu (Aktif Gün Rozeti, Gün Aç / Gün Kapat, Ara Günler Desteği)
- [x] Cari Borç Takip Ekranı (Firma bazlı, faturalar, parçalı ödeme modalı)
- [x] Personel Yönetim Ekranı (Personel kartları, dönemsel [Yıl-Ay] maaş tahakkuk butonu, anlık borç takibi, parçalı avans formu)
- [x] Alacak Takip Ekranı (Kategori bazlı filtre, Açık fatura listesi, Çift Modlu Tahsilat Modalı: [Otomatik FIFO Dağıt] veya [Faturaları Seçerek Dağıt])
- [x] Gün Kapatma Özeti & Otomatik Oluşan Yevmiye Fişi Görüntüleme Modalı
- [x] Excel ile Hesap Planı Yükleme Modalı & Örnek Şablon İndirme Butonu (`web/index.html` + SheetJS)
- [x] Mobil Uyumlu Alt Menü ve Responsive Tasarım

## Faz 4: Doğrulama & Test
- [x] 7/7 Başarılı Test (`python -m unittest discover tests`)
- [x] Excel toplu yükleme ve veritabanı doğrulama testi (`tests/test_excel_bulk.py`)
- [x] USB / Flash disk taşınabilir çalıştırma betiği (`baslat.bat` ve `app.py` - CRLF / UTF-8 uyumlu)

## Faz 5: Normal Gelir & Gider Günlük Fişi ve Demo Veri Temizliği
- [x] Backend: `gunluk_islemler` tablosuna `karsi_hesap` ve `kategori` kolonları ve migrasyonu (`db_manager.py`)
- [x] Backend: Standart hesap planına `770.02..05`, `642.01`, `649.01`, `679.01` hesapları eklenmesi (`db_manager.py`)
- [x] Backend: `NORMAL_GIDER` (Borç 770.xx / Alacak Kasa-Banka) ve `NORMAL_GELIR` (Borç Kasa-Banka / Alacak 649-600) çift taraflı yevmiye fiş üretimi (`accounting_voucher.py`)
- [x] Backend: `/api/quick-expense` ve `/api/quick-income` REST API uç noktaları (`handlers_session.py`)
- [x] Frontend: Dashboard ve Günlük Kasa sekmelerinde `[Hızlı Gider Fişi]` ve `[Hızlı Gelir Fişi]` butonları (`web/index.html`)
- [x] Frontend: Hızlı Gider Modalı (`modal-quick-expense`) ve Hızlı Gelir Modalı (`modal-quick-income`) dinamik hesap eşleştirmesi ile (`web/index.html`)
- [x] Frontend: Günlük Kasa tablosunda ve Dashboard hareketlerinde `NORMAL_GIDER` ve `NORMAL_GELIR` rozet ve yön gösterimleri
- [x] Veritabanı: SQLite veritabanındaki tüm demo verilerin tamamen silinmesi, sıfır işlemle kullanıcıya hazır hale getirilmesi (`muhasebe.db`)
- [x] Test: 7/7 birim ve entegrasyon testlerinin başarıyla çalıştırılması

## Faz 6: Satır Satır Borç/Alacak Yevmiye Fişi Girişi
- [x] Backend: `POST /api/vouchers` ve `GET /api/vouchers/next-no` REST API uç noktaları (`handlers_vouchers.py`)
- [x] Backend: Fiş atomik kaydı, hesap kodu kontrolü ve Borç == Alacak eşitliği doğrulaması
- [x] Frontend: `modal-voucher-entry` çok satırlı fiş modalı (`web/index.html`)
- [x] Frontend: Dinamik satır ekleme/silme, hesap seçimi, canlı Borç/Alacak ve Fark hesaplama
- [x] Frontend: Dashboard, Günlük Kasa ve Yevmiye Defteri sekmelerine `[+ Yeni Fiş Girişi (Borç/Alacak)]` butonlarının yerleştirilmesi
- [x] Test & Doğrulama: 8/8 birim ve uçtan uca testler ile fiş kaydı ve mizan doğrulaması

## Faz 7: Fiş Sayfası, Kısayollar, Personel Tahakkuk Fişi ve Otomatik Tamamlama
- [x] Backend: Borç çeşitleri (`personel_borc_turleri`) tablosu & migrasyonu (`db_manager.py`)
- [x] Backend: Fiş tipleri güncellemesi (MAHSUP, DUZELTME, TAHAKKUK, ACILIS, KAPANIS) (`handlers_vouchers.py`)
- [x] Backend: Geçmiş açıklamalar autocomplete API'si (`GET /api/vouchers/descriptions`) (`handlers_vouchers.py`)
- [x] Backend: Personel Tahakkuk Fişi & Borç Çeşitleri CRUD ve Raporlama API'leri (`handlers_accruals.py` & `api_handlers.py`)
- [x] Backend: Personel Silme (`DELETE /api/employees?id=X`) ve Ekleme API desteği (`handlers_employees.py`)
- [x] Frontend: Sol Kenar Çubuğu (Sidebar) açma/kapatma (toggle / collapse) mekanizması
- [x] Frontend: Fişlerin pop-up yerine tam sayfa (`tab-voucher_entry`) olarak açılması
- [x] Frontend: Fiş satırlarında hesap kodu ve adı ile canlı arama ve otomatik tamamlama (Autocomplete)
- [x] Frontend: Fiş ve satır açıklamalarında veritabanından otomatik tamamlama (Autocomplete)
- [x] Frontend: Fiş Kısayolları (Ctrl+K: Kasa ile Dengele, Tab: Yeni Satır, Ctrl+D: Üst Satırı Kopyala, F2: Satır Ekle, Ctrl+S: Kaydet)
- [x] Frontend: Personel Tahakkuk Fişi tam sayfa görünümü (`tab-employee_accrual`), borç çeşitleri yönetimi ve ay/çeşit bazlı raporlama
- [x] Frontend: Dropdown (`<select>`) etiketlerinin tamamen kaldırılarak yerine Autocomplete / Combobox ve akıllı filtreli seçim bileşenlerinin getirilmesi
- [x] Test & Doğrulama: Tüm yeni API'ler ve birim testlerinin çalıştırılarak doğrulanması (11/11 Başarılı)

## Faz 8: Demo Verileri Temizleme, Kırmızı Tehlike Alanı, Personel Türleri ve Dinamik Ek Bilgiler
- [x] Veritabanı Şeması & Demo Veri Temizliği:
  - [x] `db_manager.py`: `personel_turleri` tablosu ve varsayılan türler eklenmesi
  - [x] `db_manager.py`: `personeller` tablosuna `personel_turu_kod` kolonu migrasyonu
  - [x] `db_manager.py`: `personel_ek_bilgiler` tablosu (`id`, `personel_id`, `baslik`, `veri_tipi`, `deger`)
  - [x] `muhasebe.db`: Tüm demo kayıtların sıfırlanması
- [x] Backend API Geliştirmeleri:
  - [x] `POST /api/system/reset-database`: Kırmızı tehlike alanı zorlaştırılmış sıfırlama endpoint'i (`handlers_session.py`)
  - [x] Personel Türleri API'si (`GET /api/employee-types`, `POST /api/employee-types`, `DELETE /api/employee-types`)
  - [x] Personel Ek Bilgileri ve Personel Türü Entegrasyonu (`handlers_employees.py`)
- [x] Frontend Geliştirmeleri (`web/index.html`):
  - [x] Kırmızı Tehlike Alanı (Danger Zone) ve "SIFIRLA" yazma zorunluluğu olan güvenli onay modalı
  - [x] Personel Türleri yönetimi ve seçim bileşeni (Dropdown KESİNLİKLE YOK, buton segmenti/filtreli seçim)
  - [x] Sınırsız Dinamik Personel Ek Bilgi Alanları (Başlık + [Metin|Sayı|Tarih] 3'lü buton segmenti + Değer + Sil)
  - [x] Personel kartlarında ek bilgilerin görsel rozetlerle gösterimi
- [x] Doğrulama & Test:
  - [x] Birim ve entegrasyon testlerinin yazılması (`tests/test_danger_zone_and_employee_fields.py`)
  - [x] Dropdown (`<select>`) ve yasaklı kelime kontrolleri (0 select, 0 tekdüzen)
  - [x] Testlerin çalıştırılması ve doğrulanması (14/14 Başarılı)

## Faz 9: Tam Genişlik (%100 Enlemesine Kullanım) & Sıfır SEO/GEO/Meta
- [x] `web/index.html`: Header ve Ana Gövdedeki `max-w-7xl` sınırlamalarının kaldırılarak tam ekran (%100) enlemesine yayılım sağlanması
- [x] `web/index.html`: SEO, GEO, robot, izleme ve harici meta etiketlerinin tamamen arındırıldığının doğrulanması
- [x] `tasks/lessons.md`: Tam genişlik (%100 layout) ve Sıfır SEO/GEO/Meta kurallarının kalıcı olarak işlenmesi
- [x] Doğrulama ve Test: 14/14 testin çalıştırılması, ekran genişlik ve meta kontrollerinin yapılması

## Faz 10: Yevmiye Fiş Ekranı Minimalleşme (Geniş Çalışma Alanı) & Başlangıçta 1 Satır
- [x] `web/index.html`: Fiş üst başlık ve form alanlarının ultra-kompakt toolbar haline getirilmesi
- [x] `web/index.html`: Alt toplam ve kısayol panelinin minimal tek satıra toparlanması
- [x] `web/index.html`: Tablo çalışma alanının (min-h, max-h, tam ekran yayılımı) genişletilmesi
- [x] `web/index.html`: `initVoucherEntryPage` ve `removeVoucherPageRow` fonksiyonlarında başlangıçta ve silmede 1 satır kuralının uygulanması
- [x] `tasks/lessons.md`: Fiş girişi kompakt toolbar ve 1 satır başlangıç prensiplerinin işlenmesi
- [x] Doğrulama ve Test: Testlerin çalıştırılması, dropdown ve yasaklı kelime kontrolleri (14/14 Başarılı)

## Faz 11: Kırmızı Alanın Ayarlar Sayfasına Taşınması & Sistem ve Ayarlar Merkezi
- [x] `web/index.html`: Sidebar ve Mobil menüye "Sistem & Ayarlar" butonlarının eklenmesi
- [x] `web/index.html`: `tab-ayarlar` sekmesinin oluşturulması (Personel Türleri, Borç Çeşitleri, Hesap Planı Araçları, Sistem Bilgisi ve Kırmızı Alan)
- [x] `web/index.html`: `switchTab` yönlendirmesi ve `loadSettingsPage()` JS yönetim fonksiyonlarının yazılması
- [x] Doğrulama ve Test: Dropdown (0 select), yasaklı kelime (0 tekdüzen) ve 15/15 test doğrulaması

## Faz 12: Otomatik Tamamlamada Tab ile İlk Seçeneği Seçme & Sonraki Hücreye Akıcı Odaklanma
- [x] `web/index.html`: `focusNextElement(currentEl)` akıllı odaklanma motorunun geliştirilmesi
- [x] `web/index.html`: `attachAccountAutocomplete` motorunda ilk seçeneğin varsayılan seçilmesi (`activeIdx = 0`), görsel `Tab ⇥` rozeti ve Tab/Enter ile seçilip doğrudan Açıklama hücresine geçişi
- [x] `web/index.html`: `attachDescriptionAutocomplete` motorunda ilk açıklamanın Tab ile seçilip doğrudan Borç hücresine geçişi
- [x] `web/index.html`: `attachEmployeeAutocomplete` ve `attachCariAutocomplete` motorlarına da Tab/Enter ile ilk seçeneği seçip sonraki alana odaklanma desteğinin kazandırılması
- [x] `tests/test_danger_zone_and_employee_fields.py`: `test_05` ile Tab otomatik seçim ve hücre geçişi mantığının regresyon testi (16/16 test Başarılı)
- [x] `tasks/lessons.md`: Tab-first-select ve seri klavye navigasyonu kuralının işlenmesi

## Faz 13: Sade oftek İsimlendirmesi & "Muhasebe" Adının Arındırılması
- [x] `web/index.html`: Tarayıcı sekme başlığının `<title>oftek</title>` olarak sadeleştirilmesi
- [x] `web/index.html`: Header başlığının yalın `oftek` ve alt sloganın `Operasyonel Takip & Gün Sonu Otomatik Fiş Sistemi` yapılması
- [x] `web/index.html`: Sidebar ve içerik alanlarındaki "muhasebe" kelimelerinin arındırılması (`Operasyonel İşlemler`, `Fişler & Defterler`, `Günlük Kasa & Operasyon Yönetimi`)
- [x] `server.py`, `app.py`, `baslat.bat`: Konsol ve çalıştırma başlıklarının sade `OFTEK` haline getirilmesi
- [x] `tests/test_danger_zone_and_employee_fields.py`: `<title>oftek</title>` ve sıfır "muhasebe" regresyon test doğrulaması (16/16 test Başarılı)
- [x] `tasks/lessons.md`: Sade oftek ve muhasebe adı yasağı kuralının kalıcı işlenmesi

## Faz 14: Sistem & Ayarlar API Düzeltmeleri, 404 Kök Neden Çözümü ve Süreç Güncellemesi
- [x] Backend Kök Neden Çözümü: `handlers_session.py` içinde açık oturum olmadığında `None, 200` yerine `({}, 200)` döndürülmesi
- [x] Backend Emniyeti: `api_handlers.py` içinde `res is not None` kontrolünün `status is not None` olarak güncellenmesi
- [x] Backend Uç Nokta Çift Yolu: `/api/system/reset-database` ve `/api/system/reset-all` rotalarının her ikisinin de desteklenmesi
- [x] Süreç & Port Yönetimi: Eski arka plan sunucu sürecinin sonlandırılması ve güncel `python app.py` sunucusunun başlatılması
- [x] Canlı API Sağlık Kontrolleri:
  - `GET /api/session/active` -> HTTP 200 `{}`
  - `GET /api/employee-types` -> HTTP 200 (6 adet varsayılan tür)
  - `GET /api/employee-debt-types` -> HTTP 200 (6 adet borç çeşidi)
  - `GET /api/vouchers/descriptions` -> HTTP 200
  - `POST /api/system/reset-database` (geçersiz onay) -> HTTP 400
  - `POST /api/system/reset-database` (SIFIRLA onayı) -> HTTP 200
- [x] Test Paketi: 21/21 birim ve entegrasyon testinin (`python -m unittest discover tests`) eksiksiz yeşil geçmesi
- [x] Belgeler: `tasks/todo.md` ve `tasks/lessons.md` güncellemeleri

## Faz 15: Taşınabilir USB / Flash Bellek baslat.bat Akıllı Python Tespiti
- [x] `baslat.bat`: Sürücü kökü ve üst dizindeki taşınabilir Python yollarının taranması (`%~dp0..\python\python.exe` ve `%~d0\python\python.exe`)
- [x] `F:\python\python.exe` ve `F:\oftek\baslat.bat` yapısının otomatik tespit edilmesi ve çalıştırılması
- [x] Detaylı hata konsol çıktısı: Python bulunamadığında aranan tüm konumların kullanıcıya listelenmesi
- [x] Dokümantasyon: `tasks/lessons.md` ve `tasks/todo.md` güncellemeleri

## Faz 16: Dahili Gömülü Python (Embedded Python) Entegrasyonu
- [x] Dahili Dizin: `oftek\python\` klasöründeki Python 3.11 Embedded paketinin incelenmesi
- [x] Embedded Yol Yapılandırması: `python311._pth` dosyasına `..` ve `import site` eklenerek proje kök dizininin `sys.path`'e otomatik dahil edilmesi
- [x] Runtime Emniyeti: `app.py` içine `BASE_DIR` hesaplaması ve `sys.path.insert(0, BASE_DIR)` korumasının eklenmesi
- [x] Başlatıcı Güncellemesi: `baslat.bat` 1. öncelik sırasına dahili `%~dp0python\python.exe` yolunun yerleştirilmesi
- [x] Doğrulama & Test: Dahili gömülü Python ile tüm birim testlerinin çalıştırılması (`.\python\python.exe -m unittest discover tests` -> 21/21 Başarılı)

## Faz 17: Kullanıcı Arayüzü Kılavuzu ve Markdown (.md) Dokümantasyonlarının Güncellenmesi
- [x] `kullanim_kilavuzu.html`: Son kullanıcılar için çevrimdışı, şık ve kapsamlı HTML kılavuzun oluşturulması
- [x] Web & Sunucu Entegrasyonu: `server.py` üzerinden `/kilavuz` rotası ve `index.html` üst menü / sidebar kılavuz bağlantıları
- [x] `flash_disk_kurulum_ve_s_f_r_i_z_rehberi.md`: Dahili Python 3.11 mimarisi ve sade oftek kurallarına göre yenilenmesi
- [x] `flash_disk_otomatik_ba_lat_c_s_f_r_i_z.md`: Gizli modlu başlatıcı şablonunun güncel dahili python yollarıyla güncellenmesi
- [x] `README.md`: Tüm mimariyi, özellikleri, klavye kısayollarını ve test talimatlarını içeren ana proje tanıtım belgesinin oluşturulması

## Faz 18: ZIP Arşivinden Çıkarma Uyarısı & Tıklanabilir / Kopyalanabilir Link Standartları
- [x] `kullanim_kilavuzu.html`: En üstte belirgin kırmızı ZIP arşivinden "Tümünü Ayıkla" uyarısı
- [x] `kullanim_kilavuzu.html`: Tüm web ve kılavuz bağlantılarının tıklanabilir ve tek tıkla panoya `[📋 Kopyala]` butonlu hale getirilmesi
- [x] `README.md` ve tüm `.md` belgeleri: ZIP'ten çıkarma şartı uyarısı ve tıklanabilir `http://localhost:8080` bağlantılarının işlenmesi

## Faz 19: GitHub Açık Kaynak Dönüşümü, Kurum Bağımsızlığı & Vitrin
- [x] Eski artık dosyaların temizliği (`eski_muhasebe_arayuzu.html`, `eski_muhasebe_sunucusu.py`)
- [x] Tohum verilerin modülerleştirilmesi (`db_seed.py`) ve `db_manager.py` SRP < 300 satır uyumu
- [x] SQLite B-Tree indeksleri (12 adet) ile sorgu ve rapor hızlandırması
- [x] Kurum / İşletme Profili altyapısı:
  - [x] `sistem_ayarlari` tablosu & migrasyonu (`db_manager.py`)
  - [x] `/api/settings/profile` GET/POST API rotaları (`handlers_settings.py`, `api_handlers.py`)
  - [x] Kurum kimliği kartı (0 dropdown, 6'lı buton segmenti) & dinamik marka başlığı (`web/index.html`)
  - [x] Kurum profili birim testleri (22/22 Başarılı)
- [x] GitHub Açık Kaynak Standart Dosyalarının Oluşturulması:
  - [x] `LICENSE` (MIT Lisansı - oftek Open Source Project)
  - [x] `.github/workflows/tests.yml` (Otomatik CI/CD Test Pipeline)
  - [x] `CONTRIBUTING.md` (Katkı Kuralları, SRP, 0 Dropdown, Kod Standartları)
  - [x] `SECURITY.md` (Güvenlik Politikası & Yerel Veri Emniyeti)
- [x] `.gitignore` Dosyasının Açık Kaynak Standardına Getirilmesi (`muhasebe.db` ve `python/` harici tutulması)
- [x] `README.md` Belgesinin GitHub Açık Kaynak Vitrini Haline Getirilmesi (Shields.io rozetleri, kurum bağımsızlığı, taşınabilir kurulum)
- [x] `kullanim_kilavuzu.html` Kılavuzuna Kurum Profili Yönetiminin Eklenmesi
- [x] Test & Doğrulama (22/22 Test, Kod Kontrolleri)

## Faz 20: Kullanıcı Bilgisi & Demo Veri Derin Denetimi ve Anonimlik Karar Protokolü
- [x] Proje dosyalarında kişisel ad, soyad, e-posta ve mutlak yol derin taraması (0 sızıntı doğrulandı)
- [x] `muhasebe.db` derin analizi: Tüm operasyonel tablolarda (fiş, cari, alacak, borç, personel vb.) 0 kayıt olduğu kanıtlandı
- [x] Katalog temizliği: Testlerden kalan geçici türler silindi, 6 standart personel türü ve 6 standart borç çeşidi fabrika ayarlarına çekildi
- [x] `proje_karar_anonim_yayinlama.md` yerel karar ve uygulama rehberi belgesi oluşturuldu
- [x] `proje_karar_anonim_yayinlama.md` belgesi `.gitignore` listesine eklenerek depoya gitmesi engellendi
- [x] 22/22 testin yeşil geçtiği doğrulandı

## Faz 21: Kişisel Verisiz, Yasaksız ve Sektör Bağımsız SEO & GEO Yapılandırması
- [x] `web/index.html`: Standart SEO meta etiketleri, Open Graph, Twitter Cards, Schema.org (SoftwareApplication) ve ülke geneli (TR) GEO etiketleri eklendi
- [x] `kullanim_kilavuzu.html`: Kılavuz sayfasına SEO ve GEO meta etiketleri eklendi
- [x] Kişisel veri (0 isim, 0 e-posta, 0 özel adres), yasaklı kelime ("tekdüzen" 0 eşleşme) ve sektör bağımsızlığı (dernek/vakıf vb. kısıtlama yok) denetlendi
- [x] Sekme başlığı (`<title>oftek</title>`) ve görünür arayüzün sade `oftek` kalması korundu
- [x] Tüm test paketi çalıştırıldı ve doğrulandı (22/22 Başarılı)

## Faz 22: Frontend Modüler Mimarisi (Monolitik index.html Ayrıştırma)
- [x] `server.py`: Statik dosya (`/js/*`, `/css/*`) MIME type sunucu yönlendiricisinin eklenmesi (171 satır, SRP < 300)
- [x] `web/css/style.css`: Özel CSS kurallarının `index.html`'den ayrıştırılması
- [x] `web/js/api.js`: Genel yardımcılar (`fmt`, `showToast`, `showModal`, `hideModal`, `focusNextElement`)
- [x] `web/js/session.js`: Gün oturumu (kontrol, açma/kapatma, hızlı gelir/gider)
- [x] `web/js/dashboard.js`: Dashboard kartları ve günlük kasa hareketleri
- [x] `web/js/debts.js`: Cari borç takibi, fatura ekleme, parçalı ödeme ve cari autocomplete
- [x] `web/js/receivables.js`: Alacak takibi, FIFO ve seçimli fatura tahsilat dağıtımı
- [x] `web/js/employees.js`: Personel kartları, türleri, dinamik ek alanlar ve personel yönetimi
- [x] `web/js/vouchers.js`: Yevmiye fiş girişi, klavye kısayolları (`Tab`, `Ctrl+K`, `Ctrl+D`, `F2`, `Ctrl+S`) ve autocomplete motorları
- [x] `web/js/accruals.js`: Personel tahakkuk fişi, borç çeşitleri ve dönemlik raporlama
- [x] `web/js/accounts.js`: Genel hesap planı, arama, Excel içe aktarımı ve mizan
- [x] `web/js/settings.js`: Kurum/işletme kimliği profili ve Kırmızı Alan veritabanı sıfırlama
- [x] `web/js/reports.js`: Merkezi raporlar ve SheetJS ile Excel (.xlsx) indirme motoru
- [x] `web/js/app.js`: Tab yönetimi (`switchTab`), mali yıl filtreleri, sidebar toggle ve başlatıcılar
- [x] `web/index.html`: Gömülü ~3.180 satırlık script'in temizlenip modüler `<script src="...">` etiketlerine bağlanması (5.187 satırdan 2.012 satıra indirildi)

## Faz 23: Header Ay Seçicisinin Sadeleştirilmesi & Merkezi Raporlama ve Excel (.xlsx) Çıktısı
- [x] Header'daki kafa karıştırıcı ay seçici popover ve butonunun tamamen kaldırılması, işlemlerin tarih odaklı çalışması
- [x] Header'da sadece temiz Mali Yıl (`2026`, `2025`) seçiminin bırakılması
- [x] Backend: `handlers_reports.py` (283 satır) içinde Kasa & Nakit Akış, Cari Bakiyeler, Personel Bordro ve Mizan API'lerinin geliştirilmesi
- [x] Frontend: Sidebar ve Mobil Menüye "Raporlar & Analiz" bağlantısının eklenmesi
- [x] Frontend: 4 alt sekmeli (Kasa & Nakit Akış, Cari Bakiyeler, Personel Bordro/Hakediş, Genel Mizan) Raporlama Merkezi (`tab-raporlar`)
- [x] Frontend: SheetJS ile sıfır backend yükü ve sıfır harici bağımlılıkla tek tıkla Excel (`.xlsx`) indirme motoru (`exportReportToExcel()`)
## Faz 24: Ekran İçi Hızlı, Ölçeklenebilir ve Filtrelenebilir Canlı Raporlama Merkezi
- [x] UI Tasarımı & Filtre Toolbar: 0 Dropdown prensibiyle Hızlı Dönem Butonları ([Bugün], [Bu Hafta], [Bu Ay], [Bu Yıl], [Tümü]), Serbest Başlangıç/Bitiş Tarihi ve Canlı Arama Inputu (`#rep-instant-search`)
- [x] 5. Alt Sekme Entegrasyonu: Muavin Defteri (Hesap Ekstresi & Yürüyen Bakiye) arayüz paneli ve hesap seçimi
- [x] Modül İçi Segment Filtreleri: Kasa/Banka (`[Tümü] [100 Kasa] [102 Banka]`), Cari Bakiyeler (`[Tümü] [Müşteriler] [Tedarikçiler]` ve `[Sadece Bakiyeliler]`)
- [x] Fiş İnceleme Modalı (`#modal-report-voucher-detail`): Sayfadan çıkmadan çift taraflı fiş hareketlerini inceleme
- [x] `web/js/reports.js` Motoru: Anlık klavye filtresi, dinamik özet kartı güncellemesi, hızlı dönem hesaplayıcı, muavin defteri ve fiş modalı yönetimi
- [x] Test & Doğrulama: 29/29 birim/regresyon testi ve tarayıcı filtreleme kontrolleri tamamlandı

## Faz 25: Yeni Kurumsal Logoların (Sade Logo & İsim+Logo) Entegrasyonu ve Yeniden Boyutlandırılması
- [x] Varlık Yönetimi: `logo-sade.png` ve `logo-isim.png` varlıklarının `web/img/` dizinine yerleştirilmesi, kök ve favicon yedeklerinin oluşturulması
- [x] Header & Favicon: Ana uygulama header'ında `logo-sade.png` kullanımı, favicon ve meta etiketlerinin güncellenmesi
- [x] Dashboard Banner: Hızlı işlemler banner alanında `logo-isim.png` kullanımı ve duyarlı ölçeklendirme
- [x] Ayarlar & Marka Kimliği: Kurum profili ve sistem bilgisi alanında yeni marka kimliği vitrininin eklenmesi
- [x] Kullanım Kılavuzu: `kullanim_kilavuzu.html` başlığında ve giriş bölümünde logoların şık boyutlandırmayla yerleştirilmesi
- [x] Test & Doğrulama: 30/30 birim/regresyon testinin yeşil geçmesi ve görsel denetim

## Faz 26: GitHub Public Depo Kurulumu (oftekmuh/oftek) & CI/CD Doğrulaması
- [x] Gizlilik & Anonimlik Kontrolü: 0 kişisel veri, anonim yazar (`oftek <contact@oftek.org>`) ve `.gitignore` denetimi
- [x] GitHub Organizasyonu: `oftekmuh` organizasyonu altında `oftek` genel (public) reposunun oluşturulması
- [x] Kod İtme (Push): Ana dalın (`main`) `https://github.com/oftekmuh/oftek` adresine başarıyla itilmesi
- [x] CI/CD Doğrulaması: GitHub Actions üzerinde Ubuntu/Windows ve Python 3.11/3.12 matrisinde tüm testlerin eksiksiz yeşil geçmesi

## Faz 27: Yerel Ağ ve Çoklu Cihaz (Wi-Fi / LAN) Giriş Özelliği ve Dokümantasyonu
- [x] Python Web Sunucusu Mimarisi: `server.py` `0.0.0.0:8080` üzerinde tüm yerel ağ arayüzlerini dinler; terminalde yerel IP (`http://192.168.1.X:8080`) yayınlanır
- [x] Dokümantasyon (`README.md`): Çoklu cihaz erişim özelliği ve "📱 Aynı Ağdaki Diğer Cihazlardan (Telefon / Tablet) Nasıl Girilir?" rehberi eklendi
- [x] Dokümantasyon (`kullanim_kilavuzu.html`): Sol menüye ve ana gövdeye "📱 Aynı Ağdaki Diğer Cihazlardan Erişim" görsel adımlı rehberi eklendi
- [x] Standartlar & Dersler (`tasks/lessons.md`): Yerel Ağ ve Çoklu Cihaz Girişi kuralı kaydedildi
- [x] Git & Depo Senkronizasyonu: Değişiklikler anonim kimlikle GitHub (`oftekmuh/oftek`) deposuna push edildi

## Faz 28: Dahili Python (~20 MB) Depo Entegrasyonu ve Gelişmiş Hata Teşhis Mekanizması
- [x] .gitignore Güncellemesi: `python/` klasörü dışlaması kaldırılarak gömülü Python motoru git takibine dahil edildi
- [x] `baslat.bat` Hata Teşhis & Geri Bildirim: Python bulunamadığında veya sunucu çöktüğünde kapanmayan (pause), renkli Türkçe teşhis, olası 4 neden ve net çözüm adımları sunan akıllı başlatıcı
- [x] Dokümantasyon (`kullanim_kilavuzu.html`): Sol menüye ve 13. Bölüme "🛠️ Olası Hatalar, Python Kurulumu ve Sorun Giderme Rehberi" (ZIP uyarısı, Defender, manuel Python kurma, port çakışması, mobil Wi-Fi) eklendi
- [x] Dokümantasyon (`README.md`): Dahili Python vurgusu, resmi python.org manuel kurulum adımları ve hızlı sorun giderme maddeleri eklendi
- [x] Standartlar & Dersler (`tasks/lessons.md`): Dahili Python ve Gelişmiş Hata Teşhis kuralı kaydedildi
- [x] Test & Doğrulama: 30/30 testin yeşil geçmesi ve GitHub'a push edilmesi

## Faz 29: baslat.bat Batch Syntax / Parantez Düzeltmesi ve Windows Konsol UTF-8 İyileştirmesi
- [x] `baslat.bat`: cmd.exe sözdizimi hatası (`The syntax of the command is incorrect`) yaratan parantez ve değişken blokları temizlendi, kurşun geçirmez tek satırlı yapıya geçirildi
- [x] `server.py`: Windows konsolunda Türkçe karakterlerin bozulmasını önleyen `sys.stdout.reconfigure(encoding="utf-8")` eklendi
- [x] Doğrulama: `cmd.exe /c baslat.bat` ile arka planda sunucunun sorunsuz ayağa kalktığı ve dinlediği doğrulandı
- [x] Test & Git: 30/30 test yeşil, anonim kimlikle GitHub'a push edildi

## Faz 30: Kriptografik Kimlik Doğrulama (Auth), Giriş Ekranı ve API Güvenlik Zırhı
- [x] Veritabanı Şeması (`db_manager.py`): `kullanicilar` ve `oturumlar` tabloları ve B-Tree indeksleri (`idx_oturumlar_token`, `idx_kullanicilar_kadi`)
- [x] Güvenlik Motoru (`auth_manager.py`): PBKDF2-HMAC-SHA256 (100.000 iterasyon + 16 byte tuz), `hmac.compare_digest`, token yönetimi (< 300 satır)
- [x] API Servisi (`handlers_auth.py`): Status, Setup, Login, Logout, Change-Password uç noktaları (< 300 satır)
- [x] API Yönlendirici & Güvenlik Bekçisi (`server.py` & `api_handlers.py`): Korumalı rotalar için 401 Unauthorized yetki kontrolü ve .db/.py dosya indirme engeli (HTTP 403)
- [x] Kullanıcı Arayüzü (`web/index.html`, `web/js/auth.js`): İlk Kurulum Sihirbazı, Güvenli Giriş (Login) Ekranı, Header [Çıkış Yap] butonu, kullanıcı rozeti ve Ayarlar Şifre Değiştirme
- [x] Testler & Doğrulama: `tests/test_auth.py` ile PBKDF2, yetkilendirme ve API zırh testlerinin yazılması, 35/35 testin eksiksiz yeşil geçmesi
- [x] Dokümantasyon & Git: `README.md`, `kullanim_kilavuzu.html`, `tasks/lessons.md` güncellemeleri ve GitHub push







