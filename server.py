from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import logging
from datetime import datetime
import os
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)

# Database path
DB_PATH = "logs.db"

# Ensure static directory exists
os.makedirs('static', exist_ok=True)

# Ensure tables exist
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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

@app.route("/")
def dashboard():
    return send_from_directory(app.static_folder, 'dashboard.html')

if __name__ == "__main__":
    init_db()  # Ensure DB tables exist on startup
    app.run(host="0.0.0.0", port=5000, debug=True)