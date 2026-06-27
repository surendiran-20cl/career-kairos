from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app import models
from app.routers import auth_routes, resume_routes , job_routes , match_routes

# Create any tables that don't exist yet (safe to call every startup)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Resume Matcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(resume_routes.router)
app.include_router(job_routes.router)
app.include_router(match_routes.router)

@app.get("/")
def read_root():
    return {"message": "AI Resume Matcher API is running!"}