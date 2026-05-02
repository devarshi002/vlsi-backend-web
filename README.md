# NanoCore VLSI — Backend API

FastAPI backend for the NanoCore VLSI Training Institute website.  
Handles enquiry forms → MongoDB + Google Sheets + Email alerts.

---

## Stack
- **FastAPI** — API framework
- **Motor** — async MongoDB driver
- **SlowAPI** — rate limiting
- **Google Sheets API** — lead spreadsheet
- **Gmail SMTP** — email alerts
- **Pydantic** — input validation

---

## Local Setup

### 1. Clone & install
```bash
git clone https://github.com/yourname/nanocore-backend.git
cd nanocore-backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Open .env and fill in all values (see comments inside)
```

### 3. Google Sheets setup
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project → **Enable** `Google Sheets API` + `Google Drive API`
3. Go to **IAM & Admin → Service Accounts** → Create service account
4. Create a JSON key → download → save as `credentials.json` in project root
5. Create a new [Google Sheet](https://sheets.google.com)
6. **Share** the sheet with the service account email (give Editor access)
7. Copy the Sheet ID from the URL and paste into `.env`

### 4. Gmail App Password setup
1. Use a Gmail account (e.g. `nanocore.alerts@gmail.com`)
2. Go to **Google Account → Security → 2-Step Verification → ON**
3. Go to **App Passwords** → Select app: Mail → Generate
4. Copy the 16-character password into `.env` as `SMTP_PASSWORD`

### 5. Run locally
```bash
uvicorn app.main:app --reload
```
API is live at: `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

---

## API Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/api/enquiry/popup` | Scroll popup form | 5/min per IP |
| POST | `/api/enquiry/contact` | Contact page form | 3/min per IP |
| GET | `/api/health` | DB health check | — |
| GET | `/docs` | Swagger UI | — |

### Example request
```bash
curl -X POST http://localhost:8000/api/enquiry/popup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","phone":"9876543210","email":"test@test.com","course":"RTL Design"}'
```

---

## Deploy to Render (Free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set these:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all `.env` variables in Render → Environment tab
6. Upload `credentials.json` content as an environment variable:
   - Key: `GOOGLE_CREDENTIALS_JSON`
   - Value: paste the entire JSON content
   - Then update `sheets_service.py` to read from env var instead of file
7. Deploy → copy your Render URL
8. Paste Render URL into React frontend `.env` as `VITE_API_URL`
9. Add your Render URL to `ALLOWED_ORIGINS` in backend `.env`

---

## What happens on each form submission

```
User submits form
      ↓
FastAPI validates input (Pydantic)
      ↓
Rate limit check (SlowAPI)
      ↓
Save to MongoDB Atlas   ←── always first, synchronous
      ↓
Background tasks (non-blocking, parallel):
  ├── Send email alert via Gmail SMTP
  └── Append row to Google Sheets
      ↓
Return JSON response to user instantly
```

---

## Security Features
- **Rate limiting** — 5 req/min (popup), 3 req/min (contact) per IP
- **Input validation** — Pydantic rejects malformed data
- **CORS whitelist** — only your frontend domain can call the API
- **No secrets in frontend** — all keys stay server-side
- **Email/Sheets failures are non-blocking** — won't crash the API
