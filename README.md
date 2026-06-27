# Career Kairos - AI Resume Matcher

> An AI-powered tool that compares your resume against a job description, scores the match, and tells you exactly which skills you're missing.

**🔗 Live demo:** _coming soon_
**📺 Demo video / screenshots:** _coming soon_

---

## About

I built this to go beyond a typical CRUD app - it combines a real
authentication system, NLP-based resume/job parsing, and a
configurable matching engine (TF-IDF, keyword overlap, or a hybrid
of both) into one working tool. The goal was to practice building
something close to a real product: a FastAPI backend with its own
database and auth, talking to a separate frontend over a clean REST
API, the way a real client-server app is structured in production.

## Features

-  Email/password authentication with JWT tokens
-  Resume upload (PDF/DOCX) with automatic skill & section extraction
-  Job description input via pasted text (or URL scraping, best-effort)
-  Resume-to-job matching with 3 selectable methods (hybrid, TF-IDF, keyword)
-  Match score, missing required/preferred skills, and tailored recommendations
-  Match history per user

## Tech Stack

| Layer       | Technology                                       |
|-------------|---------------------------------------------------|
| Backend     | FastAPI, SQLAlchemy, PostgreSQL                   |
| Frontend    | Streamlit                                         |
| NLP/Parsing | spaCy, scikit-learn, pdfminer.six, python-docx    |
| Auth        | JWT (python-jose), bcrypt password hashing        |
| Database    | PostgreSQL (via Docker locally / Neon in production) |

## Screenshots

> _To Add 2-3 screenshots here once deployed: the login screen, a resume upload, and a match result with scores._

## Project Structure

```
resume-matcher/
├── docker-compose.yml
├── start.bat                 # one-click local launcher (Windows)
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── routers/          # auth, resume, job, match endpoints
│   │   └── services/         # parser, scraper, matcher logic
│   ├── requirements.txt
│   ├── .env.example
│   └── create_tables.py
└── frontend/
    ├── app.py
    └── requirements.txt
```

## Setup (run it locally)

### Prerequisites
- Python 3.11+ (tested on 3.12.4)
- Docker Desktop (for PostgreSQL)

### 1. Clone and configure environment variables

```bash
git clone <your-repo-url>
cd resume-matcher
copy backend\.env.example backend\.env
```

Open `backend/.env` and fill in real values - especially generate a
proper `SECRET_KEY` rather than using the placeholder:

```python
import secrets; print(secrets.token_hex(32))
```

### 2. Start the database

```bash
docker-compose up -d
```

### 3. Set up the backend (its own virtual environment)

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python create_tables.py
uvicorn app.main:app --reload
```

Backend will be running at `http://127.0.0.1:8000` (interactive API
docs at `http://127.0.0.1:8000/docs`).

### 4. Set up the frontend (a *separate* virtual environment)

In a new terminal:

```bash
cd frontend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Frontend will open at `http://localhost:8501`.

### Why two separate virtual environments?

Streamlit and this version of FastAPI need different, incompatible
versions of a shared dependency (Starlette). Installing both into
one environment causes one to silently break the other. Keeping
backend and frontend isolated avoids this, and means a future
upgrade on one side can never break the other.

### Shortcut: `start.bat`

Once both venvs are set up once (steps 3 & 4 above), `start.bat` in
the project root launches the database, backend, and frontend
together, each in its own terminal window.

## Known Limitations

- **Job URL scraping is best-effort.** Many job sites (LinkedIn,
  Indeed, etc.) actively block automated scrapers, so `/job/scrape`
  may fail on many real-world URLs. **Pasting the job description
  text directly** (`/job/parse-text`) is the reliable path and is
  the default tab in the UI.
- Skill extraction is based on a curated skill taxonomy rather than
  a fully general-purpose NLP model, so unusual or very niche skills
  may not be detected.

## Possible Future Improvements

- Headless-browser based scraping (e.g. Playwright) for more
  reliable job URL imports
- Resume improvement suggestions powered by an LLM
- Export match results as a PDF report
- Dockerize the frontend and backend together for one-command startup
- Automated tests (currently none)

## License

MIT