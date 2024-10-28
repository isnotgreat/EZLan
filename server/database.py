import sqlite3
from threading import Lock

class Database:
    def __init__(self):
        self.lock = Lock()
        self.conn = sqlite3.connect('users.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    name TEXT PRIMARY KEY,
                    password_hash TEXT,
                    ip TEXT,
                    timestamp FLOAT
                )
            ''')
            self.conn.commit()

    def update_user(self, user_data):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (name, password_hash, ip, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                user_data['name'],
                user_data['password_hash'],
                user_data['ip'],
                user_data['timestamp']
            ))
            self.conn.commit()

    def get_active_users(self, cutoff_time):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT name, ip, timestamp FROM users
                WHERE timestamp > ?
            ''', (cutoff_time,))
            users = cursor.fetchall()
            return [
                {
                    'name': user[0],
                    'ip': user[1],
                    'timestamp': user[2]
                }
                for user in users
            ]
