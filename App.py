import os
import json
import psutil
import datetime
import platform
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types
import save as sv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("API key not found! Make sure .env file contains GEMINI_API_KEY=")

genai.configure(api_key=api_key)

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_info():
    memory = psutil.virtual_memory()
    return {
        "total_gb": f"{memory.total / (1024 ** 3):.2f}",
        "available_gb": f"{memory.available / (1024 ** 3):.2f}",
        "used_gb": f"{memory.used / (1024 ** 3):.2f}",
        "percentage_used": memory.percent
    }

def get_disk_info(path='/'):
    try:
        disk = psutil.disk_usage(path)
        return {
            "path": path,
            "total_gb": f"{disk.total / (1024 ** 3):.2f}",
            "used_gb": f"{disk.used / (1024 ** 3):.2f}",
            "free_gb": f"{disk.free / (1024 ** 3):.2f}",
            "percentage_used": disk.percent
        }
    except FileNotFoundError:
        return {"path": path, "error": "Disk path not found."}

def get_cpu_temps():
    if not hasattr(psutil, "sensors_temperatures"):
        return {"error": "Temperature sensors not supported on this platform."}

    temps = psutil.sensors_temperatures()
    if not temps:
        return {"info": "No temperature sensors detected."}

    output = {}
    for name, entries in temps.items():
        output[name] = [
            {"label": e.label or "N/A", "current_celsius": e.current}
            for e in entries
        ]
    return output

def get_battery_info():
    if not hasattr(psutil, "sensors_battery"):
        return {"error": "Battery info not supported on this platform."}

    battery = psutil.sensors_battery()
    if battery is None:
        return {"status": "No battery detected."}

    return {
        "percentage": f"{battery.percent:.2f}",
        "power_plugged": battery.power_plugged,
        "time_left": (
            "Charging" if battery.power_plugged
            else str(datetime.timedelta(seconds=battery.secsleft))
        )
    }

def get_processes_info():
    processes = []
    attrs = ['pid', 'name', 'username', 'cpu_percent', 'memory_percent']
    for proc in psutil.process_iter(attrs=attrs, ad_value=None):
        try:
            info = proc.info
            info['memory_percent'] = round(info.get('memory_percent', 0), 2)
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)[:5]

def collect_system_data():
    """Collect all system metrics and return JSON string"""
    psutil.cpu_percent(interval=None)  # reset measurement
    system_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "platform": platform.system(),
        "cpu_usage_percent": get_cpu_usage(),
        "memory": get_memory_info(),
        "disk_root": get_disk_info('/'),
        "temperatures": get_cpu_temps(),
        "battery": get_battery_info(),
        "top_processes": get_processes_info(),
    }
    return json.dumps(system_data, indent=4)

# gemini model setup
config = types.GenerationConfig(
    temperature=0.1,
    max_output_tokens=200,
)

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=(
        "You are an AI system health advisor. "
        "Use the provided system data to detect anomalies, suggest optimizations, "
        "and provide clear, concise explanations.\n"
    ),
    generation_config=config
)

def main():
    print("System Health Assistant started. Type 'exit' to quit.\n")
    while True:
        user_input = input("What do you want to ask?\n> ").strip()
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        # Refresh system info for every new query
        system_data_json = collect_system_data()

        full_prompt = f"System Metrics:\n{system_data_json}\n\nUser Question: {user_input}"
        response = model.generate_content(full_prompt)
        if response.candidates and response.candidates[0].content.parts:
            sv.save_chat_to_json(user_input, response.text)
            print("\nResponse:\n", response.text)
            print("-" * 60)
        else:
            print("No valid text generated. Possibly blocked by safety filters.")
        

if __name__ == "__main__":
    main()
    
    # View Chat History.
    choice = input("Do you want to view the chat history? (y/n): ").strip().lower()
    if choice == 'y':
        print("\n🧾 Full Chat History:")
        for chat in sv.fetch_chats_from_json():
            print(f"{chat['timestamp']} - {chat['important_points']}")
    else:
        print("Exiting...")
    
