import sqlite3
import logging

DB_FILE = "tracking.db"

def init_db():
    """Database aur table create karega agar nahi bani hai toh."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pickup_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                pincode TEXT NOT NULL,
                UNIQUE(user_id, url, pincode)
            )
        ''')
    logging.info("Database initialized.")

def add_tracking(user_id: int, url: str, pincode: str) -> bool:
    """Naya URL aur Pincode save karega."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT INTO pickup_tracking (user_id, url, pincode) VALUES (?, ?, ?)", 
                (user_id, url, pincode)
            )
        return True
    except sqlite3.IntegrityError:
        return False # Agar same user ne same URL aur Pincode already add kiya hua hai

def remove_tracking(user_id: int, url: str, pincode: str) -> bool:
    """Tracked item ko database se delete karega."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute(
            "DELETE FROM pickup_tracking WHERE user_id = ? AND url = ? AND pincode = ?", 
            (user_id, url, pincode)
        )
        return cursor.rowcount > 0 # True if deleted, False if not found

def get_user_tracking(user_id: int):
    """User ki saari tracking list return karega."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT url, pincode FROM pickup_tracking WHERE user_id = ?", (user_id,))
        return cursor.fetchall()
