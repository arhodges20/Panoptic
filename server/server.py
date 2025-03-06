import sqlite3
import logging
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

DB_PATH = "logs.db"

# Ensure tables exist
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            ip TEXT,
            cpu REAL,
            memory REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS new_processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            ip TEXT,
            pid INTEGER,
            name TEXT,
            user TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS privileged_processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            ip TEXT,
            pid INTEGER,
            name TEXT,
            user TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()  # Ensure DB tables exist on startup

# Insert data into database
def insert_log(table, columns, values):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(values))})"
    cursor.execute(query, values)
    conn.commit()
    conn.close()

@app.route("/api/system_stats", methods=["GET"])
def get_system_stats():
    start = request.args.get("start")
    end = request.args.get("end")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT timestamp, ip, cpu, memory FROM system_stats WHERE timestamp BETWEEN ? AND ?"
    cursor.execute(query, (start, end))
    rows = cursor.fetchall()

    conn.close()

    return jsonify([{"timestamp": row[0], "ip": row[1], "cpu": row[2], "memory": row[3]} for row in rows])

@app.route("/api/new_processes", methods=["GET"])
def get_new_processes():
    start = request.args.get("start")
    end = request.args.get("end")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT timestamp, ip, pid, name, user FROM new_processes WHERE timestamp BETWEEN ? AND ?"
    cursor.execute(query, (start, end))
    rows = cursor.fetchall()

    conn.close()

    return jsonify([{"timestamp": row[0], "ip": row[1], "pid": row[2], "name": row[3], "user": row[4]} for row in rows])

@app.route("/api/privileged_processes", methods=["GET"])
def get_privileged_processes():
    start = request.args.get("start")
    end = request.args.get("end")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT timestamp, ip, pid, name, user FROM privileged_processes WHERE timestamp BETWEEN ? AND ?"
    cursor.execute(query, (start, end))
    rows = cursor.fetchall()

    conn.close()

    return jsonify([{"timestamp": row[0], "ip": row[1], "pid": row[2], "name": row[3], "user": row[4]} for row in rows])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)