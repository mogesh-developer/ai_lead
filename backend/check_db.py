import db
try:
    db.init_db()
    print("Database initialized successfully")
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DESCRIBE leads")
    rows = cursor.fetchall()
    print("--- TABLE STRUCTURE ---")
    for r in rows:
        print(f"{r[0]}: {r[1]}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
