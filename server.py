from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
CORS(app)

# Получаем URL базы данных из переменных окружения
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    # Render предоставляет DATABASE_URL в формате postgres://
    # но psycopg2 требует postgresql://
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        db_url = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    else:
        db_url = DATABASE_URL
    
    conn = psycopg2.connect(db_url)
    return conn

def init_db():
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS entries (
                        id SERIAL PRIMARY KEY,
                        date TEXT NOT NULL UNIQUE,
                        hours REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")

@app.route('/')
def index():
    return send_from_directory('.', 'work-hours-tracker-db.html')

@app.route('/api/entries', methods=['GET'])
def get_entries():
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT date, hours FROM entries ORDER BY date DESC')
                entries = cursor.fetchall()
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
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO entries (date, hours) 
                    VALUES (%s, %s)
                    ON CONFLICT (date) DO UPDATE SET hours = %s
                ''', (date, hours, hours))
                conn.commit()
        
        return jsonify({'success': True, 'date': date, 'hours': hours})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<date>', methods=['DELETE'])
def delete_entry(date):
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute('DELETE FROM entries WHERE date = %s', (date,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    print("📊 База данных: PostgreSQL")
    app.run(debug=False, host='0.0.0.0', port=port)
