import mysql.connector
from mysql.connector import Error
import os
import json
from dotenv import load_dotenv

load_dotenv()
# Also check parent directory for .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

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
        
        # Add name column if it doesn't exist (critical for many functions)
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN name VARCHAR(255) AFTER id")
        except Error:
            pass  # Column might already exist

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
            
        # Add status column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN status VARCHAR(20) DEFAULT 'new'")
        except Error:
            pass  # Column might already exist

        # Add tracking columns
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN opened BOOLEAN DEFAULT FALSE")
            cursor.execute("ALTER TABLE leads ADD COLUMN opened_at TIMESTAMP NULL")
        except Error:
            pass
            
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN replied BOOLEAN DEFAULT FALSE")
            cursor.execute("ALTER TABLE leads ADD COLUMN replied_at TIMESTAMP NULL")
            cursor.execute("ALTER TABLE leads ADD COLUMN reply_subject VARCHAR(255)")
            cursor.execute("ALTER TABLE leads ADD COLUMN reply_body TEXT")
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
        
        # Campaigns Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Conversations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT NOT NULL,
            title VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
        )
        """)

        # Conversation messages
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            conversation_id INT NOT NULL,
            sender VARCHAR(100),
            direction ENUM('outbound','inbound') DEFAULT 'outbound',
            message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
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

        # Lead Tags Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_tags (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            color VARCHAR(7) DEFAULT '#3B82F6',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Lead-Tag Relationship Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_tag_relations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT NOT NULL,
            tag_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES lead_tags(id) ON DELETE CASCADE,
            UNIQUE KEY unique_lead_tag (lead_id, tag_id)
        )
        """)

        # Lead Segments Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_segments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            criteria JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Lead Scores Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_scores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT NOT NULL,
            score_type ENUM('ai_business', 'engagement', 'demographic', 'overall') DEFAULT 'overall',
            score INT NOT NULL,
            reasoning TEXT,
            scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
        )
        """)

        # Lead Enrichment Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_enrichment (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT NOT NULL,
            data_type ENUM('social_media', 'company_info', 'contact_details', 'financial_data') NOT NULL,
            data JSON,
            source VARCHAR(255),
            confidence_score INT DEFAULT 0,
            enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
        )
        """)

        # Email Tracking Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_tracking (
            id INT AUTO_INCREMENT PRIMARY KEY,
            outreach_log_id INT,
            event_type ENUM('sent', 'delivered', 'opened', 'clicked', 'bounced', 'complained') NOT NULL,
            event_data JSON,
            occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (outreach_log_id) REFERENCES outreach_logs(id) ON DELETE CASCADE
        )
        """)

        # Lead Sources Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_sources (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            source_type ENUM('web_search', 'justdial', 'manual', 'import', 'api', 'referral') DEFAULT 'manual',
            source_details JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Add source_id to leads if it doesn't exist
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN source_id INT")
            cursor.execute("ALTER TABLE leads ADD FOREIGN KEY (source_id) REFERENCES lead_sources(id)")
        except Error:
            pass

        # A/B Tests Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_tests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            test_type ENUM('subject_line', 'email_body', 'send_time') DEFAULT 'subject_line',
            variant_a JSON,
            variant_b JSON,
            winner VARCHAR(10),
            test_duration_days INT DEFAULT 7,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL
        )
        """)

        # CRM Integrations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_integrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            crm_type ENUM('hubspot', 'salesforce', 'pipedrive', 'zoho', 'custom') NOT NULL,
            name VARCHAR(255) NOT NULL,
            config JSON,
            is_active BOOLEAN DEFAULT FALSE,
            last_sync TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Lead Validation Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_validation (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT NOT NULL,
            validation_type ENUM('email', 'phone', 'domain') NOT NULL,
            is_valid BOOLEAN,
            validation_details JSON,
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
        )
        """)

        # Reminders Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT NULL,
            message TEXT NOT NULL,
            remind_at TIMESTAMP NOT NULL,
            recurrence ENUM('none','daily','weekly','monthly') DEFAULT 'none',
            metadata JSON NULL,
            sent BOOLEAN DEFAULT FALSE,
            sent_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL
        )
        """)

        # Notifications Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            notif_type VARCHAR(50),
            payload JSON,
            is_read BOOLEAN DEFAULT FALSE,
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
        sql = """INSERT INTO leads (name, email, website, phone, company, location, status, trust_score, source, campaign_id) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        val = (data.get('name'), data.get('email'), data.get('website'), data.get('phone'), data.get('company'), data.get('location'), data.get('status', 'new'), data.get('trust_score', 0), data.get('source', 'upload'), data.get('campaign_id'))
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

# Conversations helpers

def create_conversation_for_lead(lead_id, title=None):
    conn = get_db_connection()
    conv_id = None
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (lead_id, title) VALUES (%s, %s)", (lead_id, title))
        conn.commit()
        conv_id = cursor.lastrowid
        cursor.close()
        conn.close()
    return conv_id


def get_conversations_for_lead(lead_id):
    conn = get_db_connection()
    convs = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM conversations WHERE lead_id = %s ORDER BY created_at DESC", (lead_id,))
        convs = cursor.fetchall()
        cursor.close()
        conn.close()
    return convs


def add_conversation_message(conversation_id, sender, direction, message):
    conn = get_db_connection()
    msg_id = None
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversation_messages (conversation_id, sender, direction, message) VALUES (%s, %s, %s, %s)", (conversation_id, sender, direction, message))
        conn.commit()
        msg_id = cursor.lastrowid
        cursor.close()
        conn.close()
    return msg_id


def get_conversation_messages(conversation_id):
    conn = get_db_connection()
    msgs = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM conversation_messages WHERE conversation_id = %s ORDER BY sent_at ASC", (conversation_id,))
        msgs = cursor.fetchall()
        cursor.close()
        conn.close()
    return msgs

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

def update_lead_status(lead_id, status):
    """Backwards-compatible helper to update a lead's status."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "UPDATE leads SET status = %s WHERE id = %s"
        cursor.execute(sql, (status, lead_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False

def log_outreach(lead_id, outreach_type, message, update_status=True):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO outreach_logs (lead_id, type, message) VALUES (%s, %s, %s)"
        cursor.execute(sql, (lead_id, outreach_type, message))
        
        # Update lead status and last_outreach_at
        if update_status:
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
    stats = {
        'total': 0, 
        'analyzed': 0, 
        'outreach_sent': 0, 
        'converted': 0,
        'opened': 0,
        'replied': 0,
        'bounced': 0
    }
    if conn:
        cursor = conn.cursor()
        
        # Generic status counts
        cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
        results = cursor.fetchall()
        total = 0
        for status, count in results:
            if status in stats:
                stats[status] = count
            total += count
        stats['total'] = total

        # Tracked behavior counts
        cursor.execute("SELECT SUM(opened), SUM(replied) FROM leads")
        row = cursor.fetchone()
        if row:
            stats['opened'] = int(row[0] or 0)
            stats['replied'] = int(row[1] or 0)
            
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

def mark_lead_opened(lead_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE leads SET opened = TRUE, opened_at = NOW() WHERE id = %s", (lead_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False

def mark_lead_replied(lead_id, subject, body):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE leads SET replied = TRUE, replied_at = NOW(), status = 'replied', reply_subject = %s, reply_body = %s WHERE id = %s", (subject, body, lead_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False

def get_follow_up_candidates(days=2):
    """Get leads that were contacted X days ago and haven't replied yet."""
    conn = get_db_connection()
    leads = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM leads 
            WHERE status IN ('outreach_sent', 'followup_sent')
            AND replied = FALSE 
            AND last_outreach_at <= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY last_outreach_at ASC
        """
        cursor.execute(query, (days,))
        leads = cursor.fetchall()
        cursor.close()
        conn.close()
    return leads

def get_auto_follow_up_candidates(days=2, max_step=3):
    """Get leads for automatic follow-up sequence."""
    conn = get_db_connection()
    leads = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM leads 
            WHERE status IN ('outreach_sent', 'followup_sent')
            AND replied = FALSE 
            AND current_sequence_step < %s
            AND last_outreach_at <= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        cursor.execute(query, (max_step, days))
        leads = cursor.fetchall()
        cursor.close()
        conn.close()
    return leads

def get_replied_leads(limit=100):
    conn = get_db_connection()
    leads = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM leads WHERE replied = TRUE ORDER BY replied_at DESC LIMIT %s", (limit,))
        leads = cursor.fetchall()
        cursor.close()
        conn.close()
    return leads

# ===== NEW ENHANCED FEATURES FUNCTIONS =====

# Lead Tagging Functions
def create_lead_tag(name, color='#3B82F6'):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO lead_tags (name, color) VALUES (%s, %s)"
        cursor.execute(sql, (name, color))
        tag_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return tag_id
    return None

def get_lead_tags():
    conn = get_db_connection()
    tags = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lead_tags ORDER BY name")
        tags = cursor.fetchall()
        cursor.close()
        conn.close()
    return tags

def add_tag_to_lead(lead_id, tag_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT IGNORE INTO lead_tag_relations (lead_id, tag_id) VALUES (%s, %s)"
        cursor.execute(sql, (lead_id, tag_id))
        conn.commit()
        cursor.close()
        conn.close()

def remove_tag_from_lead(lead_id, tag_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "DELETE FROM lead_tag_relations WHERE lead_id = %s AND tag_id = %s"
        cursor.execute(sql, (lead_id, tag_id))
        conn.commit()
        cursor.close()
        conn.close()

def get_lead_tags_by_lead_id(lead_id):
    conn = get_db_connection()
    tags = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        sql = """
        SELECT t.* FROM lead_tags t
        JOIN lead_tag_relations r ON t.id = r.tag_id
        WHERE r.lead_id = %s
        ORDER BY t.name
        """
        cursor.execute(sql, (lead_id,))
        tags = cursor.fetchall()
        cursor.close()
        conn.close()
    return tags

# Lead Scoring Functions
def save_lead_score(lead_id, score_type, score, reasoning=""):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = """
        INSERT INTO lead_scores (lead_id, score_type, score, reasoning)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE score = VALUES(score), reasoning = VALUES(reasoning), scored_at = CURRENT_TIMESTAMP
        """
        cursor.execute(sql, (lead_id, score_type, score, reasoning))
        conn.commit()
        cursor.close()
        conn.close()

def get_lead_scores(lead_id):
    conn = get_db_connection()
    scores = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lead_scores WHERE lead_id = %s ORDER BY scored_at DESC", (lead_id,))
        scores = cursor.fetchall()
        cursor.close()
        conn.close()
    return scores

def get_overall_lead_score(lead_id):
    scores = get_lead_scores(lead_id)
    if not scores:
        return 0
    
    # Calculate weighted average
    weights = {'ai_business': 0.4, 'engagement': 0.3, 'demographic': 0.2, 'overall': 0.1}
    total_score = 0
    total_weight = 0
    
    for score in scores[-3:]:  # Use last 3 scores
        weight = weights.get(score['score_type'], 0.1)
        total_score += score['score'] * weight
        total_weight += weight
    
    return round(total_score / total_weight) if total_weight > 0 else 0

# Lead Enrichment Functions
def save_lead_enrichment(lead_id, data_type, data, source="", confidence_score=0):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = """
        INSERT INTO lead_enrichment (lead_id, data_type, data, source, confidence_score)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (lead_id, data_type, json.dumps(data), source, confidence_score))
        enrichment_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return enrichment_id
    return None

def get_lead_enrichment(lead_id):
    conn = get_db_connection()
    enrichment = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lead_enrichment WHERE lead_id = %s ORDER BY enriched_at DESC", (lead_id,))
        enrichment = cursor.fetchall()
        # Parse JSON data
        for item in enrichment:
            if item['data']:
                item['data'] = json.loads(item['data'])
        cursor.close()
        conn.close()
    return enrichment

# Email Tracking Functions
def track_email_event(outreach_log_id, event_type, event_data=None):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO email_tracking (outreach_log_id, event_type, event_data) VALUES (%s, %s, %s)"
        cursor.execute(sql, (outreach_log_id, event_type, json.dumps(event_data) if event_data else None))
        conn.commit()
        cursor.close()
        conn.close()

def get_email_tracking_stats(outreach_log_id=None):
    conn = get_db_connection()
    stats = {}
    if conn:
        cursor = conn.cursor(dictionary=True)
        if outreach_log_id:
            cursor.execute("SELECT event_type, COUNT(*) as count FROM email_tracking WHERE outreach_log_id = %s GROUP BY event_type", (outreach_log_id,))
        else:
            cursor.execute("SELECT event_type, COUNT(*) as count FROM email_tracking GROUP BY event_type")
        results = cursor.fetchall()
        for result in results:
            stats[result['event_type']] = result['count']
        cursor.close()
        conn.close()
    return stats

# Lead Source Functions
def create_lead_source(name, source_type='manual', source_details=None):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO lead_sources (name, source_type, source_details) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, source_type, json.dumps(source_details) if source_details else None))
        source_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return source_id
    return None

