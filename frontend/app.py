"""
Career Kairos - AI Resume Matcher - Streamlit Frontend
========================================
This file is the ENTIRE user interface. It does not talk to the
database directly - it only ever talks to our FastAPI backend
(http://127.0.0.1:8000) over HTTP, using the `requests` library.

Big picture flow:
  1. User logs in or registers -> we get a JWT "access_token" back
     and store it in st.session_state (Streamlit's way of remembering
     things between reruns - more on this below).
  2. Every other request to the backend includes that token in an
     "Authorization: Bearer <token>" header, so the backend knows
     who is asking.
  3. Three tabs let the user: upload a resume, add a job, and run a
     match between a saved resume + saved job.

WHAT IS st.session_state?
Streamlit re-runs this entire script top-to-bottom every time the
user clicks something. Normal Python variables would reset every
time. st.session_state is a dictionary that Streamlit keeps alive
across those reruns - it's how we "remember" that someone is logged
in, what their token is, etc.
"""

import requests
import streamlit as st

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Career Kairos - AI Resume Matcher", page_icon="🧩", layout="wide")


# ----------------------------------------------------------------------
# SESSION STATE SETUP
# ----------------------------------------------------------------------
# This runs every rerun, but the `if key not in st.session_state` guard
# means we only ever SET these once - after that, Streamlit remembers
# whatever value they currently hold.
def init_session_state():
    defaults = {
        "token": None,       # the JWT string once logged in
        "user_email": None,  # just for displaying "Logged in as ..."
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ----------------------------------------------------------------------
# API HELPER
# ----------------------------------------------------------------------
# Every single network call in this app goes through this one function.
# Centralizing it means we only have to handle "backend is down" or
# "token expired" errors in ONE place instead of repeating try/except
# blocks everywhere.
def api_call(method, path, **kwargs):
    """
    Wraps requests.get/post/etc with consistent error handling.

    method: "get" or "post"
    path: e.g. "/auth/login" (gets appended to API_BASE)
    kwargs: passed straight through to requests (json=, data=, files=, headers=)

    Returns the parsed JSON response on success, or None on failure.
    On failure, it also shows a st.error() message, so calling code
    just needs to check `if result is None: return` and stop.
    """
    url = f"{API_BASE}{path}"
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Can't reach the backend. Is FastAPI running at "
            f"{API_BASE}? (Check your other terminal.)"
        )
        return None
    except requests.exceptions.Timeout:
        st.error("❌ The backend took too long to respond (timed out).")
        return None

    if response.status_code == 401:
        # Token missing/expired/invalid - the backend always uses 401
        # for auth failures. Kick the user back to the login screen.
        st.error("Your session expired. Please log in again.")
        st.session_state.token = None
        st.session_state.user_email = None
        st.rerun()
        return None

    if not response.ok:
        # Try to surface FastAPI's error detail message if there is one,
        # otherwise just show the raw status code.
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        st.error(f"❌ {detail}")
        return None

    if response.status_code == 204 or not response.content:
        return {}

    return response.json()


def auth_headers():
    """Every protected endpoint needs this header. Small helper so we
    don't retype it everywhere."""
    return {"Authorization": f"Bearer {st.session_state.token}"}


# ----------------------------------------------------------------------
# LOGIN / REGISTER SCREEN
# ----------------------------------------------------------------------
def show_login_page():
    st.title("🧩 Career Kairos - AI Resume Matcher")
    st.caption("Log in or create an account to continue.")

    login_tab, register_tab = st.tabs(["Log In", "Register"])

    # ---- LOG IN ----
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In", use_container_width=True)

        if submitted:
            if not email or not password:
                st.warning("Please fill in both fields.")
            else:
                # IMPORTANT: /auth/login expects OAuth2 FORM data, not JSON.
                # That means `data=` (form-encoded), not `json=`. The field
                # names the backend expects are "username" and "password"
                # even though "username" is actually the email address -
                # that's just how OAuth2PasswordRequestForm works.
                result = api_call(
                    "post",
                    "/auth/login",
                    data={"username": email, "password": password},
                )
                if result is not None:
                    st.session_state.token = result["access_token"]
                    st.session_state.user_email = email
                    st.rerun()

    # ---- REGISTER ----
    with register_tab:
        with st.form("register_form"):
            new_email = st.text_input("Email", key="register_email")
            new_password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input(
                "Confirm Password", type="password", key="register_confirm"
            )
            submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            if not new_email or not new_password:
                st.warning("Please fill in all fields.")
            elif new_password != confirm_password:
                st.warning("Passwords don't match.")
            else:
                # /auth/register expects JSON matching the UserCreate schema:
                # {"email": ..., "password": ...}
                result = api_call(
                    "post",
                    "/auth/register",
                    json={"email": new_email, "password": new_password},
                )
                if result is not None:
                    st.success("Account created! Please log in using the 'Log In' tab.")


