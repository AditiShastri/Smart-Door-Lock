from flask import Flask, render_template, request
import csv
from datetime import datetime
import os

app = Flask(__name__)
LOG_FILE = 'intrusion_log.csv'
IMAGE_DIR = 'static/images'

# Ensure log file and image directory exist
os.makedirs(IMAGE_DIR, exist_ok=True)

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Type', 'Status', 'Image'])

@app.route('/')
def index():
    with open(LOG_FILE, 'r') as f:
        reader = csv.DictReader(f)
        logs = list(reader)
    return render_template('index.html', logs=logs[::-1])  # newest first

@app.route('/log', methods=['POST'])
def log():
    data = request.json
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    event_type = data.get('type', 'Unknown')
    status = data.get('status', 'Unknown')
    image = data.get('image', '')

    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, event_type, status, image])

    return {'message': 'Logged'}, 200

if __name__ == '__main__':
    app.run(debug=True)
