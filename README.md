# ⚡ Roblox Asset Permission Sharing Tool

> **Tool Otomatis & Mandiri (Standalone) untuk Berbagi Izin Pemakaian (Use Permission) Aset Roblox via Open Cloud API.**

Tool ini dirancang untuk membagikan izin aset Roblox (Audio Musik, Animasi Dance, Model, dll.) ke **User**, **Group**, **Universe (Game)**, maupun **Public (All Experiences)** secara cepat, aman, dan tanpa ribet.

---

## 🌟 Fitur Utama

1. **Multi-Target Dispatch**:
   - `Group`: Bagikan ke Group ID tertentu.
   - `User`: Bagikan langsung ke Roblox User ID.
   - `Universe`: Bagikan ke Universe / Game ID.
   - `Public` / `All`: Buka akses aset untuk **seluruh game di Roblox (Open Use)**.
   - `Group Games`: Ambil seluruh Experience di suatu Group dan bagikan ke semuanya sekaligus dalam satu perintah (`--group-games <GROUP_ID>`).
2. **Multi-Account Auto-Fallback**:
   - Jika Anda memiliki aset di beberapa akun Roblox berbeda, tool otomatis mencoba akun kedua/ketiga jika akun pertama bukan pemilik aset.
3. **Universal ID Extractor**:
   - Tidak perlu repot membersihkan teks! Masukkan file teks mentah, tabel Lua (`ModuleScript`, format CENZ `{SoundId = "..."}`), URL Roblox (`rbxassetid://`, `roblox.com/library/...`), atau angka koma—tool otomatis mengekstrak ID numeriknya.
4. **Auto-Batching & Anti-Rate Limit**:
   - Mengirim dalam batch aman (default 30 aset per request) dengan jeda waktu otomatis dan penanganan HTTP 429 (auto-retry).
5. **Watch Mode (Pantau Berkala & Auto-Share)**:
   - Jika buyer belum menaikkan rank akun Anda di grupnya, aktifkan `--watch`. Tool akan memeriksa setiap 60 detik dan langsung otomatis mengirim seluruh aset begitu izin dibuka!
6. **Dual Mode (Interactive & CLI)**:
   - Pengguna pemula cukup double-click `run.bat` atau jalankan `python share_permission.py` untuk menu interaktif.
   - Pengguna mahir dapat menggunakan one-liner CLI.
7. **Activity Ledger**:
   - Setiap transaksi tercatat rapi di `logs/ACTIVITY_LOG.md` (tabel markdown) dan file detail `.json`.

---

## 📁 Struktur Folder (Pemfolderan)

```text
roblox-small-toolkit/
├── share_permission.py      # Script utama (CLI & Menu Interaktif)
├── run.bat                  # Shortcut Windows (Double-click untuk jalan langsung)
├── requirements.txt         # Kebutuhan library (hanya library requests)
├── .env.example             # Template konfigurasi API Key
├── .gitignore               # Proteksi agar file .env tidak ter-upload ke git
├── sample_assets.txt        # Contoh file daftar aset (tabel Lua, URL, angka)
├── logs/                    # Folder riwayat transaksi (otomatis dibuat)
│   ├── .gitkeep
│   └── ACTIVITY_LOG.md      # Tabel ringkasan log seluruh share
└── README.md                # Dokumentasi panduan lengkap
```

---

## 🚀 Panduan Instalasi & Persiapan

