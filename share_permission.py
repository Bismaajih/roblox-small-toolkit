#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ROBLOX OPEN CLOUD - INSTANT ASSET PERMISSION SHARING TOOL
=============================================================================
Repository: Bismaajih/roblox-small-toolkit
Deskripsi : Tool instan & otomatis untuk membagikan izin pemakaian (Use Permission)
            aset Roblox (Audio, Animasi, Model, dll) ke:
            - Group (Group ID)
            - User (Roblox User ID)
            - Universe / Experience (Game ID)
            - Public / All Experiences (Buka Akses Bebas Global)
            - Seluruh Game dalam Group (--group-games)
=============================================================================
"""

import os
import sys
import re
import json
import time
import argparse
from datetime import datetime

# Pastikan encoding terminal Windows mendukung UTF-8
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Warna Terminal (ANSI Colors)
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
MASTER_SHARE_HISTORY_FILE = os.path.join(LOGS_DIR, "share_history.json")
MASTER_ACTIVITY_LOG_MD = os.path.join(LOGS_DIR, "ACTIVITY_LOG.md")

PERMISSIONS_URL = "https://apis.roblox.com/asset-permissions-api/v1/assets/permissions"

# ==============================================================================
# UTILITIES & CONFIG
# ==============================================================================

def safe_print(msg=""):
    try:
        print(msg)
    except Exception:
        enc = sys.stdout.encoding or "utf-8"
        try:
            print(str(msg).encode(enc, errors="replace").decode(enc))
        except Exception:
            print(str(msg).encode("ascii", errors="replace").decode("ascii"))

def print_banner(title):
    w = 72
    safe_print(f"\n{C.CYAN}╔{'═' * (w - 2)}╗{C.RESET}")
    safe_print(f"{C.CYAN}║{C.BOLD}{C.WHITE} {title.center(w - 4)} {C.CYAN}║{C.RESET}")
    safe_print(f"{C.CYAN}╚{'═' * (w - 2)}╝{C.RESET}\n")

def load_env_file():
    """Membaca file .env secara otomatis tanpa butuh library eksternal."""
    env_file = os.path.join(BASE_DIR, ".env")
    env = {}
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    return env

def get_all_api_keys():
    """Mengambil semua Roblox Open Cloud API Key dari .env atau environment system."""
    env = load_env_file()
    keys = []
    seen = set()

    for k, v in env.items():
        if k.startswith("ROBLOX_API_KEY") and v:
            name = k.replace("ROBLOX_API_KEY_", "").replace("ROBLOX_API_KEY", "PRIMARY").strip("_")
            if not name:
                name = "PRIMARY"
            if v not in seen:
                seen.add(v)
                keys.append({"env_var": k, "name": name, "key": v})

    for k, v in os.environ.items():
        if k.startswith("ROBLOX_API_KEY") and v:
            name = k.replace("ROBLOX_API_KEY_", "").replace("ROBLOX_API_KEY", "PRIMARY").strip("_")
            if not name:
                name = "PRIMARY"
            if v not in seen:
                seen.add(v)
                keys.append({"env_var": k, "name": name, "key": v})

    return keys

def extract_ids_from_text(text):
    """
    Universal Extractor:
    Mengekstrak ID angka Roblox dari teks biasa, tabel Lua (format SoundId / Id), URL, maupun koma.
    Otomatis mengabaikan komentar baris (-- atau #) agar metadata tracking tidak terserap.
    """
    clean_lines = [l for l in text.splitlines() if not l.strip().startswith(("--", "#", "//"))]
    clean_text = "\n".join(clean_lines)

    ids = []
    # 1. Tabel Lua (SoundId = "...", Id = "...", AudioId = ...)
    found_lua = re.findall(r'\b(?:SoundId|AudioId|AnimationId|AssetId|Id)\s*=\s*["\']?(?:rbxassetid://)?([0-9,\s]+)["\']?', clean_text, re.IGNORECASE)
    if found_lua:
        for group in found_lua:
            ids.extend(re.findall(r'\b\d{6,}\b', group))

    # 2. URL Roblox (rbxassetid://, library/, asset/?id=, catalog/)
    found_urls = re.findall(r'(?:asset/\?id=|library/|rbxassetid://|catalog/)(\d{6,})', clean_text, re.IGNORECASE)
    if found_urls:
        ids.extend(found_urls)

    # 3. Angka mandiri (minimal 6 digit)
    if not ids:
        ids = re.findall(r'\b\d{6,}\b', clean_text)

    # Filter unik dengan mempertahankan urutan
    seen = set()
    unique = []
    for x in ids:
        clean_id = str(x).strip()
        if clean_id and clean_id not in seen:
            seen.add(clean_id)
            unique.append(clean_id)
    return unique

def extract_ids_from_file(filepath):
    """Membaca file lokal dan mengekstrak seluruh Asset ID."""
    if not os.path.isabs(filepath):
        candidates = [
            filepath,
            os.path.join(BASE_DIR, filepath)
        ]
        actual = filepath
        for c in candidates:
            if os.path.exists(c):
                actual = c
                break
    else:
        actual = filepath

    if not os.path.exists(actual):
        return [], actual

    with open(actual, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    return extract_ids_from_text(content), actual

# ==============================================================================
# LOGGING & ACTIVITY LEDGER
# ==============================================================================

def load_share_history():
    if os.path.exists(MASTER_SHARE_HISTORY_FILE):
        try:
            with open(MASTER_SHARE_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_share_history(history):
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(MASTER_SHARE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    update_activity_markdown(history)

def update_activity_markdown(history):
    lines = [
        "# 📜 ROBLOX OPEN CLOUD PERMISSION ACTIVITY LOG",
        "",
        "> Catatan riwayat pembagian izin pemakaian aset via Roblox Open Cloud API.",
        f"> Terakhir diperbarui: **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}** | Total Transaksi: **{len(history)}**",
        "",
        "| No | Tanggal & Jam | Buyer / Klien | Target Type | Target ID | Sumber Aset | Sukses | Gagal | Status | Akun Pengirim |",
        "|---|---|---|---|---|---|---|---|---|---|"
    ]
    sorted_history = sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)
    for idx, item in enumerate(sorted_history, 1):
        ts = item.get("timestamp", "-")
        bname = item.get("buyer", "-") or "-"
        ttype = item.get("targetType", "-")
        tid = item.get("targetId", "-")
        src = item.get("source", "-")
        succ = item.get("successCount", 0)
        fail = item.get("failedCount", 0)
        tot = item.get("total", succ + fail)
        st = "✅ Full" if fail == 0 and succ > 0 else ("⚠️ Partial" if succ > 0 else "❌ Failed")
        accs = ", ".join([f"{k}:{v}" for k, v in item.get("accountStats", {}).items() if v > 0]) or "-"
        lines.append(f"| {idx} | {ts} | **{bname}** | `{ttype}` | `{tid}` | {src} | {succ}/{tot} | {fail} | {st} | {accs} |")

    try:
        with open(MASTER_ACTIVITY_LOG_MD, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception:
        pass

def record_share_entry(target_id, target_type, buyer_name, source_name, total, succ_count, fail_count, account_stats, failed_ids, log_filename):
    history = load_share_history()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "buyer": buyer_name or "Direct",
        "targetType": target_type,
        "targetId": str(target_id),
        "source": source_name or "Manual",
        "total": total,
        "successCount": succ_count,
        "failedCount": fail_count,
        "accountStats": account_stats,
        "failedIds": failed_ids,
        "logFile": os.path.basename(log_filename)
    }
    history.append(entry)
    save_share_history(history)

# ==============================================================================
# CORE FUNCTION: DISPATCH PERMISSION SHARE
# ==============================================================================

def execute_share(target_id, target_type, ids, batch_size=30, delay=0.3, buyer_name=None, source_name=None, account_filter=None, no_save=False):
    """
    Eksekutor utama:
    Mengirimkan HTTP PATCH ke API permissions Roblox.
    Mendukung multi-akun: jika aset tidak dimiliki akun pertama, otomatis dicoba oleh akun kedua.
    """
    try:
        import requests
    except ImportError:
        safe_print(f"{C.RED}[ERROR] Library 'requests' belum terinstall. Jalankan: pip install requests{C.RESET}")
        return False

    api_keys = get_all_api_keys()
    if account_filter:
        af = str(account_filter).strip().lower()
        filtered = [k for k in api_keys if af in k["name"].lower() or af in k["env_var"].lower()]
        if filtered:
            api_keys = filtered
        else:
            safe_print(f"{C.YELLOW}[WARNING] Filter akun '{account_filter}' tidak ditemukan. Menggunakan semua akun yang tersedia.{C.RESET}")

    if not api_keys:
        safe_print(f"{C.RED}[ERROR] Tidak ditemukan ROBLOX_API_KEY di file .env!{C.RESET}")
        safe_print("Silakan salin .env.example menjadi .env lalu isi API Key Open Cloud Anda.")
        return False

    is_public = str(target_type).lower() in ["all", "public"]
    effective_target_type = "All" if is_public else target_type
    effective_target_id = "" if is_public else str(target_id)

    os.makedirs(LOGS_DIR, exist_ok=True)
    print_banner("ROBLOX OPEN CLOUD • ASSET PERMISSION DISPATCH")
    if buyer_name:
        safe_print(f"  • Buyer / Klien : {C.BOLD}{C.WHITE}{buyer_name}{C.RESET}")
    if is_public:
        safe_print(f"  • Target        : {C.BOLD}{C.CYAN}Public / All Experiences (Open Use Global){C.RESET}")
    else:
        safe_print(f"  • Target        : {C.BOLD}{C.CYAN}{target_type} ID {target_id}{C.RESET}")
    safe_print(f"  • Total Aset    : {C.BOLD}{C.GREEN}{len(ids)} Assets{C.RESET}")
    safe_print(f"  • Akun Aktif    : {C.YELLOW}{', '.join([k['name'] for k in api_keys])}{C.RESET}")
    safe_print(f"  • Batch Size    : {batch_size} aset per request (delay: {delay}s)\n")

    batches = [ids[i:i + batch_size] for i in range(0, len(ids), batch_size)]
    total_batches = len(batches)

    success_ids = []
    failed_ids = []
    account_stats = {k["name"]: 0 for k in api_keys}

    start_time = time.time()
    last_resp_error = None

    for idx, chunk in enumerate(batches, 1):
        pending_ids = list(chunk)
        chunk_success = []

        for acc in api_keys:
            if not pending_ids:
                break

            headers = {
                "x-api-key": acc["key"],
                "Content-Type": "application/json"
            }
            payload = {
                "subjectType": effective_target_type,
                "subjectId": effective_target_id,
                "action": "Use",
                "assetIds": pending_ids
            }

            for attempt in range(4):
                try:
                    resp = requests.patch(PERMISSIONS_URL, headers=headers, json=payload, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        succ_ids = [str(x) for x in data.get("successAssetIds", [])]
                        for aid in succ_ids:
                            chunk_success.append(aid)
                            account_stats[acc["name"]] += 1
                        pending_ids = [aid for aid in pending_ids if aid not in succ_ids]
                        break
                    elif resp.status_code == 429:
                        time.sleep(2.0 * (attempt + 1))
                        continue
                    else:
                        try:
                            err_json = resp.json()
                            msg = err_json.get("error", {}).get("message") or err_json.get("message") or resp.text
                            last_resp_error = f"{acc['name']} -> HTTP {resp.status_code}: {msg}"
                        except Exception:
                            last_resp_error = f"{acc['name']} -> HTTP {resp.status_code}: {resp.text}"
                        break
                except Exception as e:
                    last_resp_error = f"{acc['name']} -> Exception: {e}"
                    time.sleep(1.0)

        success_ids.extend(chunk_success)
        failed_ids.extend(pending_ids)

        pct = (idx / total_batches) * 100
        bar_len = 20
        filled = int(bar_len * idx / total_batches)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r  [{bar}] {pct:5.1f}% | Batch {idx:02d}/{total_batches:02d} | [✓] {len(chunk_success)} | [✗] {len(pending_ids)}")
        sys.stdout.flush()
        time.sleep(delay)

    safe_print("\n")
    dur = round(time.time() - start_time, 1)

    safe_print(f"  {C.GREEN}{C.BOLD}HASIL DISPATCH:{C.RESET}")
    safe_print(f"  • Berhasil : {C.GREEN}{len(success_ids)}/{len(ids)}{C.RESET}")
    safe_print(f"  • Gagal    : {C.RED if failed_ids else C.WHITE}{len(failed_ids)}/{len(ids)}{C.RESET}")
    if failed_ids and last_resp_error:
        safe_print(f"  • Respons Error Terakhir : {C.YELLOW}{last_resp_error}{C.RESET}")
    safe_print(f"  • Durasi   : {dur} detik")
    for acc_name, cnt in account_stats.items():
        if cnt > 0:
            safe_print(f"    - Akun {acc_name}: {cnt} aset dibagikan")

    if not no_save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target_id = target_id if target_id else "All"
        log_file = os.path.join(LOGS_DIR, f"share_{target_type}_{safe_target_id}_{timestamp}.json")
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump({
                    "targetType": target_type,
                    "targetId": target_id,
                    "timestamp": timestamp,
                    "total": len(ids),
                    "successCount": len(success_ids),
                    "failedCount": len(failed_ids),
                    "accountStats": account_stats,
                    "failedIds": failed_ids
                }, f, indent=2)

            record_share_entry(
                target_id=target_id,
                target_type=target_type,
                buyer_name=buyer_name,
                source_name=source_name,
                total=len(ids),
                succ_count=len(success_ids),
                fail_count=len(failed_ids),
                account_stats=account_stats,
                failed_ids=failed_ids,
                log_filename=log_file
            )
            safe_print(f"\n  {C.CYAN}Log detail  : {log_file}{C.RESET}")
            safe_print(f"  {C.GREEN}[✓] Dicatat ke Activity Log: {MASTER_ACTIVITY_LOG_MD}{C.RESET}")
        except Exception as e:
            safe_print(f"  {C.YELLOW}[!] Gagal menulis log: {e}{C.RESET}")
    else:
        safe_print(f"\n  {C.YELLOW}[i] Mode no-save aktif: log tidak disimpan.{C.RESET}")

    return len(failed_ids) == 0

# ==============================================================================
# WATCH MODE & GROUP GAMES HELPERS
# ==============================================================================

def probe_access(target_id, target_type, test_asset_id):
    """Mengecek apakah akun API memiliki hak akses ke subject (Group/Universe/User)."""
    import requests
    api_keys = get_all_api_keys()
    if not api_keys:
        return False, None, "Tidak ada ROBLOX_API_KEY di .env"

    last_error = "Unknown error"
    for acc in api_keys:
        headers = {
            "x-api-key": acc["key"],
            "Content-Type": "application/json"
        }
        payload = {
            "subjectType": target_type,
            "subjectId": str(target_id),
            "action": "Use",
            "assetIds": [str(test_asset_id)]
        }
        try:
            resp = requests.patch(PERMISSIONS_URL, headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                succ_ids = [str(x) for x in data.get("successAssetIds", [])]
                if str(test_asset_id) in succ_ids or succ_ids:
                    return True, acc["name"], "Akses Diberikan (200 OK)"
            elif resp.status_code == 403:
                last_error = f"{acc['name']}: Forbidden (403)"
            elif resp.status_code == 429:
                last_error = f"{acc['name']}: Rate limited (429)"
            else:
                last_error = f"{acc['name']}: HTTP {resp.status_code}"
        except Exception as e:
            last_error = f"{acc['name']}: {e}"

    return False, None, last_error

def watch_and_share(target_id, target_type, ids, batch_size=30, delay=0.3, buyer_name=None, source_name=None, interval=60, max_retries=0):
    """Memantau secara berkala (watch) sampai akun memiliki akses ke target, lalu otomatis eksekusi share."""
    print_banner("ROBLOX OPEN CLOUD • WATCH & AUTO-DISPATCH")
    safe_print(f"  • Target       : {C.BOLD}{C.CYAN}{target_type} ID {target_id}{C.RESET}")
    safe_print(f"  • Buyer Klien  : {C.BOLD}{C.WHITE}{buyer_name or 'Direct'}{C.RESET}")
    safe_print(f"  • Total Aset   : {C.BOLD}{C.GREEN}{len(ids)} Assets{C.RESET}")
    safe_print(f"  • Interval Cek : {interval} detik")
    safe_print(f"  • Batas Cek    : {'Tanpa batas (loop terus)' if max_retries <= 0 else f'{max_retries} kali'}\n")

    attempt = 0
    test_asset_id = ids[0] if ids else "140529015040235"

    while True:
        attempt += 1
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ok, acc_name, message = probe_access(target_id, target_type, test_asset_id)
        if ok:
            safe_print(f"\n{C.GREEN}{C.BOLD}[{now_str}] [✓] AKSES DITERIMA! Izin berhasil diberikan pada akun {acc_name}!{C.RESET}")
            safe_print(f"  Memulai proses sharing otomatis {len(ids)} aset sekarang...\n")
            time.sleep(1)
            return execute_share(target_id, target_type, ids, batch_size, delay, buyer_name=buyer_name, source_name=source_name)

        safe_print(f"  [{now_str}] Attempt #{attempt:03d}: Menunggu role/izin owner... ({message})")

        if max_retries > 0 and attempt >= max_retries:
            safe_print(f"\n{C.RED}[!] Telah mencapai batas maksimal {max_retries} percobaan. Watch dihentikan.{C.RESET}\n")
            return False

        time.sleep(interval)

def share_all_group_games(group_id, ids, batch_size=30, delay=0.3, buyer_name=None, source_desc="Group Games"):
    """Mengambil seluruh Experience/Game di dalam suatu Group dan membagikan ke setiap Universe."""
    import requests
    gid = str(group_id).strip()
    print_banner(f"FETCHING ALL EXPERIENCES FOR GROUP ID {gid}")
    try:
        r = requests.get(f"https://games.roblox.com/v2/groups/{gid}/games?accessFilter=All&sortOrder=Asc&limit=50", timeout=15)
        games = r.json().get("data", [])
    except Exception as e:
        safe_print(f"{C.RED}[ERROR] Gagal mengambil daftar game grup: {e}{C.RESET}")
        return False

    if not games:
        safe_print(f"{C.YELLOW}[!] Tidak ada experience yang ditemukan di grup {gid}.{C.RESET}")
        return False

    safe_print(f"  {C.GREEN}[✓] Ditemukan {len(games)} game di dalam grup {gid}:{C.RESET}")
    for g_idx, g in enumerate(games, 1):
        clean_name = g.get('name', '').encode('ascii', 'ignore').decode()
        safe_print(f"    {g_idx:2d}. Universe ID: {C.BOLD}{g.get('id')}{C.RESET} | Game: {clean_name}")

    safe_print(f"\n  Memulai proses sharing ke seluruh {len(games)} game...")
    summary = []
    for g_idx, g in enumerate(games, 1):
        clean_name = g.get('name', '').encode('ascii', 'ignore').decode()
        safe_print(f"\n{C.CYAN}──────────────────────────────────────────────────────────────────────{C.RESET}")
        safe_print(f"[{g_idx}/{len(games)}] PROSES GAME: {clean_name} (Universe ID: {g.get('id')})")
        safe_print(f"{C.CYAN}──────────────────────────────────────────────────────────────────────{C.RESET}")
        ok = execute_share(
            str(g.get('id')),
            "Universe",
            ids,
            batch_size=batch_size,
            delay=delay,
            buyer_name=buyer_name,
            source_name=f"{source_desc} (Group Game: {clean_name})"
        )
        summary.append({"name": clean_name, "id": g.get('id'), "success": ok})

    print_banner("RINGKASAN SHARING SELURUH GAME GRUP")
    sukses_cnt = sum(1 for s in summary if s['success'])
    safe_print(f"  • Group ID     : {gid}")
    safe_print(f"  • Total Game   : {len(games)}")
    safe_print(f"  • Status Akhir : {C.GREEN}{sukses_cnt}/{len(games)} Game Selesai{C.RESET}\n")
    for s in summary:
        st = f"{C.GREEN}[✓] Sukses{C.RESET}" if s['success'] else f"{C.YELLOW}[!] Periksa{C.RESET}"
        safe_print(f"    - {s['name']} (ID {s['id']}): {st}")
    return sukses_cnt == len(games)

# ==============================================================================
# INTERACTIVE CLI WIZARD
# ==============================================================================

def interactive_wizard():
    while True:
        print_banner("ROBLOX ASSET PERMISSION SHARE • MENU UTAMA")
        safe_print(f"  {C.CYAN}[1]{C.RESET} Share ke Group (Group ID)")
        safe_print(f"  {C.CYAN}[2]{C.RESET} Share ke User (Roblox User ID)")
        safe_print(f"  {C.CYAN}[3]{C.RESET} Share ke Experience (Universe ID)")
        safe_print(f"  {C.CYAN}[4]{C.RESET} Share ke Public / All Experiences (Buka Akses Bebas Global)")
        safe_print(f"  {C.CYAN}[5]{C.RESET} Share ke Seluruh Experience dalam Suatu Group (Group Games)")
        safe_print(f"  {C.CYAN}[6]{C.RESET} Mode Watch & Auto-Dispatch (Tunggu Role Diberikan)")
        safe_print(f"  {C.CYAN}[7]{C.RESET} Cek Riwayat Share (Activity Log)")
        safe_print(f"  {C.RED}[0]{C.RESET} Keluar\n")

        pilihan = input("  Pilih menu [0-7]: ").strip()
        if pilihan == "0":
            safe_print("\n  Sampai jumpa!\n")
            break

        elif pilihan in ["1", "2", "3", "4", "5", "6"]:
            target_type = "Group"
            if pilihan == "1":
                target_type = "Group"
            elif pilihan == "2":
                target_type = "User"
            elif pilihan == "3":
                target_type = "Universe"
            elif pilihan == "4":
                target_type = "Public"
            elif pilihan == "5":
                target_type = "GroupGames"
            elif pilihan == "6":
                sub_type = input("  Target tipe untuk Watch [1: Group, 2: User, 3: Universe] (default: 1): ").strip() or "1"
                target_type = "User" if sub_type == "2" else ("Universe" if sub_type == "3" else "Group")

            target_id = ""
            if target_type != "Public":
                label = "Group ID" if target_type in ["Group", "GroupGames"] else ("User ID" if target_type == "User" else "Universe ID")
                target_id = input(f"  Masukkan {label}: ").strip()
                if not target_id:
                    safe_print(f"  {C.RED}ID target tidak boleh kosong!{C.RESET}\n")
                    continue

            buyer_name = input("  Nama Buyer / Klien (opsional): ").strip()

            safe_print("\n  Pilih Sumber Aset:")
            safe_print("    - Masukkan path file (contoh: sample_assets.txt, list.lua)")
            safe_print("    - ATAU paste langsung ID aset (pisahkan koma/spasi)")
            src = input("  Sumber Aset: ").strip()
            if not src:
                safe_print(f"  {C.RED}Sumber aset tidak boleh kosong!{C.RESET}\n")
                continue

            ids = []
            source_desc = "Direct"
            if os.path.exists(src):
                ids, actual = extract_ids_from_file(src)
                source_desc = os.path.basename(actual)
            else:
                ids = extract_ids_from_text(src)
                source_desc = f"Direct Input ({len(ids)} IDs)"

            if not ids:
                safe_print(f"  {C.RED}Tidak ada Asset ID Roblox yang ditemukan dari input tersebut!{C.RESET}\n")
                continue

            safe_print(f"  {C.GREEN}[✓] Ditemukan {len(ids)} Asset ID siap diproses.{C.RESET}\n")

            if pilihan == "5":
                share_all_group_games(target_id, ids, buyer_name=buyer_name, source_desc=source_desc)
            elif pilihan == "6":
                inv = input("  Interval pengecekan dalam detik (default: 60): ").strip()
                interval = int(inv) if inv.isdigit() and int(inv) > 0 else 60
                watch_and_share(target_id, target_type, ids, buyer_name=buyer_name, source_name=source_desc, interval=interval)
            else:
                execute_share(target_id, target_type, ids, buyer_name=buyer_name, source_name=source_desc)

        elif pilihan == "7":
            history = load_share_history()
            print_banner(f"RIWAYAT AKTIVITAS SHARE ({len(history)} TRANSAKSI)")
            if not history:
                safe_print("  Belum ada riwayat transaksi share.\n")
            else:
                for item in reversed(history[-15:]):
                    st = "✅ Full" if item.get("failedCount", 0) == 0 else "⚠️ Partial"
                    safe_print(f"  [{item.get('timestamp')}] {st} | Buyer: {C.BOLD}{item.get('buyer')}{C.RESET} | Target: {item.get('targetType')} {item.get('targetId')} | {item.get('successCount')}/{item.get('total')} sukses")
                safe_print(f"\n  Lihat catatan tabel lengkap di: {C.CYAN}{MASTER_ACTIVITY_LOG_MD}{C.RESET}\n")

        input(f"\n  {C.DIM}Tekan ENTER untuk kembali ke menu...{C.RESET}")

# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Roblox Open Cloud Asset Permission Sharing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh Penggunaan CLI:
  python share_permission.py --target 10653990168 --type Group --file assets.txt
  python share_permission.py --target 7327571817 --type User --id 140529015040235
  python share_permission.py --type Public --file assets.txt
  python share_permission.py --group-games 10653990168 --file assets.txt
  python share_permission.py --target 10653990168 --type Group --file assets.txt --watch --interval 30
        """
    )
    parser.add_argument("--target", "-t", help="Target ID numerik (User ID, Group ID, atau Universe ID). Pisahkan koma jika banyak.")
    parser.add_argument("--type", choices=["User", "Group", "Universe", "Public", "All"], default="Group", help="Tipe target penerima izin (default: Group)")
    parser.add_argument("--group-games", help="Group ID untuk membagikan ke SELURUH Experience/Universe di grup tersebut")
    parser.add_argument("--file", "-f", help="Path file sumber aset (.txt, .lua, atau teks lainnya)")
    parser.add_argument("--id", help="Asset ID langsung (satu ID atau beberapa ID pisahkan koma)")
    parser.add_argument("--buyer", "-b", help="Nama buyer atau catatan klien untuk dicatat di log")
    parser.add_argument("--batch", type=int, default=30, help="Jumlah aset per batch request (default: 30)")
    parser.add_argument("--delay", type=float, default=0.3, help="Jeda antar batch dalam detik (default: 0.3)")
    parser.add_argument("--watch", "-w", action="store_true", help="Aktifkan Watch Mode: cek izin berkala dan auto-dispatch saat akses diberikan")
    parser.add_argument("--interval", type=int, default=60, help="Interval waktu cek pada Watch Mode dalam detik (default: 60)")
    parser.add_argument("--max-retries", type=int, default=0, help="Batas maksimal pengecekan pada Watch Mode (0 = tanpa batas)")
    parser.add_argument("--account", help="Filter akun pengirim tertentu jika memiliki multi-akun di .env")
    parser.add_argument("--no-save", action="store_true", help="Jangan simpan log hasil eksekusi ke file JSON dan Markdown")
    parser.add_argument("--history", action="store_true", help="Tampilkan riwayat transaksi share")

    # Jika dipanggil tanpa argumen, tampilkan menu interaktif
    if len(sys.argv) == 1:
        interactive_wizard()
        return

    args = parser.parse_args()

    if args.history:
        history = load_share_history()
        print_banner(f"RIWAYAT AKTIVITAS SHARE ({len(history)} TRANSAKSI)")
        if not history:
            safe_print("  Belum ada riwayat transaksi share.\n")
        else:
            for item in reversed(history[-20:]):
                st = "✅ Full" if item.get("failedCount", 0) == 0 else "⚠️ Partial"
                safe_print(f"  [{item.get('timestamp')}] {st} | Buyer: {C.BOLD}{item.get('buyer')}{C.RESET} | Target: {item.get('targetType')} {item.get('targetId')} | {item.get('successCount')}/{item.get('total')} sukses")
        return

    # Ekstraksi ID
    ids = []
    source_desc = "Manual"
    if args.file:
        ids, actual = extract_ids_from_file(args.file)
        source_desc = os.path.basename(actual) if actual else args.file
    elif args.id:
        ids = extract_ids_from_text(args.id)
        source_desc = f"Direct ID ({len(ids)} Assets)"
    else:
        safe_print(f"{C.RED}[ERROR] Masukkan sumber aset dengan --file <path> atau --id <id>!{C.RESET}")
        return

    if not ids:
        safe_print(f"{C.RED}[ERROR] Tidak ada Asset ID yang ditemukan! Periksa file atau parameter --id.{C.RESET}")
        return

    # Mode Group Games
    if args.group_games:
        share_all_group_games(
            group_id=args.group_games,
            ids=ids,
            batch_size=args.batch,
            delay=args.delay,
            buyer_name=args.buyer,
            source_desc=source_desc
        )
        return

    is_public = str(args.type).lower() in ["all", "public"]
    if not args.target and not is_public:
        safe_print(f"{C.RED}[ERROR] Masukkan --target <ID> atau gunakan --type Public atau --group-games!{C.RESET}")
        return

    targets = [t.strip() for t in str(args.target).split(",") if t.strip()] if args.target else ([""] if is_public else [])

    # Mode Watch
    if args.watch:
        for t in targets:
            watch_and_share(
                target_id=t,
                target_type=args.type,
                ids=ids,
                batch_size=args.batch,
                delay=args.delay,
                buyer_name=args.buyer,
                source_name=source_desc,
                interval=args.interval,
                max_retries=args.max_retries
            )
        return

    # Mode Direct Share
    for t in targets:
        execute_share(
            target_id=t,
            target_type=args.type,
            ids=ids,
            batch_size=args.batch,
            delay=args.delay,
            buyer_name=args.buyer,
            source_name=source_desc,
            account_filter=args.account,
            no_save=args.no_save
        )

if __name__ == "__main__":
    main()
