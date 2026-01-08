import psutil
import datetime
import platform
import time
import json
import os
import collections
from toon import encode

SAMPLE_INTERVAL_SECONDS = 10
AGGREGATE_EVERY_N_SAMPLES = 60
MAX_RAW_SAMPLES = 120
TOP_PROCESSES_AGG = 50
MAX_AGGREGATED_RECORDS = 500
DATA_FILE = "data/history.json"

def get_cpu_usage():
    return psutil.cpu_percent(interval=None)

def get_cpu_freq():
    try:
        freq = psutil.cpu_freq()
        if freq:
            return {"current_mhz": freq.current, "min_mhz": freq.min, "max_mhz": freq.max}
    except Exception:
        pass
    return None

def get_memory_info():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "ram": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent
        },
        "swap": {
            "used_gb": round(swap.used / (1024**3), 2),
            "percent": swap.percent
        }
    }

def get_disk_info():
    disk = psutil.disk_usage(os.getcwd())
    return {
        "total_gb": round(disk.total / (1024**3), 2),
        "used_gb": round(disk.used / (1024**3), 2),
        "percent": disk.percent
    }

def get_network_info():
    net = psutil.net_io_counters()
    return {
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv
    }

def get_cpu_temps():
    if platform.system() == "Windows":
        return {"status": "unavailable_windows"}

    if not hasattr(psutil, "sensors_temperatures"):
        return {"status": "unsupported"}

    temps = psutil.sensors_temperatures()
    if not temps:
        return {"status": "no_sensors"}

    result = {}
    for name, entries in temps.items():
        result[name] = [{"current": e.current, "max": e.high} for e in entries]
    return result

def get_processes_info():
    procs = []
    for p in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            if p.info["cpu_percent"] is not None:
                procs.append(p.info)
        except Exception:
            pass
    procs.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return procs[:100]

def aggregate_samples(samples):
    cpu_vals = [s["cpu"]["usage"] for s in samples]
    mem_vals = [s["memory"]["ram"]["percent"] for s in samples]
    disk_vals = [s["disk"]["percent"] for s in samples]

    proc_map = {}
    for s in samples:
        for p in s["processes"]:
            proc_map.setdefault(p["pid"], []).append(p["cpu_percent"])

    top_procs = sorted(
        ((pid, sum(v)/len(v)) for pid, v in proc_map.items()),
        key=lambda x: x[1],
        reverse=True
    )[:TOP_PROCESSES_AGG]

    return {
        "start": samples[0]["timestamp"],
        "end": samples[-1]["timestamp"],
        "cpu": {
            "avg": round(sum(cpu_vals)/len(cpu_vals), 2),
            "min": min(cpu_vals),
            "max": max(cpu_vals)
        },
        "memory_avg_percent": round(sum(mem_vals)/len(mem_vals), 2),
        "disk_avg_percent": round(sum(disk_vals)/len(disk_vals), 2),
        "top_processes_avg_cpu": top_procs
    }

def main():
    if not os.path.exists(DATA_FILE):
        directory = os.path.dirname(DATA_FILE)
        if directory and not os.path.exists(directory):
            os.makedirs(directory) # Creates directory and any necessary parent directories

        with open(DATA_FILE, 'w') as f:
                    f.write("[\n]")
    psutil.cpu_percent(interval=None)

    state = {
        "raw_samples": collections.deque(maxlen=MAX_RAW_SAMPLES),
        "aggregated_samples": []
    }

    # if os.path.exists(DATA_FILE):
    #     with open(DATA_FILE, "r") as f:
    #         saved = json.load(f)
    #     data = saved.get("data", {})
    #     state["aggregated_samples"] = data.get("aggregated_samples", [])
    #     state["raw_samples"] = collections.deque(
    #         data.get("raw_samples", []),
    #         maxlen=MAX_RAW_SAMPLES
    #     )

    try:
        while True:
            sample = {
                "timestamp": datetime.datetime.now().isoformat(),
                "cpu": {
                    "usage": get_cpu_usage(),
                    "freq": get_cpu_freq()
                },
                "memory": get_memory_info(),
                "disk": get_disk_info(),
                "network": get_network_info(),
                "temps": get_cpu_temps(),
                "processes": get_processes_info()
            }

            state["raw_samples"].append(sample)

            if len(state["raw_samples"]) >= AGGREGATE_EVERY_N_SAMPLES:
                block = list(state["raw_samples"])[:AGGREGATE_EVERY_N_SAMPLES]
                state["aggregated_samples"].append(aggregate_samples(block))
                for _ in range(AGGREGATE_EVERY_N_SAMPLES):
                    state["raw_samples"].popleft()

                if len(state["aggregated_samples"]) > MAX_AGGREGATED_RECORDS:
                    state["aggregated_samples"] = state["aggregated_samples"][-MAX_AGGREGATED_RECORDS:]

            safe_state = {
                "raw_samples": list(state["raw_samples"]),
                "aggregated_samples": state["aggregated_samples"]
            }

            payload = {
                "schema_version": "2.0",
                "machine": {
                    "hostname": platform.node(),
                    "os": platform.system(),
                    "arch": platform.machine(),
                    "boot_time": psutil.boot_time()
                },
                "data": safe_state,
                "encoded": encode(safe_state)
            }

            with open(DATA_FILE, "w") as f:
                json.dump(payload, f, indent=2)

            time.sleep(SAMPLE_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
