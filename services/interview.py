"""Interview coach: 20 practice questions + AI feedback in easy English.
The coach never writes a full answer for the student and always says: answer truthfully."""
import json
import random
import re

from . import llm

QUESTIONS = [
    {"id": 1, "cat": "Study plan", "q": "Why do you want to study in the UK?",
     "tip": "Give 2 or 3 real reasons: the course quality, the subject, what you want to learn.",
     "kw": ["course", "quality", "learn", "subject", "university"]},
    {"id": 2, "cat": "Study plan", "q": "Why did you choose this university?",
     "tip": "Name something real: a department, a module, a teacher, a lab, its ranking for your subject.",
     "kw": ["university", "module", "department", "research", "ranking"]},
    {"id": 3, "cat": "Study plan", "q": "Why did you choose this course?",
     "tip": "Link the course to your past study and your future job.",
     "kw": ["course", "background", "career", "skills", "interest"]},
    {"id": 4, "cat": "Study plan", "q": "Tell me about the modules you will study.",
     "tip": "Name 3 to 4 modules from your course page and say what each teaches.",
     "kw": ["module", "semester", "year", "learn", "project"]},
    {"id": 5, "cat": "Money", "q": "How will you pay for your tuition fees and living costs?",
     "tip": "Say who pays, how much, and where the money is. Your answer must match your documents.",
     "kw": ["tuition", "living", "savings", "sponsor", "bank", "parents"]},
    {"id": 6, "cat": "Money", "q": "Who is paying for your studies, and what do they do?",
     "tip": "Say the name, the relationship and the work or business of your sponsor. Be exact.",
     "kw": ["father", "mother", "sponsor", "business", "job", "income"]},
    {"id": 7, "cat": "Money", "q": "How much are your tuition fees and how much have you paid?",
     "tip": "Know the exact numbers from your CAS and your receipt.",
     "kw": ["fees", "paid", "deposit", "cas", "pounds", "remaining"]},
    {"id": 8, "cat": "Future", "q": "What are your plans after you finish the course?",
     "tip": "Give a clear plan: the job, the type of company, the skills you will use.",
     "kw": ["plan", "career", "job", "return", "skills", "company"]},
    {"id": 9, "cat": "Future", "q": "Do you plan to return to Pakistan after your studies? Why?",
     "tip": "Be honest. Talk about your family, work chances and goals at home.",
     "kw": ["return", "pakistan", "family", "career", "opportunity"]},
    {"id": 10, "cat": "Study plan", "q": "Why not study this course in Pakistan?",
     "tip": "Explain what the UK course offers that you cannot get at home. Do not speak badly about Pakistan.",
     "kw": ["different", "opportunity", "quality", "facilities", "research", "experience"]},
    {"id": 11, "cat": "Background", "q": "Tell me about your education so far.",
     "tip": "Go in order: school, college, university, with years and grades.",
     "kw": ["school", "college", "degree", "year", "grade", "cgpa"]},
    {"id": 12, "cat": "Background", "q": "Do you have any gap in your studies? Please explain.",
     "tip": "Tell the true reason and show what you did in that time (work, courses, family).",
     "kw": ["gap", "work", "course", "reason", "experience"]},
    {"id": 13, "cat": "Life in UK", "q": "Where will you live in the UK?",
     "tip": "Say if you have university housing or a private plan, the area and the rough cost.",
     "kw": ["accommodation", "hall", "rent", "area", "city", "cost"]},
    {"id": 14, "cat": "Life in UK", "q": "Do you have family or friends in the UK?",
     "tip": "Answer truthfully. If yes, say who and where. If no, say you will use university support.",
     "kw": ["family", "friend", "relative", "city", "support"]},
    {"id": 15, "cat": "Background", "q": "Have you travelled or studied abroad before? Have you ever been refused a visa?",
     "tip": "Always tell the truth. Hiding a refusal is much worse than telling it.",
     "kw": ["travel", "visa", "refused", "country", "never", "before"]},
    {"id": 16, "cat": "Background", "q": "Tell me about your English test. How did you prepare?",
     "tip": "Know your scores and test date. Say how you practised.",
     "kw": ["ielts", "score", "band", "prepare", "practice", "test"]},
    {"id": 17, "cat": "Life in UK", "q": "Do you plan to work while you study? What are the rules?",
     "tip": "Know the work-hour limit on your visa. Say your main goal is to study.",
     "kw": ["work", "hours", "part-time", "limit", "study", "visa"]},
    {"id": 18, "cat": "Life in UK", "q": "Where is the university and what do you know about the city?",
     "tip": "Say the city, how you will travel there, and one or two things you learned about it.",
     "kw": ["city", "location", "transport", "near", "campus"]},
    {"id": 19, "cat": "Future", "q": "What career do you want and how does this course help?",
     "tip": "Name the job and link 2 skills from the course to it.",
     "kw": ["career", "job", "skills", "course", "industry", "goal"]},
    {"id": 20, "cat": "Study plan", "q": "Is the course worth the cost to you? Why?",
     "tip": "Show you thought about it: what you gain in skills and job chances compared with the cost.",
     "kw": ["cost", "worth", "value", "skills", "career", "investment"]},
]

