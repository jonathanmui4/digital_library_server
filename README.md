# Digital Library Server 🖥️

A lightweight Flask server for the Digital Library mobile app. This server receives and logs book transactions (borrow/return) and new book additions from the mobile application.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📖 Overview

This server is designed to work with the [Digital Library Mobile App](https://github.com/jonathanmui4/digital-library-app) built for low-resource schools in Jakarta, Indonesia. It provides a simple API to receive transaction data from the mobile app over WiFi.

### Current Features
- ✅ Receive book borrow transactions
- ✅ Receive book return transactions  
- ✅ Receive new book additions
- ✅ Pretty-printed console logging with color coding
- ✅ CORS enabled for cross-origin requests
- ✅ Health check endpoint
- ✅ Works with Android emulator during development

### Coming Soon
- 🔄 Transaction history API
- 🔄 Book search and lookup
- 🔄 Data export functionality

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/library-server.git
cd library-server
```

2. **Create and activate virtual environment**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Running the Server

```bash
python server.py
```

The server will start on `http://0.0.0.0:5000`

You should see output like:
```
============================================================
🚀 Digital Library Server Starting...
============================================================

Server running on: http://0.0.0.0:5000
For Android Emulator, use: http://10.0.2.2:5000
For your Mac IP: Check with 'ipconfig getifaddr en0'
```

## 📡 API Endpoints

### Base URL
- **Local Development**: `http://localhost:5000`
- **Android Emulator**: `http://10.0.2.2:5000`
- **Network**: `http://YOUR_IP:5000`

### Endpoints

#### `GET /`
Health check and server information.

**Response:**
```json
{
  "status": "running",
  "message": "Digital Library Server is running",
  "endpoints": [
    "/api/transaction (POST)",
    "/api/book (POST)",
    "/health (GET)"
  ]
}
```

#### `GET /health`
Simple health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-20T10:30:00.000Z"
}
```

#### `POST /api/transaction`
Receive book borrow or return transactions.

**Borrow Request Body:**
```json
{
  "action": "borrow",
  "student_name": "Ahmad Rizki",
  "student_grade": "5A",
  "book_id": "BOOK-001",
  "borrow_date": "2025-10-20T10:30:00.000Z",
  "due_date": "2025-11-03T10:30:00.000Z"
}
```

**Return Request Body:**
```json
{
  "action": "return",
  "book_id": "BOOK-001",
  "return_date": "2025-10-20T10:30:00.000Z"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Transaction (borrow) received successfully",
  "timestamp": "2025-10-20T10:30:00.000Z"
}
```

#### `POST /api/book`
Receive new book additions.

**Request Body:**
```json
{
  "action": "add_book",
  "book_id": "BOOK-123",
  "title": "To Kill a Mockingbird",
  "author": "Harper Lee",
  "isbn": "978-0-06-112008-4",
  "category": "Fiction",
  "added_date": "2025-10-20T10:30:00.000Z"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Book added successfully",
  "timestamp": "2025-10-20T10:30:00.000Z"
}
```

## 🔧 Configuration

### Changing the Port

Edit `server.py` and modify the last line:

```python
app.run(host='0.0.0.0', port=5000, debug=True)  # Change 5000 to your desired port
```

### Finding Your Mac's IP Address

To allow the mobile app to connect from a real device (not emulator):

```bash
# On Mac/Linux
ipconfig getifaddr en0

# On Windows
ipconfig
```

Then update the Flutter app's `lib/services/api_service.dart`:
```dart
static const String _defaultServerUrl = 'http://YOUR_IP:5000';
```

## 🧪 Testing

### Test with curl

**Test borrow transaction:**
```bash
curl -X POST http://localhost:5000/api/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "action": "borrow",
    "student_name": "Test Student",
    "student_grade": "5A",
    "book_id": "BOOK-001",
    "borrow_date": "2025-10-20T10:00:00.000Z",
    "due_date": "2025-11-03T10:00:00.000Z"
  }'
```

**Test return transaction:**
```bash
curl -X POST http://localhost:5000/api/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "action": "return",
    "book_id": "BOOK-001",
    "return_date": "2025-10-20T10:00:00.000Z"
  }'
```

**Test add book:**
```bash
curl -X POST http://localhost:5000/api/book \
  -H "Content-Type: application/json" \
  -d '{
    "action": "add_book",
    "book_id": "BOOK-123",
    "title": "Test Book",
    "author": "Test Author",
    "isbn": "123-456",
    "category": "Fiction",
    "added_date": "2025-10-20T10:00:00.000Z"
  }'
```

### Expected Console Output

When a borrow transaction is received:
```
============================================================
📚 TRANSACTION RECEIVED
============================================================
Action: BORROW
Student: Ahmad Rizki (5A)
Book ID: BOOK-001
Borrow Date: 2025-10-20T10:30:00.000Z
Due Date: 2025-11-03T10:30:00.000Z

