# evaluator.py
# analyze() takes a fresh submission dict and returns LLM scores + feedback.
# socratic_questions is returned as a Python list[str] — caller handles serialization.
# On API failure: retry up to 3 times with 15s wait, then return {"error": str(e)}

import os
from dotenv import load_dotenv
import time
import json
from groq import Groq

load_dotenv(override=True)
client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are a rigorous quantitative finance mentor evaluating 
market intuition journal entries. Be tough and specific — not encouraging.

Return ONLY valid JSON with exactly these keys:
{
    "score": <int 1-10>,
    "assessment": <string>
}

Scoring rubric (synthesize into one score):
- causality: is the why mechanistically sound, beyond surface correlation?
- signal_specificity: is the signal concrete, falsifiable, implementable — or vague?
- contrarian_thinking: did they consider the other side, tail risks, what consensus missed?
- conciseness: is the view tight and precise, or rambling and hedged?

Include in the assessment what the analysis should be
"""

def build_user_prompt(entry: dict, history: list, news: str, price_summary: str) -> str:
    string_builder = "My analysis:\n"
    for k, v in entry.items():
        if k in ['id', 'date']: continue
        string_builder += f"{k}: {v}\n"
    string_builder += "Last 3 History Scores by date: \n"
    for his in history[:3]:
        string_builder += f"- {his['date']}: {his['score']}\n"
    string_builder += f"News: {news}\nPrice Summary: {price_summary}"
    return string_builder

def analyze(entry: dict, history: list, news: str, price_summary: str) -> dict:
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            user_prompt = build_user_prompt(entry, history, news, price_summary)
            completion = client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            return json.loads(completion.choices[0].message.content)
        
        except Exception as e:
            if attempt == max_attempts:
                print("All retries exhausted. Throwing final error.")
                return {'error': str(e)}
            time.sleep(15)
