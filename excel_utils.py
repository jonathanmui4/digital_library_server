from pathlib import Path
from datetime import datetime, timedelta, timezone
from threading import Lock
from openpyxl import Workbook, load_workbook
from zoneinfo import ZoneInfo
import json

# Excel file path (same folder as server.py)
BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "library_data.xlsx"

CATALOGUE_SHEET = "Katalog Buku"
LOG_SHEET = "Riwayat Transaksi Buku"
SUMMARY_SHEET = "Ringkasan Transaksi Buku" 

# Jakarta timezone (WIB = UTC+7)
JAKARTA_TZ = timezone(timedelta(hours=7))

_excel_lock = Lock()


def _now_wib():
    """Return current datetime in Jakarta timezone (WIB)."""
    return datetime.now(JAKARTA_TZ)

def _now_wib_str():
    """Return current Jakarta time as formatted string."""
    return _now_wib().strftime("%d %b %Y, %H:%M:%S WIB")

def _format_dt(value):
    """
    Format any datetime-like value into 'DD Mon YYYY, HH:MM:SS WIB'.

    - Handles ISO strings and Python datetime
    - Adds WIB timezone indicator
    """
    if not value:
        return ""

    # If already datetime → convert to WIB
    if isinstance(value, datetime):
        return value.astimezone(JAKARTA_TZ).strftime("%d %b %Y, %H:%M:%S WIB")

    # Try parsing ISO strings
    try:
        # If string ends with Z, treat as UTC
        s = str(value)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

        dt = datetime.fromisoformat(s)
        dt = dt.astimezone(JAKARTA_TZ)
        return dt.strftime("%d %b %Y, %H:%M:%S WIB")
    except Exception:
        # If unparseable, return original
        return value

    
def init_excel():
    """
    Create the Excel file with the 2 sheets if it does not exist yet.
    Headers are fixed and use Indonesian labels.
    """
    if EXCEL_FILE.exists():
        return

    wb = Workbook()

    # -------- Catalogue sheet --------
    ws_catalogue = wb.active
    ws_catalogue.title = CATALOGUE_SHEET
    ws_catalogue.append([
        "Kode Buku",          # book_id
        "Judul Buku",         # title
        "Penulis",            # author
        "Kategori",           # category
        "Tanggal Ditambahkan" # added_date (local Jakarta time if missing)
    ])

    # -------- Log sheet --------
    ws_log = wb.create_sheet(LOG_SHEET)
    ws_log.append([
        "Waktu",             # timestamp (Jakarta)
        "Kode Buku",         # book_id
        "Judul Buku",        # title (if sent)
        "Nama Peminjam",     # student_name
        "Kelas",             # student_grade
        "Tanggal Pinjam",    # borrow_date
        "Jatuh Tempo",       # due_date
        "Tanggal Kembali",   # return_date
    ])

    # -------- Summary sheet --------
    ws_summary = wb.create_sheet(SUMMARY_SHEET)
    ws_summary.append([
        "Kode Buku",                    # book_id (PRIMARY KEY)
        "Judul Buku",                   # last known title
        "Status",                       # Dipinjam / Tersedia
        "Nama Terakhir",                # last borrower name
        "Kelas Terakhir",               # last borrower class
        "Tanggal Transaksi Terakhir",   # last borrow/return date
        "Tanggal Jatuh Tempo Terakhir", # last due date (if any)
        "Total Dipinjam",               # how many times borrowed
    ])

    wb.save(EXCEL_FILE)
    print(f"[INIT] Created Excel database at {EXCEL_FILE}")


def _get_workbook():
    """
    Load existing workbook (assuming init_excel already ran).
    """
    if not EXCEL_FILE.exists():
        init_excel()
    return load_workbook(EXCEL_FILE)

def _get_or_create_summary_sheet(wb):
    """Get the Summary sheet, create with headers if missing."""
    if SUMMARY_SHEET in wb.sheetnames:
        ws = wb[SUMMARY_SHEET]
    else:
        ws = wb.create_sheet(SUMMARY_SHEET)
        ws.append([
            "Kode Buku",
            "Judul Buku",
            "Status",
            "Nama Terakhir",
            "Kelas Terakhir",
            "Tanggal Transaksi Terakhir",
            "Tanggal Jatuh Tempo Terakhir",
            "Total Dipinjam",
        ])
    return ws

def _update_summary_for_book(ws_summary, book_id, title, borrower, kelas,
                             jenis, tanggal_transaksi, tanggal_jatuh_tempo):
    """
    Update or create a summary row for a given book_id.

    - If book_id exists -> update that row
    - If not -> append new row
    - jenis: "Pinjam" or "Kembali"
    """
    if not book_id:
        return  # nothing to summarize

    status = "Dipinjam" if jenis == "Pinjam" else "Tersedia"

    existing_row = None
    for row in ws_summary.iter_rows(min_row=2):
        if (row[0].value or "") == book_id:
            existing_row = row
            break

    if existing_row:
        # Update existing row cells
        # Columns: 0=Kode,1=Judul,2=Status,3=Nama,4=Kelas,5=TglTrans,6=TglJatuh,7=Total
        existing_row[1].value = title or existing_row[1].value
        existing_row[2].value = status
        existing_row[3].value = borrower or existing_row[3].value
        existing_row[4].value = kelas or existing_row[4].value
        existing_row[5].value = tanggal_transaksi or existing_row[5].value
        if tanggal_jatuh_tempo:
            existing_row[6].value = tanggal_jatuh_tempo

        # update Total Dipinjam only on borrow
        total = existing_row[7].value or 0
        try:
            total_int = int(total)
        except Exception:
            total_int = 0
        if jenis == "Pinjam":
            total_int += 1
        existing_row[7].value = total_int
    else:
        # New row
        total_int = 1 if jenis == "Pinjam" else 0
        ws_summary.append([
            book_id,              # Kode Buku
            title or "",          # Judul Buku
            status,               # Status
            borrower or "",       # Nama Terakhir
            kelas or "",          # Kelas Terakhir
            tanggal_transaksi,    # Tanggal Transaksi Terakhir
            tanggal_jatuh_tempo,  # Tanggal Jatuh Tempo Terakhir
            total_int,            # Total Dipinjam
        ])

