import os
import tempfile
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db
from app.services.parser import ResumeParser

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/parse")
async def parse_resume(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    # Save the upload to a temporary file so our parser (which reads
    # from a file path) can work with it, then clean up afterward.
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_path = tmp_file.name
        contents = await file.read()
        tmp_file.write(contents)

    try:
        raw_text = ResumeParser.extract_text(tmp_path)
    finally:
        os.unlink(tmp_path)

    parsed = ResumeParser.parse_resume(raw_text)

    # Save this resume to the database, linked to whoever is logged in.
    resume_record = models.Resume(
        user_id=current_user.id,
        filename=file.filename,
        raw_text=parsed["raw_text"],
        skills=",".join(parsed["skills"]),
        summary=parsed["summary"],
    )
    db.add(resume_record)
    db.commit()
    db.refresh(resume_record)

    return {
        "resume_id": resume_record.id,
        "filename": file.filename,
        "parsed_data": parsed,
    }


@router.get("/list")
def list_my_resumes(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    resumes = (
        db.query(models.Resume)
        .filter(models.Resume.user_id == current_user.id)
        .order_by(models.Resume.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "skills": r.skills.split(",") if r.skills else [],
            "summary": r.summary,
            "created_at": r.created_at,
        }
        for r in resumes
    ]