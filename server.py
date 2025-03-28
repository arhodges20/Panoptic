from flask import Flask, request, jsonify, send_from_directory, redirect, make_response
import sqlite3
import logging
from datetime import datetime, timedelta
import os
from flask_cors import CORS
import jwt
import bcrypt
from functools import wraps

app = Flask(__name__, static_folder='static')
CORS(app, supports_credentials=True)  # Enable CORS with credentials support

# Configure logging and add secret key
logging.basicConfig(level=logging.INFO)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # In production, use environment variable

# Database path
DB_PATH = "logs.db"

# Ensure static directory exists
os.makedirs('static', exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
    """)

    # Create default admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        # Hash the default password 'admin123'
        hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      ("admin", hashed.decode('utf-8')))

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            ip TEXT,
            cpu REAL,
            memory REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS new_processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            ip TEXT,
            pid INTEGER,
            name TEXT,
            user TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS privileged_processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            ip TEXT,
            pid INTEGER,
            name TEXT,
            user TEXT
        )
    """)
    conn.commit()
    conn.close()

# Insert data into database
def insert_log(table, columns, values):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(values))})"
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check for token in cookies
        token = request.cookies.get('token')
        logging.info(f"Checking token in request. Token present: {token is not None}")

        if not token:
            logging.warning("No token found in request cookies")
            return jsonify({'message': 'Token is missing'}), 401

        try:
            # Decode the token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            logging.info(f"Token decoded successfully for user: {data.get('username')}")

            # Get current user
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (data['username'],))
            current_user = cursor.fetchone()
            conn.close()

            if not current_user:
                logging.warning(f"No user found for token username: {data.get('username')}")
                return jsonify({'message': 'Invalid token'}), 401

        except jwt.ExpiredSignatureError:
            logging.warning("Token has expired")
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            logging.warning(f"Invalid token error: {str(e)}")
            return jsonify({'message': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated

@app.route("/api/login", methods=["POST"])
def login():
    auth = request.get_json()

    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Missing credentials'}), 401

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username = ?', (auth.get('username'),))
    user = cursor.fetchone()
    conn.close()

    if not user or not bcrypt.checkpw(auth.get('password').encode('utf-8'),
                                     user[2].encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401

    # Generate token
    token = jwt.encode({
        'username': user[1],
        'exp': datetime.utcnow() + timedelta(days=1 if auth.get('remember', False) else 1)
    }, app.config['SECRET_KEY'])

    logging.info(f"Login successful for user: {user[1]}")

    response = make_response(jsonify({'message': 'Login successful'}))
    response.set_cookie('token', token,
                       httponly=True,
                       secure=False,  # Disabled for development
                       samesite=None,  # Disabled for development
                       max_age=86400 * (30 if auth.get('remember', False) else 1))  # 30 days or 1 day

    return response

@app.route("/api/logout")
def logout():
    response = make_response(redirect('/login'))
    response.delete_cookie('token')
    return response

@app.route("/")
def index():
    return redirect('/login')

@app.route("/login")
def login_page():
    return send_from_directory(app.static_folder, 'login.html')

@app.route("/dashboard")
@token_required
def dashboard():
    return send_from_directory(app.static_folder, 'dashboard.html')

@app.route("/api/logs", methods=["POST"])
def receive_logs():
    client_ip = request.remote_addr
    data = request.get_json()

    if not data:
        logging.warning("Received empty or invalid JSON data")
        return jsonify({"error": "Invalid data"}), 400

    try:
        # Store system stats
        if "cpu" in data and "memory" in data:
            insert_log("system_stats",
                      ["ip", "cpu", "memory"],
                      [client_ip, data["cpu"], data["memory"]])

        # Store new processes
        if "new_processes" in data:
            for process in data["new_processes"]:
                insert_log("new_processes",
                          ["ip", "pid", "name", "user"],
                          [client_ip, process["pid"], process["name"], process["user"]])

        # Store privileged processes
        if "privileged_processes" in data:
            for process in data["privileged_processes"]:
                insert_log("privileged_processes",
                          ["ip", "pid", "name", "user"],
                          [client_ip, process["pid"], process["name"], process["user"]])

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logging.error(f"Error storing logs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/system_stats", methods=["GET"])
@token_required
def get_system_stats():
    start = request.args.get("start")
    end = request.args.get("end")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if start and end:
        query = """
            SELECT timestamp, ip, cpu, memory
            FROM system_stats
            WHERE datetime(timestamp) BETWEEN datetime(?) AND datetime(?)
            ORDER BY timestamp DESC
        """
        cursor.execute(query, (start, end))
    else:
        query = """
            SELECT timestamp, ip, cpu, memory
            FROM system_stats
            ORDER BY timestamp DESC
        """
        cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()

    return jsonify([{
        "timestamp": row[0],
        "ip": row[1],
        "cpu": row[2],
        "memory": row[3]
    } for row in rows])

@app.route("/api/new_processes", methods=["GET"])
@token_required
def get_new_processes():
    start = request.args.get("start")
    end = request.args.get("end")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if start and end:
        query = """
            SELECT timestamp, ip, pid, name, user
            FROM new_processes
            WHERE datetime(timestamp) BETWEEN datetime(?) AND datetime(?)
            ORDER BY timestamp DESC
        """
        cursor.execute(query, (start, end))
    else:
        query = """
            SELECT timestamp, ip, pid, name, user
            FROM new_processes
            ORDER BY timestamp DESC
        """
        cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()

    return jsonify([{
        "timestamp": row[0],
        "ip": row[1],
        "pid": row[2],
        "name": row[3],
        "user": row[4]
    } for row in rows])

@app.route("/api/privileged_processes", methods=["GET"])
@token_required
def get_privileged_processes():
    start = request.args.get("start")
    end = request.args.get("end")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if start and end:
        query = """
            SELECT timestamp, ip, pid, name, user
            FROM privileged_processes
            WHERE datetime(timestamp) BETWEEN datetime(?) AND datetime(?)
            ORDER BY timestamp DESC
        """
        cursor.execute(query, (start, end))
    else:
        query = """
            SELECT timestamp, ip, pid, name, user
            FROM privileged_processes
            ORDER BY timestamp DESC
        """
        cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()

    return jsonify([{
        "timestamp": row[0],
        "ip": row[1],
        "pid": row[2],
        "name": row[3],
        "user": row[4]
    } for row in rows])

if __name__ == "__main__":
    init_db()  # Ensure DB tables exist on startup
    app.run(host="0.0.0.0", port=5000, debug=True)