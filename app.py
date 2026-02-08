from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import sqlite3
import os
import json
from google import genai

client = genai.Client(api_key="AIzaSyCDPdZQDp7JyPCYq5QQdR0rJiO1jpkopRQ")



app = Flask(__name__)
CORS(app)

# SQLite for multi-user support
conn = sqlite3.connect("roadmaps.db", check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS roadmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    skill TEXT,
    roadmap TEXT
)
''')
conn.commit()

# Predefined fallback template
def fallback_roadmap(skill):
    return [
        f"Learn basics of {skill}",
        f"Explore intermediate {skill} concepts",
        f"Apply {skill} in a small project",
        f"Review & improve your {skill} skills",
        f"Keep practicing {skill}"
    ]

# Call LLM API
def call_LLM_api(prompt):
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )
    return response.text

    
@app.route("/generate", methods=["POST"])
def generate_roadmap():
    data = request.json
    skill = data.get("skill")
    user_id = data.get("user_id", "default_user")

    # Check if roadmap exists
    c.execute("SELECT roadmap FROM roadmaps WHERE user_id=? AND skill=?", (user_id, skill))
    result = c.fetchone()
    if result:
        print(eval(result[0]))

    # Construct prompt for LLM
    prompt = f"Generate an array of 5-6 clear UNNUMBERED steps to learn {skill} as a roadmap. \
    Create it as an array of steps (array of strings). Do not include Markdown formatting or code fences."

    # Call HF API
    generated_text = call_LLM_api(prompt)
    
    #steps = generated_text
    steps = json.loads(generated_text)
    if not generate_roadmap:
        steps = fallback_roadmap(skill)

    # Save to DB
    c.execute("INSERT INTO roadmaps (user_id, skill, roadmap) VALUES (?, ?, ?)", (user_id, skill, str(steps)))
    conn.commit()
    
    return jsonify({"roadmap": steps})

if __name__ == "__main__":
    app.run(debug=True)
