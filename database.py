import sqlite3

DB_PATH = "data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tracking
                 (user_id INTEGER, url TEXT, pincode TEXT, 
                  UNIQUE(user_id, url, pincode))''')
    conn.commit()
    conn.close()

def add_tracking(user_id, url, pincode):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO tracking VALUES (?, ?, ?)", (user_id, url, pincode))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def remove_tracking(user_id, url, pincode):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tracking WHERE user_id=? AND url=? AND pincode=?", (user_id, url, pincode))
    rows_deleted = c.rowcount
    conn.commit()
    conn.close()
    return rows_deleted > 0

def get_user_tracking(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT url, pincode FROM tracking WHERE user_id=?", (user_id,))
    items = c.fetchall()
    conn.close()
    return items

def get_all_tracking():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, url, pincode FROM tracking")
    items = c.fetchall()
    conn.close()
    return items
