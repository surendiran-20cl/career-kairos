from typing import Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ResumeMatcher:

    @staticmethod
    def calculate_match(
        resume_skills: List[str],
        job_required_skills: List[str],
        job_preferred_skills: List[str],
        method: str = "hybrid",
    ) -> Dict:
        if method == "tfidf":
            return ResumeMatcher._tfidf_match(resume_skills, job_required_skills, job_preferred_skills)
        elif method == "keyword":
            return ResumeMatcher._keyword_match(resume_skills, job_required_skills, job_preferred_skills)
        else:
            return ResumeMatcher._hybrid_match(resume_skills, job_required_skills, job_preferred_skills)

    # ---------- TF-IDF based similarity ----------

    @staticmethod
    def _tfidf_match(resume_skills: List[str], required: List[str], preferred: List[str]) -> Dict:
        resume_str = " ".join(resume_skills) or "none"
        job_str = " ".join(required + preferred) or "none"

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([resume_str, job_str])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        score = float(similarity[0][0] * 100)

        missing_required, missing_preferred = ResumeMatcher._find_missing(resume_skills, required, preferred)

        return {
            "match_score": round(score, 2),
            "missing_required_skills": missing_required,
            "missing_preferred_skills": missing_preferred,
            "method": "tfidf",
        }

    # ---------- Simple keyword overlap ----------

    @staticmethod
    def _keyword_match(resume_skills: List[str], required: List[str], preferred: List[str]) -> Dict:
        resume_set = {s.lower() for s in resume_skills}
        required_set = {s.lower() for s in required}
        preferred_set = {s.lower() for s in preferred}

        matched_required = required_set & resume_set
        matched_preferred = preferred_set & resume_set

        required_score = (len(matched_required) / len(required_set) * 100) if required_set else 100.0
        preferred_score = (len(matched_preferred) / len(preferred_set) * 100) if preferred_set else 100.0

        # Required skills matter more than preferred ones
        score = (required_score * 0.7) + (preferred_score * 0.3)

        missing_required, missing_preferred = ResumeMatcher._find_missing(resume_skills, required, preferred)

        return {
            "match_score": round(score, 2),
            "required_skills_coverage": round(required_score, 2),
            "preferred_skills_coverage": round(preferred_score, 2),
            "missing_required_skills": missing_required,
            "missing_preferred_skills": missing_preferred,
            "method": "keyword",
        }

    # ---------- Hybrid: average of both ----------

    @staticmethod
    def _hybrid_match(resume_skills: List[str], required: List[str], preferred: List[str]) -> Dict:
        tfidf_result = ResumeMatcher._tfidf_match(resume_skills, required, preferred)
        keyword_result = ResumeMatcher._keyword_match(resume_skills, required, preferred)

        avg_score = (tfidf_result["match_score"] + keyword_result["match_score"]) / 2

        return {
            "match_score": round(avg_score, 2),
            "required_skills_coverage": keyword_result.get("required_skills_coverage"),
            "preferred_skills_coverage": keyword_result.get("preferred_skills_coverage"),
            "missing_required_skills": keyword_result["missing_required_skills"],
            "missing_preferred_skills": keyword_result["missing_preferred_skills"],
            "method": "hybrid",
        }

    # ---------- Shared helper ----------

    @staticmethod
    def _find_missing(resume_skills: List[str], required: List[str], preferred: List[str]):
        resume_set = {s.lower() for s in resume_skills}
        missing_required = [s for s in required if s.lower() not in resume_set]
        missing_preferred = [s for s in preferred if s.lower() not in resume_set]
        return missing_required, missing_preferred

    @staticmethod
    def generate_recommendations(missing_required: List[str], missing_preferred: List[str]) -> List[str]:
        recommendations = []
        if missing_required:
            shown = ", ".join(missing_required[:5])
            recommendations.append(
                f"You're missing {len(missing_required)} required skill(s): {shown}"
                f"{', ...' if len(missing_required) > 5 else ''}"
            )
        if missing_preferred:
            shown = ", ".join(missing_preferred[:5])
            recommendations.append(
                f"Consider adding these preferred skills: {shown}"
                f"{', ...' if len(missing_preferred) > 5 else ''}"
            )
        if not missing_required and not missing_preferred:
            recommendations.append("Great match! All required and preferred skills are covered.")
        return recommendations