from flask import Flask, jsonify
from pathlib import Path
import os
import json
from datetime import datetime

API_KEY = "4917fa0ce4694529a9b97ead1a60c932"
COOKIE_FILE = "tps_cookies.json"

app = Flask(__name__)

def load_cookies_from_file():
    if not os.path.exists(COOKIE_FILE):
        return None, None
    try:
        with open(COOKIE_FILE, 'r') as f:
            cookie_data = json.load(f)
        timestamp = datetime.fromisoformat(cookie_data['timestamp'])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        if age_hours > 12:
            return None, None
        return cookie_data['cookies'], cookie_data['user_agent']
    except Exception:
        return None, None

@app.route('/check_cookies', methods=['GET'])
def check_cookies():
    cookies, user_agent = load_cookies_from_file()
    if not cookies:
        return jsonify({'valid': False, 'message': 'No valid cookies found'})
    return jsonify({'valid': True, 'message': 'Valid cookies found'})

if __name__ == "__main__":
    app.run(debug=True, port=5001) 