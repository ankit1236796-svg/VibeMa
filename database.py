import sqlite3
import logging

logger = logging.getLogger(__name__)
DB_FILE = "pickup_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            url TEXT,
            pincode TEXT,
            UNIQUE(user_id, url, pincode)
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

def add_tracking(user_id: int, url: str, pincode: str) -> bool:
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tracking (user_id, url, pincode) VALUES (?, ?, ?)", (user_id, url, pincode))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False # Already exists

def get_all_combos() -> list:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, url, pincode FROM tracking")
    rows = cursor.fetchall()
    conn.close()
    return [{"user_id": r[0], "url": r[1], "pincode": r[2]} for r in rows]

