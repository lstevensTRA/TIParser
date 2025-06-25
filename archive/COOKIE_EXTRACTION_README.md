# TPS Cookie Extraction System

This system provides automated cookie extraction for the TPS (Tax Problem Solver) platform using Playwright browser automation.

## Overview

The cookie extraction system matches your backend API approach:
1. Uses Playwright to launch a Chromium browser
2. Navigates to the TPS login page
3. Automatically fills in username and password fields
4. Handles login with retry logic for session issues
5. Extracts all cookies after successful authentication
6. Saves cookies in JSON format for use in API requests

## Files

- `extract_tps_cookies.py` - Main automated cookie extraction script
- `cookie_sync.py` - Flask service for cookie management and refresh
- `setup_cookies.py` - Setup script for initial installation
- `tps_cookies.json` - Generated cookie file (created after extraction)

## Quick Start

### 1. Initial Setup

```bash
# Run the setup script to install dependencies
python setup_cookies.py
```

### 2. Extract Cookies

```bash
# Run the automated extraction (will prompt for credentials)
python extract_tps_cookies.py
```

### 3. Use Cookie Sync Service (Optional)

```bash
# Start the cookie sync service
python cookie_sync.py
```

## Configuration

### Environment Variables

You can set your TPS credentials as environment variables to avoid manual input:

```bash
export TPS_USERNAME='your_email@example.com'
export TPS_PASSWORD='your_password'
```

### Cookie File Format

The generated `tps_cookies.json` file contains:

```json
{
  "cookies": "ASP.NET_SessionId=...; IRSCookie=...; ...",
  "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
  "timestamp": "2025-06-19T11:51:39.964070",
  "cookie_count": 15,
  "cookie_names": ["ASP.NET_SessionId", "IRSCookie", "SessionDeviceID", ...]
}
```

## Usage Options

### Manual Cookie Extraction

```bash
python extract_tps_cookies.py
```

**Features:**
- Interactive credential input (if not set as environment variables)
- Visual browser window for debugging (set `headless=False`)
- Detailed progress logging
- Automatic retry logic for login issues
- Comprehensive error handling

### Automated Cookie Sync Service

```bash
python cookie_sync.py
```

**Available Endpoints:**
- `GET /check_cookies` - Check if valid cookies exist
- `POST /refresh_cookies` - Refresh cookies using automated login
- `GET /cookie_info` - Get detailed cookie information

**Example Usage:**
```bash
# Check cookie status
curl http://localhost:5001/check_cookies

# Refresh cookies
curl -X POST http://localhost:5001/refresh_cookies

# Get cookie info
curl http://localhost:5001/cookie_info
```

## Integration with Main App

The main Streamlit app (`app.py`) automatically loads cookies from `tps_cookies.json`:

```python
def load_cookies_from_file():
    """Load cookies from the tps_cookies.json file"""
    if not os.path.exists(COOKIE_FILE):
        logger.warning("Cookie file not found")
        return None, None
    
    try:
        with open(COOKIE_FILE, 'r') as f:
            cookie_data = json.load(f)
            
        # If we have cookies and user agent, return them regardless of timestamp
        if cookie_data.get('cookies') and cookie_data.get('user_agent'):
            return cookie_data['cookies'], cookie_data['user_agent']
            
    except Exception as e:
        logger.warning(f"Error reading cookie file: {str(e)}")
        return None, None
```

## Advanced Configuration

### Headless Operation

For production use, you can run the browser in headless mode by editing `extract_tps_cookies.py`:

```python
browser = p.chromium.launch(
    headless=True,  # Set to True for headless operation
    args=['--no-sandbox', '--disable-dev-shm-usage']
)
```

### Custom Browser Arguments

You can add additional browser arguments for specific environments:

```python
browser = p.chromium.launch(
    headless=False,
    args=[
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor'
    ]
)
```

### Cookie Validation

The system includes comprehensive cookie validation:

- Checks for required fields (cookies, user_agent, timestamp)
- Validates JSON format
- Checks cookie age (expires after 12 hours)
- Provides detailed error messages

## Error Handling

The system handles various error scenarios:

- **Login failures**: Retry logic with multiple attempts
- **Session issues**: Automatic detection and handling
- **Network timeouts**: Configurable timeout settings
- **Missing credentials**: Graceful fallback to manual input
- **Browser launch issues**: Detailed error reporting

## Troubleshooting

### Common Issues

1. **Playwright not installed**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Browser launch fails**
   - Check if Chromium is installed: `playwright install chromium`
   - Try running with `headless=False` for debugging

3. **Login fails repeatedly**
   - Verify credentials are correct
   - Check if TPS site is accessible
   - Try running manually first to verify login process

4. **Cookies not being saved**
   - Check file permissions in the current directory
   - Verify JSON format is valid
   - Check for disk space issues

### Debug Mode

For debugging, run with visual browser:

```python
browser = p.chromium.launch(headless=False)  # Shows browser window
```

### Logging

The script provides detailed logging for troubleshooting:

```
🚀 Starting automated TPS login and cookie extraction...
🌐 Navigating to https://tps.logiqs.com/Login.aspx...
⏳ Waiting for login form...
🔐 Filling in login credentials...
🔄 Submitting login form...
⏳ Waiting for authentication...
✅ Successfully logged in!
🍪 Extracting cookies...
✅ Successfully saved 15 cookies to tps_cookies.json
```

## Security Considerations

- Credentials are only stored in environment variables or prompted interactively
- Cookie file contains session data only (no passwords)
- Cookies expire automatically after 12 hours
- No persistent storage of login credentials

## Dependencies

- `playwright>=1.40.0` - Browser automation
- `flask` - Cookie sync service (optional)
- Standard Python libraries: `json`, `datetime`, `os`, `subprocess`

## License

This system is part of the TPS Transcript Parser project. 