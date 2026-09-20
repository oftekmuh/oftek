@echo off
chcp 65001 >nul
title OFTEK - Baslatiliyor...
cd /d "%~dp0"

set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUNBUFFERED=1"
set "PYTHON_EXE="

REM 1. ONCELIK: Proje dizini icindeki dahili Python (oftek\python\python.exe)
if exist "%~dp0python\python.exe" (
    set "PYTHON_EXE=%~dp0python\python.exe"
    goto :found_python
)

REM 2. ONCELIK: Ust dizindeki veya yan klasordeki Python
if exist "%~dp0..\python\python.exe" (
    set "PYTHON_EXE=%~dp0..\python\python.exe"
    goto :found_python
)

REM 3. ONCELIK: Surucu kokundeki Python (F:\python\python.exe)
if exist "%~d0\python\python.exe" (
    set "PYTHON_EXE=%~d0\python\python.exe"
    goto :found_python
)

REM 4. ONCELIK: Alternatif python-embed klasorleri
if exist "%~dp0python-embed\python.exe" (
    set "PYTHON_EXE=%~dp0python-embed\python.exe"
    goto :found_python
)
if exist "%~dp0..\python-embed\python.exe" (
    set "PYTHON_EXE=%~dp0..\python-embed\python.exe"
    goto :found_python
)

REM 5. ONCELIK: Sistem PATH ortaminda kurulu python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_EXE=python"
    goto :found_python
)

REM 6. ONCELIK: Standart Windows kullanici yukleme konumlari
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
    goto :found_python
)
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
    goto :found_python
)
if exist "%LocalAppData%\Programs\Python\Python310\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python310\python.exe"
    goto :found_python
)

REM ============================================================================
REM PYTHON BULUNAMADI - DETAYLI HATA VE YONLENDIRME
REM ============================================================================
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
echo     Eger projeyi .ZIP arsiv icinden dogrudan actiysaniz, Windows dosyalari
echo     gecici bellekte calistirir ve "python" klasorunu goremez.
echo     ---^> COZUM: .zip dosyasina sag tiklayip "Tumunu Ayikla..." secenegini
echo     kullanin ve cikarilan klasordeki baslat.bat'i calistirin.
echo.
echo [2] "python" KLASORU EKSIK VEYA SILINMIS OLABILIR
echo     Proje dizinindeki dahili "python" klasoru tasinirken kopyalanmamis olabilir.
echo     Aranan yer: %~dp0python\python.exe
echo     ---^> COZUM: Projeyi GitHub'dan eksiksiz olarak tekrar indiriniz:
echo     https://github.com/oftekmuh/oftek
echo.
echo [3] WINDOWS DEFENDER VEYA ANTIVIRUS ENGELI
echo     Guvenlik yaziliminiz "python.exe"yi karantinaya almis olabilir.
echo     ---^> COZUM: Antivirus gecmisini kontrol edip bu klasore izin veriniz.
echo.
echo [4] SISTEM GENELINE PYTHON KURMAK ISTERSENIZ
echo     1. https://www.python.org/downloads/ adresine gidin.
echo     2. Python 3.10 veya uzeri surumunu indirin.
echo     3. Kurarken "Add Python to PATH" kutusunu MUTLAKA isaretleyin!
echo     4. Kurulum bitince baslat.bat'i tekrar calistirin.
echo.
echo ================================================================================
echo Ayrintili rehber icin "kullanim_kilavuzu.html" dosyasini acabilirsiniz.
echo ================================================================================
echo.
pause
exit /b 1

REM ============================================================================
REM PYTHON BULUNDU - SUNUCUYU BASLAT
REM ============================================================================
:found_python
cls
title OFTEK - Calisiyor
echo ================================================================================
echo                                  OFTEK
echo               Operasyonel Takip ^& Gun Sonu Otomatik Fis Sistemi
echo ================================================================================
echo.
echo [*] Python Yolu      : %PYTHON_EXE%
echo [*] Yerel Sunucu     : http://localhost:8080
echo [*] Kullanim Kilavuzu: http://localhost:8080/kilavuz
echo.
echo [*] Cikis yapmak icin bu konsol penceresini kapatabilir veya Ctrl+C yapabilirsiniz.
echo.
echo --------------------------------------------------------------------------------
echo Sunucu baslatiliyor, tarayiciniz otomatik acilacaktir...
echo --------------------------------------------------------------------------------
echo.

"%PYTHON_EXE%" app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    color 0C
    echo ================================================================================
    echo                   [HATA] OFTEK SUNUCUSU BEKLENMEDIK SEKILDE KAPANDI!
    echo ================================================================================
    echo.
    echo Olasi Sorunlar:
    echo 1. 8080 numarali port baska bir program tarafindan kullaniliyor olabilir.
    echo 2. Onceki oftek oturumu arka planda acik kalmis olabilir.
    echo 3. Veritabani dosyasi kilitli veya salt-okunur olabilir.
    echo.
    echo Ayrintili cozumler icin "kullanim_kilavuzu.html" dosyasini inceleyiniz.
    echo ================================================================================
    echo.
    pause
)
