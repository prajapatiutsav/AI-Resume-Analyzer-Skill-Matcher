from flask import Flask, render_template, request
import os
import json
import pdfplumber
import pandas as pd
import uuid

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def load_skills():

    with open("skills.json") as f:
        data = json.load(f)

    return data["skills"]

def extract_text_from_pdf(file_path):

    text = ""

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text

    return text.lower()

def extract_skills(text, skills_list):

    found_skills = []

    for skill in skills_list:

        if skill.lower() in text:
            found_skills.append(skill)

    return list(set(found_skills))

def create_chart(found_skills, job_skills):

    plt.figure(figsize=(6,4))

    matched = len(found_skills)
    total = len(job_skills)

    missing = total - matched

    labels = ["Matched Skills", "Missing Skills"]
    values = [matched, missing]

    plt.pie(values, labels=labels, autopct='%1.0f%%', startangle=90)

    plt.title("Resume Skill Match Overview")

    filename = f"chart_{uuid.uuid4().hex}.png"
    chart_path = os.path.join("static", filename)

    plt.savefig(chart_path)
    plt.close()

    return chart_path

@app.route("/", methods=["GET", "POST"])
def index():

    match = None
    skills = []
    chart = None

    if request.method == "POST":

        file = request.files["resume"]
        job_description = request.form["job"].lower()

        if file:

            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            resume_text = extract_text_from_pdf(filepath)

            skills_list = load_skills()

            resume_skills = extract_skills(resume_text, skills_list)
            job_skills = extract_skills(job_description, skills_list)

            skills = list(set(resume_skills) & set(job_skills))

            if len(job_skills) > 0:
                match = round((len(skills) / len(job_skills)) * 100, 2)
            else:
                match = 0

            chart = create_chart(skills, job_skills)

    return render_template(
        "index.html",
        match=match,
        skills=skills,
        chart=chart
    )

if __name__ == "__main__":

    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    app.run(debug=True)