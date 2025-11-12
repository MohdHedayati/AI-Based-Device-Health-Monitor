import json
import os
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types

CHAT_JSON_FILE = "system_health_chatlog.json"

# -------- GEMINI SETUP --------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("API key not found! Make sure .env file contains GEMINI_API_KEY=")

genai.configure(api_key=api_key)

config = types.GenerationConfig(
    temperature=0.2,
    max_output_tokens=300,
)

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=(
        "You are a system health analysis assistant. "
        "Extract structured insights like CPU status, memory, temperature, virus detection, and suggestions "
        "from the given conversation between the user and the AI."
    ),
    generation_config=config,
)

def extract_key_points(user_input, bot_response):
    """
    Uses Gemini model to extract key system health points
    from the user and bot conversation.
    """
    prompt = f"""
Chat:
User: {user_input}
Bot: {bot_response}

Return a JSON object with fields:
{{
"cpu_status": "",
"memory_status": "",
"temperature": "",
"virus_detected": "",
"suggested_action": ""
}}
"""

    response = model.generate_content(prompt)
    response_text = response.text
    if response_text is None:
        print("No content generated\n")
        return None
    try:
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        extracted_json = response_text[json_start:json_end]
        important_points = json.loads(extracted_json)
    except Exception:
        important_points = {"error": "Failed to parse JSON from model output"}

    return important_points

def save_chat_to_json(user_input, bot_response):
    """
    Extracts key points using Gemini and saves the chat with structured info.
    """
    important_points = extract_key_points(user_input, bot_response)
    if important_points is None:
        return None
    data = {
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

    chats.append(data)

    with open(CHAT_JSON_FILE, "w") as f:
        json.dump(chats, f, indent=4)

    print(f"✅ Chat saved successfully at {data['timestamp']}")
    return data

def fetch_chats_from_json():
    """
    Load and return all chat data from the JSON file.
    """
    if not os.path.exists(CHAT_JSON_FILE):
        print("No chat history found.")
        return []

    with open(CHAT_JSON_FILE, "r") as f:
        chats = json.load(f)

    return chats

# if __name__ == "__main__":
#     user_message = "My laptop is overheating and CPU usage stays above 90% even when idle."
#     bot_reply = "High CPU usage and overheating could indicate a background process or dust issue. Try cleaning vents and checking Task Manager."

#     chat_entry = save_chat_to_json(user_message, bot_reply)

#     print("\nExtracted Key Points:")
#     print(json.dumps(chat_entry["important_points"], indent=4))

#     print("\n🧾 Full Chat History:")
#     for chat in fetch_chats_from_json():
#         print(chat["timestamp"], "-", chat["important_points"])
