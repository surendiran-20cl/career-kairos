from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models, auth
from app.database import get_db
from app.services.scraper import JobScraper

router = APIRouter(prefix="/job", tags=["job"])


class JobUrlRequest(BaseModel):
    url: str


class JobTextRequest(BaseModel):
    text: str


def _save_job(db: Session, user_id: int, parsed: dict, url: str = None) -> models.Job:
    job_record = models.Job(
        user_id=user_id,
        url=url,
        raw_text=parsed["raw_text"],
        required_skills=",".join(parsed["required_skills"]),
        preferred_skills=",".join(parsed["preferred_skills"]),
        summary=parsed["summary"],
    )
    db.add(job_record)
    db.commit()
    db.refresh(job_record)
    return job_record


@router.post("/scrape")
def scrape_job(
    request: JobUrlRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    text = JobScraper.scrape_from_url(request.url)
    if not text:
        raise HTTPException(status_code=400, detail="Could not retrieve job description from that URL")

    parsed = JobScraper.parse_job_description(text)
    job_record = _save_job(db, current_user.id, parsed, url=request.url)

    return {"job_id": job_record.id, "url": request.url, "parsed_data": parsed}


@router.post("/parse-text")
def parse_job_text(
    request: JobTextRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Job text cannot be empty")

    parsed = JobScraper.parse_job_description(request.text)
    job_record = _save_job(db, current_user.id, parsed)

    return {"job_id": job_record.id, "parsed_data": parsed}


@router.get("/list")
def list_my_jobs(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    jobs = (
        db.query(models.Job)
        .filter(models.Job.user_id == current_user.id)
        .order_by(models.Job.created_at.desc())
        .all()
    )
    return [
        {
            "id": j.id,
            "url": j.url,
            "required_skills": j.required_skills.split(",") if j.required_skills else [],
            "preferred_skills": j.preferred_skills.split(",") if j.preferred_skills else [],
            "summary": j.summary,
            "created_at": j.created_at,
        }
        for j in jobs
    ]