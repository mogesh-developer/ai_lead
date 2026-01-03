import db
try:
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    # Clean up common "empty" strings
    empty_vals = ['None', 'null', 'N/A', 'unknown', '']
    
    for val in empty_vals:
        cursor.execute("UPDATE leads SET company = NULL WHERE company = %s", (val,))
        cursor.execute("UPDATE leads SET website = NULL WHERE website = %s", (val,))
        cursor.execute("UPDATE leads SET location = NULL WHERE location = %s", (val,))
    
    # Also fix the name column - if it's NULL, try to get it from company
    cursor.execute("UPDATE leads SET name = company WHERE name IS NULL AND company IS NOT NULL")
    
    conn.commit()
    print("Database cleanup complete.")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
