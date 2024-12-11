from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Database setup
DATABASE = 'stats.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu REAL,
            memory REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# API to receive stats from agents
@app.route('/stats', methods=['POST'])
def receive_stats():
    data = request.json
    if not data or 'cpu' not in data or 'memory' not in data:
        return {"error": "Invalid payload"}, 400
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO stats (cpu, memory) VALUES (?, ?)', (data['cpu'], data['memory']))
    conn.commit()
    conn.close()
    return {"message": "Stats received"}, 200

# API to retrieve the latest stats
@app.route('/stats', methods=['GET'])
def get_stats():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM stats ORDER BY timestamp DESC LIMIT 10')
    rows = c.fetchall()
    conn.close()
    stats = [{"id": row[0], "cpu": row[1], "memory": row[2], "timestamp": row[3]} for row in rows]
    return jsonify(stats)

if __name__ == '__main__':
    # Run the Flask server
    app.run(host='0.0.0.0', port=5000)
