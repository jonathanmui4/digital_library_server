from pathlib import Path
from datetime import datetime, timedelta, timezone
from threading import Lock
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill
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

# Color fills for status indicators (Summary sheet)
FILL_GREEN = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
FILL_YELLOW = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
FILL_RED = PatternFill(start_color="F8CBAD", end_color="F8CBAD", fill_type="solid")

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

    def _to_wib(dt: datetime):
        """Coerce naive datetimes to UTC before converting to Jakarta."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(JAKARTA_TZ)

    # If already datetime → convert to WIB
    if isinstance(value, datetime):
        return _to_wib(value).strftime("%d %b %Y, %H:%M:%S WIB")

    # Try parsing ISO strings
    try:
        # If string ends with Z, treat as UTC
        s = str(value)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

        dt = datetime.fromisoformat(s)
        dt = _to_wib(dt)
        return dt.strftime("%d %b %Y, %H:%M:%S WIB")
    except Exception:
        # If unparseable, return original
        return value

def _to_wib_datetime(value):
    """
    Convert a datetime-like value to a timezone-aware datetime in WIB.
    Returns None if parsing fails.
    """
    if not value:
        return None

    def _as_wib(dt: datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(JAKARTA_TZ)

    if isinstance(value, datetime):
        return _as_wib(value)

    try:
        s = str(value)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        return _as_wib(dt)
    except Exception:
        pass

    # Fallback: try common date-only formats (often typed directly in Excel)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(str(value), fmt)
            return _as_wib(dt)
        except Exception:
            continue

    # Fallback: formatted with month abbreviations and WIB suffix
    try:
        dt = datetime.strptime(str(value), "%d %b %Y, %H:%M:%S WIB")
        return _as_wib(dt)
    except Exception:
        pass

    # If still not parsable, give up
    return None
    
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
        "Book ID (Kode Buku)",                  # book_id
        "Title (Judul Buku)",                   # title
        "Author (Penulis)",                     # author
        "Category (Kategori)",                  # category
        "Added Date (Tanggal Ditambahkan)",     # added_date (local Jakarta time if missing)
    ])

    # -------- Log sheet --------
    ws_log = wb.create_sheet(LOG_SHEET)
    ws_log.append([
        "Transaction Type (Jenis Transaksi)",     # Pinjam / Kembali
        "Transaction Date (Tanggal Transaksi)",    # borrow/return date
        "Book ID (Kode Buku)",                     # book_id
        "Book Title (Judul Buku)",                 # title
        "Borrower Name (Nama Peminjam)",           # student_name
        "Class (Kelas)",                           # student_grade
        "Due Date (Tanggal Jatuh Tempo)",          # due_date
    ])

    # -------- Summary sheet --------
    ws_summary = wb.create_sheet(SUMMARY_SHEET)
    ws_summary.append([
        "Book ID (Kode Buku)",                             # book_id (PRIMARY KEY)
        "Book Title (Judul Buku)",                         # last known title
        "Status",                                          # Dipinjam / Tersedia
        "Last Borrower (Nama Terakhir)",                   # last borrower name
        "Last Class (Kelas Terakhir)",                     # last borrower class
        "Last Transaction Date (Tanggal Transaksi Terakhir)",   # last borrow/return date
        "Last Due Date (Tanggal Jatuh Tempo Terakhir)",     # last due date (if any)
        "Total Borrowed (Total Dipinjam)",                  # how many times borrowed
        "Overdue Status (Status Keterlambatan)",            # overdue indicator
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
            "Book ID (Kode Buku)",
            "Book Title (Judul Buku)",
            "Status",
            "Last Borrower (Nama Terakhir)",
            "Last Class (Kelas Terakhir)",
            "Last Transaction Date (Tanggal Transaksi Terakhir)",
            "Last Due Date (Tanggal Jatuh Tempo Terakhir)",
            "Total Borrowed (Total Dipinjam)",
            "Overdue Status (Status Keterlambatan)",
        ])

    # Ensure exactly one overdue status column (handle legacy duplicates)
    headers = [cell.value for cell in ws[1]]
    overdue_header = "Overdue Status (Status Keterlambatan)"
    overdue_cols = [idx + 1 for idx, val in enumerate(headers) if val == overdue_header]

    if not overdue_cols:
        ws.cell(row=1, column=len(headers) + 1).value = overdue_header
    elif len(overdue_cols) > 1:
        # Keep the first, remove the rest to avoid duplicated columns
        for col_idx in reversed(overdue_cols[1:]):  # delete from the right to left
            ws.delete_cols(col_idx)
    return ws

def _lookup_title_by_book_id(wb, book_id: str) -> str:
    """
    Find the book title in the Catalogue sheet by book_id (case-insensitive).
    Returns empty string if not found.
    """
    if not book_id:
        return ""

    if CATALOGUE_SHEET not in wb.sheetnames:
        return ""

    ws_catalogue = wb[CATALOGUE_SHEET]
    target = str(book_id).strip().lower()

    for row in ws_catalogue.iter_rows(min_row=2, values_only=True):
        existing_id = str(row[0]).strip().lower() if row[0] else ""
        if existing_id == target:
            return row[1] or ""

    return ""

def _latest_borrow_info(wb, book_id: str):
    """
    Return the most recent borrow info for a given book_id from Log sheet.
    Uses appended order (bottom is latest). Returns dict with keys:
    title, student_name, student_grade, due_date, tanggal_transaksi.
    """
    if not book_id or LOG_SHEET not in wb.sheetnames:
        return {}

    ws_log = wb[LOG_SHEET]
    target = str(book_id).strip().lower()

    # Iterate from bottom to find latest matching borrow
    for row in reversed(list(ws_log.iter_rows(min_row=2, values_only=True))):
        if not row:
            continue
        jenis = (row[0] or "").strip().lower()
        logged_book_id = str(row[2]).strip().lower() if len(row) > 2 and row[2] else ""
        if jenis == "pinjam" and logged_book_id == target:
            return {
                "title": row[3] or "",
                "student_name": row[4] or "",
                "student_grade": row[5] or "",
                "due_date": row[6] or "",
                "tanggal_transaksi": row[1] or "",
            }
    return {}

def _compute_overdue_status(status_value, due_date_value):
    """
    Given status ("Dipinjam"/"Tersedia") and due_date value, return
    (status_text, fill_color) where fill_color is an openpyxl PatternFill.
    """
    # Available books or missing due dates are treated as not overdue
    if status_value != "Dipinjam":
        return "Tersedia / Tidak Terlambat", FILL_GREEN

    due_dt = _to_wib_datetime(due_date_value)
    if not due_dt:
        return "Belum ada jatuh tempo", FILL_GREEN

    delta_days = (_now_wib().date() - due_dt.date()).days

    if delta_days > 7:
        return f"Terlambat {delta_days} hari", FILL_RED
    elif delta_days > 0:
        return f"Terlambat {delta_days} hari", FILL_YELLOW
    else:
        return "Belum Jatuh Tempo", FILL_GREEN

def _refresh_overdue_status(ws_summary):
    """
    Update the overdue status text and color for every row in the Summary sheet.
    Should be called after any log update (borrow/return) to keep statuses fresh.
    """
    # Determine column indices based on header names for resilience
    headers = [cell.value for cell in ws_summary[1]]
    try:
        idx_status = headers.index("Status")
        idx_due = headers.index("Last Due Date (Tanggal Jatuh Tempo Terakhir)")
        idx_overdue = headers.index("Overdue Status (Status Keterlambatan)")
    except ValueError:
        return  # headers not as expected; fail silently

    for row in ws_summary.iter_rows(min_row=2):
        status_val = row[idx_status].value or ""
        due_val = row[idx_due].value or ""

        text, fill = _compute_overdue_status(status_val, due_val)

        # Ensure the overdue status cell exists
        overdue_cell = row[idx_overdue]
        overdue_cell.value = text
        overdue_cell.fill = fill

def refresh_summary_overdue_status():
    """
    Public helper to refresh overdue status in the Summary sheet.
    Useful to call on server startup.
    """
    wb = _get_workbook()
    ws_summary = _get_or_create_summary_sheet(wb)
    _refresh_overdue_status(ws_summary)
    wb.save(EXCEL_FILE)

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

    def _norm(value):
        return str(value).strip().lower() if value is not None else ""

    existing_row = None
    target = _norm(book_id)
    for row in ws_summary.iter_rows(min_row=2):
        if _norm(row[0].value) == target:
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
            "",                   # Status Keterlambatan (filled later)
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
                "Jenis Transaksi",
                "Tanggal Transaksi",
                "Kode Buku",
                "Judul Buku",
                "Nama Peminjam",
                "Kelas",
                "Tanggal Jatuh Tempo",
            ])

        # Timestamp now (WIB)
        #waktu_log = _now_wib_str()

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

        # Prefer payload title; fall back to catalogue lookup
        title = data.get("title") or _lookup_title_by_book_id(wb, data.get("book_id", ""))

        # For return: backfill missing borrower/class/due_date from latest borrow
        if jenis == "Kembali":
            last_borrow = _latest_borrow_info(wb, data.get("book_id", ""))
            data_student_name = data.get("student_name") or last_borrow.get("student_name", "")
            data_student_grade = data.get("student_grade") or last_borrow.get("student_grade", "")
            tanggal_jatuh_tempo = tanggal_jatuh_tempo or last_borrow.get("due_date", "")
            # If no title found yet, try last borrow title
            if not title:
                title = last_borrow.get("title", "")
        else:
            data_student_name = data.get("student_name", "")
            data_student_grade = data.get("student_grade", "")

        # Append to Log sheet
        row_values = [
            jenis,
            tanggal_transaksi,
            data.get("book_id", ""),
            title,
            data_student_name,
            data_student_grade,
            tanggal_jatuh_tempo,
        ]
        ws.append(row_values)

        # Update Summary tab as well
        ws_summary = _get_or_create_summary_sheet(wb)
        _update_summary_for_book(
            ws_summary,
            book_id=data.get("book_id", ""),
            title=title,
            borrower=data_student_name,
            kelas=data_student_grade,
            jenis=jenis,
            tanggal_transaksi=tanggal_transaksi,
            tanggal_jatuh_tempo=tanggal_jatuh_tempo,
        )

        # Refresh overdue status coloring/text
        _refresh_overdue_status(ws_summary)

        # Save everything
        wb.save(EXCEL_FILE)
        print("[EXCEL] Log + Summary updated successfully")
