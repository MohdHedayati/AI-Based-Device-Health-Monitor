import json
import os
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# -------- CONFIG --------
MODEL_NAME = "google/gemma-2b-it"     # You can use a smaller or quantized version if needed
CHAT_JSON_FILE = "system_health_chatlog.json"

# -------- LOAD MODEL --------
print("🔹 Loading Gemma model... (first time may take a few mins)")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
llm = pipeline("text-generation", model=model, tokenizer=tokenizer)

# -------- EXTRACT IMPORTANT POINTS USING LLM --------
def extract_key_points(user_input, bot_response):
    """
    Uses an open-source LLM (Gemma) to extract key system health points
    from the user and bot conversation.
    """
    prompt = f"""
You are a system health analysis assistant. Extract key structured information from the chat below.
Only return a valid JSON object with details like CPU, memory, temperature, virus, and suggested actions.

Chat:
User: {user_input}
Bot: {bot_response}

Return JSON with fields like:
{{"cpu_status": "", "memory_status": "", "temperature": "", "virus_detected": "", "suggested_action": ""}}
"""

    output = llm(prompt, max_new_tokens=200, temperature=0.3)
    response_text = output[0]['generated_text']

    # Try to find JSON substring
    try:
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        extracted_json = response_text[json_start:json_end]
        important_points = json.loads(extracted_json)
    except Exception:
        important_points = {"error": "Failed to parse JSON from model output"}

    return important_points


# -------- SAVE FUNCTION --------
def save_chat_to_json(user_input, bot_response):
    """
    Extracts key points using Gemma and saves the chat with structured info.
    """
    important_points = extract_key_points(user_input, bot_response)

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


# -------- FETCH FUNCTION --------
def fetch_chats_from_json():
    """
    Load and return all chat data from the JSON file.
    """
    if not os.path.exists(CHAT_JSON_FILE):
        print("⚠️ No chat history found.")
        return []

    with open(CHAT_JSON_FILE, "r") as f:
        chats = json.load(f)

    return chats


# -------- EXAMPLE USAGE --------
if __name__ == "__main__":
    user_message = "My laptop is overheating and CPU usage stays above 90% even when idle."
    bot_reply = "High CPU usage and overheating could indicate a background process or dust issue. Try cleaning vents and checking Task Manager."

    chat_entry = save_chat_to_json(user_message, bot_reply)

    print("\n🔍 Extracted Key Points:")
    print(json.dumps(chat_entry["important_points"], indent=4))

    print("\n🧾 Full Chat History:")
    for chat in fetch_chats_from_json():
        print(chat["timestamp"], "-", chat["important_points"])
