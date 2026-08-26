# Innovix (LiveDoc AI)

Innovix is a multi-tenant documentation assistant that analyzes GitHub repositories and generates:
- architecture documentation
- Mermaid diagrams
- commit history summaries

It uses:
- FastAPI backend
- Static frontend (HTML/CSS/JS)
- MongoDB for storage
- Gemini for AI-generated summaries

## Project Structure

```text
backend/
	main.py
	auth.py
	middleware.py
	db.py
	config.py
	services/
		ai_service.py
		github_service.py
		parser_service.py

frontend/
	index.html         # Login page
	register.html      # Register page (separate)
	dashboard.html     # Main app page
	script.js          # Login logic
	register.js        # Register logic
	style.css
```

## Authentication Pages

- Login page: `frontend/index.html`
- Register page: `frontend/register.html`

Current behavior:
- Login page calls `POST /login`
- Register page calls `POST /register`
- After success, JWT token is saved and user is redirected to dashboard

## Environment Variables

Create `backend/.env` file:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=livedoc

JWT_SECRET_KEY=change_this_secret
ACCESS_TOKEN_EXPIRE_MINUTES=60

GEMINI_API_KEY=your_gemini_api_key
GITHUB_API_KEY=your_github_token

GITHUB_ACTION_SECRET=super-secret-default-key
```

Notes:
- `GITHUB_API_KEY` is strongly recommended to avoid GitHub rate limits.
- If the token is missing/invalid, some GitHub API calls can fail.

## Local Run

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend URLs:
- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

### 2. Frontend

Open another terminal:

```powershell
cd frontend
python -m http.server 3000
```

Frontend URL:
- http://127.0.0.1:3000

## Main API Endpoints

- `POST /register`
- `POST /login`
- `POST /analyze`
- `POST /commit-history`
- `POST /api/trigger-update`

## Common Issues

### Login/Register not working
- Ensure backend is running at `http://127.0.0.1:8000`
- Ensure frontend is served from `http://127.0.0.1:3000`
- Check browser console/network for 401/500 responses

### Commit history empty
- Usually GitHub API rate limit or invalid token
- Add valid `GITHUB_API_KEY` in `backend/.env`
- Restart backend after editing `.env`

### Mermaid syntax error
- Some AI-generated diagrams can be invalid
- Frontend now includes Mermaid sanitization and fallback rendering

## Deployment (Vercel + Render)

Recommended setup:
- Frontend: Vercel
- Backend: Render
- Database: MongoDB Atlas

### Do you need MongoDB Atlas for cloud hosting?
Yes. If backend is deployed to Render/Vercel stack, local MongoDB (`localhost`) will not be accessible. Use Atlas connection string in `MONGODB_URI`.

### Deployment checklist

1. Backend on Render:
- Build command: `pip install -r backend/requirements.txt`
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Set env vars: `MONGODB_URI`, `MONGODB_DB`, `JWT_SECRET_KEY`, `GEMINI_API_KEY`, `GITHUB_API_KEY`

2. Frontend on Vercel:
- Deploy `frontend/` as static app
- Update API base URL in frontend scripts to your Render backend URL

3. Security:
- Use strong `JWT_SECRET_KEY`
- Restrict CORS origins in production
- Do not commit `.env`