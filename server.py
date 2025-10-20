from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'Digital Library Server is running',
        'endpoints': [
            '/api/transaction (POST)',
            '/api/book (POST)',
            '/health (GET)'
        ]
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/transaction', methods=['POST'])
def receive_transaction():
    try:
        data = request.get_json()
        
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
    print(f"{Colors.BOLD}{Colors.OKGREEN}")
    print("=" * 60)
    print("🚀 Digital Library Server Starting...")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Server running on: http://0.0.0.0:80{Colors.ENDC}")
    print(f"{Colors.WARNING}For Android Emulator, use: http://10.0.2.2:80{Colors.ENDC}")
    print(f"{Colors.WARNING}For your Mac IP: Check with 'ipconfig getifaddr en0'{Colors.ENDC}")
    print()
    
    # Run on all interfaces so emulator can access it
    app.run(host='0.0.0.0', port=80, debug=True)