Raw JSON:
{
  "action": "borrow",
  "student_name": "Ahmad Rizki",
  "student_grade": "5A",
  "book_id": "BOOK-001",
  "borrow_date": "2025-10-20T10:30:00.000Z",
  "due_date": "2025-11-03T10:30:00.000Z"
}
============================================================
```

## 🐛 Troubleshooting

### Connection Issues

**Problem:** Mobile app can't connect to server

**Solutions:**
1. Make sure the server is running (check terminal for Flask output)
2. Check firewall settings - allow incoming connections on port 5000
3. For Android emulator, use `http://10.0.2.2:5000`
4. For real device, ensure both device and computer are on the same WiFi network
5. Use your computer's actual IP address, not `localhost` or `127.0.0.1`

### Port Already in Use

**Problem:** `Address already in use`

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

Or change the port in `server.py`.

### Module Not Found

**Problem:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## 📁 Project Structure

```
library-server/
├── server.py           # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── .gitignore         # Git ignore rules
└── venv/              # Virtual environment (not in git)
```

## 🤝 Integration with Mobile App

This server is designed to work with the [Digital Library Mobile App](https://github.com/jonathanmui4/digital_library).

To enable communication:

1. **Start this server** on your computer
2. **Update the mobile app** configuration in `lib/services/api_service.dart`:
   ```dart
   static const String _defaultServerUrl = 'http://10.0.2.2:5000'; // For emulator
   // OR
   static const String _defaultServerUrl = 'http://YOUR_IP:5000'; // For real device
   ```
3. **Uncomment** the API calls in the mobile app's `transaction_provider.dart`
4. **Run the mobile app** and perform transactions

The server will receive and log all transactions in real-time!

## 🎯 Design Philosophy

This server is being built for a **tech-illiterate librarian** at a school in Jakarta. Every design decision prioritizes:

1. **Zero Configuration** - It should "just work" without technical knowledge
2. **Visual Feedback** - The librarian needs to *see* that it's working
3. **Automatic Operation** - No command line, no manual starting/stopping
4. **Reliability** - Works despite WiFi issues, power outages, or app crashes

### Why Version 1.1 Features Matter

**❓ Problem:** "The librarian has to find the computer's IP address and type it into the phone app"  
**✅ Solution (mDNS):** Phone automatically finds the server. Librarian never thinks about IP addresses.

**❓ Problem:** "The librarian doesn't know if the server is running or if data is being received"  
**✅ Solution (GUI Dashboard):** Big green checkmark = working. Red X = problem. Shows recent book scans.

**❓ Problem:** "The librarian has to open a terminal and type `python server.py` every morning"  
**✅ Solution (Auto-Start):** Computer turns on → Server runs automatically. Icon in system tray shows it's working.

## 🗺️ Roadmap

### Version 1.0 (Current)
- ✅ Basic API endpoints
- ✅ Console logging
- ✅ CORS support
- ✅ Android emulator compatibility

### Version 1.1 (Next - Critical for Librarian Use)
**Goal: Make it "just work" for a non-technical librarian**

- [ ] **mDNS/Zero-Configuration Networking**
  - Server broadcasts itself as `library-server.local`
  - Mobile app automatically discovers server on WiFi
  - No need to manually enter IP addresses
  - Uses `zeroconf` (Python) + `nsd_android` (Flutter)
  
- [ ] **Simple GUI Dashboard**
  - Web-based interface at `http://localhost:5000/dashboard`
  - Shows connection status (Connected ✓ / Waiting for connection...)
  - Displays recent transactions in real-time
  - Large, clear text suitable for non-technical users
  - Visual indicators (green = good, red = problem)
  
- [ ] **Auto-Start Executable**
  - Package server as standalone `.exe` (Windows) using PyInstaller
  - Create `.app` bundle for macOS
  - Add to system startup automatically
  - Librarian just turns on computer - server runs automatically
  - System tray icon showing server status
  - Right-click menu: "Open Dashboard", "View Logs", "Stop Server"

### Version 1.2 (Data Persistence)
- [ ] SQLite database integration
- [ ] Persistent transaction storage
- [ ] GET endpoints for data retrieval
- [ ] View transaction history in dashboard
- [ ] Search and filter capabilities

### Version 2.0 (Advanced Features)
- [ ] Export data to Excel/CSV for reports
- [ ] Print transaction receipts
- [ ] Overdue book notifications
- [ ] Student borrowing history
- [ ] Book inventory management
- [ ] Analytics dashboard (most borrowed books, etc.)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Jonathan Mui - *Initial work* - [@jonathanmui4](https://github.com/jonathanmui4)

## 🙏 Acknowledgments

- Built to support the Digital Library Mobile App
- Designed for low-resource schools in Jakarta, Indonesia
- Flask framework for simplicity and reliability

## 📞 Support

For issues, questions, or contributions:
- **GitHub Issues**: [Create an issue](https://github.com/yourusername/library-server/issues)
- **Mobile App Repo**: [Digital Library App](https://github.com/jonathanmui4/digital-library-app)

---

**Built with ❤️ for education and accessibility**

*Last updated: October 2025*
