#!/usr/bin/env python3
"""
AI Terminal Life Dashboard
---------------------------
A single-file Python program that turns your terminal into an
intelligent system monitor: CPU, RAM, disk, network, battery,
temperature and uptime, with trend-based AI insights, an event
log, live ASCII graphs and an overall health score.

Usage:
    python dashboard.py

Dependencies:
    pip install psutil rich
"""

import time
import socket
from collections import deque
from datetime import datetime

import psutil
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.box import ROUNDED

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
REFRESH_INTERVAL = 2.0      # seconds between refreshes
HISTORY_LENGTH = 60         # data points kept for trends/graphs
PING_HOST = "8.8.8.8"
PING_PORT = 53
PING_TIMEOUT = 1.0


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------
def bar(percent, width=20, filled_char="█", empty_char="░"):
    """Render a simple ASCII progress bar for a 0-100 percentage."""
    percent = max(0, min(100, percent))
    filled = int(width * percent / 100)
    return filled_char * filled + empty_char * (width - filled)


def sparkline(data, width=30):
    """Render a compact unicode sparkline graph from a sequence of numbers."""
    if not data:
        return " " * width
    blocks = " ▁▂▃▄▅▆▇█"
    data = list(data)[-width:]
    lo, hi = min(data), max(data)
    rng = hi - lo if hi != lo else 1
    chars = [blocks[int((v - lo) / rng * (len(blocks) - 1))] for v in data]
    return "".join(chars).rjust(width)


def format_uptime(seconds):
    d, r = divmod(int(seconds), 86400)
    h, r = divmod(r, 3600)
    m, _ = divmod(r, 60)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    parts.append(f"{m}m")
    return " ".join(parts)


# ------------------------------------------------------------------
# Metrics collection
# ------------------------------------------------------------------
class MetricsCollector:
    def __init__(self):
        self.history = {
            "cpu": deque(maxlen=HISTORY_LENGTH),
            "ram": deque(maxlen=HISTORY_LENGTH),
            "ping": deque(maxlen=HISTORY_LENGTH),
            "battery": deque(maxlen=HISTORY_LENGTH),
            "disk": deque(maxlen=HISTORY_LENGTH),
        }

    def ping(self):
        try:
            start = time.perf_counter()
            with socket.create_connection((PING_HOST, PING_PORT), timeout=PING_TIMEOUT):
                pass
            return round((time.perf_counter() - start) * 1000, 1)
        except OSError:
            return None

    def temperature(self):
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return None
            for _name, entries in temps.items():
                if entries:
                    return entries[0].current
            return None
        except (AttributeError, NotImplementedError):
            return None

    def battery(self):
        try:
            b = psutil.sensors_battery()
            if b is None:
                return None
            return {"percent": b.percent, "plugged": b.power_plugged, "secsleft": b.secsleft}
        except (AttributeError, NotImplementedError):
            return None

    def collect(self):
        cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        ping = self.ping()
        temp = self.temperature()
        batt = self.battery()
        uptime = time.time() - psutil.boot_time()

        self.history["cpu"].append(cpu)
        self.history["ram"].append(vm.percent)
        self.history["disk"].append(disk.percent)
        if ping is not None:
            self.history["ping"].append(ping)
        if batt is not None:
            self.history["battery"].append(batt["percent"])

        return {
            "cpu": cpu,
            "ram": vm.percent,
            "ram_used_gb": vm.used / (1024 ** 3),
            "ram_total_gb": vm.total / (1024 ** 3),
            "disk": disk.percent,
            "disk_used_gb": disk.used / (1024 ** 3),
            "disk_total_gb": disk.total / (1024 ** 3),
            "ping": ping,
            "temp": temp,
            "battery": batt,
            "uptime": uptime,
        }


# ------------------------------------------------------------------
# Health score
# ------------------------------------------------------------------
class HealthScorer:
    def score(self, metrics):
        score = 100

        if metrics["cpu"] > 85:
            score -= 25
        elif metrics["cpu"] > 70:
            score -= 12

        if metrics["ram"] > 90:
            score -= 25
        elif metrics["ram"] > 75:
            score -= 12

        if metrics["disk"] > 95:
            score -= 20
        elif metrics["disk"] > 85:
            score -= 10

        if metrics["ping"] is None:
            score -= 15
        elif metrics["ping"] > 200:
            score -= 15
        elif metrics["ping"] > 100:
            score -= 7

        batt = metrics["battery"]
        if batt and not batt["plugged"] and batt["percent"] < 15:
            score -= 15

        return max(0, min(100, score))

    def stars(self, score):
        filled = round(score / 20)
        return "★" * filled + "☆" * (5 - filled)


