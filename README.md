# MarketRooster: AI-Powered News Filtering & Alerts  

**Hackathon Case:** Wellershoff & Partners × IBM – *Financial News Detection*  
**Team 5** 

---

## 🚀 Problem Statement  
Analysts and portfolio managers drown in financial news every day.  
Relevant updates (CEO exits, M&A deals, earnings surprises, regulations) are hidden in thousands of low-impact headlines. This wastes analyst time and increases the risk of **missing critical signals**.  

---

## 💡 Our Solution: MarketRooster  
A real-time platform that:  
1. **Ingests financial news** (MarketAux, NewsAPI, SEC filings)  
2. **Filters and classifies** events via **LLM-based AI**  
3. **Summarizes** news with *"Why it matters"* context  
4. **Ranks** importance with a logistic regression model  
5. **Delivers** actionable insights directly to analysts via:  
   - React Dashboard (review & approve)  
   - Slack DM alerts  
   - Email notifications  

---

## 🖼️ System Architecture  
```
News APIs + SEC Filings
        ↓
   AI Filtering (priority by CEO Exit, M&A, etc.)
        ↓
   LLM Classification (tags, tickers, sectors)
        ↓
   Executive Summary (headline, bullets, why it matters)
        ↓
   ML Ranker (LogReg scoring)
        ↓
   Analyst Review (React dashboard)
        ↓
   Client Delivery (Slack DM, Email alerts)
```

---

## 🛠️ Key Technologies  
- **Frontend**: React, TailwindCSS  
- **Backend**: Node.js + Express, LowDB (JSON-based DB)  
- **AI/NLP**: OpenAI GPT (summarization, text merging)  
- **Infrastructure**: IBM Watson Cloud, Realtime APIs  
- **Integrations**: Slack API (DM + Webhooks), Nodemailer (Email)  

---

## ⚙️ Installation & Setup  

### 1️⃣ Clone Repository  
```bash
git clone https://github.com/MarlonSteiner/Starthack-IBM-Market-Evaluation
```

### 2️⃣ Install Dependencies  
Backend:  
```bash
cd backend
npm install
```

Frontend:  
```bash
cd ../frontend
npm install
```

### 3️⃣ Environment Variables  
Create `backend/.env` with:  
```ini
# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
SLACK_BOT_TOKEN=xoxb-XXXXXXXX
SLACK_USER_ID=UXXXXXXXX

# OpenAI
OPENAI_API_KEY=sk-XXXXXXXX

# Email
EMAIL_SENDER=yourmail@gmail.com
EMAIL_PASSWORD=your-app-password
```

### 4️⃣ Run Backend  
```bash
cd backend
node server.js
```
→ Runs at `http://localhost:3001`  

### 5️⃣ Run Frontend  
```bash
cd frontend
npm start
```
→ Opens at `http://localhost:3000`  

---

## 📂 Project Structure  
```
wp-news-dashboard/
│
├── backend/                 # Express API + LowDB
│   ├── server.js            # Main backend server
│   ├── db.json              # Local DB (articles, tags, subscriptions)
│   └── approved.json        # Analyst-approved texts
│
├── frontend/                # React Dashboard
│   ├── src/components/      # UI Components (Cards, Filters, Header)
│   ├── src/pages/           # DashboardPage, ReviewPage
│   └── src/App.jsx          # Main app logic
│
└── README.md
```

---

## 👥 Team  
- **Dario** – Backend
- **Fabian** - Frontend, UI
- **Peter** - AI integration
- **Marlon** - Ideation, UX