def get_lead_sources():
    conn = get_db_connection()
    sources = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lead_sources ORDER BY created_at DESC")
        sources = cursor.fetchall()
        # Parse JSON details
        for source in sources:
            if source['source_details']:
                source['source_details'] = json.loads(source['source_details'])
        cursor.close()
        conn.close()
    return sources

# A/B Testing Functions
def create_ab_test(name, test_type, variant_a, variant_b, test_duration_days=7):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = """
        INSERT INTO ab_tests (name, test_type, variant_a, variant_b, test_duration_days)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (name, test_type, json.dumps(variant_a), json.dumps(variant_b), test_duration_days))
        test_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return test_id
    return None

def get_ab_tests():
    conn = get_db_connection()
    tests = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ab_tests ORDER BY created_at DESC")
        tests = cursor.fetchall()
        # Parse JSON variants
        for test in tests:
            if test['variant_a']:
                test['variant_a'] = json.loads(test['variant_a'])
            if test['variant_b']:
                test['variant_b'] = json.loads(test['variant_b'])
        cursor.close()
        conn.close()
    return tests

# CRM Integration Functions
def save_crm_integration(crm_type, name, config, is_active=False):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = """
        INSERT INTO crm_integrations (crm_type, name, config, is_active)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (crm_type, name, json.dumps(config), is_active))
        integration_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return integration_id
    return None

