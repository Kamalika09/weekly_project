# 🧠 AI Terminal Life Dashboard

A beautiful single-file Python project that transforms your terminal into an intelligent system monitor.

---

## Features

✅ Live CPU Usage
✅ RAM Usage
✅ Disk Monitoring
✅ Network Latency
✅ Battery Information
✅ Temperature (where available)
✅ System Uptime
✅ AI Generated Insights
✅ Health Score
✅ Event Logger
✅ Live ASCII Graphs
✅ Colorful Dashboard

---

## Installation

```bash
git clone https://github.com/yourname/life-dashboard
cd life-dashboard
pip install psutil rich
```

## Run

```bash
python dashboard.py
```

Press `Ctrl+C` to exit.

---

## Requirements

- Python 3.10+
- psutil
- rich

---

## AI Features

The dashboard analyses trends over a rolling history window rather than
just showing raw numbers. It generates observations such as:

- Memory leak suspected
- CPU spike detected
- Battery draining unusually fast
- Network instability
- Disk nearing capacity

---

## Project Structure

Everything is contained inside one file.

```
dashboard.py
├── MetricsCollector   — gathers CPU/RAM/disk/network/battery/temp data
├── HealthScorer        — computes the 0-100 health score
├── InsightEngine        — trend-based AI-style observations
├── EventLogger          — rolling log of notable state changes
├── DashboardRenderer    — builds the rich terminal layout
└── main()               — the live refresh loop
```

---

## Why this project?

This project demonstrates:

- Python
- OOP
- Terminal UI
- Real-time Monitoring
- Data Visualization
- System Programming
- Clean Architecture

while remaining a single Python file.

---

## License

MIT
