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
        Matching tolerates:
        - spacing/punctuation variants between words ("power bi",
          "power-bi", "powerbi" all match the same skill)
        - trailing version numbers/symbols directly after a skill
          name ("html5", "css3", "angular10", "python3" all match
          their base skill, since resumes commonly append versions
          with no separating space)
        """
        normalized_text = normalize(text)
        found = set()
        for skill in SKILLS_SET:
            words = skill.split(" ")
            flexible_pattern = r"[\s\-_]*".join(re.escape(word) for word in words)
            # \b at the start still requires a real word boundary before
            # the skill. At the end, instead of \b (which fails right
            # before a digit, since digits count as "word" characters),
            # we use a lookahead that allows the skill to be followed by
            # punctuation/space/end-of-string, OR a version-like suffix
            # (optional dot/space/hyphen then digits), but not by
            # another letter (which would mean it's part of a longer word).
            pattern = r"\b" + flexible_pattern + r"(?:[\s.\-]?\d+(?:[.\d+]*)?)?(?![a-zA-Z])"
            if re.search(pattern, normalized_text):
                found.add(skill)
        return sorted(found)
# What this changes precisely: instead of ending with \b, we end with (?:[\s.\-]?\d+(?:[.\d+]*)?)? (optionally swallow a version-like suffix: optional space/dot/hyphen, then digits, then more dots/digits — covers 5, .6, -10, 6/8 partially, 10+) followed by (?![a-zA-Z]) — a negative lookahead meaning "not immediately followed by another letter." This correctly matches html5, css3, angular10 while still correctly rejecting a skill like "r" matching inside "prepare" (since prepare has letters right after, the lookahead blocks it).


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