# ----------------------------------------------------------------------
# TAB 1: RESUME UPLOAD
# ----------------------------------------------------------------------
def show_resume_tab():
    st.header("📄 Upload a Resume")
    st.caption("Accepted formats: PDF or DOCX")

    uploaded_file = st.file_uploader(
        "Choose a resume file", type=["pdf", "docx"], key="resume_uploader"
    )

    if uploaded_file is not None:
        if st.button("Parse & Save Resume", type="primary"):
            with st.spinner("Parsing resume..."):
                # `files=` tells requests to send this as multipart/form-data,
                # which is what FastAPI's UploadFile expects. The field name
                # MUST be "file" - that's the parameter name in resume_routes.py.
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type,
                    )
                }
                result = api_call(
                    "post",
                    "/resume/parse",
                    headers=auth_headers(),
                    files=files,
                )

            if result is not None:
                st.success(f"✅ Saved as resume #{result['resume_id']}: {result['filename']}")
                parsed = result["parsed_data"]

                with st.expander("📋 Parsed details", expanded=True):
                    st.markdown(f"**Summary:** {parsed.get('summary', 'N/A')}")

                    skills = parsed.get("skills", [])
                    if skills:
                        st.markdown("**Detected skills:**")
                        st.write(", ".join(skills))

                    experience = parsed.get("experience")
                    if experience:
                        st.markdown("**Experience:**")
                        st.write(experience)

                    education = parsed.get("education")
                    if education:
                        st.markdown("**Education:**")
                        st.write(education)

    st.divider()
    st.subheader("Your Saved Resumes")
    show_resume_list()


def show_resume_list():
    resumes = api_call("get", "/resume/list", headers=auth_headers())
    if resumes is None:
        return
    if not resumes:
        st.info("No resumes uploaded yet.")
        return

    for r in resumes:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**#{r['id']} — {r['filename']}**")
                if r.get("summary"):
                    st.caption(r["summary"])
                if r.get("skills"):
                    st.caption("Skills: " + ", ".join(r["skills"]))
            with col2:
                st.caption(str(r.get("created_at", ""))[:10])


# ----------------------------------------------------------------------
# TAB 2: JOB INPUT
# ----------------------------------------------------------------------
def show_job_tab():
    st.header("💼 Add a Job")

    text_tab, url_tab = st.tabs(["📋 Paste Job Text (recommended)", "🔗 Scrape from URL"])

    # ---- PASTE TEXT (primary/reliable path) ----
    with text_tab:
        st.caption("Paste the full job description text below. This is the most reliable option.")
        job_text = st.text_area("Job description", height=250, key="job_text_input")

        if st.button("Parse Job Text", type="primary", key="parse_text_btn"):
            if not job_text.strip():
                st.warning("Please paste some job description text first.")
            else:
                with st.spinner("Parsing job description..."):
                    result = api_call(
                        "post",
                        "/job/parse-text",
                        headers=auth_headers(),
                        json={"text": job_text},
                    )
                if result is not None:
                    st.success(f"✅ Saved as job #{result['job_id']}")
                    show_parsed_job(result["parsed_data"])

    # ---- URL SCRAPE (secondary, may fail) ----
    with url_tab:
        st.warning(
            "⚠️ Scraping may not work reliably on all job sites "
            "(LinkedIn, Indeed, etc. often block scrapers). "
            "If it fails, copy the job text and use the 'Paste Job Text' tab instead."
        )
        job_url = st.text_input("Job posting URL", key="job_url_input")

        if st.button("Scrape Job", key="scrape_btn"):
            if not job_url.strip():
                st.warning("Please enter a URL first.")
            else:
                with st.spinner("Scraping job posting..."):
                    result = api_call(
                        "post",
                        "/job/scrape",
                        headers=auth_headers(),
                        json={"url": job_url},
                    )
                if result is not None:
                    st.success(f"✅ Saved as job #{result['job_id']}")
                    show_parsed_job(result["parsed_data"])

    st.divider()
    st.subheader("Your Saved Jobs")
    show_job_list()


def show_parsed_job(parsed):
    with st.expander("📋 Parsed details", expanded=True):
        if parsed.get("summary"):
            st.markdown(f"**Summary:** {parsed['summary']}")
        if parsed.get("required_skills"):
            st.markdown("**Required skills:**")
            st.write(", ".join(parsed["required_skills"]))
        if parsed.get("preferred_skills"):
            st.markdown("**Preferred skills:**")
            st.write(", ".join(parsed["preferred_skills"]))


