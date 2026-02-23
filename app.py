# ============================================================
# COMPLETE RESUME SCREENING ATS - REAL TIME & MULTI-ROLE
# ============================================================

import streamlit as st
st.set_page_config(page_title="Resume Screening ATS", layout="wide")

import sqlite3
import os
import re
import pandas as pd
import altair as alt
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

DB_FILE = "resume_portal.db"
FORMAT_DIR = "resume_formats"
RESUME_DIR = "candidate_resumes"

os.makedirs(FORMAT_DIR, exist_ok=True)
os.makedirs(RESUME_DIR, exist_ok=True)

SKILLS = [
    "python", "sql", "excel", "tableau", "power bi", "aws",
    "docker", "java", "git", "spark", "numpy", "pandas",
    "machine learning", "deep learning", "html", "css", "javascript"
]

# ============================================================
# DATABASE HELPERS
# ============================================================

def db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def columns(conn, table):
    return [c[1] for c in conn.execute(f"PRAGMA table_info({table})")]

def ensure_column(conn, table, col, dtype="TEXT"):
    if col not in columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}")

# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    conn = db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        created_at TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_title TEXT,
        job_desc TEXT,
        created_by TEXT,
        timestamp TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS screening_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        job_title TEXT,
        resume_name TEXT,
        match_score REAL,
        weighted_score REAL,
        skills TEXT,
        experience_years REAL,
        timestamp TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS resume_formats (
        id INTEGER PRIMARY KEY AUTOINCREMENT
    )
    """)

    # Auto migrate columns for resume_formats
    for col in ["title", "filename", "uploaded_by", "timestamp"]:
        ensure_column(conn, "resume_formats", col)

    conn.commit()
    conn.close()

def seed_users():
    conn = db()
    users = [
        ("super_admin", "root123", "Super Admin"),
        ("hr_admin", "admin123", "HR"),
        ("agent1", "agent123", "Agent"),
        ("candidate1", "pass123", "Candidate")
    ]
    for u, p, r in users:
        conn.execute("""
        INSERT OR IGNORE INTO users
        (username,password,role,created_at)
        VALUES (?,?,?,?)
        """, (u, p, r, datetime.now().isoformat()))
    conn.commit()
    conn.close()

init_db()
seed_users()

# ============================================================
# NLP / SCORING LOGIC
# ============================================================

def clean_text(text):
    return " ".join(re.findall(r"[a-zA-Z0-9]+", text.lower()))

def similarity_score(jd, resume):
    jd_words = set(clean_text(jd).split())
    rs_words = set(clean_text(resume).split())
    if not jd_words:
        return 0.0
    return round(len(jd_words & rs_words) / len(jd_words) * 100, 2)

def extract_skills(text):
    t = text.lower()
    return [s for s in SKILLS if s in t]

def extract_experience(text):
    yrs = re.findall(r"(\d+)\s*(years|yrs)", text.lower())
    return max([int(y[0]) for y in yrs], default=0)

# ============================================================
# SESSION STATE
# ============================================================

if "logged" not in st.session_state:
    st.session_state.logged = False

# ============================================================
# LOGIN / REGISTER
# ============================================================

st.title("🎯 Resume Screening ATS")

if not st.session_state.logged:
    login_tab, register_tab = st.tabs(["Login", "Candidate Register"])

    with login_tab:
        user = st.text_input("Username", key="login_user")
        pwd = st.text_input("Password", type="password", key="login_pwd")
        if st.button("Login"):
            conn = db()
            r = conn.execute(
                "SELECT role FROM users WHERE username=? AND password=?",
                (user, pwd)
            ).fetchone()
            conn.close()
            if r:
                st.session_state.logged = True
                st.session_state.user = user
                st.session_state.role = r[0]
                st.rerun()
            else:
                st.error("Invalid credentials")

    with register_tab:
        st.subheader("Candidate Registration")
        new_user = st.text_input("New Username", key="reg_user")
        new_pwd = st.text_input("New Password", type="password", key="reg_pwd")
        if st.button("Register"):
            if new_user and new_pwd:
                conn = db()
                exists = conn.execute(
                    "SELECT * FROM users WHERE username=?", (new_user,)
                ).fetchone()
                if exists:
                    st.error("Username already exists")
                else:
                    conn.execute(
                        "INSERT INTO users (username,password,role,created_at) VALUES (?,?,?,?)",
                        (new_user, new_pwd, "Candidate", datetime.now().isoformat())
                    )
                    conn.commit()
                    st.success("Candidate registered successfully")
                conn.close()
            else:
                st.warning("Enter username and password")
    st.stop()

# ============================================================
# SIDEBAR AND LOGOUT
# ============================================================

st.sidebar.markdown(f"👤 **{st.session_state.user}**")
st.sidebar.markdown(f"🔐 **{st.session_state.role}**")

if st.sidebar.button("Logout"):
    st.session_state.logged = False
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()

menu = [
    "Dashboard",
    "HR: Job Postings",
    "Screening",
    "Resume Formats (Manage)",
    "Notifications Panel",
    "Change Password",
    "Profile"
]
page = st.sidebar.radio("Navigation", menu)

# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":
    conn = db()
    st.metric("Jobs Posted", pd.read_sql("SELECT * FROM jobs", conn).shape[0])
    st.metric("Applications", pd.read_sql("SELECT * FROM screening_results", conn).shape[0])
    conn.close()

# ============================================================
# JOB POSTINGS
# ============================================================

elif page == "HR: Job Postings" and st.session_state.role in ["HR", "Super Admin"]:
    st.header("Create Job Posting")
    title = st.text_input("Job Title")
    desc = st.text_area("Job Description", height=200)
    if st.button("Post Job"):
        conn = db()
        conn.execute("""
        INSERT INTO jobs (job_title,job_desc,created_by,timestamp)
        VALUES (?,?,?,?)
        """, (title, desc, st.session_state.user, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        st.success("Job Posted Successfully")

# ============================================================
# SCREENING
# ============================================================

elif page == "Screening" and st.session_state.role in ["HR", "Super Admin", "Agent"]:
    conn = db()
    jobs = pd.read_sql("SELECT * FROM jobs", conn)
    conn.close()

    if jobs.empty:
        st.warning("No jobs available")
        st.stop()

    job_id = st.selectbox(
        "Select Job",
        jobs.job_id,
        format_func=lambda x: jobs[jobs.job_id == x].job_title.iloc[0]
    )

    threshold = st.slider("Shortlisting Threshold (%)", 0, 100)

    jd = jobs[jobs.job_id == job_id].job_desc.iloc[0]
    files = st.file_uploader("Upload Resumes", accept_multiple_files=True)

    if st.button("Run Screening"):
        conn = db()

        # Clear old results for this job
        conn.execute(
            "DELETE FROM screening_results WHERE job_title=?",
            (jobs[jobs.job_id == job_id].job_title.iloc[0],)
        )
        conn.commit()

        for f in files:
            text = f.getvalue().decode(errors="ignore")
            score = similarity_score(jd, text)

            conn.execute("""
            INSERT INTO screening_results
            (username,job_title,resume_name,match_score,
             weighted_score,skills,experience_years,timestamp)
            VALUES (?,?,?,?,?,?,?,?)
            """, (
                st.session_state.user,
                jobs[jobs.job_id == job_id].job_title.iloc[0],
                f.name,
                score,
                score,
                ", ".join(extract_skills(text)),
                extract_experience(text),
                datetime.now().isoformat()
            ))

        conn.commit()

        df = pd.read_sql("""
        SELECT resume_name, weighted_score
        FROM screening_results
        WHERE job_title=?
        """, conn, params=(jobs[jobs.job_id == job_id].job_title.iloc[0],))
        conn.close()

        df["status"] = df["weighted_score"].apply(
            lambda x: "Shortlisted" if x >= threshold else "Rejected"
        )

        st.subheader("📊 Ranking Bar Chart")
        st.altair_chart(
            alt.Chart(df).mark_bar().encode(
                x=alt.X("weighted_score:Q", title="Score"),
                y=alt.Y("resume_name:N", sort="-x"),
                color="status:N"
            ),
            use_container_width=True
        )

        st.subheader("📊 Status Pie Chart")
        pie = df["status"].value_counts().reset_index()
        pie.columns = ["status", "count"]
        st.altair_chart(
            alt.Chart(pie).mark_arc().encode(
                theta="count:Q", color="status:N"
            ),
            use_container_width=True
        )

        st.subheader("✅ Shortlisted Candidates")
        st.dataframe(df[df["weighted_score"] >= threshold])

# ============================================================
# RESUME FORMATS
# ============================================================

elif page == "Resume Formats (Manage)" and st.session_state.role in ["HR", "Super Admin"]:
    st.header("Upload Resume Format")
    title = st.text_input("Format Title")
    f = st.file_uploader("Upload Format")
    if f and st.button("Upload"):
        with open(os.path.join(FORMAT_DIR, f.name), "wb") as out:
            out.write(f.getbuffer())

        conn = db()
        conn.execute("""
        INSERT INTO resume_formats
        (title,filename,uploaded_by,timestamp)
        VALUES (?,?,?,?)
        """, (title, f.name, st.session_state.user, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        st.success("Format Uploaded Successfully")

# ============================================================
# NOTIFICATIONS
# ============================================================

elif page == "Notifications Panel":
    df = pd.read_sql("""
    SELECT job_title, resume_name, weighted_score
    FROM screening_results
    ORDER BY timestamp DESC
    """, db())
    st.dataframe(df)

# ============================================================
# CHANGE PASSWORD
# ============================================================

elif page == "Change Password":
    st.header("Change Password")
    old = st.text_input("Old Password", type="password")
    new = st.text_input("New Password", type="password")
    if st.button("Update Password"):
        conn = db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (st.session_state.user, old)
        )
        if cur.fetchone():
            cur.execute(
                "UPDATE users SET password=? WHERE username=?",
                (new, st.session_state.user)
            )
            conn.commit()
            st.success("Password Updated")
        else:
            st.error("Old password incorrect")
        conn.close()

# ============================================================
# PROFILE
# ============================================================

elif page == "Profile":
    df = pd.read_sql(
        "SELECT username, role, created_at FROM users WHERE username=?",
        db(),
        params=(st.session_state.user,)
    )
    st.table(df)
