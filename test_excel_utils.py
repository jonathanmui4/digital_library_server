from excel_utils import init_excel, append_catalogue_row, append_log_row
from datetime import datetime

# 1. Make sure the Excel file & sheets are created
init_excel()
print("✅ init_excel() called")

# 2. Test writing a fake book to Catalogue
sample_book = {
    "book_id": "BOOK-TEST-001",
    "title": "Test Book From Script",
    "author": "Tester",
    "isbn": "123-456-789",
    "category": "Test Category",
    "added_date": datetime.now().isoformat(),
    "qr_raw": "QR-CONTENT-123"  # pretend this came from QR
}
append_catalogue_row(sample_book)
print("✅ append_catalogue_row() called")

# 3. Test writing a fake transaction to Log
sample_transaction = {
    "action": "borrow",
    "book_id": "BOOK-TEST-001",
    "student_name": "Test Student",
    "student_grade": "5A",
    "borrow_date": datetime.now().isoformat(),
    "due_date": datetime.now().isoformat(),
    "qr_raw": "QR-CONTENT-123",  # again, pretend QR data
    "extra_field_from_app": "anything_here"
}
append_log_row(sample_transaction)
print("✅ append_log_row() called")

print("🎉 Done. Now open library_data.xlsx and check the data.")
