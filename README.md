# AI Lead Outreach Agent

A full-fledged AI-powered autonomous lead outreach SaaS application built with Python Flask and React.

## 🚀 Features

- **Lead Ingestion**: Upload CSV/Excel files with lead data.
- **AI Discovery**: Real-time web search using DuckDuckGo to find leads by industry and location.
- **Advanced Web Scraping**: Playwright-powered scraping that can handle JavaScript-heavy websites.
- **AI Analysis**: Uses Gemini 1.5 Flash to analyze business trust and maturity.
- **Autonomous Mode**: Background scheduler that automatically processes leads without manual intervention.
- **Thanglish Outreach**: Generates emotional, personalized messages in Thanglish (Tamil + English) using Groq (LLaMA-3).
- **Real Email Sending**: SMTP integration for actual email delivery.
- **Dashboard**: Track leads, status, and conversion stats with autopilot toggle.

## 🛠 Tech Stack

- **Backend**: Python, Flask, MySQL, Playwright, BeautifulSoup
- **Frontend**: React, Vite, Tailwind CSS
- **AI**: Google Gemini 1.5 Flash, Groq (LLaMA-3)
- **Database**: MySQL
- **Web Scraping**: DuckDuckGo Search API, Playwright browser automation

## 📋 Prerequisites

- Python 3.8+
- Node.js & npm
- MySQL Server (XAMPP recommended)
- API Keys for Gemini and Groq

## 🚀 Setup Instructions

### 1. Backend Setup

1. Navigate to the backend folder:
   ```bash
   cd ai-lead-outreach/backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers (required for web scraping):
   ```bash
   python -m playwright install
   ```

4. Configure environment variables:
   - Open `.env` and add your API keys and DB credentials.
   - Ensure your MySQL server is running and create a database named `ai_lead_outreach` (or update `.env`).
   - Add SMTP credentials for real email sending (optional):
     ```
     SMTP_EMAIL=mogeshwaran09@gmail.com
     SMTP_PASSWORD=gimf mmti qtot mtdo
     ```

5. Run the server:
   ```bash
   python app.py
   ```
   The server will start on `http://localhost:5000`. The database tables will be created automatically on the first run.

### 2. Frontend Setup

1. Navigate to the frontend folder:
   ```bash
   cd ai-lead-outreach/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:5173`.

## 🎯 Usage

### Finding Leads

1. **Upload Leads**: Go to **Upload Leads** and upload CSV/Excel files with columns: name, email, phone, company, location.

2. **AI Discovery**: Go to **Find Leads** → **AI Discovery**:
   - Enter Industry (e.g., "Software Companies")
   - Enter Location (e.g., "Bangalore")
   - The AI agent will search the web, visit company websites, and extract contact information automatically.

3. **Web Scraper**: Go to **Find Leads** → **Web Scraper**:
   - Enter a specific URL (e.g., a contact page)
   - The agent will scrape that exact page for emails and phone numbers.

### Processing Leads

1. **Manual Processing**: Click on individual leads in the dashboard to analyze them with AI and send personalized messages.

2. **Autonomous Mode**: 
   - Toggle **Autopilot Mode** ON in the dashboard
   - The system will automatically:
     - Analyze new leads every 30 seconds
     - Decide whether to outreach based on trust scores
     - Generate and send Thanglish messages
     - Log all activities

### Monitoring

- **Dashboard**: View KPIs, lead status distribution, and recent activities.
- **Lead Details**: Click any lead to see AI analysis, trust scores, and outreach history.

## 📁 Project Structure

```
ai-lead-outreach/
 ├─ backend/
 │   ├─ app.py              # Main Flask App + AI Agents
 │   ├─ db.py               # MySQL Database Connection & Queries
 │   ├─ requirements.txt    # Python dependencies
 │   └─ .env                # API Keys & Config
 │
 ├─ frontend/
 │   ├─ src/
 │   │   ├─ pages/          # Landing, Upload, Dashboard, LeadDetail, SearchLeads
 │   │   ├─ components/     # Navbar, StatCard, LeadsTable
 │   │   ├─ api.js          # Axios setup
 │   │   ├─ App.jsx         # Routing
 │   │   └─ main.jsx
 │   ├─ package.json
 │   └─ tailwind.config.js
 │
 ├─ sample_leads.csv        # Sample data for testing
 └─ README.md
```

## 🔧 API Endpoints

- `POST /api/upload-leads` - Upload CSV/Excel files
- `GET /api/dashboard-stats` - Get dashboard statistics
- `GET /api/leads` - Get all leads
- `GET /api/leads/<id>` - Get specific lead details
- `POST /api/analyze/<id>` - Run AI analysis on a lead
- `POST /api/outreach/<id>` - Generate and send outreach message
- `POST /api/search-leads` - AI-powered lead discovery
- `POST /api/scrape-url` - Scrape specific URL for contacts
- `GET/POST /api/settings` - Get/set autopilot settings

## 🤖 AI Agents

1. **Lead Ingestion Agent**: Parses CSV/Excel and stores in MySQL
2. **Lead Discovery Agent**: Searches web using DuckDuckGo API
3. **Web Scraping Agent**: Uses Playwright to extract contacts from websites
4. **Business Analysis Agent**: Gemini AI analyzes company trustworthiness
5. **Decision Agent**: Determines outreach priority based on analysis
6. **Message Strategy Agent**: Plans communication approach
7. **Message Generation Agent**: Creates Thanglish messages using Groq
8. **Outreach Agent**: Sends emails via SMTP
9. **Response Analysis Agent**: Analyzes incoming responses
10. **Follow-up Agent**: Manages follow-up sequences

## 🔒 Security & Configuration

- Use `.env` for all sensitive data (API keys, DB credentials)
- Enable Autopilot mode only when ready for automated outreach
- Monitor database logs for outreach activities
- Configure SMTP settings for real email delivery

## 🐛 Troubleshooting

- **ModuleNotFoundError**: Ensure you're using the virtual environment: `pip install -r requirements.txt`
- **Playwright errors**: Run `python -m playwright install` to install browsers
- **Database connection**: Ensure MySQL is running and credentials are correct
- **API key errors**: Check `.env` file has valid Gemini and Groq API keys

## 📈 Future Enhancements

- WhatsApp integration for multi-channel outreach
- LinkedIn scraping for professional networking
- Advanced sentiment analysis for responses
- CRM integration (Salesforce, HubSpot)
- Multi-language support beyond Thanglish
- Advanced analytics and reporting dashboard
