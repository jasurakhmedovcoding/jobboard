import sqlite3
import os

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

class DB:
    def __init__(self):
        if DATABASE_URL:
            self.conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
            self.is_postgres = True
        else:
            self.conn = sqlite3.connect('jobboard.db')
            self.conn.row_factory = sqlite3.Row
            self.is_postgres = False
        self.cur = self.conn.cursor()

    def execute(self, sql, params=()):
        if self.is_postgres:
            sql = sql.replace('?', '%s')
        self.cur.execute(sql, params)
        return self.cur

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_db():
    return DB()

def init_db():
    db = get_db()

    if db.is_postgres:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'jobseeker',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                salary TEXT,
                category TEXT,
                description TEXT NOT NULL,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id SERIAL PRIMARY KEY,
                job_id INTEGER NOT NULL REFERENCES jobs(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                cover_letter TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'jobseeker',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                salary TEXT,
                category TEXT,
                description TEXT NOT NULL,
                posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                cover_letter TEXT,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

    db.commit()
    db.close()
    print("Database ready!")