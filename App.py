import psutil
import datetime
import platform
import time
import os
import json
import collections
from typing import Optional, List
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from toon import encode


class SystemAnalysis(BaseModel):
    status: str = Field(..., description="System status: 'Critical' or 'Stable'")
    root_cause: str = Field(..., description="Brief analysis of the issue based on the TOON history.")
    fix_script: Optional[dict] = Field(None, description="A JSON object containing the fix (e.g. {'command': 'kill', 'pid': 1234}). Only provide if Critical.")

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_info():
    memory = psutil.virtual_memory()
    return {
        "total_gb": round(memory.total / (1024**3), 2),
        "available_gb": round(memory.available / (1024**3), 2),
        "used_gb": round(memory.used / (1024**3), 2),
        "percentage_used": memory.percent
    }

def get_disk_info(path='/'):
    try:
        disk = psutil.disk_usage(path)
        return {
            "path": path,
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percentage_used": disk.percent
        }
    except FileNotFoundError:
        return {"path": path, "error": "Disk path not found."}

def get_cpu_temps():
    if not hasattr(psutil, "sensors_temperatures"):
        return {"error": "Platform not supported"}
    temps = psutil.sensors_temperatures()
    if not temps: return {"info": "No sensors"}
    
    if 'coretemp' in temps:
        core_temps = {}
        for i, entry in enumerate(temps['coretemp']):
            core_temps[f"core_{i}"] = entry.current
        return {"coretemp": core_temps}
    return {"info": "Sensors found but structure varies"}

def get_battery_info():
    if not hasattr(psutil, "sensors_battery"): return {"error": "No battery"}
    battery = psutil.sensors_battery()
    if battery is None: return {"status": "No battery"}
    return {
        "percentage": round(battery.percent, 2),
        "power_plugged": battery.power_plugged
    }

def get_processes_info():
    processes = []
    attrs = ['pid', 'name', 'cpu_percent'] 
    for proc in psutil.process_iter(attrs=attrs, ad_value=None):
        try:
            p = proc.info
            if p['cpu_percent']:
                processes.append(p)
        except: pass
    return sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)[:5]

def main():
    client = genai.Client()
    
    HISTORY_LENGTH = 12 
    CPU_THRESHOLD = 5 
    MEMORY_THRESHOLD = 80
    
    data_history = collections.deque(maxlen=HISTORY_LENGTH)
    psutil.cpu_percent(interval=None) 

    print(f"--- System Monitor Started (CPU > {CPU_THRESHOLD}%, Mem > {MEMORY_THRESHOLD}%) ---")

    try:
        while True:
            current_cpu = get_cpu_usage()
            memory_info = get_memory_info()
            current_memory = memory_info['percentage_used']
            
            system_data = {
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                "platform": platform.system(),
                "cpu": {"usage_percent": current_cpu},
                "memory": memory_info,
                "disk": get_disk_info('/'),
                "battery": get_battery_info(),
                "processes": get_processes_info()
            }
            
            data_history.append(system_data)
            
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"Monitoring- CPU: {current_cpu}% | Memory: {current_memory}%")
            
            if current_cpu > CPU_THRESHOLD or current_memory > MEMORY_THRESHOLD:
                print(f"\nHigh Load Detected (CPU: {current_cpu}%, Mem: {current_memory}%). Preparing TOON data...")

                root_object = {"system_history": list(data_history)}
                toon_data = encode(root_object)
                
                print(f"Sending {len(toon_data)} chars of TOON data to Gemini-2.5...")
                trigger_msg = []
                if current_cpu > CPU_THRESHOLD: trigger_msg.append(f"CPU is over {CPU_THRESHOLD}%")
                if current_memory > MEMORY_THRESHOLD: trigger_msg.append(f"Memory is over {MEMORY_THRESHOLD}%")
                
                prompt = f"""
                Here is the recent system history in TOON format:
                
                {toon_data}
                
                ALERT: {", ".join(trigger_msg)}.
                Identify the process causing the issue in the history and provide a JSON fix to kill it.
                """

                config = types.GenerateContentConfig(
                    system_instruction="You are an expert System Administrator. Analyze TOON metrics and output structured JSON fixes.",
                    temperature=0.0,
                    max_output_tokens=500,
                    response_mime_type="application/json",
                    response_json_schema=SystemAnalysis.model_json_schema()
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt],
                    config=config
                )

                if response.text:
                    result = json.loads(response.text)
 
                    print(json.dumps(result, indent=2))
                    # if result.get('fix_script'):
                    #     pid = result['fix_script'].get('pid')
                    #     os.kill(pid, 9)
                    
                    input("\nPress Enter to continue monitoring...")
                else:
                    print("AI is not able to diagnose the issue.")
                
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping Monitor.")

if __name__ == "__main__":
    main()