import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'ai_lead_outreach')
)
cursor = conn.cursor()
cursor.execute("ALTER TABLE leads ADD COLUMN source VARCHAR(50) DEFAULT 'upload'")
conn.commit()
cursor.close()
conn.close()
print('Source column added successfully')