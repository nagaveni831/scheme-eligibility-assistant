import requests
from flask import Flask, render_template, request, jsonify
import json
import os
from dotenv import load_dotenv
load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

app = Flask(__name__)

# ---------- LOAD SCHEMES ----------
with open("schemes.json", "r") as f:
    schemes = json.load(f)
last_result = ""
# ---------- QUESTIONS ----------
questions = [
    "What is your age?",
    "What is your gender?",
    "Are you a student, employed, unemployed, or self-employed?",
    "What is your annual family income?"
]

keys = ["age","gender","job","income"]
sessions = {}

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- CHAT ----------
def classify_message(msg):

    msg = msg.lower()

    if any(w in msg for w in ["hi","hello","hey"]):
        return "greeting"

    if any(w in msg for w in ["women","female","girl","lady"]):
        return "gender"

    if any(w in msg for w in ["student","farmer","worker","youth","disabled","senior"]):
        return "category"

    if any(w in msg for w in ["under","below","less","within"]) and any(c.isdigit() for c in msg):
        return "income"

    if "list" in msg or "show" in msg or "give" in msg:
        return "list"

    if "eligibility" in msg:
        return "eligibility"

    return "ai"



def format_schemes(list_data):

    if not list_data:
        return "No schemes found."

    text = "<b>Matching Schemes:</b><br><br>"

    for s in list_data[:10]:
        text += f"""
<div style='padding:10px;margin-bottom:12px;background:#eef2ff;border-radius:10px'>
<b>{s['name']}</b><br>
State → {s['state']}<br>
Category → {s['category']}<br>
<a href="{s['apply']}" target="_blank">Apply Here</a>
</div>
"""
    return text



