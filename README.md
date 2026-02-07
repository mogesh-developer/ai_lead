<div align="center">

# 🤖 AI Lead Outreach Agent

### *Intelligent Lead Generation & Autonomous Outreach Platform*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18.x-61dafb.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*An AI-powered SaaS platform that autonomously discovers, analyzes, and reaches out to potential leads using advanced web scraping, NLP, and multi-agent AI systems.*

[Features](#-features) • [Tech Stack](#-tech-stack) • [Setup](#-setup-instructions) • [Usage](#-usage) • [API](#-api-endpoints)

---

</div>

## 📋 Overview

AI Lead Outreach Agent is a full-stack SaaS application that revolutionizes lead generation and outreach through autonomous AI agents. Built with Python Flask backend and React frontend, it leverages cutting-edge AI models (Google Gemini 1.5 Flash & Groq LLaMA-3) to intelligently discover, analyze, and engage with potential business leads.

## ✨ Key Features

### 🎯 Lead Management
- **CSV/Excel Import**: Bulk upload leads with comprehensive data fields
- **Real-time Dashboard**: Track KPIs, conversion rates, and lead status
- **Lead Scoring**: AI-driven trust and maturity analysis

### 🔍 Intelligent Discovery
- **AI-Powered Search**: DuckDuckGo integration for industry-specific lead discovery
- **Web Scraping**: Playwright-powered extraction of contact information
- **JustDial Integration**: Automated business directory scraping

### 🤖 Autonomous Operations
- **Autopilot Mode**: Background scheduler processes leads automatically every 30 seconds
- **Smart Decision Making**: AI determines outreach priority based on trust scores
- **Automatic Follow-ups**: Manages communication sequences intelligently

### 💬 Personalized Outreach
- **Thanglish Messages**: Generates culturally-relevant Tamil+English hybrid communications
- **Emotional Intelligence**: Creates personalized, context-aware messaging
- **SMTP Integration**: Real email delivery with tracking

### 📊 Analytics & Monitoring
- **Comprehensive Dashboard**: Visual insights into lead pipeline
- **Activity Logs**: Complete audit trail of all AI actions
- **Performance Metrics**: Conversion tracking and success rates

## 🛠 Tech Stack

### Backend
- **Framework**: Flask 3.x
- **Language**: Python 3.8+
- **Database**: MySQL
- **Web Scraping**: Playwright, BeautifulSoup4
- **Search**: DuckDuckGo API

### Frontend
- **Framework**: React 18.x
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios

### AI & ML
- **Analysis**: Google Gemini 1.5 Flash
- **Text Generation**: Groq (LLaMA-3)
- **Multi-Agent System**: Custom autonomous agents

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js & npm** - [Download](https://nodejs.org/)
- **MySQL Server** - [XAMPP](https://www.apachefriends.org/) recommended
- **API Keys**:
  - [Google Gemini API](https://makersuite.google.com/app/apikey)
  - [Groq API](https://console.groq.com/)

## 🚀 Setup Instructions

### 1️⃣ Backend Setup

```bash
# Navigate to backend directory
cd ai_lead/backend

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for web scraping)
python -m playwright install
```

**Configure Environment Variables:**

Create a `.env` file in the `backend` directory:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=ai_lead_outreach

# AI API Keys
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# SMTP Configuration (for email sending)
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**Initialize Database:**

```bash
# Start MySQL server (XAMPP/WAMP)
# Create database
mysql -u root -p
CREATE DATABASE ai_lead_outreach;
exit;

# Run the Flask application (tables will be created automatically)
python app.py
```

The backend server will start on `http://localhost:5000`

### 2️⃣ Frontend Setup

```bash
# Navigate to frontend directory
cd ai_lead/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🎯 Usage

### Finding Leads

#### 📤 Manual Upload
1. Navigate to **Upload Leads**
2. Upload CSV/Excel with columns: `name`, `email`, `phone`, `company`, `location`
3. Leads will be automatically ingested into the system

#### 🔎 AI Discovery
1. Go to **Find Leads** → **AI Discovery**
2. Enter Industry (e.g., "Software Companies")
3. Enter Location (e.g., "Bangalore")
4. AI agent will search the web and extract contacts automatically

#### 🌐 Web Scraper
1. Go to **Find Leads** → **Web Scraper**
2. Enter a specific URL (e.g., company contact page)
3. Agent scrapes emails and phone numbers from the page

### Processing Leads

#### 🖱️ Manual Processing
- Click individual leads in the dashboard
- View AI analysis and trust scores
- Send personalized messages with one click

#### 🤖 Autonomous Mode
1. Toggle **Autopilot Mode ON** in dashboard
2. System automatically:
   - Analyzes new leads every 30 seconds
   - Decides outreach priority based on trust scores
   - Generates and sends Thanglish messages
   - Logs all activities

### Monitoring

- **Dashboard**: View KPIs, lead status distribution, recent activities
- **Lead Details**: Click any lead for AI analysis, trust scores, outreach history
- **Activity Logs**: Monitor all autonomous agent actions

## 📁 Project Structure

```
ai_lead/
├── backend/
│   ├── app.py                    # Main Flask App + AI Agents
│   ├── db.py                     # MySQL Database Connection
│   ├── justdial_scraper.py       # JustDial scraping logic
│   ├── requirements.txt          # Python dependencies
│   └── .env                      # API Keys & Configuration
│
├── frontend/
│   ├── src/
│   │   ├── pages/                # Landing, Upload, Dashboard, LeadDetail
│   │   ├── components/           # Navbar, StatCard, LeadsTable
│   │   ├── api.js                # Axios setup
│   │   ├── App.jsx               # React Router
│   │   └── main.jsx              # Entry point
│   ├── package.json
│   └── tailwind.config.js
│
├── sample_leads.csv              # Sample data for testing
└── README.md
```

## 🔌 API Endpoints

### Lead Management
```http
POST   /api/upload-leads          # Upload CSV/Excel files
GET    /api/leads                 # Get all leads
GET    /api/leads/<id>            # Get specific lead details
GET    /api/dashboard-stats       # Dashboard statistics
```

### AI Operations
```http
POST   /api/analyze/<id>          # Run AI analysis on lead
POST   /api/outreach/<id>         # Generate & send outreach message
POST   /api/search-leads          # AI-powered lead discovery
POST   /api/scrape-url            # Scrape URL for contacts
```

### Settings
```http
GET    /api/settings              # Get autopilot settings
POST   /api/settings              # Update autopilot settings
```

## 🤖 AI Agent Architecture

| Agent | Responsibility |
|-------|---------------|
| **Lead Ingestion Agent** | Parses CSV/Excel and stores in MySQL |
| **Lead Discovery Agent** | Searches web using DuckDuckGo API |
| **Web Scraping Agent** | Extracts contacts using Playwright |
| **Business Analysis Agent** | Analyzes company trustworthiness (Gemini AI) |
| **Decision Agent** | Determines outreach priority |
| **Message Strategy Agent** | Plans communication approach |
| **Message Generation Agent** | Creates Thanglish messages (Groq LLaMA-3) |
| **Outreach Agent** | Sends emails via SMTP |
| **Response Analysis Agent** | Analyzes incoming responses |
| **Follow-up Agent** | Manages follow-up sequences |

## 🔐 Security & Best Practices

- ✅ Store all sensitive data in `.env` files (never commit to Git)
- ✅ Enable Autopilot only when ready for production outreach
- ✅ Monitor database logs for compliance
- ✅ Use app-specific passwords for Gmail SMTP
- ✅ Rate-limit API calls to prevent blocking

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **ModuleNotFoundError** | Ensure virtual environment: `pip install -r requirements.txt` |
| **Playwright errors** | Run: `python -m playwright install` |
| **Database connection** | Verify MySQL is running and credentials are correct |
| **API key errors** | Check `.env` file has valid Gemini and Groq keys |
| **CORS errors** | Ensure backend is running on port 5000 |

## 📈 Future Enhancements

- [ ] WhatsApp integration for multi-channel outreach
- [ ] LinkedIn scraping for professional networking
- [ ] Advanced sentiment analysis for responses
- [ ] CRM integration (Salesforce, HubSpot)
- [ ] Multi-language support beyond Thanglish
- [ ] Advanced analytics and reporting dashboard
- [ ] A/B testing for message effectiveness
- [ ] Voice call integration

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue or contact the maintainer.

---

<div align="center">

**Made with ❤️ using AI-powered automation**

⭐ Star this repository if you find it helpful!

</div>