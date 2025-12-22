import psutil
import datetime
import platform
import time
import json
import os
import collections
from toon import encode
from pathlib import Path
def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_info():
    memory = psutil.virtual_memory()
    return {
        "total_gb": f"{memory.total / (1024**3):.2f}",
        "available_gb": f"{memory.available / (1024**3):.2f}",
        "used_gb": f"{memory.used / (1024**3):.2f}",
        "percentage_used": memory.percent
    }

def get_disk_info(path='/'):
    try:
        disk = psutil.disk_usage(path)
        return {
            "path": path,
            "total_gb": f"{disk.total / (1024**3):.2f}",
            "used_gb": f"{disk.used / (1024**3):.2f}",
            "free_gb": f"{disk.free / (1024**3):.2f}",
            "percentage_used": disk.percent
        }
    except FileNotFoundError:
        return {"path": path, "error": "Disk path not found."}

def get_cpu_temps():
    if not hasattr(psutil, "sensors_temperatures"):
        return {"error": "Platform not supported for temperature sensors via psutil."}
        
    temps = psutil.sensors_temperatures()
    
    if not temps:
        return {"info": "Could not find any temperature sensors."}

    if 'coretemp' in temps:
        core_temps = {}
        for i, entry in enumerate(temps['coretemp']):
            core_temps[f"core_{i}"] = {
                "current_celsius": entry.current,
                "high_celsius": entry.high,
                "critical_celsius": entry.critical
            }
        return {"coretemp": core_temps}
    
    all_temps = {}
    for sensor_name, entries in temps.items():
        all_temps[sensor_name] = []
        for entry in entries:
            all_temps[sensor_name].append({
                "label": entry.label or 'N/A',
                "current_celsius": entry.current
            })
    return all_temps


def get_battery_info():
    if not hasattr(psutil, "sensors_battery"):
        return {"error": "Platform not supported for battery sensors via psutil."}

    battery = psutil.sensors_battery()

    if battery is None:
        return {"status": "No battery detected."}

    return {
        "percentage": f"{battery.percent:.2f}",
        "secs_left": "N/A" if battery.secsleft < 0 else battery.secsleft,
        "secs_left_human": "Charging" if battery.power_plugged else str(datetime.timedelta(seconds=battery.secsleft)),
        "power_plugged": battery.power_plugged
    }

def get_processes_info():
    processes = []
    attrs = ['pid', 'name', 'username', 'cpu_percent', 'memory_percent']
    for proc in psutil.process_iter(attrs=attrs, ad_value=None):
        try:
            p_info = proc.info
            if p_info['cpu_percent'] is not None and p_info['memory_percent'] is not None:
                p_info['memory_percent'] = round(p_info['memory_percent'], 2)
                processes.append(p_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    sorted_processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)
    
    return sorted_processes[:5]

def main():
    history_length = 12 
    data_history = collections.deque(maxlen=history_length)
    psutil.cpu_percent(interval=None) 

    try:
        while True:
            timestamp = datetime.datetime.now().isoformat()

            system_data = {
                "timestamp": timestamp,
                "platform": platform.system(),
                "cpu": {
                    "usage_percent": get_cpu_usage() 
                },
                "memory": get_memory_info(),
                "disk_root": get_disk_info('/'),
                "temperatures": get_cpu_temps(),
                "battery": get_battery_info(),
                "processes": get_processes_info()
            }
            
            data_history.append(system_data)
            
            os.system('cls' if os.name == 'nt' else 'clear')
            
            root_object = {
                "system_history": list(data_history)
            }
            result = encode(root_object)
            print(result)
            file_path = "data/history.json"
            if not os.path.exists(file_path):
                directory = os.path.dirname(file_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory) # Creates directory and any necessary parent directories

                with open(file_path, 'w') as f:
                    f.write("[\n]")
            lis = json.load(open(file_path,'r'))
            lis.append(result)
            if len(lis) > 100:
                lis = lis[1::-1]
            json.dump(lis, open(file_path,'w'),indent = 4)
            time.sleep(5)

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()