def get_crm_integrations():
    conn = get_db_connection()
    integrations = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM crm_integrations ORDER BY created_at DESC")
        integrations = cursor.fetchall()
        # Parse JSON config
        for integration in integrations:
            if integration['config']:
                integration['config'] = json.loads(integration['config'])
        cursor.close()
        conn.close()
    return integrations

# Lead Validation Functions
def save_lead_validation(lead_id, validation_type, is_valid, validation_details=None):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = """
        INSERT INTO lead_validation (lead_id, validation_type, is_valid, validation_details)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (lead_id, validation_type, is_valid, json.dumps(validation_details) if validation_details else None))
        validation_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return validation_id
    return None

def get_lead_validation(lead_id):
    conn = get_db_connection()
    validations = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lead_validation WHERE lead_id = %s ORDER BY validated_at DESC", (lead_id,))
        validations = cursor.fetchall()
        # Parse JSON details
        for validation in validations:
            if validation['validation_details']:
                validation['validation_details'] = json.loads(validation['validation_details'])
        cursor.close()
        conn.close()
    return validations

# Reminders & Notifications

def create_reminder(lead_id, remind_at, message, recurrence='none', metadata=None):
    conn = get_db_connection()
    reminder_id = None
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO reminders (lead_id, remind_at, message, recurrence, metadata) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (lead_id, remind_at, message, recurrence, json.dumps(metadata) if metadata else None))
        reminder_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
    return reminder_id


def get_reminders(limit=200):
    conn = get_db_connection()
    reminders = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM reminders ORDER BY remind_at ASC LIMIT %s", (limit,))
        reminders = cursor.fetchall()
        # Parse JSON metadata
        for r in reminders:
            if r.get('metadata'):
                r['metadata'] = json.loads(r['metadata'])
        cursor.close()
        conn.close()
    return reminders


def get_reminders_for_lead(lead_id):
    conn = get_db_connection()
    reminders = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM reminders WHERE lead_id = %s ORDER BY remind_at ASC", (lead_id,))
        reminders = cursor.fetchall()
        for r in reminders:
            if r.get('metadata'):
                r['metadata'] = json.loads(r['metadata'])
        cursor.close()
        conn.close()
    return reminders


def get_due_reminders(limit=100):
    conn = get_db_connection()
    reminders = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM reminders WHERE remind_at <= NOW() AND sent = FALSE ORDER BY remind_at ASC LIMIT %s", (limit,))
        reminders = cursor.fetchall()
        for r in reminders:
            if r.get('metadata'):
                r['metadata'] = json.loads(r['metadata'])
        cursor.close()
        conn.close()
    return reminders


def mark_reminder_sent(reminder_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE reminders SET sent = TRUE, sent_at = NOW() WHERE id = %s", (reminder_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False


def update_reminder_time(reminder_id, next_remind_at):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE reminders SET remind_at = %s, sent = FALSE, sent_at = NULL WHERE id = %s", (next_remind_at, reminder_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False


def delete_reminder(reminder_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = %s", (reminder_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False


def create_notification(notif_type, payload):
    conn = get_db_connection()
    notif_id = None
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO notifications (notif_type, payload) VALUES (%s, %s)"
        cursor.execute(sql, (notif_type, json.dumps(payload)))
        notif_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
    return notif_id


def get_notifications(unread_only=True, limit=200):
    conn = get_db_connection()
    notifs = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        if unread_only:
            cursor.execute("SELECT * FROM notifications WHERE is_read = FALSE ORDER BY created_at DESC LIMIT %s", (limit,))
        else:
            cursor.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT %s", (limit,))
        notifs = cursor.fetchall()
        for n in notifs:
            if n.get('payload'):
                n['payload'] = json.loads(n['payload'])
        cursor.close()
        conn.close()
    return notifs


def mark_notification_read(notification_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notification_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False

# Enhanced Analytics Functions
def get_enhanced_dashboard_stats():
    conn = get_db_connection()
    stats = {
        'total_leads': 0,
        'leads_by_source': {},
        'leads_by_tag': {},
        'average_score': 0,
        'email_performance': {},
        'conversion_rate': 0,
        'top_performing_campaigns': [],
        'lead_quality_distribution': {}
    }
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Total leads
        cursor.execute("SELECT COUNT(*) as count FROM leads")
        stats['total_leads'] = cursor.fetchone()['count']
        
        # Leads by source
        cursor.execute("""
        SELECT ls.name, COUNT(l.id) as count 
        FROM lead_sources ls 
        LEFT JOIN leads l ON ls.id = l.source_id 
        GROUP BY ls.id, ls.name
        """)
        for row in cursor.fetchall():
            stats['leads_by_source'][row['name']] = row['count']
        
        # Leads by tag
        cursor.execute("""
        SELECT t.name, COUNT(ltr.lead_id) as count 
        FROM lead_tags t 
        LEFT JOIN lead_tag_relations ltr ON t.id = ltr.tag_id 
        GROUP BY t.id, t.name
        """)
        for row in cursor.fetchall():
            stats['leads_by_tag'][row['name']] = row['count']
        
        # Average lead score
        cursor.execute("SELECT AVG(score) as avg_score FROM lead_scores WHERE score_type = 'overall'")
        result = cursor.fetchone()
        stats['average_score'] = round(result['avg_score'] or 0, 1)
        
        # Email performance
        cursor.execute("""
        SELECT event_type, COUNT(*) as count 
        FROM email_tracking 
        GROUP BY event_type
        """)
        for row in cursor.fetchall():
            stats['email_performance'][row['event_type']] = row['count']
        
        # Conversion rate (replied leads)
        cursor.execute("SELECT COUNT(*) as replied FROM leads WHERE replied = TRUE")
        replied = cursor.fetchone()['replied']
        stats['conversion_rate'] = round((replied / stats['total_leads']) * 100, 1) if stats['total_leads'] > 0 else 0
        
        cursor.close()
        conn.close()
    
    return stats
