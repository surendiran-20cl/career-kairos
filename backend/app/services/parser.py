from typing import Dict, List
import re
import pdfminer.high_level
import docx
import spacy

from app.services.skills_data import SKILLS_SET, normalize

nlp = spacy.load("en_core_web_sm")


class ResumeParser:

    # ---------- Text extraction ----------

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        return pdfminer.high_level.extract_text(file_path)

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)

    @staticmethod
    def extract_text(file_path: str) -> str:
        lower_path = file_path.lower()
        if lower_path.endswith(".pdf"):
            return ResumeParser.extract_text_from_pdf(file_path)
        elif lower_path.endswith(".docx"):
            return ResumeParser.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format. Use PDF or DOCX.")

    # ---------- Parsing ----------

    @staticmethod
    def parse_resume(text: str) -> Dict:
        skills = ResumeParser.extract_skills(text)
        experience = ResumeParser._extract_experience(text)
        education = ResumeParser._extract_education(text)

        return {
            "raw_text": text,
            "skills": skills,
            "experience": experience,
            "education": education,
            "summary": ResumeParser._generate_summary(skills, experience, education),
        }

    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """
        Scan the text for any skill in our curated taxonomy.
        This is a simple substring match, which is intentionally easy
        to reason about: if the skill name appears anywhere in the
        text, we count it as present.
        """
        normalized_text = normalize(text)
        found = set()

        for skill in SKILLS_SET:
            # \b...\b avoids partial-word matches (e.g. "r" matching inside "your")
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, normalized_text):
                found.add(skill)

        return sorted(found)

    @staticmethod
    def _extract_experience(text: str) -> List[Dict]:
        doc = nlp(text)
        experiences = []
        current_job = {}
        date_pattern = r"\b(19|20)\d{2}\s*[-–]\s*((19|20)\d{2}|Present)\b"

        for sent in doc.sents:
            sent_text = sent.text.strip()
            if re.search(date_pattern, sent_text, re.IGNORECASE):
                if current_job:
                    experiences.append(current_job)
                current_job = {"text": sent_text}
            elif current_job:
                current_job["text"] += " " + sent_text

        if current_job:
            experiences.append(current_job)

        return experiences if experiences else [{"text": "No experience section detected"}]

    @staticmethod
    def _extract_education(text: str) -> List[Dict]:
        degree_pattern = r"\b(Bachelor|Master|PhD|B\.?Sc|M\.?Sc|MBA|University|College|Institute)\b"
        educations = []

        for sent in nlp(text).sents:
            if re.search(degree_pattern, sent.text, re.IGNORECASE):
                educations.append({"text": sent.text.strip()})

        return educations if educations else [{"text": "No education section detected"}]

    @staticmethod
    def _generate_summary(skills: List[str], experience: List[Dict], education: List[Dict]) -> str:
        parts = []
        if skills:
            shown = ", ".join(skills[:5])
            parts.append(f"Skills: {shown}{', ...' if len(skills) > 5 else ''}")
        parts.append(f"Experience entries: {len(experience)}")
        parts.append(f"Education entries: {len(education)}")
        return " | ".join(parts)