# ------------------------------------------------------------------
# AI-style insight engine (trend analysis over recent history)
# ------------------------------------------------------------------
class InsightEngine:
    def __init__(self, history):
        self.history = history

    def _trend(self, key):
        data = self.history[key]
        if len(data) < 6:
            return 0
        data = list(data)
        mid = len(data) // 2
        first_half = sum(data[:mid]) / mid
        second_half = sum(data[mid:]) / (len(data) - mid)
        return second_half - first_half

    def generate(self, metrics):
        insights = []

        # CPU
        if metrics["cpu"] > 85:
            insights.append(("⚠", "CPU usage critically high.",
                              "Close unnecessary applications or check for runaway processes."))
        elif self._trend("cpu") > 15:
            insights.append(("⚠", "CPU has been climbing steadily.",
                              "Possible background process ramping up — worth a check."))
        else:
            insights.append(("✓", "CPU stable.", None))

        # RAM
        if self._trend("ram") > 10 and metrics["ram"] > 60:
            insights.append(("⚠", "Memory increasing steadily.",
                              "Possible memory leak — consider restarting long-running apps."))
        elif metrics["ram"] > 90:
            insights.append(("⚠", "Memory nearly exhausted.",
                              "Free up RAM to avoid swapping and slowdowns."))
        else:
            insights.append(("✓", "Memory usage normal.", None))

        # Disk
        if metrics["disk"] > 90:
            insights.append(("⚠", "Disk usage above 90%.",
                              "Clear temporary files or move data off this drive."))
        else:
            insights.append(("✓", "Disk space sufficient.", None))

        # Network
        if metrics["ping"] is None:
            insights.append(("⚠", "Network unreachable.", "Check your internet connection."))
        elif metrics["ping"] > 150:
            insights.append(("⚠", "Network latency elevated.",
                              "Connection may be congested or unstable."))
        else:
            insights.append(("✓", "Network latency normal.", None))

        # Battery
        batt = metrics["battery"]
        if batt:
            trend = self._trend("battery")
            if not batt["plugged"] and trend < -8:
                insights.append(("⚠", "Battery draining unusually fast.",
                                  "Check for power-hungry background apps."))
            elif not batt["plugged"] and batt["percent"] < 20:
                insights.append(("⚠", "Battery low.", "Consider plugging in soon."))
            else:
                insights.append(("✓", "Battery status normal.", None))

        return insights


