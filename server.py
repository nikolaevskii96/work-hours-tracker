from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DATABASE = 'work_hours.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                hours REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

@app.route('/')
def index():
    return send_from_directory('.', 'work-hours-tracker-db.html')

@app.route('/api/entries', methods=['GET'])
def get_entries():
    try:
        with get_db() as conn:
            cursor = conn.execute('SELECT date, hours FROM entries ORDER BY date DESC')
            entries = [dict(row) for row in cursor.fetchall()]
        return jsonify(entries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries', methods=['POST'])
def add_entry():
    try:
        data = request.json
        date = data.get('date')
        hours = data.get('hours')
        
        if not date or hours is None:
            return jsonify({'error': 'Требуются поля date и hours'}), 400
        
        with get_db() as conn:
            conn.execute('''
                INSERT INTO entries (date, hours) 
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET hours = ?
            ''', (date, hours, hours))
            conn.commit()
        
        return jsonify({'success': True, 'date': date, 'hours': hours})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<date>', methods=['DELETE'])
def delete_entry(date):
    try:
        with get_db() as conn:
            conn.execute('DELETE FROM entries WHERE date = ?', (date,))
            conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    print("📊 База данных: work_hours.db")
    app.run(debug=False, host='0.0.0.0', port=port)
