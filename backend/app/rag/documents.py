import json

def load_portfolio(
    file_path: str = "data/portfolio.json"
) -> dict:

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def create_documents(
    file_path: str = "data/portfolio.json"
) -> list[dict]:

    portfolio = load_portfolio(file_path)

    documents = []

    # Personal information
    personal = portfolio.get("personal", {})

    documents.append({
        "text": (
            f"Name: {personal.get('name', '')}\n"
            f"Email: {personal.get('email', '')}\n"
            f"Location: {personal.get('location', '')}\n"
            f"LinkedIn: {personal.get('linkedin', '')}\n"
            f"GitHub: {personal.get('github', '')}"
        ),
        "category": "personal"
    })

    # Education
    for education in portfolio.get("education", []):

        text = (
            f"Education:\n"
            f"Degree: {education.get('degree', '')}\n"
            f"Institution: {education.get('institution', '')}\n"
            f"Location: {education.get('location', '')}\n"
            f"Start Year: {education.get('start_year', '')}\n"
            f"End Year: {education.get('end_year', '')}\n"
            f"CGPA: {education.get('cgpa', '')}\n"
            f"Relevant Coursework: "
            f"{', '.join(education.get('relevant_coursework', []))}"
        )

        documents.append({
            "text": text,
            "category": "education"
        })

    # Experience
    for experience in portfolio.get("experience", []):

        description = "\n".join(
            f"- {item}"
            for item in experience.get("description", [])
        )

        text = (
            f"Suryansh Gupta's professional experience.\n"
            f"This document describes an internship and professional "
            f"work experience.\n\n"
            f"Company: {experience.get('company', '')}\n"
            f"Role: {experience.get('role', '')}\n"
            f"Location: {experience.get('location', '')}\n"
            f"Start Date: {experience.get('start_date', '')}\n"
            f"End Date: {experience.get('end_date', '')}\n\n"
            f"Internship experience:\n"
            f"{description}"
        )

        documents.append({
            "text": text,
            "category": "experience",
            "company": experience.get("company", ""),
            "role": experience.get("role", "")
        })

    # Projects
    for project in portfolio.get("projects", []):
        technologies = ", ".join(project.get("technologies", []))

        text = (
            f"Suryansh Gupta's technical project.\n"
            f"This document describes one of his software, "
            f"machine learning, NLP, or AI projects.\n\n"

            f"Project Name: {project.get('name', '')}\n"
            f"Description: {project.get('description', '')}\n"
            f"Technologies Used: {technologies}\n"
            f"GitHub: {project.get('github', '')}"
        )

        documents.append({
            "text": text,
            "category": "project",
            "project_name": project.get("name", "")
        })

    # Skills
    skills = portfolio.get("skills", [])

    if skills:
        skills_text = ", ".join(skills)
        documents.append({
            "text": (
            "Suryansh Gupta's technical skills and technologies.\n"
            "He has experience and familiarity with the following "
            "technical areas, tools, frameworks, and technologies:\n\n"
            f"{skills_text}"
            ),
            "category": "skills"
        })

    # Achievements
    for achievement in portfolio.get("achievements", []):

        documents.append({
            "text": f"Achievement: {achievement}",
            "category": "achievement"
        })

    # Certifications
    for certification in portfolio.get("certifications", []):

        documents.append({
            "text": f"Certification: {certification}",
            "category": "certification"
        })

    # Summary
    summary = portfolio.get("summary", "")

    if summary:

        documents.append({
            "text": f"Professional Summary:\n{summary}",
            "category": "summary"
        })

    return documents