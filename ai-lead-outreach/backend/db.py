import mysql.connector
from mysql.connector import Error
import os
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
        
        # Add analysis columns if they don't exist
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN ai_analysis TEXT")
        except Error:
            pass  # Column might already exist
            
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN trust_score INT DEFAULT 0")
        except Error:
            pass  # Column might already exist
            
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN status VARCHAR(20) DEFAULT 'pending'")
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
        
        # Campaigns Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Add campaign_id to leads if it doesn't exist
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN campaign_id INT")
            cursor.execute("ALTER TABLE leads ADD FOREIGN KEY (campaign_id) REFERENCES campaigns(id)")
        except Error:
            pass  # Column might already exist

        # Add sequence tracking columns to leads
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN current_sequence_step INT DEFAULT 0")
        except Error:
            pass
            
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN last_outreach_at TIMESTAMP NULL")
        except Error:
            pass

        # Campaign Sequences Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_sequences (
            id INT AUTO_INCREMENT PRIMARY KEY,
            campaign_id INT,
            day_offset INT,
            template_subject VARCHAR(255),
            template_body TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
        """)

        # Email Templates Table (Global)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_templates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            subject VARCHAR(255),
            body TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Email Templates Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_templates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            subject VARCHAR(255),
            body TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully.")

def add_template(name, subject, body):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO email_templates (name, subject, body) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, subject, body))
        conn.commit()
        cursor.close()
        conn.close()

def get_templates():
    conn = get_db_connection()
    templates = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM email_templates ORDER BY created_at DESC")
        templates = cursor.fetchall()
        cursor.close()
        conn.close()
    return templates

def delete_template(template_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_templates WHERE id = %s", (template_id,))
        conn.commit()
        cursor.close()
        conn.close()

def add_campaign_sequence(campaign_id, day_offset, subject, body):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO campaign_sequences (campaign_id, day_offset, template_subject, template_body) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (campaign_id, day_offset, subject, body))
        conn.commit()
        cursor.close()
        conn.close()

def get_campaign_sequences(campaign_id):
    conn = get_db_connection()
    sequences = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM campaign_sequences WHERE campaign_id = %s ORDER BY day_offset ASC", (campaign_id,))
        sequences = cursor.fetchall()
        cursor.close()
        conn.close()
    return sequences

def create_campaign(name, description):
    conn = get_db_connection()
    campaign_id = None
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO campaigns (name, description) VALUES (%s, %s)"
        cursor.execute(sql, (name, description))
        conn.commit()
        campaign_id = cursor.lastrowid
        cursor.close()
        conn.close()
    return campaign_id

def get_campaigns():
    conn = get_db_connection()
    campaigns = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM campaigns ORDER BY created_at DESC")
        campaigns = cursor.fetchall()
        cursor.close()
        conn.close()
    return campaigns

def insert_lead(data):
    conn = get_db_connection()
    lead_id = None
    if conn:
        cursor = conn.cursor()
        sql = """INSERT INTO leads (name, email, phone, company, location, status, trust_score, source, campaign_id) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        val = (data.get('name'), data.get('email'), data.get('phone'), data.get('company'), data.get('location'), data.get('status', 'new'), data.get('trust_score', 0), data.get('source', 'upload'), data.get('campaign_id'))
        cursor.execute(sql, val)
        conn.commit()
        lead_id = cursor.lastrowid
        cursor.close()
        conn.close()
    return lead_id

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
        # Also get leads that might need follow-up (status='outreach_sent')
        cursor.execute("SELECT * FROM leads WHERE status = 'new' OR (status = 'analyzed' AND trust_score > 60) OR (status = 'outreach_sent' AND campaign_id IS NOT NULL)")
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
        
        # Update lead status and last_outreach_at
        update_sql = "UPDATE leads SET status = 'outreach_sent', last_outreach_at = NOW() WHERE id = %s"
        cursor.execute(update_sql, (lead_id,))
        
        conn.commit()
        cursor.close()
        conn.close()

def update_lead_sequence_step(lead_id, step):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "UPDATE leads SET current_sequence_step = %s WHERE id = %s"
        cursor.execute(sql, (step, lead_id))
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

def add_template(name, subject, body):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO email_templates (name, subject, body) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, subject, body))
        conn.commit()
        cursor.close()
        conn.close()

def get_templates():
    conn = get_db_connection()
    templates = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM email_templates ORDER BY created_at DESC")
        templates = cursor.fetchall()
        cursor.close()
        conn.close()
    return templates

def get_template_by_id(template_id):
    conn = get_db_connection()
    template = None
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM email_templates WHERE id = %s", (template_id,))
        template = cursor.fetchone()
        cursor.close()
        conn.close()
    return template

def delete_template(template_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_templates WHERE id = %s", (template_id,))
        conn.commit()
        cursor.close()
        conn.close()
