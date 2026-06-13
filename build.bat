@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  Spirit Voice Assistant — Build ^& Package
echo ============================================
echo.

:: ── Step 1: Build exe with PyInstaller ──────────────────────────────────────
echo [1/2] Building Spirit.exe with PyInstaller...
pyinstaller spirit.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed. See output above.
    pause
    exit /b 1
)
echo Done. Executable at: dist\Spirit.exe
echo.

:: ── Step 2: Compile Inno Setup installer ────────────────────────────────────
echo [2/2] Compiling installer with Inno Setup...

:: Try common Inno Setup install locations
set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo.
    echo WARNING: Inno Setup not found. Skipping installer compilation.
    echo Download from: https://jrsoftware.org/isdl.php
    echo Then run:  ISCC.exe installer\spirit_installer.iss
    echo.
    echo Spirit.exe is ready at: dist\Spirit.exe
    pause
    exit /b 0
)

%ISCC% installer\spirit_installer.iss
if errorlevel 1 (
    echo.
    echo ERROR: Inno Setup compilation failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  SUCCESS!
echo  Installer: dist\SpiritSetup.exe
echo ============================================
pause
