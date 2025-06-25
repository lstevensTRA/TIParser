from flask import Flask, jsonify
from pathlib import Path
import os
import json
from datetime import datetime
import subprocess
import sys

API_KEY = "4917fa0ce4694529a9b97ead1a60c932"
COOKIE_FILE = "tps_cookies.json"

app = Flask(__name__)

def load_cookies_from_file():
    """Load cookies from file with enhanced validation"""
    if not os.path.exists(COOKIE_FILE):
        return None, None, "Cookie file not found"
    
    try:
        with open(COOKIE_FILE, 'r') as f:
            cookie_data = json.load(f)
        
        # Validate required fields
        if not cookie_data.get('cookies'):
            return None, None, "No cookies found in file"
        if not cookie_data.get('user_agent'):
            return None, None, "No user agent found in file"
        if not cookie_data.get('timestamp'):
            return None, None, "No timestamp found in file"
        
        # Check cookie age
        timestamp = datetime.fromisoformat(cookie_data['timestamp'])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        
        if age_hours > 12:
            return None, None, f"Cookies are {age_hours:.1f} hours old (max 12 hours)"
        
        return cookie_data['cookies'], cookie_data['user_agent'], "Valid"
        
    except json.JSONDecodeError:
        return None, None, "Invalid JSON in cookie file"
    except Exception as e:
        return None, None, f"Error reading cookie file: {str(e)}"

def refresh_cookies():
    """Run the automated cookie extraction script"""
    try:
        print("🔄 Running automated cookie extraction...")
        result = subprocess.run([
            sys.executable, "extract_tps_cookies.py"
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            return True, "Cookies refreshed successfully"
        else:
            return False, f"Cookie extraction failed: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Cookie extraction timed out"
    except Exception as e:
        return False, f"Error running cookie extraction: {str(e)}"

@app.route('/check_cookies', methods=['GET'])
def check_cookies():
    """Check if valid cookies exist"""
    cookies, user_agent, message = load_cookies_from_file()
    
    if not cookies:
        return jsonify({
            'valid': False, 
            'message': message,
            'needs_refresh': True
        })
    
    return jsonify({
        'valid': True, 
        'message': message,
        'cookie_count': len(cookies.split(';')),
        'needs_refresh': False
    })

@app.route('/refresh_cookies', methods=['POST'])
def refresh_cookies_endpoint():
    """Refresh cookies using automated extraction"""
    success, message = refresh_cookies()
    
    if success:
        # Verify the new cookies
        cookies, user_agent, verify_message = load_cookies_from_file()
        if cookies:
            return jsonify({
                'success': True,
                'message': message,
                'cookie_count': len(cookies.split(';'))
            })
        else:
            return jsonify({
                'success': False,
                'message': f"Refresh completed but verification failed: {verify_message}"
            })
    else:
        return jsonify({
            'success': False,
            'message': message
        })

@app.route('/cookie_info', methods=['GET'])
def cookie_info():
    """Get detailed cookie information"""
    cookies, user_agent, message = load_cookies_from_file()
    
    if not cookies:
        return jsonify({
            'valid': False,
            'message': message
        })
    
    try:
        with open(COOKIE_FILE, 'r') as f:
            cookie_data = json.load(f)
        
        timestamp = datetime.fromisoformat(cookie_data['timestamp'])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        
        return jsonify({
            'valid': True,
            'timestamp': cookie_data['timestamp'],
            'age_hours': round(age_hours, 2),
            'cookie_count': cookie_data.get('cookie_count', len(cookies.split(';'))),
            'cookie_names': cookie_data.get('cookie_names', []),
            'user_agent': user_agent
        })
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': f"Error reading cookie info: {str(e)}"
        })

if __name__ == "__main__":
    print("🍪 TPS Cookie Sync Service")
    print("Available endpoints:")
    print("  GET  /check_cookies     - Check if valid cookies exist")
    print("  POST /refresh_cookies   - Refresh cookies using automated login")
    print("  GET  /cookie_info       - Get detailed cookie information")
    print()
    
    app.run(debug=True, port=5001) 