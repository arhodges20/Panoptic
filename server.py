from flask import Flask, request, jsonify, send_from_directory, redirect, make_response, url_for
import sqlite3
import logging
from datetime import datetime, timedelta
import os
from flask_cors import CORS
import jwt
import bcrypt
from functools import wraps
from flask_session import Session

# Database path
DB_PATH = "logs.db"

def init_db():
    """Initialize the database and create tables"""
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

# Create Flask application
app = Flask(__name__, 
    static_folder='static',  # Set static folder
    static_url_path=''      # Empty string for serving from root
)

# Enable CORS
CORS(app, supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
Session(app)

# Ensure static directory exists
os.makedirs('static', exist_ok=True)

# Initialize database
try:
    init_db()
    logging.info("Database initialized successfully")
except Exception as e:
    logging.error(f"Error initializing database: {str(e)}")

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

        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401

        # Check for token in cookies if not in header
        if not token:
            token = request.cookies.get('token')

        if not token:
            logging.warning("No token found in request")
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

# Basic routes
@app.route('/')
def index():
    return redirect('/login')

@app.route('/login')
def login_page():
    return send_from_directory('static', 'login.html')

@app.route('/dashboard')
@token_required
def dashboard_page():
    try:
        logging.info("Attempting to serve dashboard.html")
        response = make_response(send_from_directory('static', 'dashboard.html'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logging.error(f"Error serving dashboard: {str(e)}")
        return jsonify({'message': 'Error loading dashboard'}), 500

# Serve static files
@app.route('/<path:filename>')
def serve_static(filename):
    try:
        if filename == 'dashboard.html':
            return redirect('/dashboard')
        logging.info(f"Attempting to serve static file: {filename}")
        return send_from_directory('static', filename)
    except Exception as e:
        logging.error(f"Error serving static file {filename}: {str(e)}")
        return jsonify({'message': 'File not found'}), 404

# API routes
@app.route("/api/login", methods=["POST"])
def login():
    try:
        auth = request.get_json()
        logging.info("Login attempt received")

        if not auth:
            logging.warning("No JSON data in login request")
            return jsonify({'message': 'Missing credentials - No JSON data'}), 401

        if not auth.get('username'):
            logging.warning("Missing username in login request")
            return jsonify({'message': 'Missing username'}), 401

        if not auth.get('password'):
            logging.warning("Missing password in login request")
            return jsonify({'message': 'Missing password'}), 401

        logging.info(f"Login attempt for username: {auth.get('username')}")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (auth.get('username'),))
        user = cursor.fetchone()
        conn.close()

        if not user:
            logging.warning(f"User not found: {auth.get('username')}")
            return jsonify({'message': 'Invalid credentials'}), 401

        if not bcrypt.checkpw(auth.get('password').encode('utf-8'),
                            user[2].encode('utf-8')):
            logging.warning(f"Invalid password for user: {auth.get('username')}")
            return jsonify({'message': 'Invalid credentials'}), 401

        # Generate token
        token = jwt.encode({
            'username': user[1],
            'exp': datetime.utcnow() + timedelta(days=1 if auth.get('remember', False) else 1)
        }, app.config['SECRET_KEY'])

        logging.info(f"Login successful for user: {user[1]}")

        response = make_response(jsonify({
            'message': 'Login successful',
            'token': token,
            'username': user[1]
        }))
        
        # Set cookie with token
        response.set_cookie(
            'token',
            token,
            httponly=True,
            secure=False,  # Set to True in production
            samesite=None,  # Set to 'Strict' in production
            max_age=86400 * (30 if auth.get('remember', False) else 1)
        )

        return response

    except sqlite3.Error as e:
        logging.error(f"Database error during login: {str(e)}")
        return jsonify({'message': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Unexpected error during login: {str(e)}")
        return jsonify({'message': 'An unexpected error occurred'}), 500

@app.route("/api/logout", methods=['GET', 'POST'])
@token_required
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}))
    response.delete_cookie('token')
    return response

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
    app.run(host="0.0.0.0", port=5000, debug=True)
