import streamlit as st
import sqlite3
import hashlib
import PyPDF2
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="AI Placement System", page_icon="🎓", layout="wide")

# ---------- DATABASE ----------
conn = sqlite3.connect("placement.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            resume TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            job_role TEXT,
            description TEXT)""")

conn.commit()

# ---------- PASSWORD HASH ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- PDF TEXT ----------
def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

def clean_text(text):
    text = re.sub(r'[^a-zA-Z ]', '', text)
    return text.lower()

# ---------- MENU ----------
st.title("🎓 AI-Integrated Placement Management System")

menu = st.sidebar.selectbox("Select Role", ["Student", "Company", "Admin"])

# ================= STUDENT =================
if menu == "Student":

    action = st.selectbox("Action", ["Register", "Login"])

    if action == "Register":
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

        if st.button("Register"):
            if resume_file:
                resume_text = extract_text_from_pdf(resume_file)
                c.execute("INSERT INTO students (name,email,password,resume) VALUES (?,?,?,?)",
                          (name, email, hash_password(password), resume_text))
                conn.commit()
                st.success("Registered Successfully ✅")

    elif action == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            c.execute("SELECT * FROM students WHERE email=? AND password=?",
                      (email, hash_password(password)))
            user = c.fetchone()

            if user:
                st.success("Login Successful ✅")
                st.write("Welcome,", user[1])
            else:
                st.error("Invalid Credentials ❌")

# ================= COMPANY =================
elif menu == "Company":

    action = st.selectbox("Action", ["Register", "Login"])

    if action == "Register":
        name = st.text_input("Company Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            c.execute("INSERT INTO companies (name,email,password) VALUES (?,?,?)",
                      (name, email, hash_password(password)))
            conn.commit()
            st.success("Company Registered ✅")

    elif action == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            c.execute("SELECT * FROM companies WHERE email=? AND password=?",
                      (email, hash_password(password)))
            company = c.fetchone()

            if company:
                st.success("Login Successful ✅")

                st.subheader("Post Job")
                job_role = st.text_input("Job Role")
                description = st.text_area("Job Description")

                if st.button("Post Job"):
                    c.execute("INSERT INTO jobs (company_name,job_role,description) VALUES (?,?,?)",
                              (company[1], job_role, description))
                    conn.commit()
                    st.success("Job Posted ✅")

            else:
                st.error("Invalid Credentials ❌")

# ================= ADMIN =================
elif menu == "Admin":

    st.subheader("Admin Dashboard")

    jobs = c.execute("SELECT * FROM jobs").fetchall()
    students = c.execute("SELECT * FROM students").fetchall()

    if jobs and students:

        job = st.selectbox("Select Job", jobs, format_func=lambda x: x[2])

        if st.button("Run AI Ranking"):

            jd_clean = clean_text(job[3])

            results = []

            for student in students:
                resume_clean = clean_text(student[4])

                documents = [resume_clean, jd_clean]

                vectorizer = TfidfVectorizer()
                tfidf_matrix = vectorizer.fit_transform(documents)

                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
                match_percentage = round(float(similarity[0][0]) * 100, 2)

                results.append({
                    "Student Name": student[1],
                    "Match Score (%)": match_percentage
                })

            df = pd.DataFrame(results)
            df = df.sort_values(by="Match Score (%)", ascending=False)

            st.subheader("📊 Ranking Results")
            st.dataframe(df)

    else:
        st.info("Add students and jobs first.")
