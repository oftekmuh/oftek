@echo off
chcp 65001 >nul
title OFTEK - Guvenli Sistem Guncelleyici
cd /d "%~dp0"

echo ================================================================================
echo                                 OFTEK
echo                    Guvenli Otomatik Sistem Guncelleyici
echo ================================================================================
echo.

REM 1. ADIM: CALISAN OFTEK / PYTHON SURECLERINI KONTROL ET
echo [*] Calisan sunucu surecleri kontrol ediliyor...
tasklist /fi "imagename eq python.exe" 2>nul | find /i "python.exe" >nul
if %ERRORLEVEL% NEQ 0 goto :check_db

echo [!] DIKKAT: Arka planda calisan bir Python / OFTEK oturumu tespit edildi.
echo [*] Veritabani dosyalarinin kilitli kalmamasi icin calisan oturum kapatiliyor...
taskkill /f /im python.exe >nul 2>nul
timeout /t 1 /nobreak >nul

:check_db
echo.
echo ================================================================================
echo  1. ASAMA: ATOMIK VE GUVENLI VERITABANI YEDEGI
echo ================================================================================

if not exist "muhasebe.db" goto :no_existing_db

REM Yedekler klasorunu olustur
if not exist "yedekler" mkdir "yedekler"

REM Gecici yarim kalmis eski dosya varsa temizle
if exist "yedekler\_gecici_yedek.tmp" del /f /q "yedekler\_gecici_yedek.tmp" >nul 2>nul

echo [*] "muhasebe.db" veritabani kopyalaniyor [Asil dosyaya kesinlikle dokunulmaz]...

REM Guvenlik: muhasebe.db ASLA tasinmaz veya silinmez; sadece salt okunur kopyalanir
copy /y "muhasebe.db" "yedekler\_gecici_yedek.tmp" >nul
if %ERRORLEVEL% NEQ 0 goto :copy_failed

REM Dosya boyut kontrolu: Gecici dosya olustu mu ve bos degil mi?
set "TMP_SIZE=0"
for %%F in ("yedekler\_gecici_yedek.tmp") do set "TMP_SIZE=%%~zF"
if "%TMP_SIZE%"=="" set "TMP_SIZE=0"
if %TMP_SIZE% LEQ 0 goto :empty_backup_failed

REM PowerShell ile guvenilir zaman damgasi uret [YYYYMMDD_HHMMSS]
set "TS="
for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmmss'" 2^>nul`) do set "TS=%%A"
if "%TS%"=="" set "TS=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TS=%TS: =0%"

set "YEDEK_ADI=yedekler\muhasebe_oto_yedek_%TS%.db"
move /y "yedekler\_gecici_yedek.tmp" "%YEDEK_ADI%" >nul

echo [OK] Veritabani basariyla yedeklendi:
echo      -^> %YEDEK_ADI%
echo [BILGI] Olası bir elektrik kesintisi veya yarim kalmada "muhasebe.db" ASLA bozulmaz.
echo.
goto :proceed_update

:no_existing_db
echo [*] Mevcut bir "muhasebe.db" veritabani bulunamadi [Sifir kurulum guncellemesi].
goto :proceed_update

:copy_failed
echo.
echo [HATA] Veritabani gecici yedek dosyasina kopyalanamadi!
echo [GUVENLIK] Verilerinizin guvenligi icin guncelleme derhal DURDURULDU.
echo [BILGI] Asil "muhasebe.db" dosyaniz sapasaglam yerinde durmaktadir.
echo.
pause
exit /b 1

:empty_backup_failed
echo.
echo [HATA] Kopyalanan gecici yedek dosyasi 0 bayt gorunuyor!
echo [GUVENLIK] Veri butunlugu riske atilamaz. Guncelleme DURDURULDU.
if exist "yedekler\_gecici_yedek.tmp" del /f /q "yedekler\_gecici_yedek.tmp" >nul 2>nul
echo.
pause
exit /b 1

:proceed_update
echo ================================================================================
echo  2. ASAMA: GUNCEL SURUM KODLARININ YUKLENMESI
echo ================================================================================

REM 1. SECENEK: Eger .git klasoru varsa Git Pull yap
if not exist ".git" goto :download_zip
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 goto :download_zip

echo [*] Git deposu algilandi, 'git pull origin main' calistiriliyor...
git pull origin main
if %ERRORLEVEL% EQU 0 goto :update_success
echo [!] Git pull basarisiz oldu, ZIP indirme yontemine geciliyor...

:download_zip
echo [*] GitHub uzerinden en guncel surum paketi indiriliyor...
echo     Hedef: https://github.com/oftekmuh/oftek/archive/refs/heads/main.zip

if exist "_update_temp" rd /s /q "_update_temp" >nul 2>nul
mkdir "_update_temp"

REM PowerShell ile guvenli indirme ve ayiklama
powershell -NoProfile -Command "$ProgressPreference = 'SilentlyContinue'; try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/oftekmuh/oftek/archive/refs/heads/main.zip' -OutFile '_update_temp\guncel.zip'; Expand-Archive -Path '_update_temp\guncel.zip' -DestinationPath '_update_temp\extracted' -Force; Write-Host '[OK] Guncelleme paketi basariyla indirildi ve ayiklandi.'; } catch { Write-Error $_.Exception.Message; exit 1; }"

if %ERRORLEVEL% NEQ 0 goto :download_failed

echo [*] Yeni sistem dosyalari uygulaniyor...
if exist "_update_temp\extracted\oftek-main" (
    xcopy /s /e /y /i "_update_temp\extracted\oftek-main\*" "." >nul
)
if not exist "_update_temp\extracted\oftek-main" (
    xcopy /s /e /y /i "_update_temp\extracted\*" "." >nul
)

if exist "_update_temp" rd /s /q "_update_temp" >nul 2>nul
goto :update_success

:download_failed
echo.
echo [HATA] GitHub uzerinden guncelleme paketi indirilemedi!
echo [NEDEN] Internet baglantinizi veya guvenlik duvari ayarlarini kontrol ediniz.
echo [BILGI] Veritabaniniz ve mevcut sisteminiz eksiksiz korunmaktadir.
if exist "_update_temp" rd /s /q "_update_temp" >nul 2>nul
echo.
pause
exit /b 1

:update_success
echo.
echo ================================================================================
echo  TEBRIKLER: OFTEK BASARIYLA EN GUNCEL SURUME YUKSELTILDI!
echo ================================================================================
echo.
echo  [+] Tum program kodlari, guvenlik yamalari ve arayuz guncellendi.
echo  [+] "muhasebe.db" veritabani eksiksiz korundu.
if not "%YEDEK_ADI%"=="" (
    echo  [+] Guvenlik amaciyla alinan otomatik yedek: %YEDEK_ADI%
)
echo.
echo  Sistemi hemen calistirmak icin "baslat.bat" dosyasina tiklayabilirsiniz.
echo ================================================================================
echo.
pause
exit /b 0
