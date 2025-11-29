# System Info Dumper v1.0  
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)  
![psutil](https://img.shields.io/badge/psutil-required-orange)  
![Status](https://img.shields.io/badge/Status-Prototype-brightgreen)

A small cross-platform Python utility that collects core system information: OS and platform details, CPU cores/frequency/instant usage, RAM and swap stats, disk partition usage, local IP addresses and (optionally) public IP. The tool outputs both a machine-readable JSON file (system_info.json) and a human-readable text summary (system_info.txt). Ideal for quick diagnostics, inventory scripts, VM snapshots, or small automation workflows. Install dependencies via pip install -r requirements.txt and run python system_info_dumper.py. Note: requests is optional (used to fetch public IP); psutil is required for accurate CPU/memory/disk metrics.

•	Running will capture hardware/system info — avoid sharing JSON publicly if it contains sensitive host identifiers.
	•	Public IP is fetched from third-party services (api.ipify.org or ifconfig.me); optional and requires requests.
	•	Works cross-platform (Windows/Linux/macOS) — psutil support may require build tools on some systems.
