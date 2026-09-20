# oftek - Gizli Mod (Sıfır İz) Otomatik Başlatıcı Rehberi

Bu belge, **oftek** sistemini tarayıcı geçmişi ve çerez kırıntısı dahi bırakmadan doğrudan **Gizli Modda (InPrivate / Incognito)** çalıştırmak isteyen kullanıcılar için özel başlatıcı betik şablonunu içerir.

---

> ### ⚠️ ÇOK ÖNEMLİ: Dosyalar ZIP Arşivindeyse MUTLAKA ZİPTEN ÇIKARINIZ!
> Programı `.zip` (sıkıştırılmış arşiv) olarak taşıdıysanız, **kesinlikle zip penceresinin içindeyken başlatıcı çalıştırmayınız!**  
> Önce zip arşivine sağ tıklayıp **"Tümünü Ayıkla..."** diyerek dosyaları normal bir klasöre veya flash diske çıkartınız; ardından çalıştırınız.

---

## 1. Gizli Mod Başlatıcı Kodu (`baslat_gizli.bat`)

Dilerseniz aşağıdaki içeriği `baslat_gizli.bat` adında yeni bir dosya olarak kaydedip flash diskinize ekleyebilirsiniz:

```cmd
@echo off
title OFTEK - Gizli Mod Calistirici
chcp 65001 >nul
cd /d "%~dp0"

echo =======================================================
echo    OFTEK (TAŞINABİLİR / SIFIR İZ ÇALIŞMA MODU)
echo =======================================================
echo.
echo [*] Güvenlik: Bilgisayarda hiçbir çerez ve geçmiş bırakılmaz.
echo [*] Konum   : %~dp0
echo.

:: 1. Python önbellek kırıntılarını (.pyc / __pycache__) engelle
set PYTHONDONTWRITEBYTECODE=1
set PYTHONUNBUFFERED=1

:: 2. Dahili gömülü Python motorunu tespit et
set PYTHON_EXE=
if exist "%~dp0python\python.exe" set PYTHON_EXE="%~dp0python\python.exe"
if not defined PYTHON_EXE if exist "%~dp0..\python\python.exe" set PYTHON_EXE="%~dp0..\python\python.exe"
if not defined PYTHON_EXE if exist "%~d0\python\python.exe" set PYTHON_EXE="%~d0\python\python.exe"
if not defined PYTHON_EXE where python >nul 2>nul && set PYTHON_EXE=python

if not defined PYTHON_EXE (
    echo [HATA] Python motoru bulunamadı!
    pause
    exit /b 1
)

:: 3. HTTP sunucusunu arka planda başlat
echo [*] Sunucu başlatılıyor...
start /b "" %PYTHON_EXE% app.py >nul 2>&1

:: 4. Sunucunun hazır olması için kısa bir bekleme (1.5 saniye)
timeout /t 2 /nobreak >nul

:: 5. Tarayıcıyı bilgisayarda HİÇBİR GEÇMİŞ/ÇEREZ bırakmaması için GİZLİ SEKMEDE aç
echo [*] Tarayıcı Gizli/InPrivate modda açılıyor...
start msedge -inprivate http://localhost:8080 || start chrome --incognito http://localhost:8080 || start firefox -private-window http://localhost:8080 || start http://localhost:8080

echo.
echo =======================================================
echo   SİSTEM AKTİF!
echo   Tüm veriler yalnızca bu sürücüdeki 'muhasebe.db'
echo   dosyasına yazılmaktadır. Bilgisayara hiçbir şey kaydedilmez.
echo.
echo   Kapatmak istediğinizde bu siyah pencereyi kapatınız.
echo =======================================================
echo.

:: Pencere açık kalsın, kullanıcı kapatana kadar sunucu çalışır
pause >nul
```

---

## 2. Neden Bu Mod Tercih Edilir?
- **Sıfır Tarayıcı Geçmişi:** Misafir veya ortak kullanılan bir bilgisayarda çalışırken girilen finansal kayıtlar veya açılan sekmeler tarayıcının geçmişine eklenmez.
- **Sıfır Çerez:** Oturum kapatıldığında geçici bellek anında temizlenir.
- **Tam Bağımsızlık:** Program yalnızca flash disk içindeki veritabanı dosyasına (`muhasebe.db`) okuma ve yazma yapar.

---

## 3. Tıklanabilir Bağlantılar
- **Web Ekranı:** [http://localhost:8080](http://localhost:8080) veya [http://127.0.0.1:8080](http://127.0.0.1:8080)
- **Kılavuz:** [http://localhost:8080/kilavuz](http://localhost:8080/kilavuz)