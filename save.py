import json
import os
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types

CHAT_JSON_FILE = "system_health_chatlog.json"

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("API key not found! Make sure .env file contains GEMINI_API_KEY=")

genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=(
        "Extract short system-health insights. Return ONLY valid JSON. "
        "If unsure, leave fields empty."
    ),
    generation_config=types.GenerationConfig(
        temperature=0.0,
        max_output_tokens=150
    )
)

def safe_get_text(response):
    """Safely handle empty, blocked, or missing model output."""
    try:
        if not response.candidates:
            return ""

        parts = response.candidates[0].content.parts
        if not parts:
            return ""

        text = parts[0].text
        return text if text else ""
    except:
        return ""


def extract_key_points(user_input, bot_response):
    prompt = f"""
Extract short system health insights from the conversation.

User: {user_input}
Bot: {bot_response}

Return ONLY a JSON object like this:
{{
  "cpu_status": "",
  "memory_status": "",
  "temperature": "",
  "virus_detected": "",
  "suggested_action": ""
}}

Rules:
- No text outside JSON.
- Leave empty strings if unknown.
"""

    response = model.generate_content(prompt)
    raw = safe_get_text(response).strip()
    if raw == "":
        return {
            "cpu_status": "",
            "memory_status": "",
            "temperature": "",
            "virus_detected": "",
            "suggested_action": ""
        }
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        clean_json = raw[start:end]
        return json.loads(clean_json)
    except:
        return {
            "error": "JSON parse error",
            "raw_model_output": raw
        }

def save_chat_to_json(user_input, bot_response):
    important_points = extract_key_points(user_input, bot_response)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_input": user_input,
        "bot_response": bot_response,
        "important_points": important_points
    }

    if os.path.exists(CHAT_JSON_FILE):
        with open(CHAT_JSON_FILE, "r") as f:
            chats = json.load(f)
    else:
        chats = []

    chats.append(entry)

    with open(CHAT_JSON_FILE, "w") as f:
        json.dump(chats, f, indent=4)

    return entry


def fetch_chats_from_json():
    if not os.path.exists(CHAT_JSON_FILE):
        return []
    with open(CHAT_JSON_FILE, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    user_message = "My laptop is overheating and CPU usage stays above 90% even when idle."
    bot_reply = "High CPU usage and overheating could indicate a background process or dust issue. Try cleaning vents and checking Task Manager."

    chat_entry = save_chat_to_json(user_message, bot_reply)

    print("\nExtracted Key Points:")
    print(json.dumps(chat_entry["important_points"], indent=4))

    print("\n🧾 Full Chat History:")
    for chat in fetch_chats_from_json():
        print(chat["timestamp"], "-", chat["important_points"])