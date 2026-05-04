import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "forensics.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Table for Windows Event Log records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT,
            timestamp TEXT,
            source TEXT,
            computer TEXT,
            message TEXT,
            level TEXT,
            file_source TEXT
        )
    """)

    # Table for Registry entries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registry_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hive TEXT,
            key_path TEXT,
            value_name TEXT,
            value_data TEXT,
            value_type TEXT,
            file_source TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at: {DB_PATH}")

def clear_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events")
    cursor.execute("DELETE FROM registry_entries")
    conn.commit()
    conn.close()
    print("[DB] Database cleared.")

if __name__ == "__main__":
    init_db()