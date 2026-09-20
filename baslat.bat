@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYTHONDONTWRITEBYTECODE=1
set PYTHONUNBUFFERED=1

set PYTHON_EXE=

:: 1. ÖNCELİK: Proje dizini içindeki dahili gömülü Python (Örn: oftek\python\python.exe)
if exist "%~dp0python\python.exe" (
    set PYTHON_EXE="%~dp0python\python.exe"
    goto :found_python
)

:: 2. ÖNCELİK: Bir üst dizindeki / yan klasördeki Python (Örn: F:\python\python.exe)
if exist "%~dp0..\python\python.exe" (
    set PYTHON_EXE="%~dp0..\python\python.exe"
    goto :found_python
)

:: 3. ÖNCELİK: Sürücü kökündeki Python (Örn: F:\python\python.exe)
if exist "%~d0\python\python.exe" (
    set PYTHON_EXE="%~d0\python\python.exe"
    goto :found_python
)

:: 4. Alternatif taşınabilir Python klasörleri
if exist "%~dp0python-embed\python.exe" (
    set PYTHON_EXE="%~dp0python-embed\python.exe"
    goto :found_python
)
if exist "%~dp0..\python-embed\python.exe" (
    set PYTHON_EXE="%~dp0..\python-embed\python.exe"
    goto :found_python
)

:: 5. Sistem PATH'inde python var mı?
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_EXE=python
    goto :found_python
)

:: 6. Standart Windows Kullanıcı Kurulum Yolları
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set PYTHON_EXE="%LocalAppData%\Programs\Python\Python312\python.exe"
    goto :found_python
)
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set PYTHON_EXE="%LocalAppData%\Programs\Python\Python311\python.exe"
    goto :found_python
)
if exist "%LocalAppData%\Programs\Python\Python310\python.exe" (
    set PYTHON_EXE="%LocalAppData%\Programs\Python\Python310\python.exe"
    goto :found_python
)

:: Python hiçbir yerde bulunamadıysa detaylı rehber göster
echo ================================================================
echo    OFTEK
echo ================================================================
echo.
echo [HATA] Python calistirilabilir dosyasi (python.exe) bulunamadi!
echo.
echo Aranan konumlar:
echo   1. %~dp0python\python.exe (Dahili Gömülü Python)
echo   2. %~dp0..\python\python.exe
echo   3. %~d0\python\python.exe
echo   4. Sistem PATH (python)
echo.
echo Lutfen Python'in dogru klasorde oldugundan veya sistemde kurulu
echo oldugundan emin olunuz.
echo.
pause
exit /b 1

:found_python
echo ================================================================
echo    OFTEK
echo ================================================================
echo [*] Dahili Python : %PYTHON_EXE%
echo [*] Sunucu        : http://localhost:8080
echo [*] Kapatmak icin bu pencereyi kapatabilirsiniz veya Ctrl+C
echo.

%PYTHON_EXE% app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Sunucu calisirken bir sorun olustu.
    pause
)
