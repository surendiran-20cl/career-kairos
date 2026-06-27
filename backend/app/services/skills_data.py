"""
A curated list of common professional/technical skills used to scan
resume and job description text. This is intentionally a plain Python
list (not a fancy ML model) so it's easy to read, easy to extend, and
easy to explain in an interview: "I used a curated taxonomy plus an
NLP fallback for anything not in the list."

Feel free to add more terms relevant to the kinds of jobs you're
targeting with this project.
"""

SKILLS_TAXONOMY = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c",
    "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
    "r", "matlab", "perl", "sql", "bash", "shell scripting",

    # Web / frontend
    "html", "css", "react", "react.js", "vue", "vue.js", "angular",
    "next.js", "svelte", "tailwind css", "bootstrap", "redux",
    "jquery", "webpack", "sass",

    # Backend frameworks
    "fastapi", "flask", "django", "express.js", "spring boot",
    "node.js", "ruby on rails", ".net", "asp.net", "graphql", "rest api",
    "grpc",

    # Databases
    "postgresql", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
    "oracle", "dynamodb", "cassandra", "firebase", "supabase",

    # Cloud / DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "terraform", "ansible", "jenkins", "ci/cd", "github actions",
    "gitlab ci", "nginx", "linux", "cloudformation",

    # Data / ML / AI
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "data science", "data analysis", "data engineering",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "spacy", "opencv", "tableau", "power bi", "spark", "hadoop",
    "etl", "data visualization", "statistics", "a/b testing",

    # Tools / practices
    "git", "github", "gitlab", "jira", "agile", "scrum", "kanban",
    "unit testing", "test driven development", "tdd", "microservices",
    "api development", "object oriented programming", "oop",
    "system design", "ci", "cd", "postman", "figma",

    # Soft / general (kept short on purpose, hard to scan from text reliably)
    "leadership", "communication", "project management", "problem solving",
    "team collaboration",
]


def normalize(text: str) -> str:
    """Lowercase and strip text for consistent matching."""
    return text.lower().strip()


# A normalized lookup set for fast matching against resume/job text.
SKILLS_SET = {normalize(skill) for skill in SKILLS_TAXONOMY}