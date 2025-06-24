#!/usr/bin/env python3
"""
TPS Cookie Extraction Script
Mimics the JavaScript authentication approach exactly
"""

import json
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from pathlib import Path
import getpass

# Configuration
LOGIQS_URL = 'https://tps.logiqs.com'
COOKIES_FILE = 'logiqs-cookies.json'

def authenticate_and_sync_cookies():
    """Main authentication function that mimics the JavaScript approach"""
    print('🔐 Starting Logiqs authentication...')
    
    # Get credentials from environment variables or prompt user
    username = os.getenv('LOGIQS_USERNAME')
    password = os.getenv('LOGIQS_PASSWORD')
    if not username:
        username = input('Enter your Logiqs username/email: ')
    if not password:
        password = getpass.getpass('Enter your Logiqs password: ')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # Set to True for headless mode
            slow_mo=1000  # Slow down actions for better reliability
        )
        
        try:
            context = browser.new_context()
            page = context.new_page()
            
            print('🌐 Navigating to Logiqs login page...')
            page.goto(LOGIQS_URL)
            
            # Wait for the login form to load
            print('⏳ Waiting for login form...')
            page.wait_for_selector('input[name="username"], input[type="email"], #username, #email', timeout=10000)
            
            print('📝 Filling in credentials...')
            
            # Try different possible selectors for username/email field (matching JS exactly)
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]', 
                '#username',
                '#email',
                'input[type="email"]',
                'input[placeholder*="username" i]',
                'input[placeholder*="email" i]'
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = page.locator(selector).first
                    if username_field.is_visible(timeout=1000):
                        print(f'✅ Found username field with selector: {selector}')
                        break
                except:
                    continue
            
            if not username_field:
                raise Exception('Could not find username/email input field')
            
            username_field.fill(username)
            
            # Find and fill password field (matching JS exactly)
            password_selectors = [
                'input[name="password"]',
                '#password',
                'input[type="password"]',
                'input[placeholder*="password" i]'
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = page.locator(selector).first
                    if password_field.is_visible(timeout=1000):
                        print(f'✅ Found password field with selector: {selector}')
                        break
                except:
                    continue
            
            if not password_field:
                raise Exception('Could not find password input field')
            
            password_field.fill(password)
            
            # Find and click login button (matching JS exactly)
            login_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                '.login-button',
                '#login-button',
                '[data-testid="login-button"]'
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = page.locator(selector).first
                    if login_button.is_visible(timeout=1000):
                        print(f'✅ Found login button with selector: {selector}')
                        break
                except:
                    continue
            
            if not login_button:
                raise Exception('Could not find login button')
            
            print('🔑 Clicking login button...')
            login_button.click()
            
            # Wait for successful login (matching JS approach exactly)
            print('⏳ Waiting for successful authentication...')
            
            try:
                # Wait for either successful login indicators or error messages
                success_selectors = [
                    '.dashboard, .user-menu, .profile, [data-testid="dashboard"]',
                    '.welcome, .user-name, .account-menu'
                ]
                
                # Try success indicators first
                success_found = False
                for selector in success_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=5000)
                        success_found = True
                        break
                    except:
                        continue
                
                # Check if we're still on login page (error case)
                current_url = page.url
                if current_url and ('login' in current_url or 'signin' in current_url):
                    # Check for error messages
                    error_selectors = ['.error', '.alert-error', '.login-error', '[data-testid="error"]']
                    for selector in error_selectors:
                        try:
                            error_element = page.locator(selector).first
                            if error_element.is_visible(timeout=1000):
                                error_text = error_element.text_content()
                                raise Exception(f'Login failed: {error_text}')
                        except:
                            continue
                    
                    if not success_found:
                        raise Exception('Login failed: Still on login page after submission')
                
                print('✅ Successfully authenticated!')
                
            except Exception as error:
                print(f'❌ Authentication failed: {str(error)}')
                raise error
            
            # Wait a bit more to ensure all cookies are set
            page.wait_for_timeout(3000)
            
            # Get all cookies
            print('🍪 Extracting cookies...')
            cookies = context.cookies()
            
            # Save cookies to file (matching JS format exactly)
            cookies_data = {
                'timestamp': datetime.now().isoformat(),
                'url': LOGIQS_URL,
                'cookies': cookies
            }
            
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies_data, f, indent=2)
            
            print(f'💾 Cookies saved to {COOKIES_FILE}')
            
            # Display cookie summary
            print(f'📊 Found {len(cookies)} cookies:')
            for cookie in cookies:
                value_preview = cookie['value'][:20] + '...' if len(cookie['value']) > 20 else cookie['value']
                print(f'   - {cookie["name"]}: {value_preview}')
            
            # Test if we can access a protected page
            print('🧪 Testing access to protected content...')
            try:
                page.goto(f'{LOGIQS_URL}/dashboard', wait_until='networkidle')
                print('✅ Successfully accessed protected content')
            except Exception as error:
                print('⚠️  Could not access dashboard, but cookies are saved')
            
            print('\n🎉 Authentication and cookie sync completed successfully!')
            print(f'📁 Cookies file: {Path(COOKIES_FILE).resolve()}')
            print('💡 You can now use these cookies in your API requests')
            
            return True
            
        except Exception as error:
            print(f'❌ Error during authentication: {str(error)}')
            raise error
        finally:
            browser.close()

def load_cookies():
    """Load cookies for use in API requests (matching JS function)"""
    try:
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, 'r') as f:
                data = json.load(f)
            return data.get('cookies')
    except Exception as error:
        print(f'Error loading cookies: {str(error)}')
    return None

def get_cookies_string():
    """Get cookies as a string for HTTP headers (matching JS function)"""
    cookies = load_cookies()
    if cookies:
        return '; '.join([f'{cookie["name"]}={cookie["value"]}' for cookie in cookies])
    return None

def main():
    """Main function to run authentication"""
    try:
        success = authenticate_and_sync_cookies()
        if success:
            print('✅ Script completed successfully')
            return True
        else:
            print('❌ Script failed')
            return False
    except Exception as error:
        print(f'❌ Script failed: {str(error)}')
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 