### 1. Prasyarat
- Pasang **Python 3.8+** di komputer Anda ([Download Python](https://www.python.org/downloads/)).
- Pastikan mencentang **"Add Python to PATH"** saat instalasi Python.

### 2. Pasang Library Dependensi
Buka Terminal / Command Prompt di folder ini, lalu jalankan:
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi API Key Roblox Open Cloud
1. Kunjungi [Roblox Creator Dashboard - Credentials](https://create.roblox.com/dashboard/credentials).
2. Buat API Key baru (**Create API Key**).
3. Pada bagian **Access Permissions**, pilih **Asset System** (atau Permissions API) dan beri akses:
   - **Read** & **Write** (atau Action: `Use` / `Permissions`).
4. Pada bagian **IP Restrictions**, tambahkan IP publik Anda (atau `0.0.0.0/0` jika IP dinamis).
5. Salin file `.env.example` menjadi `.env`:
   - Di Windows: `copy .env.example .env`
6. Buka file `.env` dengan Notepad/editor teks, lalu tempel API Key Anda:
   ```env
   ROBLOX_API_KEY=masukkan_api_key_roblox_disini
   ```
   *(Jika memiliki multi-akun, Anda bisa menambahkan `ROBLOX_API_KEY_2=...`)*

---

## 🎮 Cara Menggunakan

### Cara 1: Menu Interaktif (Paling Mudah)
Cukup **double-click** file `run.bat` (atau ketik `python share_permission.py` di terminal tanpa argumen):

```text
╔══════════════════════════════════════════════════════════════════════╗
║             ROBLOX ASSET PERMISSION SHARE • MENU UTAMA               ║
╚══════════════════════════════════════════════════════════════════════╝

  [1] Share ke Group (Group ID)
  [2] Share ke User (Roblox User ID)
  [3] Share ke Experience (Universe ID)
  [4] Share ke Public / All Experiences (Buka Akses Bebas Global)
  [5] Share ke Seluruh Experience dalam Suatu Group (Group Games)
  [6] Mode Watch & Auto-Dispatch (Tunggu Role Diberikan)
  [7] Cek Riwayat Share (Activity Log)
  [0] Keluar

  Pilih menu [0-7]:
```
Ikuti instruksi di layar, masukkan ID target dan pilih file aset atau paste ID langsung.

---

### Cara 2: Perintah CLI (Cepat & Otomatis)

#### 1. Share Aset dari File ke Group
```bash
python share_permission.py --target 10653990168 --type Group --file sample_assets.txt --buyer "NamaBuyer"
```

#### 2. Share Langsung ID Tertentu ke Akun User
```bash
python share_permission.py --target 7327571817 --type User --id 140529015040235,92726763803666
```

#### 3. Share ke Public / Open Use (Bebas Dipakai di Semua Game)
```bash
python share_permission.py --type Public --file sample_assets.txt
```

#### 4. Share ke SELURUH Game di dalam Suatu Group
Jika satu group memiliki 5 game/experience berbeda, perintah ini otomatis mendeteksi semua game dan membagikan ke setiap game:
```bash
python share_permission.py --group-games 10653990168 --file sample_assets.txt --buyer "NamaBuyer"
```

#### 5. Mode Watch (Pantau sampai Role Diberikan Owner Grup)
Jika owner grup belum menaikkan rank akun Anda, jalankan perintah ini. Tool akan memantau setiap 60 detik dan otomatis mengeksekusi sharing begitu izin aktif:
```bash
python share_permission.py --target 10653990168 --type Group --file sample_assets.txt --buyer "NamaBuyer" --watch --interval 60
```

#### 6. Melihat Riwayat Transaksi Share
```bash
python share_permission.py --history
```
*(Atau buka langsung file `logs/ACTIVITY_LOG.md` untuk melihat tabel riwayat lengkap)*

---

## 🛠️ Opsi Flag Lengkap (CLI Reference)

| Flag | Penjelasan | Contoh Nilai |
|---|---|---|
| `--target`, `-t` | Target ID (User, Group, atau Universe). Pisahkan koma jika banyak | `10653990168` |
| `--type` | Tipe subjek penerima izin (`Group`, `User`, `Universe`, `Public`, `All`) | `Group` (default) |
| `--file`, `-f` | Path ke file teks/lua sumber daftar aset | `sample_assets.txt` |
| `--id` | Asset ID langsung (satu atau pisahkan koma) | `140529015040235` |
| `--group-games` | Group ID untuk membagikan ke seluruh game di dalam grup tersebut | `10653990168` |
| `--buyer`, `-b` | Catatan nama buyer/klien untuk dicatat pada log | `"Mr_Roblox"` |
| `--watch`, `-w` | Mengaktifkan mode pantau berkala (probe) hingga role diberikan | (flag) |
| `--interval` | Jeda waktu antar pengecekan pada Watch Mode (dalam detik) | `60` (default) |
| `--batch` | Jumlah aset yang dikirim per panggilan API (default: 30) | `30` |
| `--delay` | Jeda antar batch dalam detik untuk mencegah rate limit | `0.3` (default) |
| `--history` | Menampilkan ringkasan riwayat share terakhir | (flag) |
| `--no-save` | Menjalankan share tanpa menyimpan catatan ke file log | (flag) |

---

## ❓ FAQ & Troubleshooting

- **Error `HTTP 401 Unauthorized`**:
  - API Key di file `.env` salah atau belum diisi. Periksa kembali API Key Anda di Creator Hub.
- **Error `HTTP 403 Forbidden`**:
  - Akun Anda belum memiliki izin kelola pada grup/game tujuan, ATAU API Key tidak memiliki izin `Permissions: Write` / `Asset System: Write`.
  - Jika targetnya adalah Group orang lain, pastikan akun Roblox Anda sudah dimasukkan ke grup tersebut dan diberi role yang memiliki izin **"Configure group experiences"** atau setara.
- **Error `HTTP 429 Too Many Requests`**:
  - Roblox sedang membatasi frekuensi request. Tool ini otomatis melakukan retry dan jeda. Jika sering terjadi, perbesar nilai `--delay 1.0`.

---

## 📄 Lisensi
Dibuat untuk kebutuhan operasional distribusi aset Roblox Open Cloud. Bebas dikembangkan dan dimodifikasi.