@app.route("/chat", methods=["POST"])
def chat():

    user = "default"
    msg = request.json["message"].lower()

    if user not in sessions:
        sessions[user] = {"step": -1, "data": {}}

    state = sessions[user]

    # ---------- START STATE ----------
    if state["step"] == -1:

        if msg in ["yes","ready","start","ok","sure"]:
            state["step"] = 0
            return jsonify({
                "reply": f"Great 👍 Let's begin.\n\n░░░░░░░░░░ 0%\n\n{questions[0]}"
            })
        else:
            return jsonify({
                "reply": "Please type 'ready' when you want to begin."
            })


    # ---------- QUESTION FLOW ----------
    if state["step"] < len(questions):

        state["data"][keys[state["step"]]] = msg
        state["step"] += 1

        if state["step"] < len(questions):

            progress = int((state["step"] / len(questions)) * 100)
            bar = "█" * (progress // 10) + "░" * (10 - progress // 10)

            return jsonify({
                "reply": f"{bar} {progress}%\n\n{questions[state['step']]}"
            })

        else:
            return jsonify({
                "reply": check(state["data"]) +
                "\n\nWould you like help applying for any of these schemes? (yes/no)"
            })


    # ---------- AFTER QUESTIONS → AI MODE ----------
    # ---------- AFTER QUESTIONS → SMART MODE ----------
    if state["step"] >= len(questions):

       intent = classify_message(msg)

    # YES / NO
       if msg in ["yes","yeah","y","ok","sure"]:
        return jsonify({
            "reply": "Great! 🎉<br><br>Please visit official portal and apply."
        })

       elif msg in ["no","nope","not now"]:
        return jsonify({
            "reply": "Alright 🙂 Come back anytime!"
        })
       elif intent == "gender":

          filtered = [s for s in schemes if "women" in s["category"].lower()
                or "girl" in s["category"].lower()]

          return jsonify({"reply": format_schemes(filtered)})
       elif intent == "category":

          filtered = [s for s in schemes if any(word in s["category"].lower() for word in msg.split())]

          return jsonify({"reply": format_schemes(filtered)})


       elif intent == "list":

        if not schemes:
          return jsonify({"reply":"No schemes available."})

        text = "<b>Available Schemes:</b><br><br>"

        for i, s in enumerate(schemes,1):
          text += f"""
       <div style='padding:10px;margin-bottom:12px;background:#eef2ff;border-radius:10px'>
       <b>{i}. {s['name']}</b><br>
       Category → {s['category']}<br>
       State → {s['state']}<br>
       <a href="{s['apply']}" target="_blank">Apply Here</a>
       </div>
        """

          return jsonify({"reply": text})

    # GREETING
       elif intent == "greeting":
        return jsonify({"reply":"Hello 👋 How can I help you?"})

    # LIST SCHEMES
       elif intent == "scheme_list":
        return jsonify({"reply": format_schemes(schemes)})

    # CATEGORY SCHEMES
       elif intent == "category":
        filtered = [s for s in schemes if msg in s["category"].lower()]
        return jsonify({"reply": format_schemes(filtered)})
      
       elif intent == "income":

          import re
          nums = re.findall(r"\d+", msg)

          if nums:
            income = int(nums[0])

            filtered = [s for s in schemes if income <= s["income_max"]]

            return jsonify({"reply": format_schemes(filtered)})

          return jsonify({"reply":"Please specify income like 200000 or 5lakh"})

    # ELIGIBILITY AGAIN
       elif intent == "eligibility":
           return jsonify({"reply": check(state["data"])})

    # AI QUESTIONS
       else:
        ai_reply = ask_ai(msg)
        return jsonify({"reply": ai_reply})

        


# ---------- ELIGIBILITY CHECK ----------
def check(data):

    try:
        income = int(data["income"])
    except:
        return "Please enter income in numbers only."

    job = data["job"].lower()
    gender = data.get("gender","").lower()

    ranked = []

    for s in schemes:

        score = 0
        reasons = []

        # ---------- INCOME MATCH ----------
        if income <= s.get("income_max",999999999):
            score += 40
            reasons.append("Income within limit")

        # ---------- JOB MATCH ----------
        scheme_job = s.get("job","any").lower()
        if scheme_job == job:
            score += 30
            reasons.append("Matches your occupation")

        elif scheme_job == "any":
            score += 15
            reasons.append("Open for all jobs")

        # ---------- GENDER MATCH ----------
        scheme_gender = s.get("gender","any").lower()
        if scheme_gender == gender:
            score += 20
            reasons.append("Gender eligible")

        # ---------- CATEGORY BONUS ----------
        if job in s.get("category","").lower():
            score += 10
            reasons.append("Relevant to your category")

        ranked.append((score, s, reasons))

    ranked.sort(reverse=True, key=lambda x: x[0])
    top = ranked[:10]

    if not top:
        return "No matching schemes found."

    # ---------- OUTPUT ----------
    text = "<b>Top Matching Schemes For You:</b><br><br>"

    for i,(score,s,reasons) in enumerate(top,1):

        reason_text = " + ".join(reasons) if reasons else "General eligibility"

        text += f"""
<div style='padding:12px;margin-bottom:15px;border-radius:12px;background:#f1f5ff;border-left:5px solid #2563eb;'>

<b>{i}. {s['name']}</b><br>

Relevance:
<span style="padding:4px 10px;border-radius:8px;
background:{
'#16a34a' if score>80 else '#2563eb' if score>60 else '#ea580c'
};
color:white;font-size:13px;font-weight:bold;">
{"Excellent" if score>80 else "Good" if score>60 else "Average"}
</span><br>

Reason → {reason_text}<br>

State: {s['state']}<br>
Category: {s['category']}<br>

<a href="{s['apply']}" target="_blank">Apply Here</a>

</div>
"""
    global last_result
    last_result = text
    return text + "<br><br><a href='/download'>Download PDF Report</a>"





# ---------- AI FUNCTION ----------
def ask_ai(question):

    try:

        # convert schemes database into readable text
        schemes_text = ""
        for s in schemes:
            schemes_text += f"""
Name: {s['name']}
Category: {s['category']}
State: {s['state']}
Income Limit: {s['income_max']}
"""
        prompt = f"""
You are a Government Scheme Expert Assistant.

STRICT OUTPUT FORMAT — FOLLOW EXACTLY:

1. First line → Scheme name + one line explanation.

2. Then sections in THIS ORDER:

<b>Key Aspects</b>
→ point
→ point

<b>Eligibility</b>
→ point
→ point

<b>Benefits</b>
→ point
→ point

<b>How to Apply</b>
1. Step one
2. Step two
3. Step three

<b>Extra Info</b>
→ point
→ point

RULES:
- Headings must be wrapped in <b> </b>
- Steps must be numbered
- Each point must be on new line
- Use simple language
- No markdown symbols
- No stars **
- No hashtags #
- Output must be clean HTML format

SCHEMES DATABASE:
{schemes_text}
user Question: 
{question}


"""
        models = [
        "meta-llama/llama-3-8b-instruct",
        "mistralai/mistral-7b-instruct",
        "google/gemma-7b-it"
        ]
    

        for model in models:
            

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=20
            )

            print("Status:", response.status_code)

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]

            else:
                print("Failed model:", model, response.text)

    except Exception as e:
            print("ERROR:", e)

    return "AI is currently unavailable. Try again later."

# ---------- RESET ----------
@app.route("/reset", methods=["POST"])
def reset():
    sessions.clear()
    return jsonify({"status":"reset"})


# ===== PASTE PDF ROUTE HERE =====

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
import io
import re

@app.route("/download")
def download_pdf():

    global last_result

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Government Scheme Report", styles["Title"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Generated by Eligibility Assistant", styles["Italic"]))
    elements.append(Spacer(1, 15))


    import html
    clean = html.escape(re.sub('<.*?>', '', last_result))


    for line in clean.split("\n"):
      if line.strip():
        elements.append(Paragraph(line.replace("&","&amp;"), styles["Normal"]))
        elements.append(Spacer(1, 6))


    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="scheme_report.pdf",
        mimetype="application/pdf"
    )


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)





