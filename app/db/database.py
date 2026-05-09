import sqlite3
import os

DB_PATH = os.getenv("SQLITE_DB_PATH", "data/projects.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id    TEXT PRIMARY KEY,
            device_id     TEXT NOT NULL,
            device_name   TEXT NOT NULL,
            plan          TEXT,          -- JSON
            steps         TEXT,          -- JSON array
            current_step  INTEGER DEFAULT 0,
            history       TEXT,          -- JSON array
            flowchart     TEXT,
            step_videos   TEXT,          -- JSON array
            status        TEXT DEFAULT 'in_progress',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()