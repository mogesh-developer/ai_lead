import pymysql
from pymysql import Error
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        connection = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'ai_lead_outreach'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    """Initializes the database tables if they don't exist."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Create leads table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company VARCHAR(255),
            website VARCHAR(255),
            email VARCHAR(255) UNIQUE,
            phone VARCHAR(50),
            confidence INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            location VARCHAR(255),
            trust_score INT DEFAULT 0,
            ai_analysis JSON,
            source VARCHAR(50) DEFAULT 'upload',
            notes TEXT,
            campaign_id INT,
            current_sequence_step INT DEFAULT 1,
            last_outreach_at TIMESTAMP NULL
        )
        """)

        # Add missing columns if table already exists
        columns_to_add = [
            ("company", "VARCHAR(255)"),
            ("website", "VARCHAR(255)"),
            ("email", "VARCHAR(255)"),
            ("phone", "VARCHAR(50)"),
            ("location", "VARCHAR(255)"),
            ("confidence", "INT DEFAULT 0"),
            ("notes", "TEXT"),
            ("ai_analysis", "JSON"),
            ("source", "VARCHAR(50) DEFAULT 'upload'"),
            ("campaign_id", "INT"),
            ("current_sequence_step", "INT DEFAULT 1"),
            ("last_outreach_at", "TIMESTAMP NULL")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                # Check if column exists first to avoid error noise
                cursor.execute(f"SHOW COLUMNS FROM leads LIKE '{col_name}'")
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
                    print(f"Added column {col_name} to leads table.")
            except Error as e:
                print(f"Error adding column {col_name}: {e}")
                pass 
        
        # Ensure status column can handle all our statuses
        try:
            cursor.execute("ALTER TABLE leads MODIFY COLUMN status VARCHAR(50) DEFAULT 'new'")
        except Error:
            pass
        
        # Outreach Logs Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS outreach_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT,
            type ENUM('email', 'whatsapp'),
            message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
        """)

        # Settings Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            key_name VARCHAR(50) UNIQUE,
            value VARCHAR(255)
        )
        """)
        
        # Insert default settings if not exist
        cursor.execute("INSERT IGNORE INTO settings (key_name, value) VALUES ('autopilot', 'false')")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully.")

