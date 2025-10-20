from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
import socket
import webbrowser
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


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
            'timestamp': datetime.now().isoformat()
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

        return jsonify({
            'status': 'success',
            'message': f'Transaction ({action}) received successfully',
            'timestamp': datetime.now().isoformat()
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

        # Store transaction
        transaction_record = {
            'action': 'add_book',
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        recent_transactions.insert(0, transaction_record)

        # Keep only the most recent transactions
        if len(recent_transactions) > MAX_TRANSACTIONS:
            recent_transactions.pop()

        print_separator()
        print(f"{Colors.BOLD}{Colors.OKGREEN}📖 NEW BOOK RECEIVED{Colors.ENDC}")
        print_separator()

        print(f"{Colors.OKBLUE}Book ID:{Colors.ENDC} {data.get('book_id')}")
        print(f"{Colors.OKBLUE}Title:{Colors.ENDC} {data.get('title')}")
        print(f"{Colors.OKBLUE}Author:{Colors.ENDC} {data.get('author')}")
        print(f"{Colors.OKBLUE}ISBN:{Colors.ENDC} {data.get('isbn', 'N/A')}")
        print(f"{Colors.OKBLUE}Category:{Colors.ENDC} {data.get('category', 'N/A')}")
        print(f"{Colors.OKBLUE}Added Date:{Colors.ENDC} {data.get('added_date')}")

        print(f"\n{Colors.HEADER}Raw JSON:{Colors.ENDC}")
        print(json.dumps(data, indent=2))
        print_separator()
        print()

        return jsonify({
            'status': 'success',
            'message': 'Book added successfully',
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        print(f"{Colors.FAIL}ERROR: {str(e)}{Colors.ENDC}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


if __name__ == '__main__':
    local_ip = get_local_ip()

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