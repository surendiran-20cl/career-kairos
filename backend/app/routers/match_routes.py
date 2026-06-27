from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models, auth
from app.database import get_db
from app.services.matcher import ResumeMatcher

router = APIRouter(prefix="/match", tags=["match"])


class MatchRequest(BaseModel):
    resume_id: int
    job_id: int
    method: str = "hybrid"  # "hybrid", "tfidf", or "keyword"


def _get_owned_resume(db: Session, resume_id: int, user_id: int) -> models.Resume:
    resume = (
        db.query(models.Resume)
        .filter(models.Resume.id == resume_id, models.Resume.user_id == user_id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


def _get_owned_job(db: Session, job_id: int, user_id: int) -> models.Job:
    job = (
        db.query(models.Job)
        .filter(models.Job.id == job_id, models.Job.user_id == user_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/")
def match_resume_to_job(
    request: MatchRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    resume = _get_owned_resume(db, request.resume_id, current_user.id)
    job = _get_owned_job(db, request.job_id, current_user.id)

    resume_skills = resume.skills.split(",") if resume.skills else []
    job_required_skills = job.required_skills.split(",") if job.required_skills else []
    job_preferred_skills = job.preferred_skills.split(",") if job.preferred_skills else []

    result = ResumeMatcher.calculate_match(
        resume_skills, job_required_skills, job_preferred_skills, method=request.method
    )
    recommendations = ResumeMatcher.generate_recommendations(
        result["missing_required_skills"], result["missing_preferred_skills"]
    )

    # Save this match attempt to the database for history
    match_record = models.MatchResult(
        user_id=current_user.id,
        resume_id=resume.id,
        job_id=job.id,
        match_score=result["match_score"],
        method=result["method"],
    )
    db.add(match_record)
    db.commit()
    db.refresh(match_record)

    return {
        "match_id": match_record.id,
        "resume_filename": resume.filename,
        "job_url": job.url,
        "resume_skills": resume_skills,
        "job_required_skills": job_required_skills,
        "job_preferred_skills": job_preferred_skills,
        "match_result": result,
        "recommendations": recommendations,
    }


@router.get("/history")
def match_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    matches = (
        db.query(models.MatchResult)
        .filter(models.MatchResult.user_id == current_user.id)
        .order_by(models.MatchResult.created_at.desc())
        .all()
    )
    return [
        {
            "id": m.id,
            "resume_id": m.resume_id,
            "job_id": m.job_id,
            "match_score": m.match_score,
            "method": m.method,
            "created_at": m.created_at,
        }
        for m in matches
    ]