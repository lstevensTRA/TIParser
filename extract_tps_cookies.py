import json
from datetime import datetime
from playwright.sync_api import sync_playwright

TPS_URL = "https://tps.logiqs.com/"
COOKIE_FILE = "tps_cookies.json"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        print(f"Opening {TPS_URL} ...")
        page.goto(TPS_URL)
        print("Please log in to the TPS site in the opened browser window.")
        input("Press Enter here after you have logged in and see your dashboard...")

        # Get all cookies for the domain
        cookies = context.cookies()
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        user_agent = page.evaluate("() => navigator.userAgent")

        # Save to tps_cookies.json
        cookie_data = {
            "cookies": cookie_str,
            "user_agent": user_agent,
            "timestamp": datetime.now().isoformat()
        }
        with open(COOKIE_FILE, "w") as f:
            json.dump(cookie_data, f, indent=2)
        print(f"Cookies saved to {COOKIE_FILE}")

        browser.close()

if __name__ == "__main__":
    main() 