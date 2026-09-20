# oftek Güvenlik Politikası (SECURITY)

Güvenlik ve kullanıcı verilerinin gizliliği, **oftek** projesinin en temel önceliklerinden biridir.

---

## 🛡️ Desteklenen Sürümler

| Sürüm | Destek Durumu |
| :--- | :--- |
| 1.x (Güncel Main) | :white_check_mark: Tam Destekleniyor |
| < 1.0 (Deneysel) | :x: Desteklenmiyor |

---

## 🔒 Güvenlik Mimarisi & Veri Gizliliği

oftek, doğası gereği **"Gizlilik Öncelikli" (Privacy-First)** ve **"Kapalı Devre"** çalışacak şekilde tasarlanmıştır:

1. **Sıfır Bulut Bağımlılığı & Sıfır Telemetri:**
   - oftek hiçbir harici sunucuya, buluta veya üçüncü taraf analitik servisine veri göndermez.
   - Kod tabanında izleyici (tracker), telemetri veya harici CDN çağrısı bulunmaz.
2. **Yerel SQLite Depolama:**
   - Tüm finansal veriler, personeller ve yevmiye kayıtları yalnızca yerel makinedeki `muhasebe.db` dosyasında tutulur.
3. **Savunmacı Kodlama (Defensive Coding) & SQL Enjeksiyon Koruması:**
   - Veritabanı sorgularında asla string birleştirme (`concatenation`) kullanılmaz. Tüm sorgular istisnasız **parametreli sorgular (`?` yer tutucular)** ile çalışır.
4. **Çift Korumalı Sıfırlama (Kırmızı Alan):**
   - Yanlışlıkla veri kaybını önlemek amacıyla sıfırlama isteklerinde doğrudan "SIFIRLA" onay dizesi aranır ve doğrulama yapılmadan hiçbir işlem gerçekleştirilmez.

---

## 🚨 Güvenlik Açığı Bildirimi

Eğer oftek projesinde bir güvenlik açığı, veri bütünlüğü riski veya zafiyet tespit ederseniz:

1. Lütfen açığı **herkese açık GitHub Issues üzerinde paylaşmayınız**.
2. GitHub'ın **"Security Advisory"** (Güvenlik Bildirimi) sekmesini kullanarak gizli bir bildirim oluşturunuz veya proje yöneticilerine özel kanal üzerinden iletiniz.
3. Bildiriminizde şu detaylara yer vermeniz süreci hızlandıracaktır:
   - Zafiyetin türü ve etki alanı.
   - Yeniden üretme (reproduce) adımları veya PoC (Proof of Concept) kodu.
   - Olası çözüm veya yama önerisi.

Güvenlik bildirimleri en geç 48 saat içerisinde değerlendirilecek ve gerekli yamalar öncelikle test edilerek depoya aktarılacaktır.
