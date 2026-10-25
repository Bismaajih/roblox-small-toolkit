@echo off
title Roblox Asset Permission Share Tool
cd /d "%~dp0"

echo ==============================================================================
echo ROBLOX ASSET PERMISSION SHARE TOOL
echo ==============================================================================
echo Memeriksa file konfigurasi .env ...

if not exist ".env" (
    echo [PERINGATAN] File .env belum ditemukan!
    echo Menyalin .env.example menjadi .env ...
    copy .env.example .env >nul
    echo.
    echo Silakan buka file .env dan masukkan ROBLOX_API_KEY Anda terlebih dahulu.
    echo Setelah itu jalankan kembali launcher ini.
    echo.
    pause
    exit /b
)

python share_permission.py

if %errorlevel% neq 0 (
    echo.
    echo [INFO] Terjadi error saat menjalankan script.
    echo Pastikan Python dan library requests sudah terinstall:
    echo pip install -r requirements.txt
    echo.
    pause
)
