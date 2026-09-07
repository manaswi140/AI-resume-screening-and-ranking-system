import sqlite3

DB_NAME = "users.db"

def init_db():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            """)
            conn.commit()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rank_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resume_name TEXT NOT NULL,
                score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM rank_history;")
        rows = cur.fetchall()
        for r in rows:
            print(dict(r))
        conn.close()

        print("✅ Database initialized successfully!")

    except sqlite3.Error as e:
        print(f"❌ Database initialization failed: {e}")

if __name__ == "__main__":
    init_db()