def insert_lead(data):
    """Insert a lead into the database, returns (bool, message)"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
        
        cursor = conn.cursor()
        
        # Prepare fields and values
        mapping = {
            'company': ['company', 'company_name', 'business_name'],
            'website': ['website', 'official_website', 'url', 'site'],
            'email': ['email', 'email_address', 'contact_email'],
            'phone': ['phone', 'phone_number', 'contact', 'telephone'],
            'confidence': ['confidence', 'confidence_score'],
            'location': ['location', 'address', 'city', 'full_address', 'state', 'country'],
            'notes': ['notes', 'description', 'comments'],
            'ai_analysis': ['ai_analysis', 'analysis', 'summary'],
            'trust_score': ['trust_score', 'score'],
            'source': ['source', 'origin']
        }
        
        db_data = {}
        for db_col, input_keys in mapping.items():
            for key in input_keys:
                if data.get(key) is not None:
                    val = data[key]
                    if isinstance(val, str):
                        val = val.strip()
                        if val.lower() in ['none', 'null', 'n/a', 'unknown', '']:
                            continue
                    db_data[db_col] = val
                    break
        
        if not db_data.get('email'):
            return False, "Email is a required field"

        fields = list(db_data.keys())
        placeholders = ['%s'] * len(fields)
        values = list(db_data.values())

        # Ensure status is always set
        if 'status' not in fields:
            fields.append('status')
            placeholders.append('%s')
            values.append(data.get('status', 'new'))

        # Handle JSON data
        for i, col in enumerate(fields):
            if col == 'ai_analysis' and isinstance(values[i], (dict, list)):
                values[i] = json.dumps(values[i])
            elif col == 'confidence' and isinstance(values[i], str):
                score_map = {'High': 90, 'Medium': 60, 'Low': 30}
                values[i] = score_map.get(values[i], 0)

        sql = f"INSERT INTO leads ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        
        print(f"[INSERT-LEAD] SQL: {sql}")
        print(f"[INSERT-LEAD] Values: {tuple(values)}")

        cursor.execute(sql, tuple(values))
        conn.commit()
        
        lead_id = cursor.lastrowid
        print(f"[INSERT-LEAD] OK: Committed lead ID {lead_id} for {db_data.get('email')}")
        cursor.close()
        return True, f"Lead added with ID {lead_id}"
        
    except mysql.connector.IntegrityError as e:
        if e.errno == 1062: # Duplicate entry
            error_msg = f"Duplicate entry for email '{db_data.get('email')}'"
        else:
            error_msg = f"Database integrity error: {e}"
        
        print(f"[INSERT-LEAD] ERROR: {error_msg}")
        if conn: conn.rollback()
        return False, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        print(f"[INSERT-LEAD] ERROR: {error_msg}")
        if conn: conn.rollback()
        return False, error_msg
    finally:
        if conn:
            conn.close()

def get_setting(key):
    conn = get_db_connection()
    val = None
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key_name = %s", (key,))
        result = cursor.fetchone()
        if result:
            val = result[0]
        cursor.close()
        conn.close()
    return val

def update_setting(key, value):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO settings (key_name, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value = %s", (key, value, value))
        conn.commit()
        cursor.close()
        conn.close()

def get_pending_leads():
    """Get leads that need analysis or outreach based on status"""
    conn = get_db_connection()
    leads = []
    if conn:
        cursor = conn.cursor()
        # Get 'new' leads for analysis OR 'analyzed' leads with high score for outreach
        cursor.execute("SELECT * FROM leads WHERE status = 'new' OR (status = 'analyzed' AND trust_score > 60)")
        leads = cursor.fetchall()
        cursor.close()
        conn.close()
    return leads


def get_all_leads():
    conn = get_db_connection()
    leads = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
        leads = cursor.fetchall()
        for lead in leads:
            if lead.get('ai_analysis'):
                lead['ai_analysis'] = json.loads(lead['ai_analysis'])
        cursor.close()
        conn.close()
    return leads

def get_lead_by_id(lead_id):
    conn = get_db_connection()
    lead = None
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))
        lead = cursor.fetchone()
        if lead and lead.get('ai_analysis'):
            lead['ai_analysis'] = json.loads(lead['ai_analysis'])
        cursor.close()
        conn.close()
    return lead

def get_lead_by_email(email):
    conn = get_db_connection()
    lead = None
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE email = %s", (email,))
        lead = cursor.fetchone()
        cursor.close()
        conn.close()
    return lead

def update_lead_notes(lead_id, notes):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "UPDATE leads SET notes = %s WHERE id = %s"
        cursor.execute(sql, (notes, lead_id))
        conn.commit()
        cursor.close()
        conn.close()

def update_lead_analysis(lead_id, analysis_json, trust_score, status):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "UPDATE leads SET ai_analysis = %s, trust_score = %s, status = %s WHERE id = %s"
        cursor.execute(sql, (analysis_json, trust_score, status, lead_id))
        conn.commit()
        cursor.close()
        conn.close()

def log_outreach(lead_id, outreach_type, message):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO outreach_logs (lead_id, type, message) VALUES (%s, %s, %s)"
        cursor.execute(sql, (lead_id, outreach_type, message))
        
        # Update lead status
        update_sql = "UPDATE leads SET status = 'outreach_sent' WHERE id = %s"
        cursor.execute(update_sql, (lead_id,))
        
        conn.commit()
        cursor.close()
        conn.close()

def get_dashboard_stats():
    conn = get_db_connection()
    stats = {'total': 0, 'analyzed': 0, 'outreach_sent': 0, 'converted': 0}
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
        results = cursor.fetchall()
        for status, count in results:
            if status in stats:
                stats[status] = count
            stats['total'] += count
        cursor.close()
        conn.close()
    return stats
