# Roblox Asset Permission Share

Script mandiri untuk membagikan izin pemakaian (Use Permission) aset Roblox (audio, animasi, model) ke Group, User, Experience, atau Public melalui Roblox Open Cloud API.

## Setup Cepat

1. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
2. Buat file `.env` dari template:
   ```bash
   copy .env.example .env
   ```
   Buka file `.env` lalu masukkan API Key Anda:
   ```env
   ROBLOX_API_KEY=roblox_open_cloud_api_key_disini
   ```
   *(Izin API key di Roblox Creator Hub: Permissions / Asset System -> Read & Write).*

## Cara Pakai

### 1. Menu Interaktif
Jalankan script tanpa argumen atau cukup double-click `run.bat` di Windows:
```bash
python share_permission.py
```
Ikuti petunjuk di terminal untuk memilih tipe target (Group/User/Public) dan memasukkan file/ID aset.

### 2. Command Line (CLI)

- **Share ke Group dari file:**
  ```bash
  python share_permission.py --target 10653990168 --type Group --file sample_assets.txt
  ```

- **Share ke User ID:**
  ```bash
  python share_permission.py --target 7327571817 --type User --id 140529015040235
  ```

- **Share ke seluruh game di dalam suatu Group:**
  ```bash
  python share_permission.py --group-games 10653990168 --file sample_assets.txt
  ```

- **Buka akses bebas untuk semua game (Public / Open Use):**
  ```bash
  python share_permission.py --type Public --file sample_assets.txt
  ```

- **Mode Watch (menunggu role grup diberikan, lalu otomatis share):**
  ```bash
  python share_permission.py --target 10653990168 --type Group --file sample_assets.txt --watch --interval 60
  ```

- **Lihat riwayat share:**
  ```bash
  python share_permission.py --history
  ```

## Input File Aset
Tool otomatis mengekstrak ID numerik dari:
- File teks biasa (1 ID per baris atau dipisah koma)
- Tabel Lua / ModuleScript (format `{ SoundId = "rbxassetid://..." }` atau `{ Id = "..." }`)
- URL link Roblox (`roblox.com/library/...`, `rbxassetid://...`)

## Struktur Folder
```text
roblox-small-toolkit/
├── share_permission.py   # Script utama
├── run.bat               # Launcher Windows (double-click)
├── requirements.txt      # Dependensi (requests)
├── .env.example          # Template API key
├── sample_assets.txt     # Contoh daftar ID aset
└── logs/                 # Catatan riwayat transaksi
```
