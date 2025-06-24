#!/usr/bin/env python3
"""
Setup script for TPS Cookie Extraction
This script helps set up the automated cookie extraction system.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_playwright():
    """Install Playwright and its browsers"""
    print("🔧 Installing Playwright...")
    try:
        # Install playwright
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        print("✅ Playwright installed successfully")
        
        # Install browsers
        print("🌐 Installing Playwright browsers...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("✅ Chromium browser installed successfully")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Playwright: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import playwright
        print("✅ Playwright is installed")
    except ImportError:
        print("❌ Playwright is not installed")
        return False
    
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright sync API is available")
    except ImportError:
        print("❌ Playwright sync API is not available")
        return False
    
    return True

def test_playwright():
    """Test Playwright installation"""
    print("🧪 Testing Playwright installation...")
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://example.com")
            title = page.title()
            browser.close()
            
        print(f"✅ Playwright test successful - page title: {title}")
        return True
    except Exception as e:
        print(f"❌ Playwright test failed: {e}")
        return False

def setup_environment():
    """Set up environment variables for credentials"""
    print("🔐 Setting up environment variables...")
    
    # Check if environment variables are already set
    username = os.getenv('TPS_USERNAME')
    password = os.getenv('TPS_PASSWORD')
    
    if username and password:
        print("✅ TPS_USERNAME and TPS_PASSWORD are already set")
        return True
    
    print("📝 You can set your TPS credentials as environment variables:")
    print("   export TPS_USERNAME='your_email@example.com'")
    print("   export TPS_PASSWORD='your_password'")
    print()
    print("Or you can enter them when running the cookie extraction script.")
    
    return True

def main():
    print("🚀 TPS Cookie Extraction Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("extract_tps_cookies.py").exists():
        print("❌ Please run this script from the directory containing extract_tps_cookies.py")
        return
    
    # Install Playwright if needed
    if not check_dependencies():
        print("\n📦 Installing missing dependencies...")
        if not install_playwright():
            print("❌ Failed to install dependencies")
            return
    
    # Test Playwright
    if not test_playwright():
        print("❌ Playwright test failed")
        return
    
    # Setup environment
    setup_environment()
    
    print("\n✅ Setup complete!")
    print("\n📋 Next steps:")
    print("1. Set your TPS credentials as environment variables (optional):")
    print("   export TPS_USERNAME='your_email@example.com'")
    print("   export TPS_PASSWORD='your_password'")
    print()
    print("2. Run the cookie extraction script:")
    print("   python extract_tps_cookies.py")
    print()
    print("3. Or run the cookie sync service:")
    print("   python cookie_sync.py")
    print()
    print("🔧 For automated usage, you can also:")
    print("   - Set headless=True in extract_tps_cookies.py for background operation")
    print("   - Use the cookie sync service endpoints for programmatic access")

if __name__ == "__main__":
    main() 