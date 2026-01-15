from flask import Flask, Response
import requests
from datetime import date
import xml.etree.ElementTree as ET
from xml.dom import minidom

app = Flask(__name__)

# URL zu Ihrer tasks.txt auf GitHub (Raw-Link)
GITHUB_USER = "bannanenbaer" 
TASKS_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/haushalts-planer/main/tasks.txt"

def get_tasks():
    tasks = []
    try:
        response = requests.get(TASKS_URL, timeout=10)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            for line in lines:
                if '|' in line:
                    name, interval = line.split('|')
                    tasks.append({'name': name.strip(), 'interval': interval.strip()})
    except:
        pass
    return tasks

def is_due_today(interval_str):
    today = date.today()
    weekday_map = {
        'mo': 0, 'di': 1, 'mi': 2, 'do': 3, 'fr': 4, 'sa': 5, 'so': 6
    }
    
    val = interval_str.lower()
    
    # Check if it's a weekday shortcut
    if val in weekday_map:
        return today.weekday() == weekday_map[val]
    
    # Check if it's a number (interval)
    try:
        interval = int(val)
        # Start point for intervals: 01.01.2026
        start_date = date(2026, 1, 1)
        days_since = (today - start_date).days
        return (days_since % interval) == 0
    except ValueError:
        return False

def generate_rss_feed():
    tasks = get_tasks()
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Haushalts-Planer"
    ET.SubElement(channel, "link").text = "https://github.com"
    ET.SubElement(channel, "description").text = "Ihre heutigen Aufgaben"
    
    due_tasks = [t for t in tasks if is_due_today(t['interval'])]
    
    if not due_tasks:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = "Heute keine Aufgaben - Genießen Sie den Tag!"
    else:
        for t in due_tasks:
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = f"🔔 {t['name']}"
            desc_text = f"Fällig am Wochentag: {t['interval'].upper()}" if t['interval'].lower() in ['mo','di','mi','do','fr','sa','so'] else f"Alle {t['interval']} Tage fällig."
            ET.SubElement(item, "description").text = desc_text
            
    xml_str = ET.tostring(rss, encoding="unicode")
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

@app.route("/")
def index():
    return "<h1>Haushalts-Planer RSS</h1><p><a href='/feed'>Zum Feed</a></p>"

@app.route("/feed")
def rss_feed():
    return Response(generate_rss_feed(), mimetype="application/rss+xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