# ------------------------------------------------------------------
# Event logger
# ------------------------------------------------------------------
class EventLogger:
    def __init__(self, maxlen=8):
        self.events = deque(maxlen=maxlen)

    def log(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events.append(f"[{timestamp}] {text}")

    def check(self, metrics, prev_metrics):
        if prev_metrics is None:
            self.log("Dashboard started")
            return
        if metrics["cpu"] > 85 and prev_metrics["cpu"] <= 85:
            self.log("CPU usage spiked above 85%")
        if metrics["ram"] > 90 and prev_metrics["ram"] <= 90:
            self.log("RAM usage exceeded 90%")
        if metrics["disk"] > 90 and prev_metrics["disk"] <= 90:
            self.log("Disk usage exceeded 90%")
        if metrics["ping"] is None and prev_metrics["ping"] is not None:
            self.log("Network connection lost")
        if metrics["ping"] is not None and prev_metrics["ping"] is None:
            self.log("Network connection restored")
        batt, prev_batt = metrics["battery"], prev_metrics["battery"]
        if batt and prev_batt and batt["percent"] < 15 <= prev_batt["percent"]:
            self.log("Battery dropped below 15%")


# ------------------------------------------------------------------
# Renderer
# ------------------------------------------------------------------
class DashboardRenderer:
    def render(self, metrics, history, health_score, stars, insights, events):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(name="metrics", ratio=3),
            Layout(name="side", ratio=2),
        )
        layout["side"].split_column(
            Layout(name="insights", ratio=2),
            Layout(name="events", ratio=1),
        )

        layout["header"].update(
            Align.center(Text("🧠  AI TERMINAL LIFE DASHBOARD", style="bold cyan"), vertical="middle")
        )

        # --- Metrics table ---
        table = Table(box=ROUNDED, show_header=False, expand=True, padding=(0, 1))
        table.add_column("Label", style="bold", width=8)
        table.add_column("Bar")
        table.add_column("Value", justify="right")

        cpu_color = "red" if metrics["cpu"] > 85 else "yellow" if metrics["cpu"] > 70 else "green"
        table.add_row("CPU", Text(bar(metrics["cpu"]), style=cpu_color), f"{metrics['cpu']:.0f}%")

        ram_color = "red" if metrics["ram"] > 90 else "yellow" if metrics["ram"] > 75 else "green"
        table.add_row(
            "RAM", Text(bar(metrics["ram"]), style=ram_color),
            f"{metrics['ram']:.0f}% ({metrics['ram_used_gb']:.1f}/{metrics['ram_total_gb']:.1f}GB)",
        )

        disk_color = "red" if metrics["disk"] > 90 else "yellow" if metrics["disk"] > 80 else "green"
        table.add_row(
            "Disk", Text(bar(metrics["disk"]), style=disk_color),
            f"{metrics['disk']:.0f}% ({metrics['disk_used_gb']:.0f}/{metrics['disk_total_gb']:.0f}GB)",
        )

        batt = metrics["battery"]
        if batt:
            b_color = "red" if batt["percent"] < 20 else "yellow" if batt["percent"] < 50 else "green"
            plug = " ⚡" if batt["plugged"] else ""
            table.add_row("Battery", Text(bar(batt["percent"]), style=b_color), f"{batt['percent']:.0f}%{plug}")
        else:
            table.add_row("Battery", "—", "N/A")

        ping = metrics["ping"]
        if ping is not None:
            p_color = "red" if ping > 150 else "yellow" if ping > 80 else "green"
            table.add_row("Ping", Text(bar(min(ping, 300) / 3), style=p_color), f"{ping:.0f} ms")
        else:
            table.add_row("Ping", Text(bar(0), style="red"), "offline")

        if metrics["temp"] is not None:
            t = metrics["temp"]
            t_color = "red" if t > 80 else "yellow" if t > 65 else "green"
            table.add_row("Temp", Text(bar(min(t, 100)), style=t_color), f"{t:.0f}°C")

        table.add_row("Uptime", "", format_uptime(metrics["uptime"]))

        # --- Graphs ---
        graphs = Table(box=None, show_header=False, expand=True, padding=(0, 1))
        graphs.add_column("Label", style="bold dim", width=8)
        graphs.add_column("Graph")
        graphs.add_row("CPU", sparkline(history["cpu"]))
        graphs.add_row("RAM", sparkline(history["ram"]))
        if history["ping"]:
            graphs.add_row("Ping", sparkline(history["ping"]))
        if history["battery"]:
            graphs.add_row("Batt", sparkline(history["battery"]))

        layout["metrics"].split_column(
            Layout(Panel(table, title="📊 System Metrics", border_style="cyan"), ratio=3),
            Layout(Panel(graphs, title="📈 Live Graphs", border_style="blue"), ratio=2),
        )

        # --- Insights panel ---
        insight_lines = []
        for icon, text, rec in insights:
            style = "green" if icon == "✓" else "yellow"
            insight_lines.append(Text(f"{icon} {text}", style=style))
            if rec:
                insight_lines.append(Text(f"   → {rec}", style="dim italic"))
        insight_lines.append(Text(""))
        insight_lines.append(Text(f"Health Score: {health_score}/100  {stars}", style="bold magenta"))
        insights_body = Text("\n").join(insight_lines)
        layout["insights"].update(Panel(insights_body, title="🤖 AI Insights", border_style="magenta"))

        # --- Events panel ---
        if events:
            events_text = Text("\n").join(Text(e, style="dim") for e in events)
        else:
            events_text = Text("No events logged yet.", style="dim")
        layout["events"].update(Panel(events_text, title="📜 Event Log", border_style="white"))

        layout["footer"].update(
            Align.center(Text(f"Refreshing every {REFRESH_INTERVAL:.0f}s — Press Ctrl+C to exit", style="dim"))
        )

        return layout


# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------
def main():
    console = Console()
    collector = MetricsCollector()
    scorer = HealthScorer()
    logger = EventLogger()
    renderer = DashboardRenderer()

    prev_metrics = None

    # Prime cpu_percent so the first real reading isn't 0.0
    psutil.cpu_percent(interval=None)
    time.sleep(0.2)

    try:
        with Live(console=console, refresh_per_second=4, screen=True) as live:
            while True:
                metrics = collector.collect()
                health_score = scorer.score(metrics)
                stars = scorer.stars(health_score)
                insights = InsightEngine(collector.history).generate(metrics)

                logger.check(metrics, prev_metrics)

                layout = renderer.render(
                    metrics, collector.history, health_score, stars, insights, list(logger.events)
                )
                live.update(layout)

                prev_metrics = metrics
                time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Dashboard stopped. Goodbye![/bold cyan]")


if __name__ == "__main__":
    main()