def show_job_list():
    jobs = api_call("get", "/job/list", headers=auth_headers())
    if jobs is None:
        return
    if not jobs:
        st.info("No jobs added yet.")
        return

    for j in jobs:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                label = j.get("url") or "(pasted text)"
                st.markdown(f"**#{j['id']} — {label}**")
                if j.get("summary"):
                    st.caption(j["summary"])
                if j.get("required_skills"):
                    st.caption("Required: " + ", ".join(j["required_skills"]))
                if j.get("preferred_skills"):
                    st.caption("Preferred: " + ", ".join(j["preferred_skills"]))
            with col2:
                st.caption(str(j.get("created_at", ""))[:10])


# ----------------------------------------------------------------------
# TAB 3: MATCH
# ----------------------------------------------------------------------
def show_match_tab():
    st.header("🎯 Match Resume to Job")

    resumes = api_call("get", "/resume/list", headers=auth_headers())
    jobs = api_call("get", "/job/list", headers=auth_headers())

    if resumes is None or jobs is None:
        return

    if not resumes or not jobs:
        st.info("You need at least one saved resume AND one saved job before you can run a match.")
        return

    # Build dropdown options as "id - friendly label" so the user can
    # tell entries apart, then map the chosen label back to an id.
    resume_options = {f"#{r['id']} — {r['filename']}": r["id"] for r in resumes}
    job_options = {
        f"#{j['id']} — {j.get('url') or 'pasted text'}": j["id"] for j in jobs
    }

    col1, col2 = st.columns(2)
    with col1:
        resume_label = st.selectbox("Select Resume", options=list(resume_options.keys()))
    with col2:
        job_label = st.selectbox("Select Job", options=list(job_options.keys()))

    method = st.radio(
        "Matching method",
        options=["hybrid", "tfidf", "keyword"],
        horizontal=True,
        help="Hybrid combines both approaches and is recommended for most cases.",
    )

    if st.button("Run Match", type="primary"):
        resume_id = resume_options[resume_label]
        job_id = job_options[job_label]

        with st.spinner("Matching..."):
            result = api_call(
                "post",
                "/match/",
                headers=auth_headers(),
                json={"resume_id": resume_id, "job_id": job_id, "method": method},
            )

        if result is not None:
            display_match_result(result)

    st.divider()
    st.subheader("Match History")
    show_match_history()


def display_match_result(result):
    match_result = result["match_result"]
    score = match_result.get("match_score", 0)

    st.subheader(f"Result: {result['resume_filename']} ↔ {result['job_url'] or 'pasted job'}")

    # Color-code the score for quick visual feedback.
    if score >= 75:
        st.success(f"### Match Score: {score}%")
    elif score >= 50:
        st.warning(f"### Match Score: {score}%")
    else:
        st.error(f"### Match Score: {score}%")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Your skills:**")
        st.write(", ".join(result.get("resume_skills", [])) or "None detected")
    with col2:
        st.markdown("**Job requires:**")
        st.write(", ".join(result.get("job_required_skills", [])) or "None listed")

    missing_required = match_result.get("missing_required_skills", [])
    missing_preferred = match_result.get("missing_preferred_skills", [])

    if missing_required:
        st.markdown("**❌ Missing required skills:**")
        st.write(", ".join(missing_required))
    if missing_preferred:
        st.markdown("**⚠️ Missing preferred skills:**")
        st.write(", ".join(missing_preferred))

    recommendations = result.get("recommendations")
    if recommendations:
        st.markdown("**💡 Recommendations:**")
        if isinstance(recommendations, list):
            for rec in recommendations:
                st.write(f"- {rec}")
        else:
            st.write(recommendations)


def show_match_history():
    history = api_call("get", "/match/history", headers=auth_headers())
    if history is None:
        return
    if not history:
        st.info("No matches run yet.")
        return

    for h in history:
        score = h.get("match_result", {}).get("match_score", h.get("match_score", "N/A"))
        label = f"#{h.get('match_id', h.get('id', '?'))} — Score: {score}%"
        with st.expander(label):
            st.json(h)


# ----------------------------------------------------------------------
# MAIN APP (shown only when logged in)
# ----------------------------------------------------------------------
def show_main_app():
    with st.sidebar:
        st.markdown(f"**Logged in as:**\n{st.session_state.user_email}")
        if st.button("Log Out", use_container_width=True):
            st.session_state.token = None
            st.session_state.user_email = None
            st.rerun()

    st.title("🧩 Career Kairos - AI Resume Matcher")

    tab1, tab2, tab3 = st.tabs(["📄 Resume", "💼 Job", "🎯 Match"])
    with tab1:
        show_resume_tab()
    with tab2:
        show_job_tab()
    with tab3:
        show_match_tab()


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------
if st.session_state.token is None:
    show_login_page()
else:
    show_main_app()
