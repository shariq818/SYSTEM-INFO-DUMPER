#!/usr/bin/env python3
"""
System Info Dumper v1.0
Collects basic system information (OS, CPU, RAM, disk, local IP, public IP) and saves to JSON & text.
"""
import platform
import socket
import json
import uuid
import sys
import time
from datetime import datetime

# optional dependencies
try:
    import psutil
except ImportError:
    psutil = None

try:
    import requests
except ImportError:
    requests = None

OUTPUT_JSON = "system_info.json"
OUTPUT_TEXT = "system_info.txt"

def get_basic_info():
    return {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "hostname": socket.gethostname(),
        "machine_uuid": str(uuid.getnode()),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_machine": platform.machine(),
        "platform_processor": platform.processor(),
        "python_version": platform.python_version()
    }

def get_psutil_info():
    if not psutil:
        return {"error": "psutil not installed"}
    try:
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_freq = psutil.cpu_freq()
        cpu_percent = psutil.cpu_percent(interval=0.5)
        virtual_mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disks = []
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                disks.append({
                    "device": p.device,
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "percent": usage.percent
                })
            except Exception:
                # some partitions might be inaccessible
                disks.append({"device": p.device, "error": "inaccessible"})
        return {
            "cpu_logical_cores": cpu_count_logical,
            "cpu_physical_cores": cpu_count_physical,
            "cpu_freq_mhz": cpu_freq._asdict() if cpu_freq else None,
            "cpu_percent_instant": cpu_percent,
            "memory_total_bytes": virtual_mem.total,
            "memory_available_bytes": virtual_mem.available,
            "memory_used_bytes": virtual_mem.used,
            "memory_percent": virtual_mem.percent,
            "swap_total_bytes": swap.total,
            "swap_used_bytes": swap.used,
            "disks": disks
        }
    except Exception as e:
        return {"error": f"psutil error: {e}"}

def get_network_info():
    info = {}
    try:
        # local IP addresses
        addrs = socket.getaddrinfo(socket.gethostname(), None)
        ips = set()
        for a in addrs:
            ip = a[4][0]
            # skip IPv6 link-local and localhost
            if ip.startswith("127.") or ip.startswith("::1"):
                continue
            ips.add(ip)
        info["local_ips"] = sorted(list(ips)) if ips else []
    except Exception:
        info["local_ips"] = []

    # get hostname -> local IP fallback
    try:
        info["primary_local_ip"] = socket.gethostbyname(socket.gethostname())
    except Exception:
        info["primary_local_ip"] = ""

    # public IP via external service (optional)
    pub_ip = None
    if requests:
        for url in ("https://api.ipify.org?format=json", "https://ifconfig.me/all.json"):
            try:
                r = requests.get(url, timeout=3)
                if r.ok:
                    data = r.json()
                    # ipify returns {"ip": "x.x.x.x"}
                    if "ip" in data:
                        pub_ip = data["ip"]
                        break
                    # ifconfig.me returns different structure
                    if "ip_addr" in data:
                        pub_ip = data["ip_addr"]
                        break
            except Exception:
                continue
    else:
        pub_ip = "requests not installed; install requests to fetch public IP"
    info["public_ip"] = pub_ip or ""
    return info

def format_human_readable(all_info):
    lines = []
    b = all_info.get("basic", {})
    lines.append(f"Timestamp (UTC): {b.get('timestamp_utc')}")
    lines.append(f"Hostname: {b.get('hostname')}")
    lines.append(f"Platform: {b.get('platform_system')} {b.get('platform_release')} ({b.get('platform_machine')})")
    lines.append(f"Processor: {b.get('platform_processor')}")
    lines.append(f"Python: {b.get('python_version')}")
    lines.append("")
    ps = all_info.get("psutil", {})
    if "error" in ps:
        lines.append(f"psutil: {ps['error']}")
    else:
        lines.append(f"CPU cores (logical/physical): {ps.get('cpu_logical_cores')} / {ps.get('cpu_physical_cores')}")
        cpuf = ps.get("cpu_freq_mhz")
        if cpuf:
            lines.append(f"CPU freq (Mhz): current={cpuf.get('current')} min={cpuf.get('min')} max={cpuf.get('max')}")
        lines.append(f"CPU instant usage (%): {ps.get('cpu_percent_instant')}")
        lines.append(f"Memory used/total (MB): {round(ps.get('memory_used_bytes',0)/1024/1024,2)} / {round(ps.get('memory_total_bytes',0)/1024/1024,2)}")
        lines.append(f"Memory %: {ps.get('memory_percent')}")
        lines.append("Disk partitions:")
        for d in ps.get("disks", []):
            if "error" in d:
                lines.append(f"  {d.get('device')}: {d.get('error')}")
            else:
                lines.append(f"  {d.get('mountpoint')} ({d.get('device')}) - {round(d.get('total_bytes',0)/1024/1024/1024,2)} GB, {d.get('percent')}% used")
    lines.append("")
    net = all_info.get("network", {})
    lines.append(f"Local IPs: {', '.join(net.get('local_ips',[])) or 'N/A'}")
    lines.append(f"Primary local IP (hostname resolved): {net.get('primary_local_ip') or 'N/A'}")
    lines.append(f"Public IP: {net.get('public_ip') or 'N/A'}")
    return "\n".join(lines)

def main():
    print("Collecting system info...")
    basic = get_basic_info()
    ps = get_psutil_info()
    net = get_network_info()
    all_info = {"basic": basic, "psutil": ps, "network": net}
    # write JSON
    try:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(all_info, f, indent=2)
        print(f"Saved JSON -> {OUTPUT_JSON}")
    except Exception as e:
        print(f"Error saving JSON: {e}")
    # write human readable text
    try:
        human = format_human_readable(all_info)
        with open(OUTPUT_TEXT, "w", encoding="utf-8") as f:
            f.write(human)
        print(f"Saved text -> {OUTPUT_TEXT}\n")
        print(human)
    except Exception as e:
        print(f"Error saving text: {e}")

if __name__ == "__main__":
    main()