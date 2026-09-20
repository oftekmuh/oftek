@echo off
chcp 65001 >nul
title oftek - Baslatiliyor...
cd /d "%~dp0"

set PYTHONDONTWRITEBYTECODE=1
set PYTHONUNBUFFERED=1

set PYTHON_EXE=
set PYTHON_SOURCE=

:: 1. ÖNCELİK: Proje dizini içindeki dahili gömülü Python (Örn: oftek\python\python.exe)
if exist "%~dp0python\python.exe" (
    set PYTHON_EXE="%~dp0python\python.exe"
    set PYTHON_SOURCE=Dahili Gömülü Python (%~dp0python)
    goto :found_python
)

:: 2. ÖNCELİK: Bir üst dizindeki / yan klasördeki Python (Örn: F:\python\python.exe)
if exist "%~dp0..\python\python.exe" (
    set PYTHON_EXE="%~dp0..\python\python.exe"
    set PYTHON_SOURCE=Üst Dizin Python (%~dp0..\python)
    goto :found_python
)

:: 3. ÖNCELİK: Sürücü kökündeki Python (Örn: F:\python\python.exe)
if exist "%~d0\python\python.exe" (
    set PYTHON_EXE="%~d0\python\python.exe"
    set PYTHON_SOURCE=Sürücü Kökü Python (%~d0\python)
    goto :found_python
)

:: 4. Alternatif taşınabilir Python klasörleri
if exist "%~dp0python-embed\python.exe" (
    set PYTHON_EXE="%~dp0python-embed\python.exe"
    set PYTHON_SOURCE=Dahili Python-Embed (%~dp0python-embed)
    goto :found_python
)
if exist "%~dp0..\python-embed\python.exe" (
    set PYTHON_EXE="%~dp0..\python-embed\python.exe"
    set PYTHON_SOURCE=Üst Dizin Python-Embed (%~dp0..\python-embed)
    goto :found_python
)

:: 5. Sistem PATH'inde python var mı?
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_EXE=python
    set PYTHON_SOURCE=Sistem Ortamı (PATH)
    goto :found_python
)

:: 6. Standart Windows Kullanıcı Kurulum Yolları
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set PYTHON_EXE="%LocalAppData%\Programs\Python\Python312\python.exe"
    set PYTHON_SOURCE=Kullanıcı Python 3.12 (%LocalAppData%\Programs\Python\Python312)
    goto :found_python
)
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set PYTHON_EXE="%LocalAppData%\Programs\Python\Python311\python.exe"
    set PYTHON_SOURCE=Kullanıcı Python 3.11 (%LocalAppData%\Programs\Python\Python311)
    goto :found_python
)
if exist "%LocalAppData%\Programs\Python\Python310\python.exe" (
    set PYTHON_EXE="%LocalAppData%\Programs\Python\Python310\python.exe"
    set PYTHON_SOURCE=Kullanıcı Python 3.10 (%LocalAppData%\Programs\Python\Python310)
    goto :found_python
)

:: ============================================================================
:: PYTHON HİÇBİR YERDE BULUNAMADIYSA AYRINTILI HATA VE GERİ BİLDİRİM EKRANI
:: ============================================================================
cls
color 0C
echo ================================================================================
echo                         [!] KRITIK HATA: PYTHON BULUNAMADI
echo ================================================================================
echo.
echo oftek sistemi calisabilmek icin Python motoruna ihtiyac duymaktadir.
echo Ancak aranan hicbir konumda "python.exe" tespit edilemedi!
echo.
echo --------------------------------------------------------------------------------
echo OLASI NEDENLER VE COZUM ADIMLARI:
echo --------------------------------------------------------------------------------
echo.
echo [1] EN SIK KARSILASILAN HATA: ZIP'TEN CIKARMADAN CALISTIRMA
echo     Eger projeyi .ZIP (sikistirilmis) arsiv icinden dogrudan actiysaniz, Windows
echo     dosyalari gecici bellekte calistirir ve "python" klasorunu goremez.
echo     ---^> COZUM: .zip dosyasina sag tiklayip "Tumunu Ayikla..." (Klasore Cikar)
echo     secenegini kullanin ve cikarilan klasordeki baslat.bat'i calistirin.
echo.
echo [2] "python" KLASORU EKSIK VEYA SILINMIS OLABILIR
echo     Proje dizinindeki dahili "python" klasoru tasinirken kopyalanmamis olabilir.
echo     Aranan yer: %~dp0python\python.exe
echo     ---^> COZUM: Projeyi GitHub'dan (https://github.com/oftekmuh/oftek)
echo     eksiksiz olarak tekrar indiriniz.
echo.
echo [3] WINDOWS DEFENDER VEYA ANTIVIRUS ENGELI
echo     Guvenlik yaziliminiz "python.exe"yi yanlislikla karantinaya almis olabilir.
echo     ---^> COZUM: Antivirus / Windows Guvenlik gecmisini kontrol edip bu klasore
echo     izin veriniz (Istisnalara ekleyiniz).
echo.
echo [4] SISTEM GENELINE PYTHON KURMAK ISTERSENIZ (ALTERNATIF)
echo     Sisteminizde Python kurulu degilse kendiniz de kolayca kurabilirsiniz:
echo     1. https://www.python.org/downloads/ adresine gidin.
echo     2. Python 3.10, 3.11 veya 3.12 surumunu indirin.
echo     3. Kuruluma baslarken EN ALTTAKI "Add Python to PATH" (Python'i PATH'e ekle)
echo        kutusunu MUTLAKA isaretleyin ve oyle kurun!
echo     4. Kurulum bitince bu baslat.bat dosyasini tekrar calistirin.
echo.
echo ================================================================================
echo Ayrintili rehber ve cozumler icin "kullanim_kilavuzu.html" sayfasini aciniz.
echo ================================================================================
echo.
pause
exit /b 1

:: ============================================================================
:: PYTHON BULUNDU - SUNUCUYU BAŞLAT
:: ============================================================================
:found_python
cls
title oftek - Calisiyor
echo ================================================================================
echo                                  OFTEK
echo               Operasyonel Takip ^& Gun Sonu Otomatik Fis Sistemi
echo ================================================================================
echo.
echo [*] Python Motoru  : %PYTHON_SOURCE%
echo [*] Python Yolu    : %PYTHON_EXE%
echo [*] Yerel Sunucu   : http://localhost:8080
echo [*] Kullanim Kilavuzu: http://localhost:8080/kilavuz (veya kullanim_kilavuzu.html)
echo.
echo [*] Cikis yapmak icin bu konsol penceresini kapatabilir veya Ctrl+C yapabilirsiniz.
echo.
echo --------------------------------------------------------------------------------
echo Sunucu baslatiliyor, tarayiciniz otomatik acilacaktir...
echo --------------------------------------------------------------------------------
echo.

%PYTHON_EXE% app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    color 0C
    echo ================================================================================
    echo                   [HATA] OFTEK SUNUCUSU BEKLENMEDIK SEKILDE KAPANDI!
    echo ================================================================================
    echo.
    echo Olası Sorunlar:
    echo 1. 8080 numarali port baska bir program tarafindan kullaniliyor olabilir.
    echo 2. Onceki oftek oturumu arka planda acik kalmis olabilir (Gorev Yoneticisinden
    echo    python.exe sureclerini sonlandirabilirsiniz).
    echo 3. Veritabani dosyasi (muhasebe.db) salt-okunur bir surucude veya kilitli olabilir.
    echo.
    echo Ayrintili cozumler icin "kullanim_kilavuzu.html" dosyasini inceleyiniz.
    echo ================================================================================
    echo.
    pause
)
