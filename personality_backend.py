from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os
import json
import re
from question import questions

# ---------------- LOAD ENV ----------------
load_dotenv(".env")

# ---------------- LLM ----------------

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7
)

# ---------------- BUILD QA ----------------
def build_qa_text(answers):
    qa_text = ""
    for i, (q, ans) in enumerate(zip(questions, answers)):
        qa_text += f"""
Question {i+1}: {q['question']}
Answer: {ans} - {q['options'][ans]}
"""
    return qa_text


# ---------------- STRONG JSON EXTRACTOR ----------------
def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None


# ---------------- VALIDATION ----------------
def validate_data(data):
    required_keys = [
        "career_matches",
        "universities",
        "futuristic_careers",
        "strengths",
        "skills",
        "top_skills",
        "academic",
        "exams",
        "scholarships"
    ]

    for key in required_keys:
        if key not in data or not isinstance(data[key], list):
            data[key] = []

    return data


# ---------------- MAIN FUNCTION ----------------
def generate_report_data(answers):
    qa_text = build_qa_text(answers)

    prompt = f"""
You are an expert career counselor.

Based on the student's answers:

{qa_text}

Generate a structured career report.

Return ONLY valid JSON in this format:

{{
  "career_matches": [{{"title": "...", "description": "..."}}],
  "universities": [{{"name": "...", "country": "..."}}],
  "futuristic_careers": [{{"title": "...", "description": "..."}}],
  "strengths": [{{"title": "..."}}],
  "skills": [{{"title": "...", "description": "..."}}],
  "top_skills": [{{"title": "..."}}],
  "academic": [{{"title": "...", "description": "..."}}],
  "exams": [{{"title": "...", "description": "..."}}],
  "scholarships": [{{"title": "...", "description": "..."}}]
}}

STRICT RULES:
- Output ONLY JSON
- No markdown
- No explanation
- Each list must have 6 items
"""

    # ---------------- RETRY SYSTEM ----------------
    for attempt in range(3):
        try:
            response = llm.invoke(prompt)
            raw_output = response.content.strip()

            # Remove markdown if present
            if raw_output.startswith("```"):
                raw_output = raw_output.replace("```json", "").replace("```", "").strip()

            json_text = extract_json(raw_output)

            if not json_text:
                raise ValueError("No JSON found")

            data = json.loads(json_text)

            # Validate structure
            data = validate_data(data)

            return data

        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed:", str(e))

    # ---------------- FINAL FALLBACK ----------------
    return get_fallback_data()


# ---------------- SMART FALLBACK ----------------
def get_fallback_data():
    return {
        "career_matches": [
            {
                "title": "Software Engineer",
                "description": "Strong analytical and problem-solving role."
            },
            {
                "title": "Data Analyst",
                "description": "Focus on interpreting data and trends."
            }
        ],
        "universities": [
            {"name": "Delhi University", "country": "India"},
            {"name": "IIT Delhi", "country": "India"}
        ],
        "futuristic_careers": [
            {
                "title": "AI Specialist",
                "description": "Work on intelligent systems."
            }
        ],
        "strengths": [
            {"title": "Analytical Thinking"},
            {"title": "Creativity"}
        ],
        "skills": [
            {
                "title": "Problem Solving",
                "description": "Ability to break complex problems."
            }
        ],
        "top_skills": [
            {"title": "Critical Thinking"}
        ],
        "academic": [
            {
                "title": "Focus on STEM subjects",
                "description": "Build strong fundamentals."
            }
        ],
        "exams": [
            {
                "title": "JEE",
                "description": "For engineering pathways."
            }
        ],
        "scholarships": [
            {
                "title": "Merit Scholarship",
                "description": "Based on academic excellence."
            }
        ]
    }