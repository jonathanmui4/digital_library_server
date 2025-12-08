from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from zoneinfo import ZoneInfo
from excel_utils import init_excel, append_log_row, append_catalogue_row, refresh_summary_overdue_status
import json
import socket
import webbrowser
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Ensure Excel is initialized and summary overdue status is refreshed once per process
_excel_ready = False


def ensure_excel_ready():
    global _excel_ready
    if _excel_ready:
        return
    init_excel()
    try:
        refresh_summary_overdue_status()
    except Exception as e:
        # Colors not yet defined here; use plain print
        print(f"[WARN] Failed to refresh overdue status on startup: {e}")
    _excel_ready = True


# Initialize Excel/summary at import time (safe to re-run per process)
ensure_excel_ready()


# Store recent transactions in memory
recent_transactions = []
MAX_TRANSACTIONS = 50


# Color codes for pretty console output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_separator():
    print("=" * 60)


def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Create a socket to get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 5050))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def open_browser():
    """Open the dashboard in the default browser after a short delay"""
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open('http://localhost:5050/dashboard')


@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'Digital Library Server is running',
        'endpoints': [
            '/dashboard (GET) - Web Dashboard',
            '/api/transaction (POST)',
            '/api/book (POST)',
            '/api/server-info (GET)',
            '/api/recent-transactions (GET)',
            '/health (GET)'
        ]
    })


@app.route('/dashboard')
def dashboard():
    """Serve the dashboard HTML"""
    return render_template('dashboard.html')


@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d %b %Y, %H:%M:%S")})


@app.route('/api/server-info')
def server_info():
    """Return server information including IP address"""
    local_ip = get_local_ip()
    return jsonify({
        'ip': f'{local_ip}:5050',
        'status': 'running',
        'version': '1.0'
    })


@app.route('/api/recent-transactions')
def get_recent_transactions():
    """Return recent transactions for the dashboard"""
    return jsonify({
        'transactions': recent_transactions,
        'count': len(recent_transactions)
    })


