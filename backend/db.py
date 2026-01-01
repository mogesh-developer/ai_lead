import mysql.connector
from mysql.connector import Error
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'ai_lead_outreach')
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    """Initializes the database tables if they don't exist."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Add notes column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN notes TEXT")
        except Error:
            pass  # Column might already exist
        
        # Add ai_analysis column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN ai_analysis JSON")
        except Error:
            pass  # Column might already exist
        
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
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = """INSERT INTO leads (name, email, phone, company, location, status, trust_score, source) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        val = (data.get('name'), data.get('email'), data.get('phone'), data.get('company'), data.get('location'), data.get('status', 'new'), data.get('trust_score', 0), data.get('source', 'upload'))
        cursor.execute(sql, val)
        conn.commit()
        cursor.close()
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
        cursor = conn.cursor(dictionary=True)
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
        cursor = conn.cursor(dictionary=True)
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
        cursor = conn.cursor(dictionary=True)
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
        cursor = conn.cursor(dictionary=True)
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