CATEGORIES = sorted({q["cat"] for q in QUESTIONS})


def get_question(qid: int) -> dict:
    return next(q for q in QUESTIONS if q["id"] == qid)


def random_questions(n: int = 5, seed=None) -> list:
    rng = random.Random(seed)
    return rng.sample(QUESTIONS, min(n, len(QUESTIONS)))


def _fallback(question: dict, answer: str) -> dict:
    words = len(answer.split())
    low = answer.lower()
    hits = sum(1 for k in question["kw"] if k in low)
    score = 2 if words < 15 else 4 if words < 40 else 6 if words <= 150 else 5
    score = min(10, score + min(hits, 3))
    good, improve = [], []
    if words >= 40:
        good.append("Your answer has enough detail.")
    else:
        improve.append("Add more detail. Aim for 40 to 100 words (about 20 to 40 seconds).")
    if hits >= 2:
        good.append("You touched the key points.")
    else:
        improve.append("Cover the key points: " + question["tip"])
    if words > 150:
        improve.append("Make it shorter. Officers like clear and direct answers.")
    return {"score": score, "good": good, "improve": improve,
            "tip": "Always answer truthfully and give numbers that match your documents.", "source": "basic"}


def evaluate_answer(question: dict, answer: str, language: str = "en") -> dict:
    answer = (answer or "").strip()
    if len(answer) < 5:
        return {"score": 0, "good": [], "improve": ["Please write your answer first."], "tip": "", "source": "basic"}
    lang = "simple Urdu" if language == "ur" else "very easy English"
    prompt = (
        f"Visa interview question: {question['q']}\n"
        f"What a good answer should include: {question['tip']}\n"
        f"Student answer: {llm.redact(answer)[:1500]}\n\n"
        f"Give feedback in {lang}. Return ONLY JSON like "
        '{"score": 0-10, "good": ["..."], "improve": ["..."], "tip": "..."} '
        "with at most 3 items in good and in improve. Rules: Be kind and clear. "
        "Do NOT write a new answer for the student. Do NOT suggest inventing facts. "
        "Remind them to be truthful. Keep every sentence under 18 words."
    )
    out = llm.chat(
        [{"role": "system", "content": "You are a friendly interview coach for students. You never promise visa results."},
         {"role": "user", "content": prompt}],
        max_tokens=450, temperature=0.3,
    )
    if out:
        m = re.search(r"\{.*\}", out, re.S)
        try:
            data = json.loads(m.group(0)) if m else None
            if isinstance(data, dict) and isinstance(data.get("score"), (int, float)):
                return {
                    "score": max(0, min(10, int(data["score"]))),
                    "good": [str(x) for x in data.get("good", [])][:3],
                    "improve": [str(x) for x in data.get("improve", [])][:3],
                    "tip": str(data.get("tip", "")),
                    "source": "ai",
                }
        except (ValueError, TypeError):
            pass
    return _fallback(question, answer)