from typing import Dict, List, Optional
import re
import requests
from bs4 import BeautifulSoup

from app.services.parser import ResumeParser  # reuse the skill extractor


class JobScraper:

    # ---------- Scraping from a URL ----------

    @staticmethod
    def scrape_from_url(url: str) -> Optional[str]:
        """
        Attempts to pull the main job description text out of a posting URL.
        Tries a few known site structures, then falls back to grabbing all
        paragraph text. Returns None if the page couldn't be fetched at all.
        """
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Known site-specific containers
        for class_name in ["description__text", "jobDescriptionText", "job-description"]:
            content = soup.find(class_=class_name)
            if content:
                return content.get_text(separator="\n", strip=True)

        # Fallback: all paragraph text
        paragraphs = soup.find_all("p")
        if paragraphs:
            text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            if text:
                return text

        # Last resort: whatever text is on the page at all
        full_text = soup.get_text(separator="\n", strip=True)
        return full_text if full_text else None

    # ---------- Parsing job text into structured data ----------

    @staticmethod
    def parse_job_description(text: str) -> Dict:
        required_skills, preferred_skills = JobScraper._split_required_preferred(text)
        requirements = JobScraper._extract_requirements(text)

        return {
            "raw_text": text,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "requirements": requirements,
            "summary": JobScraper._generate_summary(required_skills, preferred_skills, requirements),
        }

    @staticmethod
    def _split_required_preferred(text: str) -> (List[str], List[str]):
        """
        Splits the text into a "required" section and a "preferred" section
        based on common heading keywords, then runs skill extraction on
        each section separately. Anything found in the whole text but not
        clearly in a "preferred" section defaults to required.
        """
        required_markers = r"(required|must have|requirements|qualifications)"
        preferred_markers = r"(preferred|nice to have|bonus|plus)"

        lower_text = text.lower()

        preferred_start = None
        for match in re.finditer(preferred_markers, lower_text):
            preferred_start = match.start()
            break  # first occurrence is good enough for a simple split

        if preferred_start is not None:
            required_section = text[:preferred_start]
            preferred_section = text[preferred_start:]
        else:
            required_section = text
            preferred_section = ""

        required_skills = ResumeParser.extract_skills(required_section)
        preferred_skills = ResumeParser.extract_skills(preferred_section) if preferred_section else []

        # Avoid double-counting: anything already required shouldn't also show as preferred
        preferred_skills = [s for s in preferred_skills if s not in required_skills]

        return required_skills, preferred_skills

    @staticmethod
    def _extract_requirements(text: str) -> List[str]:
        bullet_points = re.findall(r"[•\-\u2022]\s+(.+)", text)
        cleaned = [b.strip() for b in bullet_points if len(b.strip()) > 5]
        return cleaned[:15] if cleaned else ["No bullet-point requirements detected"]

    @staticmethod
    def _generate_summary(required: List[str], preferred: List[str], requirements: List[str]) -> str:
        parts = []
        if required:
            parts.append(f"Required skills: {', '.join(required[:5])}{', ...' if len(required) > 5 else ''}")
        if preferred:
            parts.append(f"Preferred skills: {', '.join(preferred[:5])}{', ...' if len(preferred) > 5 else ''}")
        parts.append(f"Requirement bullet points: {len(requirements)}")
        return " | ".join(parts)