@app.route('/api/transaction', methods=['POST'])
def receive_transaction():
    try:
        data = request.get_json()

        # Store transaction
        transaction_record = {
            'action': data.get('action', 'unknown'),
            'data': data,
            'timestamp': datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d %b %Y, %H:%M:%S")
        }
        recent_transactions.insert(0, transaction_record)

        # Keep only the most recent transactions
        if len(recent_transactions) > MAX_TRANSACTIONS:
            recent_transactions.pop()

        print_separator()
        print(f"{Colors.BOLD}{Colors.OKCYAN}📚 TRANSACTION RECEIVED{Colors.ENDC}")
        print_separator()

        action = data.get('action', 'unknown')

        if action == 'borrow':
            print(f"{Colors.OKGREEN}Action:{Colors.ENDC} BORROW")
            print(f"{Colors.OKBLUE}Student:{Colors.ENDC} {data.get('student_name')} ({data.get('student_grade')})")
            print(f"{Colors.OKBLUE}Book ID:{Colors.ENDC} {data.get('book_id')}")
            print(f"{Colors.OKBLUE}Borrow Date:{Colors.ENDC} {data.get('borrow_date')}")
            print(f"{Colors.OKBLUE}Due Date:{Colors.ENDC} {data.get('due_date')}")
        elif action == 'return':
            print(f"{Colors.WARNING}Action:{Colors.ENDC} RETURN")
            print(f"{Colors.OKBLUE}Book ID:{Colors.ENDC} {data.get('book_id')}")
            print(f"{Colors.OKBLUE}Return Date:{Colors.ENDC} {data.get('return_date')}")
        else:
            print(f"{Colors.FAIL}Action:{Colors.ENDC} UNKNOWN")

        print(f"\n{Colors.HEADER}Raw JSON:{Colors.ENDC}")
        print(json.dumps(data, indent=2))
        print_separator()
        print()

        # write to excel
        try:
            append_log_row(data)
        except Exception as e:
            print(f"{Colors.FAIL}[EXCEL] Failed to write log: {e}{Colors.ENDC}")

        return jsonify({
            'status': 'success',
            'message': f'Transaction ({action}) received successfully',
            'timestamp': datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d %b %Y, %H:%M:%S")
        }), 200

    except Exception as e:
        print(f"{Colors.FAIL}ERROR: {str(e)}{Colors.ENDC}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


@app.route('/api/book', methods=['POST'])
def receive_book():
    try:
        data = request.get_json()

        excel_result = append_catalogue_row(data)
        if excel_result and excel_result.get("duplicate"):
            # Duplicate book: DO NOT add to recent_transactions
            book_id = data.get('book_id')
            print_separator()
            print(f"{Colors.WARNING}⚠ Duplicate Book ID, not adding to dashboard: {book_id}{Colors.ENDC}")
            print_separator()

            return jsonify({
                "status": "warning",
                "duplicate": True,
                "message": f"Duplicate Book ID: {book_id}",
                "timestamp": datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d %b %Y, %H:%M:%S")
            }), 409  # Conflict
        
        # Store transaction for dashboard
        transaction_record = {
            'action': 'add_book',
            'data': data,
            'timestamp': datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d %b %Y, %H:%M:%S")
        }
        recent_transactions.insert(0, transaction_record)

        # Store transaction for dashboard
        transaction_record = {
            'action': 'add_book',
            'data': data,
            'timestamp': datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d %b %Y, %H:%M:%S")
        }

        if len(recent_transactions) > MAX_TRANSACTIONS:
            recent_transactions.pop()

        print_separator()
        print(f"{Colors.BOLD}{Colors.OKGREEN}📖 NEW BOOK RECEIVED{Colors.ENDC}")
        print_separator()
        print(f"{Colors.OKBLUE}Book ID:{Colors.ENDC} {data.get('book_id')}")
        print(f"{Colors.OKBLUE}Title:{Colors.ENDC} {data.get('title')}")
        print(f"{Colors.OKBLUE}Author:{Colors.ENDC} {data.get('author')}")
        print(f"{Colors.OKBLUE}Category:{Colors.ENDC} {data.get('category', 'N/A')}")
        print(f"{Colors.OKBLUE}Added Date:{Colors.ENDC} {data.get('added_date')}")
        print()
        print(f"{Colors.HEADER}Raw JSON:{Colors.ENDC}")
        print(json.dumps(data, indent=2))
        print_separator()
        print()

        # NEW: Write to Excel and detect duplicates
        excel_result = append_catalogue_row(data)

        # If duplicate, warn the app
        if excel_result and excel_result.get("duplicate"):
            print(f"{Colors.WARNING}[WARN] Duplicate Book ID detected!{Colors.ENDC}")
            return jsonify({
                "status": "warning",
                "duplicate": True,
                "message": f"Duplicate Book ID: {data.get('book_id')}",
                "timestamp": datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d %b %Y, %H:%M:%S")
            }), 409  # 409 = Conflict (duplicate)

        # If no duplicate → success
        return jsonify({
            "status": "success",
            "duplicate": False,
            "message": "Book added successfully",
            "timestamp": datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d %b %Y, %H:%M:%S")
        }), 200

    except Exception as e:
        print(f"{Colors.FAIL}ERROR: {str(e)}{Colors.ENDC}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


if __name__ == '__main__':
    local_ip = get_local_ip()

    # NEW: make sure Excel file & sheets exist and refresh overdue status
    ensure_excel_ready()

    print(f"{Colors.BOLD}{Colors.OKGREEN}")
    print("=" * 60)
    print("🚀 Digital Library Server Starting...")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Dashboard: http://localhost:5050/dashboard{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Server Address: http://{local_ip}:5050{Colors.ENDC}")
    print(f"{Colors.WARNING}For Android Emulator: http://10.0.2.2:5050{Colors.ENDC}")
    print()
    print(f"{Colors.OKGREEN}✓ Dashboard will open automatically in your browser...{Colors.ENDC}")
    print()

    # Open browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run on all interfaces so emulator can access it
    app.run(host='0.0.0.0', port=5050, debug=True, use_reloader=False)