def _catalogue_has_duplicate(ws, new_book_id):
    """
    Check if the given book_id already exists in the Catalogue sheet.
    Returns True if duplicate found.
    """
    if not new_book_id:
        return False  # ignore empty entries

    for row in ws.iter_rows(min_row=2, values_only=True):
        book_id = str(row[0]) if row[0] else ""
        if book_id.lower() == new_book_id.lower():
            return True

    return False

def append_catalogue_row(data: dict):
    """
    Append a row to the Catalogue sheet.

    Mapping (JSON -> Excel columns):
        book_id      -> Kode Buku
        title        -> Judul Buku
        author       -> Penulis
        category     -> Kategori
        added_date   -> Tanggal Ditambahkan
                       (if missing, use current Jakarta time)
    """
    with _excel_lock:
        wb = _get_workbook()

        if CATALOGUE_SHEET in wb.sheetnames:
            ws = wb[CATALOGUE_SHEET]
        else:
            ws = wb.create_sheet(CATALOGUE_SHEET)
            ws.append([
                "Kode Buku",
                "Judul Buku",
                "Penulis",
                "Kategori",
                "Tanggal Ditambahkan"
            ])

        # Use app-provided added_date if present, otherwise now() in WIB
        raw_added_date = data.get("added_date")
        if raw_added_date:
            added_date = _format_dt(raw_added_date)
        else:
            added_date = _now_wib_str()

        new_book_id = data.get("book_id", "")

        # Duplicate check
        if _catalogue_has_duplicate(ws, new_book_id):
            print(f"[WARN] Duplicate Book ID detected: {new_book_id}")
            return {
                "status": "warning",
                "message": f"Duplicate Book ID: {new_book_id}",
                "duplicate": True
            }

        row_values = [
            new_book_id,
            data.get("title", ""),
            data.get("author", ""),
            data.get("category", ""),
            added_date,
        ]

        ws.append(row_values)
        try:
            wb.save(EXCEL_FILE)
            print(f"[EXCEL] New book added to Catalogue ({new_book_id})")
            return {
                "status": "success",
                "duplicate": False
            }
        except PermissionError:
            print("[EXCEL] ⚠ Excel is OPEN in EDIT mode. Changes not saved.")
            # optional: return an error dict here too


def append_log_row(data: dict):
    """
    Append a row to the Log sheet and update the Summary sheet.

    Columns in Log:
        Waktu Log         -> current local Jakarta time
        Jenis Transaksi   -> Pinjam / Kembali
        Tanggal Transaksi -> borrow or return date
        Kode Buku
        Judul Buku
        Nama Peminjam
        Kelas
        Tanggal Jatuh Tempo -> only for borrow, blank for return
    """
    with _excel_lock:
        wb = _get_workbook()

        # Ensure Log sheet exists
        if LOG_SHEET in wb.sheetnames:
            ws = wb[LOG_SHEET]
        else:
            ws = wb.create_sheet(LOG_SHEET)
            ws.append([
                "Waktu Log",
                "Jenis Transaksi",
                "Tanggal Transaksi",
                "Kode Buku",
                "Judul Buku",
                "Nama Peminjam",
                "Kelas",
                "Tanggal Jatuh Tempo",
            ])

        # Timestamp now (WIB)
        waktu_log = _now_wib_str()

        # Determine action translation
        action = (data.get("action") or "").lower()
        if action == "borrow":
            jenis = "Pinjam"
        elif action == "return":
            jenis = "Kembali"
        else:
            jenis = "Tidak Diketahui"

        # Choose correct date
        if jenis == "Pinjam":
            tanggal_transaksi = _format_dt(data.get("borrow_date"))
            tanggal_jatuh_tempo = _format_dt(data.get("due_date"))
        elif jenis == "Kembali":
            tanggal_transaksi = _format_dt(data.get("return_date"))
            tanggal_jatuh_tempo = ""
        else:
            tanggal_transaksi = _format_dt(data.get("borrow_date") or data.get("return_date"))
            tanggal_jatuh_tempo = _format_dt(data.get("due_date"))

        # Append to Log sheet
        row_values = [
            waktu_log,
            jenis,
            tanggal_transaksi,
            data.get("book_id", ""),
            data.get("title", ""),
            data.get("student_name", ""),
            data.get("student_grade", ""),
            tanggal_jatuh_tempo,
        ]
        ws.append(row_values)

        # Update Summary tab as well
        ws_summary = _get_or_create_summary_sheet(wb)
        _update_summary_for_book(
            ws_summary,
            book_id=data.get("book_id", ""),
            title=data.get("title", ""),
            borrower=data.get("student_name", ""),
            kelas=data.get("student_grade", ""),
            jenis=jenis,
            tanggal_transaksi=tanggal_transaksi,
            tanggal_jatuh_tempo=tanggal_jatuh_tempo,
        )

        # Save everything
        wb.save(EXCEL_FILE)
        print("[EXCEL] Log + Summary updated successfully")
