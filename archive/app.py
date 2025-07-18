import streamlit as st
import re
import logging
import pytesseract
from pdf2image import convert_from_bytes
import io
import tempfile
import os
import httpx
import json
from pathlib import Path
from datetime import datetime
import PyPDF2
import pandas as pd
from parsers.at_codes import interpret_transaction
from utils.api_client import render_client_profile_tab
from utils.tp_s_parser import TPSParser
from collections import defaultdict
from io import BytesIO
import time
from playwright.sync_api import sync_playwright
import sys
import subprocess


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load full form_patterns (paste your complete form_patterns JSON here)
from full_form_patterns import form_patterns  # make sure this file exists!

COOKIE_FILE = "tps_cookies.json"

def load_cookies_from_file():
    """Load cookies from the logiqs-cookies.json file (matching JS format)"""
    cookie_files = ["logiqs-cookies.json", "tps_cookies.json"]  # Try both formats
    
    for cookie_file in cookie_files:
        if not os.path.exists(cookie_file):
            continue
            
        try:
            with open(cookie_file, 'r') as f:
                cookie_data = json.load(f)
            
            # Handle new logiqs-cookies.json format (matching JS)
            if cookie_file == "logiqs-cookies.json" and 'cookies' in cookie_data:
                cookies = cookie_data['cookies']
                if cookies:
                    # Convert to string format for compatibility
                    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    
                    # Check timestamp if available
                    try:
                        timestamp = datetime.fromisoformat(cookie_data['timestamp'])
                        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                        if age_hours > 12:
                            logger.warning(f"Cookies are {age_hours:.1f} hours old but will try to use them")
                            return cookie_str, user_agent, f"Cookies are {age_hours:.1f} hours old"
                    except (KeyError, ValueError):
                        logger.warning("No timestamp found in cookie file but will try to use cookies")
                    
                    return cookie_str, user_agent, "Valid cookies found"
            
            # Handle old tps_cookies.json format
            elif cookie_file == "tps_cookies.json" and cookie_data.get('cookies') and cookie_data.get('user_agent'):
                # Try to check timestamp if available, but don't fail if it's not
                try:
                    timestamp = datetime.fromisoformat(cookie_data['timestamp'])
                    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                    if age_hours > 12:
                        logger.warning("Cookies are older than 12 hours but will try to use them")
                        return cookie_data['cookies'], cookie_data['user_agent'], f"Cookies are {age_hours:.1f} hours old"
                except (KeyError, ValueError):
                    logger.warning("No timestamp found in cookie file but will try to use cookies")
                    
                return cookie_data['cookies'], cookie_data['user_agent'], "Valid cookies found"
                
        except Exception as e:
            logger.warning(f"Error reading {cookie_file}: {str(e)}")
            continue
    
    logger.warning("No valid cookie files found")
    return None, None, "No valid cookie files found"

def get_wi_files(case_id: str) -> list:
    """
    Get list of WI files associated with a case.
    """
    cookies, user_agent, message = load_cookies_from_file()
    if not cookies:
        st.error("Authentication required. Please ensure cookies are valid.")
        st.info("Please use the '🔐 TPS Login' tab in the sidebar to authenticate.")
        return []

    cookie_header = cookies if isinstance(cookies, str) else ""

    url = f"https://tps.logiqs.com/API/Document/gridBind?caseid={case_id}&type=grid"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "User-Agent": user_agent,
        "Cookie": cookie_header
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            timeout=30,
            follow_redirects=False
        )

        if response.status_code == 302:
            location = response.headers.get("Location", "").lower()
            if "login" in location or "default.aspx" in location:
                st.error("Authentication required. Please ensure cookies are valid.")
                st.info("Please use the '🔐 TPS Login' tab in the sidebar to authenticate.")
                return []

        response.raise_for_status()
        response_data = response.json()

        if not isinstance(response_data, dict) or "Result" not in response_data:
            st.error("Invalid response structure from API")
            return []

        docs = response_data["Result"]
        if not isinstance(docs, list):
            st.error("Invalid document list format")
            return []

        # Filter for WI documents
        wi_files = []
        for doc in docs:
            if not isinstance(doc, dict):
                continue

            name = doc.get("Name", "")
            if not name:
                continue

            # Check for standalone WI in the filename (not part of another word)
            if re.search(r'\bWI\s+\d', name):  # Matches "WI" followed by a space and a number
                case_doc_id = doc.get("CaseDocumentID")
                if case_doc_id:
                    wi_files.append({
                        "FileName": name,
                        "CaseDocumentID": case_doc_id
                    })

        return wi_files

    except Exception as e:
        st.error(f"Error fetching case files: {str(e)}")
        return []

def download_file(case_doc_id: str, case_id: str) -> bytes:
    """
    Download a file using the case document ID and case ID.
    """
    cookies, user_agent, message = load_cookies_from_file()
    if not cookies:
        st.error("Authentication required. Please ensure cookies are valid.")
        return None

    cookie_header = cookies if isinstance(cookies, str) else ""

    url = f"https://tps.logiqs.com/API/Document/DownloadFile?CaseDocumentID={case_doc_id}&caseId={case_id}"
    headers = {
        "User-Agent": user_agent,
        "Cookie": cookie_header
    }

    try:
        response = httpx.get(
            url,
            headers=headers,
            timeout=30,
            follow_redirects=True
        )
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"Error downloading file: {str(e)}")
        return None

def to_float(val):
    try:
        return float(val.replace(',', ''))
    except:
        return 0.0

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF bytes using PyPDF2, then pdfplumber, then OCR as fallback."""
    import PyPDF2
    import pytesseract
    from pdf2image import convert_from_bytes
    import re
    text = ""
    used_method = None

    def is_text_readable(text):
        if not text or len(text) < 100:
            return False
        # Too many (cid:xx) patterns = garbage
        if len(re.findall(r'\(cid:\d+\)', text)) > 10:
            return False
        # Too many non-ASCII or non-printable chars
        ascii_ratio = sum(32 <= ord(c) < 127 for c in text) / len(text)
        if ascii_ratio < 0.7:
            return False
        # At least 20% letters, at least 10 spaces per 1000 chars
        letter_ratio = sum(c.isalpha() for c in text) / len(text)
        space_ratio = text.count(' ') / max(1, len(text))
        return letter_ratio > 0.2 and space_ratio > 0.01

    # Try PyPDF2 first
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        page_texts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            page_texts.append(page_text)
        text = "\n".join(page_texts)
        if is_text_readable(text):
            used_method = "PyPDF2"
            logger.info("Successfully extracted text using PyPDF2")
            return text
        else:
            logger.warning("PyPDF2 extraction unreadable, will try fallback.")
    except Exception as e:
        logger.warning(f"PyPDF2 failed: {e}")

    # Try pdfplumber next
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_texts = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                page_texts.append(page_text)
            text = "\n".join(page_texts)
        if is_text_readable(text):
            used_method = "pdfplumber"
            logger.info("Successfully extracted text using pdfplumber")
            return text
        else:
            logger.warning("pdfplumber extraction unreadable, will try OCR fallback.")
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")

    # OCR fallback
    try:
        images = convert_from_bytes(pdf_bytes)
        ocr_text = "\n".join(pytesseract.image_to_string(img) for img in images)
        if is_text_readable(ocr_text):
            used_method = "OCR"
            logger.info("Successfully extracted text using OCR fallback")
            return ocr_text
        else:
            logger.warning("OCR extraction also unreadable.")
    except Exception as e:
        logger.warning(f"OCR fallback failed: {e}")

    logger.warning("Could not extract readable text from PDF with any method.")
    return ""

def extract_header_info(text):
    """Extract header information from text"""
    logger.info("Extracting header information")
    
    # Updated SSN pattern to match "SSN Provided: XXX-XX-XXXX"
    ssn_match = re.search(r'SSN\s+Provided:\s*([\d\-Xx]{9,})', text, re.IGNORECASE)
    ssn = ssn_match.group(1) if ssn_match else 'UNKNOWN'
    
    # Updated tax period pattern to match "Tax Period Requested: Month, YYYY"
    tax_period_matches = re.findall(r'Tax\s+Period\s+Requested:\s*([A-Za-z]+),\s*(\d{4})', text, re.IGNORECASE)
    tax_periods = [f"{month} {year}" for month, year in tax_period_matches]
    tax_year = int(tax_period_matches[0][1]) if tax_period_matches else 0
    
    logger.info(f"Found SSN: {ssn} | Tax Periods: {', '.join(tax_periods)}")
    
    return ssn, tax_periods, tax_year

def extract_form_data(text, form_patterns, tax_year, filing_status='Single', combined_income=0, output_buffer=None, filename=None):
    """Extract form data from text using patterns"""
    results = {}
    def write_out(msg):
        logger.info(msg)
        if output_buffer:
            output_buffer.write(msg + "\n")
    write_out("Starting form pattern matching")
    form_like_sections = []
    for match in re.finditer(r'(^|\n)\s*Form [A-Z0-9\-]+', text, re.IGNORECASE):
        form_str = match.group(0).strip()
        line_start = text.rfind('\n', 0, match.start()) + 1
        line_end = text.find('\n', match.end())
        if line_end == -1:
            line_end = len(text)
        line = text[line_start:line_end].strip()
        if re.search(r'check box|applicable|transactions that do not flow|indicator', line, re.IGNORECASE):
            continue
        form_like_sections.append((form_str, match.start(), match.end()))
    for form_name, pattern_info in form_patterns.items():
        write_out(f"Processing form: {form_name}")
        matches = list(re.finditer(pattern_info['pattern'], text, re.MULTILINE))
        if not matches:
            write_out(f"Form {form_name}: No pattern match found")
            continue
        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            form_text = text[start:end]
            # Extract unique identifiers
            unique_id = None
            unique_label = None
            payer_blurb = None
            # Improved: Only grab the FIN line and next 1-3 lines (payer name/address), stop at Recipient: or blank
            fin_line_idx = None
            lines = form_text.splitlines()
            for i, line in enumerate(lines):
                if "Payer's Federal Identification Number (FIN):" in line:
                    fin_line_idx = i
                    break
            if fin_line_idx is not None:
                blurb_lines = [lines[fin_line_idx]]
                for j in range(fin_line_idx + 1, min(fin_line_idx + 4, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line or next_line.startswith('Recipient:'):
                        break
                    blurb_lines.append(next_line)
                payer_blurb = '\n'.join(blurb_lines).strip()
            if not payer_blurb:
                # Fallback: try to grab lines after 'Payer:' up to 3 lines
                for i, line in enumerate(lines):
                    if 'Payer:' in line:
                        blurb_lines = [line.strip()]
                        for j in range(i + 1, min(i + 4, len(lines))):
                            next_line = lines[j].strip()
                            if not next_line or next_line.startswith('Recipient:'):
                                break
                            blurb_lines.append(next_line)
                        payer_blurb = '\n'.join(blurb_lines).strip()
                        break
            if form_name == 'W-2':
                ein_match = re.search(r'Employer Identification Number \(EIN\):\s*([\d\-]+)', form_text)
                unique_id = ein_match.group(1) if ein_match else 'UNKNOWN'
                employer_match = re.search(r'Employer:\s*([A-Z0-9 &.,\-]+)', form_text)
                unique_label = employer_match.group(1).strip() if employer_match else 'UNKNOWN'
            elif form_name == '1099-INT':
                fin_match = re.search(r"Payer's Federal Identification Number \(FIN\):\s*([\d\-]+)", form_text)
                unique_id = fin_match.group(1) if fin_match else 'UNKNOWN'
                payer_match = re.search(r'Payer:\s*([A-Z0-9 &.,\-]+)', form_text)
                unique_label = payer_match.group(1).strip() if payer_match else 'UNKNOWN'
            elif form_name.startswith('1099'):
                payer_match = re.search(r'Payer:\s*([A-Z0-9 &.,\-]+)', form_text)
                unique_label = payer_match.group(1).strip() if payer_match else None
            if form_name == 'W-2':
                label_str = f" (EIN: {unique_id}, Employer: {unique_label})"
            elif form_name == '1099-INT':
                label_str = f" (FIN: {unique_id}, Payer: {unique_label})"
            elif form_name.startswith('1099') and unique_label:
                label_str = f", Payer: {unique_label}"
            else:
                label_str = ""
            write_out(f"Form {form_name} #{idx+1}{label_str}:")
            write_out("Pattern matched successfully")
            write_out(f"Using tax year {tax_year}")
            fields_data = {}
            write_out("Starting field extraction")
            for field_name, regex in pattern_info['fields'].items():
                if regex:
                    if field_name == 'TY Payments':
                        all_ty = re.findall(regex, form_text, re.IGNORECASE)
                        if all_ty:
                            fields_data[field_name] = all_ty
                            write_out(f"Field {field_name} = {all_ty}")
                        else:
                            write_out(f"Field {field_name} - No match found (Regex: {regex})")
                            write_out(f"Raw snippet: {form_text[:200]}...")
                    else:
                        field_match = re.search(regex, form_text, re.IGNORECASE)
                        if field_match:
                            value = to_float(field_match.group(1))
                            fields_data[field_name] = value
                            write_out(f"Field {field_name} = {value}")
                            write_out(f"Matched text for {field_name}: {field_match.group(0)}")
                        else:
                            write_out(f"Field {field_name} - No match found (Regex: {regex})")
                            write_out(f"Raw snippet: {form_text[:200]}...")
            write_out(f"All extracted fields for {form_name}: {fields_data}")
            if not fields_data:
                write_out(f"Form {form_name} matched but no fields were captured. Fields attempted: {list(pattern_info['fields'].keys())}")
                write_out(f"Raw form text snippet: {form_text[:300]}...")
                continue
            calc = pattern_info['calculation']
            try:
                if 'filing_status' in calc['Income'].__code__.co_varnames:
                    income = calc['Income'](fields_data, filing_status, combined_income)
                    write_out(f"Income calculation for {form_name}: fields={fields_data}, filing_status={filing_status}, combined_income={combined_income} => {income}")
                else:
                    income = calc['Income'](fields_data)
                    write_out(f"Income calculation for {form_name}: fields={fields_data} => {income}")
            except Exception as e:
                income = 0
                write_out(f"ERROR: Income calculation for {form_name} failed: {e}")
            try:
                withholding = calc['Withholding'](fields_data) if callable(calc.get('Withholding')) else 0
                write_out(f"Withholding calculation for {form_name}: fields={fields_data} => {withholding}")
            except Exception as e:
                withholding = 0
                write_out(f"ERROR: Withholding calculation for {form_name} failed: {e}")
            category = pattern_info.get('category', 'Neither')
            write_out(f"Calculated values - Income: {income}, Withholding: {withholding}, Category: {category}")
            if tax_year not in results:
                results[tax_year] = []
            results[tax_year].append({
                'Form': form_name,
                'UniqueID': unique_id if unique_id else None,
                'Label': unique_label if unique_label else None,
                'Income': income,
                'Withholding': withholding,
                'Category': category,
                'Fields': fields_data,
                'PayerBlurb': payer_blurb
            })
    matched_spans = []
    for form_name, pattern_info in form_patterns.items():
        for m in re.finditer(pattern_info['pattern'], text, re.MULTILINE):
            matched_spans.append((m.start(), m.end()))
    for form_label, start, end in form_like_sections:
        if not any(ms <= start < me for ms, me in matched_spans):
            snippet = text[start-30:end+70] if start > 30 else text[start:end+70]
            fname = filename if filename else "UNKNOWN"
            write_out(f"Potential form detected in text but no pattern matched: '{form_label}' at position {start}. [FILENAME: {fname}] Snippet: {snippet}")
    write_out("Form processing completed")
    return results

def get_transaction_alerts(transactions):
    """Get alerts for important transaction codes that require attention"""
    alerts = []
    
    # Define alert categories and their associated codes
    alert_categories = {
        'Audit Alerts': {
            'codes': ['420', '424', '430'],
            'severity': 'error',
            'icon': '🔍'
        },
        'Collection Alerts': {
            'codes': ['520', '530', '780'],
            'severity': 'error',
            'icon': '⚠️'
        },
        'Additional Tax Assessments': {
            'codes': ['290', '300'],
            'severity': 'error',
            'icon': '💸'
        },
        'Payment Issues': {
            'codes': ['706', '898'],
            'severity': 'warning',
            'icon': '💰'
        },
        'Account Holds': {
            'codes': ['570', '810'],
            'severity': 'warning',
            'icon': '🔒'
        },
        'Refund Issues': {
            'codes': ['846', '811'],
            'severity': 'warning',
            'icon': '💳'
        },
        'Amended Returns': {
            'codes': ['320'],
            'severity': 'info',
            'icon': '📝'
        },
        'Resolution Programs': {
            'codes': ['480', '482'],
            'severity': 'info',
            'icon': '✅'
        },
        'Bankruptcy': {
            'codes': ['780'],
            'severity': 'error',
            'icon': '🏛️'
        },
        'Extensions': {
            'codes': ['460'],
            'severity': 'info',
            'icon': '⏰'
        },
        'Substitute Returns': {
            'codes': ['599'],
            'severity': 'warning',
            'icon': '📋'
        },
        'Litigation/Freezes': {
            'codes': ['520', '571'],
            'severity': 'warning',
            'icon': '⚖️'
        }
    }
    
    for trans in transactions:
        code = trans.get('code')
        for category, info in alert_categories.items():
            if code in info['codes']:
                alert = {
                    'category': category,
                    'severity': info['severity'],
                    'icon': info['icon'],
                    'code': code,
                    'meaning': trans.get('meaning', ''),
                    'date': trans.get('date', ''),
                    'description': trans.get('description', ''),
                    'amount': trans.get('amount', 0),
                    'tax_year': trans.get('tax_year', '')
                }
                alerts.append(alert)
    
    return alerts

def display_alerts(alerts):
    """Display alerts in a formatted way"""
    if not alerts:
        return
    
    st.markdown("### 🚨 Important Alerts")
    
    # Group alerts by severity
    severity_order = {'error': 1, 'warning': 2, 'info': 3}
    alerts.sort(key=lambda x: (severity_order[x['severity']], x['category']))
    
    for alert in alerts:
        if alert['severity'] == 'error':
            container = st.error
        elif alert['severity'] == 'warning':
            container = st.warning
        else:
            container = st.info
            
        with container(f"{alert['icon']} {alert['category']} - Tax Year {format_year(alert['tax_year'])}"):
            st.markdown(f"""
            **Transaction Code {alert['code']}: {alert['meaning']}**  
            Date: {alert['date']}  
            Description: {alert['description']}  
            Amount: ${alert['amount']:,.2f}
            """)

def render_home():
    """Render the home page with case number input"""
    st.title("IRS Transcript Parser")
    
    # Check cookie status
    cookies, user_agent, message = load_cookies_from_file()
    if not cookies:
        st.warning("⚠️ No valid cookies found. Please use the '🔐 TPS Login' tab in the sidebar to authenticate.")
        st.info("Steps to authenticate:")
        st.markdown("""
        1. Use the '🔐 TPS Login' tab in the sidebar to authenticate.
        2. After logging in, press Enter in the terminal window.
        3. Refresh this page.
        """)
        st.info("Note: If you've manually added cookies to tps_cookies.json, you can try using the parsers, but you may need to refresh cookies if authentication fails.")
    else:
        st.success(f"✅ Authentication status: {message}")
    
    # Case ID input
    case_id = st.text_input(
        "Enter Case ID:",
        value=st.session_state.get('case_id', ''),
        help="Enter the case ID to fetch and parse documents"
    )
    
    if case_id:
        # Clear previous session data if case ID changes
        if st.session_state.get('case_id') != case_id:
            for key in ['wi_data', 'wi_form_matching', 'wi_summary', 'wi_projection', 'wi_log',
                       'at_data', 'at_form_matching', 'at_summary', 'at_projection', 'at_log']:
                if key in st.session_state:
                    del st.session_state[key]
        
        st.session_state['case_id'] = case_id
        st.success(f"✅ Case ID set to: {case_id}")
        
        # Document type detection
        if cookies:  # Only try to detect documents if we have cookies
            with st.spinner("🔍 Fetching all available documents..."):
                wi_files = get_wi_files(case_id)
                at_files = get_at_files(case_id)
                roa_files = get_roa_files(case_id)
                trt_files = get_trt_files(case_id)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("📄 **Wage & Income Documents:**", len(wi_files))
                st.write("📊 **Account Transcripts:**", len(at_files))
            with col2:
                st.write("📋 **Record of Account:**", len(roa_files))
                st.write("📝 **Tax Return Transcripts:**", len(trt_files))
            
            # Process WI documents if available
            if wi_files:
                process_wi_documents(case_id, wi_files)
                st.success("✅ Wage & Income documents processed successfully")
            
            # Process AT documents if available
            if at_files:
                process_at_documents(case_id, at_files)
                st.success("✅ Account Transcript documents processed successfully")
            
            if not any([wi_files, at_files, roa_files, trt_files]):
                st.warning("No documents found for this case ID")
        else:
            st.info("Please ensure you have valid cookies before checking for documents.")

    # After this line:
    wi_files = get_wi_files(case_id)
    # Add this:
    st.session_state['wi_files'] = wi_files

def process_wi_documents(case_id, wi_files):
    """Process all WI documents once and store results"""
    all_data = {}
    form_matching_results = []  # Track form matching results
    
    # Set up logging
    log_buffer = io.StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    log_handler.setLevel(logging.INFO)
    logger.addHandler(log_handler)
    
    with st.spinner("Processing Wage & Income documents..."):
        progress_bar = st.progress(0)
        total_files = len(wi_files)
        wi_texts = {}  # Store extracted text by filename
        for idx, wi_file in enumerate(wi_files):
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing file: {wi_file['FileName']}")
            logger.info(f"{'='*50}\n")
            
            # Extract owner from filename using TPSParser
            owner = TPSParser.extract_owner_from_filename(wi_file['FileName'])
            logger.info(f"Extracted owner from filename '{wi_file['FileName']}': {owner}")
            
            pdf_bytes = download_file(wi_file["CaseDocumentID"], case_id)
            if pdf_bytes:
                text = extract_text_from_pdf(pdf_bytes)
                if text:
                    wi_texts[wi_file['FileName']] = text
                    # Log the complete raw text
                    logger.info("Complete extracted text from PDF:")
                    logger.info("-" * 50)
                    logger.info(text)
                    logger.info("-" * 50)
                    
                    # Extract header info (returns ssn, tax_periods, tax_year)
                    ssn, tax_periods, tax_year = extract_header_info(text)
                    if ssn and tax_periods:
                        logger.info(f"Found SSN: {ssn} | Tax Periods: {tax_periods}")
                    
                    # Store form matching results
                    file_results = {
                        'filename': wi_file['FileName'],
                        'owner': owner,  # Add owner to file results
                        'ssn': ssn,
                        'tax_period': tax_periods,
                        'form_matches': []
                    }
                    
                    # Check form patterns
                    for form_name, pattern_info in form_patterns.items():
                        found_match = bool(re.search(pattern_info['pattern'], text, re.MULTILINE))
                        file_results['form_matches'].append({
                            'form_name': form_name,
                            'matched': found_match
                        })
                    
                    form_matching_results.append(file_results)
                    
                    # Process forms (first pass: all except SSA-1099)
                    forms_data = extract_form_data(text, form_patterns, tax_year, output_buffer=log_buffer, filename=wi_file['FileName'])
                    if forms_data:
                        for year, year_forms in forms_data.items():
                            if year not in all_data:
                                all_data[year] = []
                            
                            # Add owner information to each form
                            for form in year_forms:
                                form['Owner'] = owner
                                form['SourceFile'] = wi_file['FileName']  # Add source file for tracking
                                logger.info(f"Added Owner={owner} to form {form['Form']}")
                            
                            # Separate SSA-1099 and others
                            non_ssa_forms = [f for f in year_forms if f['Form'] != 'SSA-1099']
                            ssa_forms = [f for f in year_forms if f['Form'] == 'SSA-1099']
                            all_data[year].extend(non_ssa_forms)
                            # Calculate combined income for the year (excluding SSA-1099)
                            combined_income = sum(f['Income'] for f in non_ssa_forms if f.get('Income') is not None)
                            # Get marital status from client profile (if available)
                            client_data = st.session_state.get('client_data') or st.session_state.get('client_profile_data')
                            marital_status = 'Single'
                            if client_data:
                                marital_status = client_data.get('client_info', {}).get('marital_status', 'Single')
                            # Now process SSA-1099 forms with correct combined_income and marital_status
                            for ssa_form in ssa_forms:
                                fields = ssa_form.get('Fields', {})
                                calc = form_patterns['SSA-1099']['calculation']
                                try:
                                    income = calc['Income'](fields, marital_status, combined_income)
                                    logger.info(f"SSA-1099 calculation: fields={fields}, marital_status={marital_status}, combined_income={combined_income} => {income}")
                                except Exception as e:
                                    income = 0
                                    logger.info(f"ERROR: SSA-1099 income calculation failed: {e}")
                                try:
                                    withholding = calc['Withholding'](fields) if callable(calc.get('Withholding')) else 0
                                except Exception as e:
                                    withholding = 0
                                    logger.info(f"ERROR: SSA-1099 withholding calculation failed: {e}")
                                ssa_form['Income'] = income
                                ssa_form['Withholding'] = withholding
                                all_data[year].append(ssa_form)
            # Update progress bar
            progress_bar.progress((idx + 1) / total_files)
    
    # Store results in session state
    st.session_state['wi_data'] = all_data
    st.session_state['wi_log'] = log_buffer.getvalue()
    st.session_state['wi_form_matching'] = form_matching_results
    st.session_state['wi_texts'] = wi_texts
    
    # Calculate and store summary data
    summary_data = []
    for year in sorted(all_data.keys(), reverse=True):
        year_forms = all_data[year]
        
        # Calculate totals by category
        se_income = sum(form['Income'] for form in year_forms if form.get('Category') == 'SE' and form.get('Income') is not None)
        se_withholding = sum(form['Withholding'] for form in year_forms if form.get('Category') == 'SE' and form.get('Withholding') is not None)
        
        nonse_income = sum(form['Income'] for form in year_forms if form.get('Category') == 'Non-SE' and form.get('Income') is not None)
        nonse_withholding = sum(form['Withholding'] for form in year_forms if form.get('Category') == 'Non-SE' and form.get('Withholding') is not None)
        
        other_income = sum(form['Income'] for form in year_forms if form.get('Category') == 'Neither' and form.get('Income') is not None)
        other_withholding = sum(form['Withholding'] for form in year_forms if form.get('Category') == 'Neither' and form.get('Withholding') is not None)
        
        summary_data.append({
            'Tax Year': format_year(year),
            'Number of Forms': len(year_forms),
            'SE Income': se_income,
            'SE Withholding': se_withholding,
            'Non-SE Income': nonse_income,
            'Non-SE Withholding': nonse_withholding,
            'Other Income': other_income,
            'Other Withholding': other_withholding,
            'Total Income': se_income + nonse_income + other_income,
            'Total Withholding': se_withholding + nonse_withholding + other_withholding
        })
    st.session_state['wi_summary'] = summary_data
    
    # Calculate and store tax projection data
    projection_data = []
    for year in sorted(all_data.keys(), reverse=True):
        year_forms = all_data[year]
        se_income = sum(form['Income'] for form in year_forms if form.get('Category') == 'SE' and form.get('Income') is not None)
        se_withholding = sum(form['Withholding'] for form in year_forms if form.get('Category') == 'SE' and form.get('Withholding') is not None)
        nonse_income = sum(form['Income'] for form in year_forms if form.get('Category') == 'Non-SE' and form.get('Income') is not None)
        nonse_withholding = sum(form['Withholding'] for form in year_forms if form.get('Category') == 'Non-SE' and form.get('Withholding') is not None)
        other_income = sum(form['Income'] for form in year_forms if form.get('Category') == 'Neither' and form.get('Income') is not None)
        
        projection_data.append({
            'Tax Year': str(year),
            'SE Income': se_income,
            'SE Withholding': se_withholding,
            'Non-SE Income': nonse_income,
            'Non-SE Withholding': nonse_withholding,
            'Other Income': other_income
        })
    st.session_state['wi_projection'] = projection_data
    
    # Clean up logging
    logger.removeHandler(log_handler)
    log_buffer.close()

def render_wi_parser():
    """Render the WI Parser page (Wage & Income)"""
    st.title("WI Parser")
    
    # Get case_id from session state
    case_id = st.session_state.get('case_id', None)
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return

    # Check if we have data
    if 'wi_data' not in st.session_state:
        st.warning("No Wage & Income data available. Please process a case ID first.")
        return

    # Set up Streamlit tabs
    summary_tab, critical_tab, tax_projection_tab, json_tab, form_matching_tab, log_tab = st.tabs([
        "Summary", "Critical Issues", "Tax Projection", "JSON", "Form Matching", "Logs"
    ])

    with summary_tab:
        st.subheader("Income Summary")
        if st.session_state['wi_summary']:
            # Add toggle for combined/separated view
            summary_view = st.radio(
                "Show:",
                ["Combined", "Separated by Owner"],
                horizontal=True,
                key="wi_summary_view"
            )
            df = pd.DataFrame(st.session_state['wi_summary'])
            # Calculate Estimated AGI
            df['Estimated AGI'] = df['Total Income'] - (df['SE Income'] * 0.0765)
            df['Estimated AGI'] = df['Estimated AGI'].round(2)
            # Prepare owner breakdowns for each year
            owner_rows = []
            for _, row in df.iterrows():
                year = row['Tax Year']
                year_forms = st.session_state['wi_data'].get(int(year), [])
                year_data = {int(year): year_forms}
                totals = TPSParser.aggregate_income_by_owner(year_data)
                year_totals = totals.get(int(year), {})
                owner_rows.append({
                    'Tax Year': year,
                    'Taxpayer Income': year_totals.get('taxpayer', {}).get('income', 0),
                    'Spouse Income': year_totals.get('spouse', {}).get('income', 0),
                    'Joint Income': year_totals.get('joint', {}).get('income', 0),
                    'Combined Income': year_totals.get('combined', {}).get('income', 0),
                    'Taxpayer Withholding': year_totals.get('taxpayer', {}).get('withholding', 0),
                    'Spouse Withholding': year_totals.get('spouse', {}).get('withholding', 0),
                    'Joint Withholding': year_totals.get('joint', {}).get('withholding', 0),
                    'Combined Withholding': year_totals.get('combined', {}).get('withholding', 0),
                })
            owner_df = pd.DataFrame(owner_rows)
            # Format currency columns
            for col in ['Taxpayer Income', 'Spouse Income', 'Joint Income', 'Combined Income',
                        'Taxpayer Withholding', 'Spouse Withholding', 'Joint Withholding', 'Combined Withholding']:
                owner_df[col] = owner_df[col].apply(lambda x: f"${x:,.2f}")
            if summary_view == "Separated by Owner":
                st.table(owner_df)
            else:
                # Combined view: show only combined columns, plus original summary columns
                combined_df = owner_df[['Tax Year', 'Combined Income', 'Combined Withholding']].copy()
                # Merge with original summary for other fields
                display_df = df.copy()
                currency_cols = ['SE Income', 'SE Withholding', 'Non-SE Income', 'Non-SE Withholding', 
                               'Other Income', 'Other Withholding', 'Total Income', 'Estimated AGI', 'Total Withholding']
                for col in currency_cols:
                    display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
                # Reorder columns to put Estimated AGI after Total Income and before Total Withholding
                cols = list(display_df.columns)
                if 'Estimated AGI' in cols and 'Total Income' in cols and 'Total Withholding' in cols:
                    ti_idx = cols.index('Total Income')
                    tw_idx = cols.index('Total Withholding')
                    cols.remove('Estimated AGI')
                    cols.insert(ti_idx + 1, 'Estimated AGI')
                    display_df = display_df[cols]
                # Merge on Tax Year
                merged = pd.merge(combined_df, display_df, on='Tax Year', how='left')
                st.table(merged)
            
            # Add owner-based summary
            st.markdown("---")
            st.subheader("Owner-Based Summary")
            
            # Calculate totals by owner for each year
            for _, row in df.iterrows():
                year = row['Tax Year']
                year_forms = st.session_state['wi_data'].get(int(year), [])
                
                if year_forms:
                    # Use TPSParser to aggregate by owner
                    year_data = {int(year): year_forms}
                    totals = TPSParser.aggregate_income_by_owner(year_data)
                    year_totals = totals.get(int(year), {})
                    
                    with st.expander(f"📊 Tax Year {year} - Owner Breakdown", expanded=False):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown("**Taxpayer**")
                            tp_data = year_totals.get('taxpayer', {})
                            st.metric("Income", f"${tp_data.get('income', 0):,.2f}")
                            st.metric("Withholding", f"${tp_data.get('withholding', 0):,.2f}")
                        
                        with col2:
                            st.markdown("**Spouse**")
                            spouse_data = year_totals.get('spouse', {})
                            st.metric("Income", f"${spouse_data.get('income', 0):,.2f}")
                            st.metric("Withholding", f"${spouse_data.get('withholding', 0):,.2f}")
                        
                        with col3:
                            st.markdown("**Joint**")
                            joint_data = year_totals.get('joint', {})
                            st.metric("Income", f"${joint_data.get('income', 0):,.2f}")
                            st.metric("Withholding", f"${joint_data.get('withholding', 0):,.2f}")
                        
                        with col4:
                            st.markdown("**Combined**")
                            combined_data = year_totals.get('combined', {})
                            st.metric("Income", f"${combined_data.get('income', 0):,.2f}")
                            st.metric("Withholding", f"${combined_data.get('withholding', 0):,.2f}")
            
            # Display detailed breakdown for each year
            for _, row in df.iterrows():
                year = row['Tax Year']
                with st.expander(f"📅 Tax Year {year} - Detailed Breakdown", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**Self-Employment Income**")
                        st.metric("Income", f"${row['SE Income']:,.2f}")
                        st.metric("Withholding", f"${row['SE Withholding']:,.2f}")
                    
                    with col2:
                        st.markdown("**Non-Self-Employment Income**")
                        st.metric("Income", f"${row['Non-SE Income']:,.2f}")
                        st.metric("Withholding", f"${row['Non-SE Withholding']:,.2f}")
                    
                    with col3:
                        st.markdown("**Other Income**")
                        st.metric("Income", f"${row['Other Income']:,.2f}")
                        st.metric("Withholding", f"${row['Other Withholding']:,.2f}")
                    
                    # Display forms for this year
                    st.markdown("**Forms Breakdown**")
                    year_forms = st.session_state['wi_data'].get(int(year), [])
                    if year_forms:
                        # Group forms by owner
                        forms_by_owner = {}
                        for form in year_forms:
                            owner = form.get('Owner', 'TP')
                            if owner not in forms_by_owner:
                                forms_by_owner[owner] = []
                            forms_by_owner[owner].append(form)
                        
                        # Display by owner
                        for owner, forms in forms_by_owner.items():
                            owner_label = "Taxpayer" if owner == "TP" else "Spouse" if owner == "S" else "Joint"
                            st.markdown(f"**{owner_label} Forms:**")
                            
                            for form in forms:
                                form_type = form['Form']
                                category = form['Category']
                                income = form.get('Income', 0)
                                withholding = form.get('Withholding', 0)
                                label = form.get('Label', '')
                                source_file = form.get('SourceFile', 'Unknown')
                                
                                # Format the form display
                                form_label = f"{form_type}"
                                if label:
                                    form_label += f" - {label}"
                                
                                st.markdown(f"• {form_label} ({category})")
                                # Show only the payer name in a clean style
                                if label and label != "UNKNOWN":
                                    st.markdown(f"<span style='color:#444;font-size:1.05em'><b>Payer:</b> {label}</span>", unsafe_allow_html=True)
                                # Remove the full PayerBlurb display for cleanest look
                                fcol1, fcol2, fcol3 = st.columns(3)
                                with fcol1:
                                    st.write(f"Income: ${income:,.2f}")
                                with fcol2:
                                    st.write(f"Withholding: ${withholding:,.2f}")
                                with fcol3:
                                    st.write(f"Source: {source_file}")
                                st.markdown("---")
                    else:
                        st.info("No forms found for this year")
        else:
            st.info("📝 No Wage & Income data extracted")
    
    with critical_tab:
        st.subheader("Critical Extraction Issues & Forms to Check")
        wi_log = st.session_state.get('wi_log', '')
        wi_texts = st.session_state.get('wi_texts', {})
        if 'wi_data' in st.session_state and st.session_state['wi_data']:
            pass  # Placeholder for future enhancement
        if not wi_log:
            st.info("No log data available yet.")
        else:
            import re
            from collections import defaultdict
            def extract_full_form_snippet(form_name, text, start_pos=None, filename=None):
                import re
                debug_info = []
                if text is None:
                    return f"[DEBUG] No text found for filename: {filename}"
                # If start_pos is provided, use it; otherwise, find the first occurrence
                if start_pos is not None:
                    start = start_pos
                else:
                    pattern = re.compile(rf'(Form[ \-]?{re.escape(form_name)})', re.IGNORECASE)
                    match = pattern.search(text)
                    start = match.start() if match else 0
                # Find the next form after start
                next_form_match = re.search(r'(\n|^)\s*Form [A-Z0-9\-]+', text[start+1:], re.IGNORECASE)
                if next_form_match:
                    end = start + 1 + next_form_match.start()
                else:
                    end = len(text)
                # Debug info
                debug_info.append(f"[DEBUG] Filename: {filename}")
                debug_info.append(f"[DEBUG] Start pos: {start}")
                debug_info.append(f"[DEBUG] End pos: {end}")
                debug_info.append(f"[DEBUG] Text length: {len(text)}")
                snippet = text[start:end] if 0 <= start < end <= len(text) else ''
                debug_info.append(f"[DEBUG] Snippet length: {len(snippet)}")
                debug_info.append(f"[DEBUG] Snippet preview: {snippet[:100]}")
                if not snippet:
                    debug_info.append("[DEBUG] No snippet extracted. Check indices and text.")
                    return '\n'.join(debug_info)
                # Highlight the matched form name at the start
                pattern = re.compile(rf'(Form[ \-]?{re.escape(form_name)})', re.IGNORECASE)
                snippet = pattern.sub(r'>>>\1<<<', snippet, count=1)
                return '\n'.join(debug_info) + '\n' + snippet
            no_fields = []
            form_no_match = []
            regex_failures = []
            form_status = defaultdict(lambda: 'Not Attempted')
            pattern_matched_no_data = set()
            # Find forms with no fields captured
            for m in re.finditer(r"Form ([A-Z0-9\- ()]+) matched but no fields were captured\. Fields attempted: (.+?)\nRaw form text snippet: (.+?)\.\.\.\n", wi_log, re.DOTALL):
                form, fields, snippet = m.groups()
                # Try to get the filename from [FILENAME: ...] in the log entry
                file_match = re.search(r'\[FILENAME: ([^\]]+)\]', wi_log[m.start():m.end()])
                filename = file_match.group(1) if file_match else None
                wi_text = wi_texts.get(filename, wi_log)
                full_snippet = extract_full_form_snippet(form, wi_text)
                no_fields.append({"form": form.strip(), "fields": fields, "snippet": full_snippet})
                form_status[form.strip()] = 'Pattern Matched, No Data Extracted'
                pattern_matched_no_data.add(form.strip())
            # Build a set of all parsed forms by filename (from wi_data)
            parsed_forms_by_file = {}
            wi_data = st.session_state.get('wi_data', {})
            for year, forms in wi_data.items():
                for form in forms:
                    filename = form.get('SourceFile') or form.get('filename') or None
                    form_name = form.get('Form')
                    if filename and form_name:
                        if filename not in parsed_forms_by_file:
                            parsed_forms_by_file[filename] = set()
                        parsed_forms_by_file[filename].add(form_name)
            for m in re.finditer(r"Potential form detected in text but no pattern matched: '([^']+)' at position (\d+)\. \[FILENAME: ([^\]]+)\] Snippet: (.+?)\n", wi_log, re.DOTALL):
                form_label, pos_str, filename, snippet = m.groups()
                wi_text = wi_texts.get(filename, None)
                start_pos = int(pos_str)
                # Only show as a critical issue if this form is NOT present in parsed_forms_by_file for this filename
                parsed_forms = parsed_forms_by_file.get(filename, set())
                if form_label.strip() in parsed_forms:
                    continue  # Skip, it was actually parsed
                full_snippet = extract_full_form_snippet(form_label, wi_text, start_pos=start_pos, filename=filename)
                form_no_match.append({"form": form_label.strip(), "snippet": full_snippet})
            for m in re.finditer(r"Field ([^ ]+) - No match found \(Regex: ([^\)]+)\)\nRaw snippet: (.+?)\.\.\.\n", wi_log, re.DOTALL):
                field, regex, snippet = m.groups()
                regex_failures.append({"field": field, "regex": regex, "snippet": snippet.strip()})
            for m in re.finditer(r"Processing form: ([A-Z0-9\- ()]+)\n(Form \1: No pattern match found|Form \1 #[0-9]+:|Form \1: No pattern match found)", wi_log):
                form = m.group(1).strip()
                if f"Form {form}: No pattern match found" in m.group(0):
                    if form_status[form] != 'Pattern Matched, No Data Extracted':
                        form_status[form] = 'No Pattern Match'
                else:
                    if form_status[form] not in ['Fail', 'Pattern Matched, No Data Extracted']:
                        form_status[form] = 'Success'
            st.markdown("### Forms Extraction Status")
            status_colors = {'Success': 'green', 'Fail': 'red', 'Pattern Matched, No Data Extracted': 'orange', 'No Pattern Match': 'gray', 'Not Attempted': 'gray'}
            for form, status in sorted(form_status.items()):
                color = status_colors.get(status, 'gray')
                st.markdown(f"- <span style='color:{color};font-weight:bold'>{form}: {status}</span>", unsafe_allow_html=True)
            if no_fields:
                st.markdown("---\n#### Forms Detected but No Fields Extracted")
                for issue in no_fields:
                    st.error(f"**{issue['form']}**: Pattern matched, but no fields extracted. Fields attempted: {issue['fields']}")
                    with st.expander("Show raw form text snippet"):
                        st.code(issue['snippet'])
            if form_no_match:
                st.markdown("---\n#### Potential Forms Detected but No Pattern Matched")
                for issue in form_no_match:
                    st.warning(f"**{issue['form']}**: Detected in text but no pattern matched.")
                    with st.expander("Show text snippet"):
                        st.code(issue['snippet'])
            if regex_failures:
                st.markdown("---\n#### Field Extraction Regex Failures")
                for issue in regex_failures:
                    st.info(f"Field **{issue['field']}**: Regex `{issue['regex']}` failed.")
                    with st.expander("Show raw snippet"):
                        st.code(issue['snippet'])
            if not (no_fields or form_no_match or regex_failures):
                st.success("No critical extraction issues detected!")

    with tax_projection_tab:
        render_tax_projection(st.session_state['wi_projection'])
        
    with json_tab:
        st.subheader("Parsed WI Data (JSON)")
        st.json(st.session_state['wi_data'])
        
    with form_matching_tab:
        st.subheader("Form Pattern Matching")
        st.write(f"Found {len(st.session_state['wi_form_matching'])} WI documents.")
        wi_data = st.session_state.get('wi_data', {})
        wi_summary = st.session_state.get('wi_summary', [])
        wi_projection = st.session_state.get('wi_projection', [])
        # Display form matching results
        for result in st.session_state['wi_form_matching']:
            st.markdown(f"**Processing: {result['filename']}**")
            if result.get('owner'):
                st.text(f"Owner: {result['owner']}")
            if result['ssn'] and result['tax_period']:
                st.text(f"SSN: {result['ssn']} | Tax Period: {result['tax_period']}")
                st.text("-" * 50)
            st.text("🔍 Form Pattern Matching:")
            # Try to find extracted/calculated data for this file (by year)
            # We'll use wi_data and wi_summary for this
            for match in result['form_matches']:
                form_name = match['form_name']
                st.text(f"📋 {form_name}:")
                if match['matched']:
                    st.text("✅ Match found")
                    found = False
                    for year, forms in wi_data.items():
                        for form in forms:
                            # Try to match by form name and filename/source
                            form_file = form.get('SourceFile') or form.get('filename') or result['filename']
                            if form.get('Form') == form_name and form_file == result['filename']:
                                found = True
                                # Show unique identifier if available
                                unique_id = form.get('UniqueID')
                                label = form.get('Label', '')
                                extra = []
                                if unique_id and unique_id != 'UNKNOWN':
                                    extra.append(f"ID: {unique_id}")
                                if label and label != 'UNKNOWN':
                                    extra.append(label)
                                if extra:
                                    st.markdown(f"<span style='color: #888'>({' | '.join(extra)})</span>", unsafe_allow_html=True)
                                st.markdown(f"<span style='color: #888'>Source File: {form_file}</span>", unsafe_allow_html=True)
                                st.markdown(f"- **Extracted Fields:** {form.get('Fields', {})}")
                                st.markdown(f"- **Income:** {form.get('Income', 'N/A')}")
                                st.markdown(f"- **Withholding:** {form.get('Withholding', 'N/A')}")
                                st.markdown("---")
                    if not found:
                        st.warning("Pattern matched, but no fields extracted or calculated.")
                else:
                    st.text("❌ No match found")
            st.markdown("---")
    # In the Critical Issues tab, add debug output for cross-checking
            # Build a set of all parsed forms by filename (from wi_data)
            parsed_forms_by_file = {}
            wi_data = st.session_state.get('wi_data', {})
            for year, forms in wi_data.items():
                for form in forms:
                    filename = form.get('SourceFile') or form.get('filename') or None
                    form_name = form.get('Form')
                    if filename and form_name:
                        if filename not in parsed_forms_by_file:
                            parsed_forms_by_file[filename] = set()
                        parsed_forms_by_file[filename].add(form_name)
            # Debug: show parsed forms by file
            st.markdown("<details><summary>Debug: Parsed forms by file</summary><pre>" + str(parsed_forms_by_file) + "</pre></details>", unsafe_allow_html=True)
            for m in re.finditer(r"Potential form detected in text but no pattern matched: '([^']+)' at position (\d+)\. \[FILENAME: ([^\]]+)\] Snippet: (.+?)\n", wi_log, re.DOTALL):
                form_label, pos_str, filename, snippet = m.groups()
                wi_text = wi_texts.get(filename, None)
                start_pos = int(pos_str)
                # Only show as a critical issue if this form is NOT present in parsed_forms_by_file for this filename
                parsed_forms = parsed_forms_by_file.get(filename, set())
                # Debug: show cross-check for this form
                st.markdown(f"<details><summary>Debug: Checking {form_label} in {filename}</summary><pre>Parsed forms: {parsed_forms}</pre></details>", unsafe_allow_html=True)
                if form_label.strip() in parsed_forms:
                    continue  # Skip, it was actually parsed
                full_snippet = extract_full_form_snippet(form_label, wi_text, start_pos=start_pos, filename=filename)
                form_no_match.append({"form": form_label.strip(), "snippet": full_snippet})

    with log_tab:
        st.subheader("Log Output")
        st.text(st.session_state.get('wi_log', ''))

def render_tax_projection(summary_rows):
    """Render the tax projection page"""
    st.header("📊 SFR Tax Projection Calculator")
    st.markdown("---")
    
    if not summary_rows:
        st.info("💡 **No data available for tax projection.** Please process a case ID first to see tax projections.")
        st.stop()
    
    st.write("This calculator estimates what the IRS would assess if they filed a **Substitute for Return (SFR)** for you. It includes penalties and interest that would be added to your tax liability.")
    
    # SFR-specific warning
    st.warning("""
    **⚠️ SFR Projection:** This shows what the IRS would calculate if they filed for you, including:
    - Standard deduction only (no itemized deductions)
    - No credits or additional deductions
    - Failure to file penalties
    - Failure to pay penalties  
    - Interest on unpaid taxes
    """)
    
    # Tax calculation constants
    filing_status_options = [
        "Single", "Married Filing Jointly", "Married Filing Separately", "Head of Household", "Qualifying Widow(er)"
    ]
    
    # 2023 standard deduction and wage base
    std_deduction = {
        "Single": 13850,
        "Married Filing Jointly": 27700,
        "Married Filing Separately": 13850,
        "Head of Household": 20800,
        "Qualifying Widow(er)": 27700
    }
    ss_wage_base = 160200
    ss_rate = 0.124
    medicare_rate = 0.029
    
    # SFR Penalty rates
    ftf_rate = 0.05  # 5% per month for failure to file
    ftf_max = 0.25   # Maximum 25%
    ftp_rate = 0.005 # 0.5% per month for failure to pay
    interest_rate = 0.08  # 8% annual interest rate (approximate current rate)
    
    # 2023 tax brackets
    tax_brackets = {
        "Single": [
            (0, 11000, 0.10),
            (11000, 44725, 0.12),
            (44725, 95375, 0.22),
            (95375, 182100, 0.24),
            (182100, 231250, 0.32),
            (231250, 578125, 0.35),
            (578125, float('inf'), 0.37)
        ],
        "Married Filing Jointly": [
            (0, 22000, 0.10),
            (22000, 89450, 0.12),
            (89450, 190750, 0.22),
            (190750, 364200, 0.24),
            (364200, 462500, 0.32),
            (462500, 693750, 0.35),
            (693750, float('inf'), 0.37)
        ],
        "Married Filing Separately": [
            (0, 11000, 0.10),
            (11000, 44725, 0.12),
            (44725, 95375, 0.22),
            (95375, 182100, 0.24),
            (182100, 231250, 0.32),
            (231250, 346875, 0.35),
            (346875, float('inf'), 0.37)
        ],
        "Head of Household": [
            (0, 15700, 0.10),
            (15700, 59850, 0.12),
            (59850, 95350, 0.22),
            (95350, 182100, 0.24),
            (182100, 231250, 0.32),
            (231250, 578100, 0.35),
            (578100, float('inf'), 0.37)
        ],
        "Qualifying Widow(er)": [
            (0, 22000, 0.10),
            (22000, 89450, 0.12),
            (89450, 190750, 0.22),
            (190750, 364200, 0.24),
            (364200, 462500, 0.32),
            (462500, 693750, 0.35),
            (693750, float('inf'), 0.37)
        ]
    }
    
    # Process each year
    tax_rows = []
    
    for row in summary_rows:
        year = row['Tax Year']
        se_income = float(str(row['SE Income']).replace("$", "").replace(",", ""))
        nonse_income = float(str(row['Non-SE Income']).replace("$", "").replace(",", ""))
        se_withholding = float(str(row['SE Withholding']).replace("$", "").replace(",", ""))
        nonse_withholding = float(str(row['Non-SE Withholding']).replace("$", "").replace(",", ""))
        
        # Create expandable section for each year
        with st.expander(f"📅 Tax Year {year} - Click to expand", expanded=True):
            st.subheader(f"Tax Year {year}")
            
            # Income Summary Section
            st.markdown("#### 💰 Income Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Self-Employment Income", f"${se_income:,.2f}")
            with col2:
                st.metric("W-2/Other Income", f"${nonse_income:,.2f}")
            with col3:
                st.metric("Total Income", f"${se_income + nonse_income:,.2f}")
            
            # Filing Status Selection
            st.markdown("#### 📋 Filing Status")
            filing_status = st.selectbox(
                "Select your filing status for this year:",
                filing_status_options,
                key=f"fs_{year}",
                help="Choose the filing status that applies to you for this tax year"
            )
            
            # SFR Penalty Inputs
            st.markdown("#### ⏰ SFR Penalty Factors")
            col1, col2 = st.columns(2)
            
            with col1:
                months_late = st.number_input(
                    f"Months late for filing (Tax Year {year}):",
                    min_value=0,
                    max_value=60,
                    value=12,
                    key=f"months_{year}",
                    help="How many months after the due date would the IRS file the SFR?"
                )
            
            with col2:
                current_year = 2024  # Approximate current year
                years_since = current_year - int(year)
                st.info(f"**Years since {year}:** {years_since}")
            
            # Tax Calculations Section
            st.markdown("#### 🧮 SFR Tax Calculations")
            
            # Calculate taxes
            deduction = std_deduction[filing_status]
            ss_tax = min(se_income, ss_wage_base) * ss_rate
            medicare_tax = se_income * medicare_rate
            se_tax = ss_tax + medicare_tax
            taxable_income = max(0, se_income + nonse_income - deduction)
            
            # Federal tax calculation
            fed_tax = 0
            for bracket in tax_brackets[filing_status]:
                lower, upper, rate = bracket
                if taxable_income > lower:
                    fed_tax += (min(taxable_income, upper) - lower) * rate
                else:
                    break
            
            total_withholding = se_withholding + nonse_withholding
            base_tax_owed = se_tax + fed_tax - total_withholding
            
            # SFR Penalties and Interest
            if base_tax_owed > 0:
                # Failure to file penalty (5% per month, max 25%)
                ftf_penalty = min(base_tax_owed * ftf_rate * months_late, base_tax_owed * ftf_max)
                
                # Failure to pay penalty (0.5% per month)
                ftp_penalty = base_tax_owed * ftp_rate * months_late
                
                # Interest calculation (simplified - assumes average over time)
                avg_years = years_since + (months_late / 12)
                interest = base_tax_owed * interest_rate * avg_years
                
                total_owed = base_tax_owed + ftf_penalty + ftp_penalty + interest
            else:
                ftf_penalty = 0
                ftp_penalty = 0
                interest = 0
                total_owed = base_tax_owed
            
            # Display calculations in columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Deductions & Adjustments:**")
                st.write(f"• Standard Deduction: ${deduction:,.2f}")
                st.write(f"• Taxable Income: ${taxable_income:,.2f}")
                
                st.markdown("**Self-Employment Tax:**")
                st.write(f"• Social Security: ${ss_tax:,.2f}")
                st.write(f"• Medicare: ${medicare_tax:,.2f}")
                st.write(f"• **Total SE Tax: ${se_tax:,.2f}**")
            
            with col2:
                st.markdown("**Federal Income Tax:**")
                st.write(f"• Tax on ${taxable_income:,.2f}: ${fed_tax:,.2f}")
                
                st.markdown("**Withholding:**")
                st.write(f"• SE Withholding: ${se_withholding:,.2f}")
                st.write(f"• Other Withholding: ${nonse_withholding:,.2f}")
                st.write(f"• **Total Withholding: ${total_withholding:,.2f}**")
            
            # SFR Penalties Section
            if base_tax_owed > 0:
                st.markdown("#### ⚠️ SFR Penalties & Interest")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Failure to File Penalty", f"${ftf_penalty:,.2f}", delta=f"{months_late} months")
                with col2:
                    st.metric("Failure to Pay Penalty", f"${ftp_penalty:,.2f}", delta=f"{months_late} months")
                with col3:
                    st.metric("Interest", f"${interest:,.2f}", delta=f"{avg_years:.1f} years")
            
            # Tax Summary Box
            st.markdown("---")
            
            if total_owed > 0:
                st.error(f"## 💸 **SFR Assessment: ${total_owed:,.2f}**")
                st.info(f"*This is what the IRS would likely assess for {year} if they filed an SFR*")
                
                # Breakdown
                st.markdown("**Breakdown:**")
                st.write(f"• Base Tax Owed: ${base_tax_owed:,.2f}")
                if base_tax_owed > 0:
                    st.write(f"• Failure to File Penalty: ${ftf_penalty:,.2f}")
                    st.write(f"• Failure to Pay Penalty: ${ftp_penalty:,.2f}")
                    st.write(f"• Interest: ${interest:,.2f}")
            else:
                st.success(f"## 💰 **No SFR Assessment: ${abs(total_owed):,.2f}**")
                st.info(f"*No additional taxes would be assessed for {year}*")
            
            # Store for table
            tax_rows.append({
                'Year': year,
                'Filing Status': filing_status,
                'SE Income': se_income,
                'Non-SE Income': nonse_income,
                'SE Withholding': se_withholding,
                'Non-SE Withholding': nonse_withholding,
                'SE Tax': se_tax,
                'Taxable Income': taxable_income,
                'Federal Tax': fed_tax,
                'Total Withholding': total_withholding,
                'Base Tax Owed': base_tax_owed,
                'FTF Penalty': ftf_penalty,
                'FTP Penalty': ftp_penalty,
                'Interest': interest,
                'Total Tax Owed': total_owed
            })
    
    # Summary Table Section
    st.markdown("---")
    st.markdown("#### 📊 SFR Summary Table")
    st.write("Below is a summary of all SFR projections:")
    
    if tax_rows:
        # Create summary table
        display_cols = ['Year', 'Filing Status', 'Total Tax Owed', 'Base Tax Owed', 'FTF Penalty', 'FTP Penalty', 'Interest', 'SE Income', 'Non-SE Income']
        tax_df = pd.DataFrame(tax_rows)
        
        # Format currency columns
        currency_cols = ['SE Income', 'Non-SE Income', 'Base Tax Owed', 'FTF Penalty', 'FTP Penalty', 'Interest', 'Total Tax Owed']
        for col in currency_cols:
            tax_df[col] = tax_df[col].apply(lambda x: f"${x:,.2f}")
        
        # Display table with better styling
        st.dataframe(
            tax_df[display_cols], 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Year": st.column_config.NumberColumn("Tax Year", format="%d"),
                "Filing Status": st.column_config.TextColumn("Filing Status"),
                "Total Tax Owed": st.column_config.TextColumn("SFR Assessment", help="Total amount IRS would assess"),
                "Base Tax Owed": st.column_config.TextColumn("Base Tax", help="Tax before penalties"),
                "FTF Penalty": st.column_config.TextColumn("FTF Penalty", help="Failure to file penalty"),
                "FTP Penalty": st.column_config.TextColumn("FTP Penalty", help="Failure to pay penalty"),
                "Interest": st.column_config.TextColumn("Interest", help="Interest on unpaid taxes"),
                "SE Income": st.column_config.TextColumn("SE Income"),
                "Non-SE Income": st.column_config.TextColumn("W-2/Other Income")
            }
        )
        
        # Overall summary
        st.markdown("---")
        st.markdown("#### 📈 Overall SFR Summary")
        
        total_owed_all_years = sum(row['Total Tax Owed'] for row in tax_rows)
        total_base_tax = sum(row['Base Tax Owed'] for row in tax_rows)
        total_penalties = sum(row['FTF Penalty'] + row['FTP Penalty'] for row in tax_rows)
        total_interest = sum(row['Interest'] for row in tax_rows)
        total_income_all_years = sum(row['SE Income'] + row['Non-SE Income'] for row in tax_rows)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Income (All Years)", f"${total_income_all_years:,.2f}")
        with col2:
            st.metric("Base Tax Liability", f"${total_base_tax:,.2f}")
        with col3:
            st.metric("Total Penalties", f"${total_penalties:,.2f}")
        with col4:
            st.metric("Total Interest", f"${total_interest:,.2f}")
        
        st.markdown("---")
        if total_owed_all_years > 0:
            st.error(f"## 💸 **Total SFR Assessment: ${total_owed_all_years:,.2f}**")
            st.info(f"*This is the total amount the IRS would likely assess across all years*")
        else:
            st.success(f"## 💰 **No SFR Assessment: ${abs(total_owed_all_years):,.2f}**")
            st.info(f"*No additional taxes would be assessed across all years*")
    
    # Disclaimer
    st.markdown("---")
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ff6b6b;'>
    <strong>⚠️ SFR Disclaimer:</strong> This is an estimation tool for Substitute for Return scenarios. 
    Actual penalties and interest may vary based on specific circumstances, payment history, and IRS discretion. 
    This projection assumes the IRS would file an SFR with standard deduction only and no additional credits or deductions.
    Please consult with a tax professional for accurate assessment of your specific situation.
    </div>
    """, unsafe_allow_html=True)

def get_at_files(case_id: str) -> list:
    """
    Get list of AT (Account Transcript) files associated with a case.
    """
    cookies, user_agent, message = load_cookies_from_file()
    if not cookies:
        st.error("Authentication required. Please ensure cookies are valid.")
        st.info("Please use the '🔐 TPS Login' tab in the sidebar to authenticate.")
        return []

    cookie_header = cookies if isinstance(cookies, str) else ""

    url = f"https://tps.logiqs.com/API/Document/gridBind?caseid={case_id}&type=grid"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "User-Agent": user_agent,
        "Cookie": cookie_header
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            timeout=30,
            follow_redirects=False
        )

        if response.status_code == 302:
            location = response.headers.get("Location", "").lower()
            if "login" in location or "default.aspx" in location:
                st.error("Authentication required. Please ensure cookies are valid.")
                st.info("Please use the '🔐 TPS Login' tab in the sidebar to authenticate.")
                return []

        response.raise_for_status()
        response_data = response.json()

        if not isinstance(response_data, dict) or "Result" not in response_data:
            st.error("Invalid response structure from API")
            return []

        docs = response_data["Result"]
        if not isinstance(docs, list):
            st.error("Invalid document list format")
            return []

        # Filter for AT documents
        at_files = []
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            name = doc.get("Name", "")
            if not name:
                continue
            # Check for standalone AT in the filename (not part of another word)
            if re.search(r'\bAT\s+\d', name):  # Matches "AT" followed by a space and a number
                case_doc_id = doc.get("CaseDocumentID")
                if case_doc_id:
                    at_files.append({
                        "FileName": name,
                        "CaseDocumentID": case_doc_id
                    })
        return at_files
    except Exception as e:
        st.error(f"Error fetching case files: {str(e)}")
        return []

def format_year(year):
    """Format year consistently by removing commas and converting to string"""
    if isinstance(year, str):
        return year.replace(',', '')
    return str(year)

def extract_at_transactions(text):
    """Extract transaction data from AT transcript text (robust to compact and spaced formats)"""
    import re
    from datetime import datetime
    # Find the transactions section
    idx = text.find("TRANSACTIONS")
    if idx < 0:
        return []
    buf = text[idx:]
    transactions = []
    # Regex for compact format (single line, no spaces between columns)
    compact_regex = re.compile(r'^(\d{3}|n/a)([^\d\n]+?)(\d{8})\s+(\d{2}-\d{2}-\d{4})\s+(-?\$?[\d,]+\.\d{2})', re.MULTILINE)
    # Regex for spaced/multiline format (columns with headers)
    spaced_regex = re.compile(r'^(\d{3}|n/a)\s*([^\n]+)\n(?:[\w\s]*)?(\d{2}-\d{2}-\d{4})\s*\n\$?([\d,\.-]+)', re.MULTILINE)
    # Try compact format first
    for match in compact_regex.finditer(buf):
        code, desc, cyc, post, amt = match.groups()
        # Try to parse cycle date
        try:
            cycle_date = f"{cyc[:4]}-{cyc[4:6]}-{cyc[6:]}"
        except Exception:
            cycle_date = ''
        # Parse post date
        try:
            post_date = datetime.strptime(post, "%m-%d-%Y").date().isoformat()
        except Exception:
            post_date = post
        # Parse amount
        try:
            amount = float(amt.replace('$','').replace(',',''))
        except Exception:
            amount = 0.0
        transactions.append({
            "code": code.strip(),
            "meaning": desc.strip(),
            "cycle_date": cycle_date,
            "date": post_date,
            "amount": amount
        })
    # If no compact matches, try spaced format
    if not transactions:
        # Look for special lines like 'No tax return filed'
        for line in buf.splitlines():
            if re.search(r'no tax return filed', line, re.IGNORECASE):
                transactions.append({
                    'code': 'n/a',
                    'meaning': 'No tax return filed',
                    'cycle_date': '',
                    'date': '',
                    'amount': 0.0
                })
        for match in spaced_regex.finditer(buf):
            code, desc, post, amt = match.groups()
            # Parse post date
            try:
                post_date = datetime.strptime(post, "%m-%d-%Y").date().isoformat()
            except Exception:
                post_date = post
            # Parse amount
            try:
                amount = float(amt.replace('$','').replace(',',''))
            except Exception:
                amount = 0.0
            transactions.append({
                "code": code.strip(),
                "meaning": desc.strip(),
                "cycle_date": '',
                "date": post_date,
                "amount": amount
            })
    return transactions

def extract_at_data(text):
    """Extract data from Account Transcript text (robust to all formats)"""
    data = {}
    # Extract tax year (handle all known formats)
    year_match = re.search(r'Report for Tax Period Ending:\s*\d{2}-\d{2}-(\d{4})', text)
    if year_match:
        year = year_match.group(1)
        data['tax_year'] = format_year(year)
        logger.info(f"Found tax year from Report for Tax Period Ending: {data['tax_year']}")
    else:
        year_match = re.search(r'TAX PERIOD:\s*Dec\.\s*31,\s*(\d{4})', text, re.IGNORECASE)
        if year_match:
            year = year_match.group(1)
            data['tax_year'] = format_year(year)
            logger.info(f"Found tax year from TAX PERIOD: {data['tax_year']}")
        else:
            year_match = re.search(r'TAX PERIOD:\s*([A-Za-z]+\.\s*\d{1,2},?\s*\d{4})', text, re.IGNORECASE)
            if year_match:
                # Try to extract year from the matched string
                year = re.search(r'(\d{4})', year_match.group(1))
                if year:
                    data['tax_year'] = format_year(year.group(1))
                    logger.info(f"Found tax year from TAX PERIOD alt: {data['tax_year']}")
                else:
                    data['tax_year'] = 'Unknown'
            else:
                year_match = re.search(r'(\d{4})', text)
                if year_match:
                    data['tax_year'] = format_year(year_match.group(1))
                    logger.info(f"Found tax year from fallback pattern: {data['tax_year']}")
                else:
                    logger.warning("No tax year found")
                    data['tax_year'] = 'Unknown'
    # Extract financial data (robust to upper/lowercase, colon/space, missing values)
    financial_patterns = {
        'account_balance': r'(?:ACCOUNT BALANCE|Account balance)[:\s]*[\$]?([\d,\.\-]+)',
        'accrued_interest': r'(?:ACCRUED INTEREST|Accrued interest)[:\s]*[\$]?([\d,\.\-]+)',
        'accrued_penalty': r'(?:ACCRUED PENALTY|Accrued penalty)[:\s]*[\$]?([\d,\.\-]+)',
        'total_balance': r'(?:ACCOUNT BALANCE PLUS ACCRUALS|Account balance plus accruals).*?:[\s]*[\$]?([\d,\.\-]+)',
        'adjusted_gross_income': r'(?:ADJUSTED GROSS INCOME|Adjusted gross income)[:\s]*[\$]?([\d,\.\-]+)',
        'taxable_income': r'(?:TAXABLE INCOME|Taxable income)[:\s]*[\$]?([\d,\.\-]+)',
        'tax_per_return': r'(?:TAX PER RETURN|Tax per return)[:\s]*[\$]?([\d,\.\-]+)',
        'se_tax_taxpayer': r'(?:SE TAXABLE INCOME TAXPAYER|SE taxable income taxpayer)[:\s]*[\$]?([\d,\.\-]+)',
        'se_tax_spouse': r'(?:SE TAXABLE INCOME SPOUSE|SE taxable income spouse)[:\s]*[\$]?([\d,\.\-]+)',
        'total_se_tax': r'(?:TOTAL SELF EMPLOYMENT TAX|Total self employment tax)[:\s]*[\$]?([\d,\.\-]+)'
    }
    for key, pattern in financial_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                amount = float(match.group(1).replace(',', ''))
                data[key] = amount
                logger.info(f"Found {key}: {amount}")
            except ValueError:
                logger.warning(f"Could not parse amount for {key}: {match.group(1)}")
                data[key] = 0.00
        else:
            logger.warning(f"No match found for {key}")
            data[key] = 0.00
    # Extract filing status
    filing_match = re.search(r'(?:FILING STATUS|Filing status)[:\s]*([^,\n]+)', text, re.IGNORECASE)
    if filing_match:
        data['filing_status'] = filing_match.group(1).strip()
    # Extract processing date (robust to all formats)
    processing_match = re.search(r'(?:PROCESSING DATE|Processing date)[:\s]*([A-Za-z]+\.?\s+\d{1,2},?\s*\d{4})', text)
    if processing_match:
        data['processing_date'] = processing_match.group(1)
        logger.info(f"Found processing date: {data['processing_date']}")
    else:
        alt_processing_match = re.search(r'(?:PROCESSING DATE|Processing date)[:\s]*([A-Za-z]+\.?\s+\d{1,2}\s+\d{4})', text)
        if alt_processing_match:
            data['processing_date'] = alt_processing_match.group(1)
            logger.info(f"Found processing date (alt format): {data['processing_date']}")
        else:
            logger.warning("No processing date found")
    # Extract transactions
    data['transactions'] = extract_at_transactions(text)
    return data

def process_at_documents(case_id, at_files):
    """Process all AT documents once and store results"""
    from utils.tp_s_parser import TPSParser
    all_data = []
    # Set up logging
    log_buffer = io.StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    log_handler.setLevel(logging.INFO)
    logger.addHandler(log_handler)
    with st.spinner("Processing Account Transcript documents..."):
        progress_bar = st.progress(0)
        total_files = len(at_files)
        for idx, at_file in enumerate(at_files):
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing file: {at_file['FileName']}")
            logger.info(f"{'='*50}\n")
            pdf_bytes = download_file(at_file["CaseDocumentID"], case_id)
            if pdf_bytes:
                text = extract_text_from_pdf(pdf_bytes)
                if text:
                    logger.info("Complete extracted text from PDF:")
                    logger.info("-" * 50)
                    logger.info(text)
                    logger.info("-" * 50)
                    data = extract_at_data(text)
                    if data:
                        # Extract owner from filename
                        owner = TPSParser.extract_owner_from_filename(at_file['FileName'])
                        data['owner'] = owner or 'Unknown'
                        data['source_file'] = at_file['FileName']
                        all_data.append(data)
            progress_bar.progress((idx + 1) / total_files)
    st.session_state['at_data'] = all_data
    st.session_state['at_log'] = log_buffer.getvalue()
    all_alerts = []
    for year_data in all_data:
        if 'transactions' in year_data:
            alerts = get_transaction_alerts(year_data['transactions'])
            all_alerts.extend(alerts)
    st.session_state['at_alerts'] = all_alerts
    logger.removeHandler(log_handler)
    log_buffer.close()

def render_at_parser():
    """Render the AT Parser page (Account Transcript)"""
    st.title("AT Parser")
    case_id = st.session_state.get('case_id', None)
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return
    if 'at_data' not in st.session_state:
        st.warning("No Account Transcript data available. Please process a case ID first.")
        return
    alerts_tab, summary_tab, transactions_tab, json_tab, log_tab = st.tabs([
        "Alerts", "Summary", "Transactions", "JSON", "Logs"
    ])

    with alerts_tab:
        st.subheader("Account Alerts")
        alerts = st.session_state.get('at_alerts', [])
        if alerts:
            display_alerts(alerts)
        else:
            st.success("✅ No significant alerts found in the account transcripts.")

    with summary_tab:
        st.subheader("Account Transcript Summary")
        at_data = st.session_state['at_data']
        summary_rows = []
        for data in at_data:
            tax_year = data.get('tax_year', 'Unknown')
            if tax_year == 'Unknown':
                processing_date = data.get('processing_date', '')
                if processing_date:
                    year_match = re.search(r'(\d{4})', processing_date)
                    if year_match:
                        tax_year = format_year(year_match.group(1))
            # Determine if return filed using code 150 logic
            transactions = data.get('transactions', [])
            filed = False
            for trans in transactions:
                if trans.get('code') == '150':
                    filed = True
                    break
            # Also check for explicit 'No tax return filed' transaction
            for trans in transactions:
                if trans.get('meaning', '').lower().startswith('no tax return filed'):
                    filed = False
            row = {
                'Tax Year': format_year(tax_year),
                'Owner': data.get('owner', 'Unknown'),
                'Return Filed': 'Yes' if filed else 'No',
                'Filing Status': data.get('filing_status', 'Unknown'),
                'Current Balance': data.get('account_balance', 0),
                'Processing Date': data.get('processing_date', 'Unknown'),
                'AGI': data.get('adjusted_gross_income', 0),
                'Taxable Income': data.get('taxable_income', 0),
                'Tax Per Return': data.get('tax_per_return', 0)
            }
            summary_rows.append(row)
        def year_key(row):
            try:
                return int(row['Tax Year'])
            except Exception:
                return -9999
        summary_rows = sorted(summary_rows, key=year_key, reverse=True)
        if summary_rows:
            df = pd.DataFrame(summary_rows)
            currency_cols = ['Current Balance', 'AGI', 'Taxable Income', 'Tax Per Return']
            for col in currency_cols:
                df[col] = df[col].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)
            st.table(df)
        else:
            st.info("No Account Transcript data available")

    with transactions_tab:
        st.subheader("Transaction History")
        at_data = st.session_state['at_data']
        
        # Group transactions by year
        for year_data in sorted(at_data, key=lambda x: x.get('tax_year', ''), reverse=True):
            tax_year = year_data.get('tax_year', 'Unknown')
            transactions = year_data.get('transactions', [])
            
            # If tax_year is unknown, try to extract from processing date
            if tax_year == 'Unknown':
                processing_date = year_data.get('processing_date', '')
                if processing_date:
                    year_match = re.search(r'(\d{4})', processing_date)
                    if year_match:
                        tax_year = format_year(year_match.group(1))
            
            if transactions:
                with st.expander(f"Tax Year {format_year(tax_year)}", expanded=True):
                    trans_df = pd.DataFrame(transactions)
                    if not trans_df.empty:
                        # Format amount column
                        if 'amount' in trans_df.columns:
                            trans_df['amount'] = trans_df['amount'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else '')
                        st.dataframe(trans_df, use_container_width=True)
                    else:
                        st.info("No transactions found for this year")
            else:
                st.info(f"No transactions found for Tax Year {format_year(tax_year)}")

    with json_tab:
        st.subheader("Raw AT Data (JSON)")
        st.json(st.session_state['at_data'])

    with log_tab:
        st.subheader("Log Output")
        st.text(st.session_state.get('at_log', ''))

def get_roa_files(case_id: str) -> list:
    """
    Get list of ROA (Record of Account) files associated with a case.
    """
    cookies, user_agent, message = load_cookies_from_file()
    if not cookies:
        st.error("Authentication required. Please ensure cookies are valid.")
        return []

    cookie_header = cookies if isinstance(cookies, str) else ""

    url = f"https://tps.logiqs.com/API/Document/gridBind?caseid={case_id}&type=grid"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "User-Agent": user_agent,
        "Cookie": cookie_header
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            timeout=30,
            follow_redirects=False
        )

        if response.status_code == 302:
            location = response.headers.get("Location", "").lower()
            if "login" in location or "default.aspx" in location:
                st.error("Authentication required. Please ensure cookies are valid.")
                return []

        response.raise_for_status()
        response_data = response.json()

        if not isinstance(response_data, dict) or "Result" not in response_data:
            st.error("Invalid response structure from API")
            return []

        docs = response_data["Result"]
        if not isinstance(docs, list):
            st.error("Invalid document list format")
            return []

        # Filter for ROA documents
        roa_files = []
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            name = doc.get("Name", "")
            if not name:
                continue
            # Check for standalone ROA in the filename
            if re.search(r'\bROA\s+\d', name):  # Matches "ROA" followed by a space and a number
                case_doc_id = doc.get("CaseDocumentID")
                if case_doc_id:
                    roa_files.append({
                        "FileName": name,
                        "CaseDocumentID": case_doc_id
                    })
        return roa_files
    except Exception as e:
        st.error(f"Error fetching case files: {str(e)}")
        return []

def get_trt_files(case_id: str) -> list:
    """
    Get list of TRT (Tax Return Transcript) files associated with a case.
    """
    cookies, user_agent, message = load_cookies_from_file()
    if not cookies:
        st.error("Authentication required. Please ensure cookies are valid.")
        return []

    cookie_header = cookies if isinstance(cookies, str) else ""

    url = f"https://tps.logiqs.com/API/Document/gridBind?caseid={case_id}&type=grid"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "User-Agent": user_agent,
        "Cookie": cookie_header
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            timeout=30,
            follow_redirects=False
        )

        if response.status_code == 302:
            location = response.headers.get("Location", "").lower()
            if "login" in location or "default.aspx" in location:
                st.error("Authentication required. Please ensure cookies are valid.")
                return []

        response.raise_for_status()
        response_data = response.json()

        if not isinstance(response_data, dict) or "Result" not in response_data:
            st.error("Invalid response structure from API")
            return []

        docs = response_data["Result"]
        if not isinstance(docs, list):
            st.error("Invalid document list format")
            return []

        # Filter for TRT documents
        trt_files = []
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            name = doc.get("Name", "")
            if not name:
                continue
            # Check for standalone TRT in the filename
            if re.search(r'\bTRT\s+\d', name):  # Matches "TRT" followed by a space and a number
                case_doc_id = doc.get("CaseDocumentID")
                if case_doc_id:
                    trt_files.append({
                        "FileName": name,
                        "CaseDocumentID": case_doc_id
                    })
        return trt_files
    except Exception as e:
        st.error(f"Error fetching case files: {str(e)}")
        return []

def render_roa_parser():
    """Render the ROA Parser page (Record of Account)"""
    st.title("ROA Parser")
    
    # Get case_id from session state
    case_id = st.session_state.get('case_id', None)
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return

    # Set up Streamlit tabs
    summary_tab, log_tab = st.tabs(["Summary", "Logs"])

    # Set up a string buffer for logs
    import io as _io
    log_buffer = _io.StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    log_handler.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    roa_files = get_roa_files(case_id)
    if roa_files:
        with summary_tab:
            st.write(f"Found {len(roa_files)} ROA documents.")
            st.info("Summary tab is currently under development. After analyzing the logs, we will implement the relevant data extraction and summary here.")
            
        with log_tab:
            st.subheader("Log Output")
            for roa_file in roa_files:
                logger.info(f"Processing file: {roa_file['FileName']}")
                pdf_bytes = download_file(roa_file["CaseDocumentID"], case_id)
                if pdf_bytes:
                    text = extract_text_from_pdf(pdf_bytes)
                    if text:
                        logger.info("Successfully extracted text from PDF")
                        logger.info("Raw text content:")
                        logger.info("-" * 50)
                        logger.info(text)
                        logger.info("-" * 50)
                    else:
                        logger.warning(f"Failed to extract text from {roa_file['FileName']}")
                else:
                    logger.error(f"Failed to download {roa_file['FileName']}")
            st.text(log_buffer.getvalue())
    else:
        with summary_tab:
            st.warning("No ROA documents found for this case ID")

    # Clean up logging handler
    logger.removeHandler(log_handler)

def render_trt_parser():
    """Render the TRT Parser page (Tax Return Transcript)"""
    st.title("TRT Parser")
    
    # Get case_id from session state
    case_id = st.session_state.get('case_id', None)
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return

    # Set up Streamlit tabs
    summary_tab, log_tab = st.tabs(["Summary", "Logs"])

    # Set up a string buffer for logs
    import io as _io
    log_buffer = _io.StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    log_handler.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    trt_files = get_trt_files(case_id)
    if trt_files:
        with summary_tab:
            st.write(f"Found {len(trt_files)} TRT documents.")
            st.info("Summary tab is currently under development. After analyzing the logs, we will implement the relevant data extraction and summary here.")
            
        with log_tab:
            st.subheader("Log Output")
            for trt_file in trt_files:
                logger.info(f"Processing file: {trt_file['FileName']}")
                pdf_bytes = download_file(trt_file["CaseDocumentID"], case_id)
                if pdf_bytes:
                    text = extract_text_from_pdf(pdf_bytes)
                    if text:
                        logger.info("Successfully extracted text from PDF")
                        logger.info("Raw text content:")
                        logger.info("-" * 50)
                        logger.info(text)
                        logger.info("-" * 50)
                    else:
                        logger.warning(f"Failed to extract text from {trt_file['FileName']}")
                else:
                    logger.error(f"Failed to download {trt_file['FileName']}")
            st.text(log_buffer.getvalue())
    else:
        with summary_tab:
            st.warning("No TRT documents found for this case ID")

    # Clean up logging handler
    logger.removeHandler(log_handler)

def render_tax_summary():
    """Render the Tax Summary page combining data from all parsers"""
    st.title("Tax Summary")
    
    # Get case_id from session state
    case_id = st.session_state.get('case_id', None)
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return
        
    # Set up Streamlit tabs
    summary_tab, details_tab, json_tab, log_tab = st.tabs(["Summary", "Details", "JSON", "Logs"])
    
    # Get data from session state
    wi_data = st.session_state.get('wi_data', {})
    at_data = st.session_state.get('at_data', [])
    
    # Convert all years to strings for consistent comparison
    all_years = sorted(set(
        [str(year) for year in wi_data.keys()] + 
        [data['tax_year'] for data in at_data]
    ))
    
    # Convert AT data to a year-keyed dictionary for easier lookup
    at_years_dict = {data['tax_year']: data for data in at_data}
    
    with summary_tab:
        st.subheader("Tax Years Summary")
        
        # Create a DataFrame for the summary
        summary_data = []
        for year in sorted(all_years, reverse=True):
            formatted_year = format_year(year)
            at_data = at_years_dict.get(formatted_year)
            summary_data.append({
                "Tax Year": formatted_year,
                "Return Filed": "Yes" if at_data else "No AT Data"
            })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            st.table(df)
        else:
            st.info("🔄 No Account Transcript data available yet")
    
    with details_tab:
        st.info("Detailed analysis view is under development. This tab will show more specific breakdowns of income types, filing thresholds, and compliance indicators.")
    
    with json_tab:
        st.subheader("Combined Tax Data")
        
        # Create a combined summary by year
        combined_summary = {}
        
        for year in all_years:
            at_data = at_years_dict.get(str(year))
            wi_year_data = wi_data.get(int(year), [])
            
            combined_summary[year] = {
                'wi_data': {
                    'forms': wi_year_data,
                    'total_income': sum(form['Income'] for form in wi_year_data if form.get('Income') is not None),
                    'total_withholding': sum(form['Withholding'] for form in wi_year_data if form.get('Withholding') is not None)
                },
                'at_data': at_data if at_data else None,
                'return_status': 'Filed' if at_data and any(
                    trans.get('code') in ['150', '976'] 
                    for trans in at_data.get('transactions', [])
                ) else 'Not Filed',
                'has_at_data': bool(at_data)
            }
        
        st.json(combined_summary)
    
    with log_tab:
        st.info("Log view is under development. This tab will show processing logs and data validation results.")

def render_settings():
    """Render the settings page"""
    st.title("Settings")
    st.write("Application Settings and Information")
    
    # Cookie Status
    st.subheader("Authentication Status")
    cookies, user_agent, message = load_cookies_from_file()
    if cookies:
        st.success("✅ Valid cookies found")
    else:
        st.error("❌ No valid cookies found")
        st.info("Please use the '🔐 TPS Login' tab in the sidebar to authenticate.")
    
    # About Section
    st.subheader("About")
    st.write("""
    This application helps parse and analyze IRS transcripts:
    
    - **WI Parser**: Analyzes Wage & Income transcripts
        - Supports W-2, 1099s, and other income forms
        - Calculates yearly totals
        - Provides tax projections
    
    - **AT Parser**: Analyzes Account Transcripts
        - Shows account balances and status
        - Lists all transactions with explanations
        - Tracks penalties and interest
        
    - **Tax Summary**: Combines data from all sources
        - Shows combined yearly summaries
        - Tracks return filing status
        - Compares reported income with filed returns
    """)

def create_tax_summary(wi_data: dict, at_data: list) -> dict:
    """
    Combines WI and AT data to create comprehensive tax analysis
    
    Args:
        wi_data: Dictionary with years as keys, arrays of forms as values
        at_data: List of account transcript dictionaries
        
    Returns:
        Dictionary with year-by-year analysis including discrepancies and recommendations
    """
    
    def calculate_wi_totals(year_forms):
        """Calculate total income and withholding from WI forms"""
        total_income = 0
        total_withholding = 0
        
        for form in year_forms:
            # Only count SE and Non-SE income (exclude "Neither" category)
            if form.get('Category') in ['SE', 'Non-SE']:
                total_income += form.get('Income', 0)
                total_withholding += form.get('Withholding', 0)
        
        return total_income, total_withholding
    
    def find_at_data_for_year(year, at_data):
        """Find AT data for a specific year"""
        for at_record in at_data:
            at_year = at_record.get('tax_year', '')
            if at_year and str(at_year).isdigit() and int(at_year) == int(year):
                return at_record
        return None
    
    def determine_filing_status(at_record):
        """Determine if return was filed based on AT transactions"""
        if not at_record or 'transactions' not in at_record:
            return "Not Filed"
        
        # Look for transaction code 150 (Return filed) or 976 (Return filed)
        for transaction in at_record['transactions']:
            if transaction.get('code') in ['150', '976']:
                return "Filed"
        
        return "Not Filed"
    
    def calculate_simple_tax(income, filing_status="Single"):
        """Simple tax calculation for unfiled year projections"""
        # 2024 tax brackets (simplified)
        brackets = {
            "Single": [
                (0, 11600, 0.10),
                (11600, 47150, 0.12),
                (47150, 100525, 0.22),
                (100525, 191950, 0.24),
                (191950, 243725, 0.32),
                (243725, 609350, 0.35),
                (609350, float('inf'), 0.37)
            ],
            "Married Filing Joint": [
                (0, 23200, 0.10),
                (23200, 94300, 0.12),
                (94300, 201050, 0.22),
                (201050, 383900, 0.24),
                (383900, 487450, 0.32),
                (487450, 731200, 0.35),
                (731200, float('inf'), 0.37)
            ]
        }
        
        # Use Single brackets as default
        tax_brackets = brackets.get(filing_status, brackets["Single"])
        
        # Standard deduction
        std_deduction = {"Single": 14600, "Married Filing Joint": 29200}.get(filing_status, 14600)
        
        # Calculate taxable income
        taxable_income = max(0, income - std_deduction)
        
        # Calculate tax
        tax = 0
        for lower, upper, rate in tax_brackets:
            if taxable_income > lower:
                tax += (min(taxable_income, upper) - lower) * rate
            else:
                break
        
        return tax
    
    def generate_recommendations(analysis_data):
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        income_discrepancy = analysis_data.get('income_discrepancy', 0)
        return_status = analysis_data.get('return_status', 'Unknown')
        needs_amendment = analysis_data.get('needs_amendment', False)
        unfiled_liability = analysis_data.get('unfiled_liability', 0)
        
        if return_status == "Not Filed":
            if unfiled_liability > 10000:
                recommendations.append(f"URGENT: Unfiled return with estimated liability of ${unfiled_liability:,.2f}")
                recommendations.append("Consider filing immediately to stop penalty accumulation")
            elif unfiled_liability > 5000:
                recommendations.append(f"High priority: Unfiled return with estimated liability of ${unfiled_liability:,.2f}")
                recommendations.append("File return to minimize penalties and interest")
            elif unfiled_liability > 0:
                recommendations.append(f"File return to address ${unfiled_liability:,.2f} estimated liability")
            else:
                recommendations.append("Return appears to have no tax liability - consider filing for refund")
        
        elif return_status == "Filed":
            if needs_amendment and income_discrepancy > 0:
                if income_discrepancy > 10000:
                    recommendations.append(f"URGENT: Consider amended return for unreported income of ${income_discrepancy:,.2f}")
                elif income_discrepancy > 5000:
                    recommendations.append(f"Review potential unreported income of ${income_discrepancy:,.2f}")
                    recommendations.append("Consider amended return if income was legitimately excluded")
                else:
                    recommendations.append(f"Minor discrepancy of ${income_discrepancy:,.2f} - review for accuracy")
            
            elif income_discrepancy < 0:
                # AT AGI is higher than WI income (may be legitimate)
                recommendations.append(f"AT shows ${abs(income_discrepancy):,.2f} more income than WI forms")
                recommendations.append("Verify if additional income sources were properly reported")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("No significant issues detected - review for completeness")
        
        return recommendations
    
    def calculate_priority_level(analysis_data):
        """Calculate priority level (1=urgent, 2=high, 3=medium)"""
        return_status = analysis_data.get('return_status', 'Unknown')
        income_discrepancy = abs(analysis_data.get('income_discrepancy', 0))
        unfiled_liability = analysis_data.get('unfiled_liability', 0)
        
        if return_status == "Not Filed":
            if unfiled_liability > 10000:
                return 1  # Urgent
            elif unfiled_liability > 5000:
                return 2  # High
            else:
                return 3  # Medium
        elif return_status == "Filed":
            if income_discrepancy > 10000:
                return 1  # Urgent
            elif income_discrepancy > 5000:
                return 2  # High
            elif income_discrepancy > 1000:
                return 3  # Medium
            else:
                return 3  # Medium (no significant issues)
        
        return 3  # Default to medium
    
    # Initialize result structure
    result = {}
    
    # Get all unique years from both WI and AT data
    wi_years = set(int(year) for year in wi_data.keys())
    at_years = set()
    for at_record in at_data:
        tax_year = at_record.get('tax_year', '')
        if tax_year and str(tax_year).isdigit():
            at_years.add(int(tax_year))
    
    all_years = sorted(wi_years.union(at_years), reverse=True)
    
    for year in all_years:
        year_str = str(year)
        
        # Get WI data for this year
        year_forms = wi_data.get(year, [])
        wi_total_income, wi_total_withholding = calculate_wi_totals(year_forms)
        
        # Get AT data for this year
        at_record = find_at_data_for_year(year_str, at_data)
        return_status = determine_filing_status(at_record)
        
        # Calculate income discrepancy
        at_agi = at_record.get('adjusted_gross_income', 0) if at_record else 0
        income_discrepancy = wi_total_income - at_agi
        
        # Determine if amendment is needed
        needs_amendment = False
        if return_status == "Filed" and abs(income_discrepancy) > 1000:
            needs_amendment = True
        
        # Calculate unfiled liability
        unfiled_liability = 0
        if return_status == "Not Filed" and wi_total_income > 0:
            filing_status = at_record.get('filing_status', 'Single') if at_record else 'Single'
            estimated_tax = calculate_simple_tax(wi_total_income, filing_status)
            unfiled_liability = max(0, estimated_tax - wi_total_withholding)
        
        # Create analysis data
        analysis_data = {
            'income_discrepancy': income_discrepancy,
            'needs_amendment': needs_amendment,
            'unfiled_liability': unfiled_liability,
            'return_status': return_status
        }
        
        # Generate recommendations and priority
        analysis_data['recommendations'] = generate_recommendations(analysis_data)
        analysis_data['priority_level'] = calculate_priority_level(analysis_data)
        
        # Build result structure
        result[year_str] = {
            'wi_data': {
                'forms': year_forms,
                'total_income': wi_total_income,
                'total_withholding': wi_total_withholding
            },
            'at_data': at_record,
            'return_status': return_status,
            'has_at_data': at_record is not None,
            'analysis': analysis_data
        }
    
    return result

def render_comprehensive_analysis():
    """Render the Comprehensive Analysis page"""
    st.title("Comprehensive Tax Analysis")
    
    # Get case_id from session state
    case_id = st.session_state.get('case_id', None)
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return

    # Check if we have data
    wi_data = st.session_state.get('wi_data', {})
    at_data = st.session_state.get('at_data', [])
    
    if not wi_data and not at_data:
        st.warning("No data available. Please process documents first.")
        return
    
    # Create comprehensive analysis
    analysis = create_tax_summary(wi_data, at_data)
    
    # Set up Streamlit tabs
    overview_tab, detailed_tab, rec_services_tab, json_tab = st.tabs([
        "Overview", "Detailed Analysis", "Recommendations & Services", "JSON"
    ])
    
    with overview_tab:
        st.subheader("Tax Analysis Overview")
        
        # Create summary table
        summary_data = []
        for year, year_data in analysis.items():
            analysis_info = year_data['analysis']
            # Get current balance from AT data if available
            current_balance = 0
            if year_data['at_data'] and isinstance(year_data['at_data'], dict):
                current_balance = year_data['at_data'].get('account_balance', 0)
            # Actual Income (W&I)
            actual_income = year_data['wi_data']['total_income']
            # Reported Income (AT AGI or Not Reported)
            if analysis_info['return_status'] == 'Filed':
                reported_income = year_data['at_data'].get('adjusted_gross_income', 0) if year_data['at_data'] else 0
            else:
                reported_income = 'Not Reported'
            # Tax Owed: filed = current balance, unfiled = SFR liability (always a number)
            if analysis_info['return_status'] == 'Filed':
                tax_owed = float(current_balance)
            else:
                tax_owed = float(analysis_info['unfiled_liability'])
            # Income Discrepancy: only if amendment is needed
            if analysis_info['needs_amendment']:
                income_discrepancy = actual_income - (reported_income if isinstance(reported_income, (int, float)) else 0)
            else:
                income_discrepancy = ''
            summary_data.append({
                'Tax Year': year,
                'Return Status': analysis_info['return_status'],
                'Actual Income (W&I Transcript)': actual_income,
                'Reported Income (Filed Return)': reported_income,
                'Income Discrepancy': income_discrepancy,
                'Tax Owed': tax_owed,
                'Needs Amendment': 'Yes' if analysis_info['needs_amendment'] else 'No',
                'Priority Level': analysis_info['priority_level']
            })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            # Format currency columns
            currency_cols = ['Actual Income (W&I Transcript)', 'Tax Owed', 'Income Discrepancy']
            for col in currency_cols:
                df[col] = df[col].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) and x != '' else ('' if x == '' else x))
            # Format Reported Income as currency if not 'Not Reported'
            def format_reported_income(val):
                if isinstance(val, (int, float)):
                    return f"${val:,.2f}"
                return val
            df['Reported Income (Filed Return)'] = df['Reported Income (Filed Return)'].apply(format_reported_income)
            # Add priority color coding
            def color_priority(val):
                if val == 1:
                    return 'background-color: #ffcccc'  # Red for urgent
                elif val == 2:
                    return 'background-color: #ffebcc'  # Orange for high
                else:
                    return 'background-color: #e6ffe6'  # Green for medium
            styled_df = df.style.applymap(color_priority, subset=['Priority Level'])
            st.dataframe(styled_df, use_container_width=True)
            # Summary metrics (totals)
            total_tax_owed = sum(row['Tax Owed'] for row in summary_data)
            total_current_balance = sum(row['Tax Owed'] for row in summary_data if row['Return Status'] == 'Filed')
            total_projected_sfr = sum(row['Tax Owed'] for row in summary_data if row['Return Status'] == 'Not Filed')
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total IRS Debt (All Years)", f"${total_tax_owed:,.2f}")
            with col2:
                st.metric("Current IRS Balance (Filed Years)", f"${total_current_balance:,.2f}")
            with col3:
                st.metric("Projected SFR Liability (Unfiled Years)", f"${total_projected_sfr:,.2f}")
    
    with detailed_tab:
        st.subheader("Detailed Year-by-Year Analysis")
        
        for year, year_data in analysis.items():
            analysis_info = year_data['analysis']
            
            # Create expandable section for each year
            with st.expander(f"📅 Tax Year {year} - Priority Level {analysis_info['priority_level']}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Wage & Income Data**")
                    st.write(f"Total Income: ${year_data['wi_data']['total_income']:,.2f}")
                    st.write(f"Total Withholding: ${year_data['wi_data']['total_withholding']:,.2f}")
                    st.write(f"Number of Forms: {len(year_data['wi_data']['forms'])}")
                    
                    # Show forms breakdown
                    if year_data['wi_data']['forms']:
                        st.markdown("**Forms:**")
                        for form in year_data['wi_data']['forms']:
                            st.write(f"• {form['Form']} ({form['Category']}): ${form['Income']:,.2f}")
                
                with col2:
                    st.markdown("**Account Transcript Data**")
                    if year_data['at_data']:
                        at_data = year_data['at_data']
                        st.write(f"AGI: ${at_data.get('adjusted_gross_income', 0):,.2f}")
                        st.write(f"Taxable Income: ${at_data.get('taxable_income', 0):,.2f}")
                        st.write(f"Tax Per Return: ${at_data.get('tax_per_return', 0):,.2f}")
                        st.write(f"Filing Status: {at_data.get('filing_status', 'Unknown')}")
                        st.write(f"Account Balance: ${at_data.get('account_balance', 0):,.2f}")
                    else:
                        st.write("No AT data available")
                
                # TP/S Analysis section
                st.markdown("---")
                st.markdown("**TP/S Analysis**")
                
                # Use TPSParser for owner analysis
                year_forms = year_data['wi_data']['forms']
                filing_status = year_data['at_data'].get('filing_status', 'Single') if year_data['at_data'] else 'Single'
                
                # Aggregate by owner
                year_data_dict = {year: year_forms}
                totals = TPSParser.aggregate_income_by_owner(year_data_dict)
                year_totals = totals.get(year, {})
                
                # Generate TP/S analysis
                tps_analysis = TPSParser.generate_tps_analysis_summary(year_data_dict, filing_status)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Income by Owner:**")
                    tp_data = year_totals.get('taxpayer', {})
                    spouse_data = year_totals.get('spouse', {})
                    joint_data = year_totals.get('joint', {})
                    combined_data = year_totals.get('combined', {})
                    
                    st.write(f"Taxpayer: ${tp_data.get('income', 0):,.2f}")
                    st.write(f"Spouse: ${spouse_data.get('income', 0):,.2f}")
                    st.write(f"Joint: ${joint_data.get('income', 0):,.2f}")
                    st.write(f"Combined: ${combined_data.get('income', 0):,.2f}")
                
                with col2:
                    st.markdown("**Missing Data Analysis:**")
                    missing_recs = tps_analysis.get('missing_data_recommendations', [])
                    if missing_recs:
                        for rec in missing_recs:
                            st.warning(f"⚠️ {rec}")
                    else:
                        st.success("✅ TP/S data appears complete")
                
                # Analysis section
                st.markdown("---")
                st.markdown("**Analysis Results**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    discrepancy = analysis_info['income_discrepancy']
                    if discrepancy > 0:
                        st.error(f"Income Discrepancy: +${discrepancy:,.2f}")
                        st.write("WI income > AT AGI")
                    elif discrepancy < 0:
                        st.warning(f"Income Discrepancy: ${discrepancy:,.2f}")
                        st.write("AT AGI > WI income")
                    else:
                        st.success("No income discrepancy")
                
                with col2:
                    if analysis_info['return_status'] == "Not Filed":
                        liability = analysis_info['unfiled_liability']
                        if liability > 0:
                            st.error(f"Unfiled Liability: ${liability:,.2f}")
                        else:
                            st.success("No estimated liability")
                    else:
                        st.success("Return Filed")
                
                with col3:
                    priority = analysis_info['priority_level']
                    if priority == 1:
                        st.error(f"Priority: URGENT ({priority})")
                    elif priority == 2:
                        st.warning(f"Priority: HIGH ({priority})")
                    else:
                        st.success(f"Priority: MEDIUM ({priority})")
    
    with rec_services_tab:
        st.subheader('Recommended Services')
        # --- Recommended Services Panel ---
        recs = []
        unfiled_years = [row['Tax Year'] for row in summary_data if row['Return Status'] == 'Not Filed']
        if unfiled_years:
            recs.append({
                'icon': '📝',
                'title': 'Tax Preparation & Filing',
                'desc': f'File returns for unfiled years: {", ".join(map(str, unfiled_years))}',
                'blurb': "Filing unfiled returns stops IRS substitute returns (SFRs), reduces penalties, and starts the CSED clock. The IRS can file for you using worst-case assumptions, often resulting in a much higher tax bill."
            })
        amend_years = [row['Tax Year'] for row in summary_data if row['Needs Amendment'] == 'Yes']
        if amend_years:
            recs.append({
                'icon': '✏️',
                'title': 'Tax Preparation & Amendment',
                'desc': f'Amend returns for years: {", ".join(map(str, amend_years))}',
                'blurb': "Amending corrects discrepancies between your return and IRS records, helps avoid audits, and reduces risk of accuracy penalties (up to 20% of underpayment) and interest."
            })
        balance_years = [row['Tax Year'] for row in summary_data if row['Tax Owed'] > 0 and row['Return Status'] == 'Filed']
        if balance_years:
            recs.append({
                'icon': '💸',
                'title': 'Payment Plan Setup',
                'desc': f'Set up payment plans for years: {", ".join(map(str, balance_years))}',
                'blurb': "A payment plan helps avoid IRS levies or liens, lets you pay over time, and may reduce additional penalties. The IRS charges setup fees and interest continues to accrue until paid in full."
            })
        if recs:
            for rec in recs:
                st.write(f"{rec['icon']} **{rec['title']}**: {rec['desc']}")
                st.write(f"{rec['blurb']}")
        else:
            st.success('No urgent services required at this time!')
        st.markdown('---')
        st.subheader('Year-by-Year Actionable Recommendations')
        # --- Year-by-year actionable recommendations (restored) ---
        urgent_issues = []
        high_priority = []
        medium_priority = []
        for year, year_data in analysis.items():
            analysis_info = year_data['analysis']
            priority = analysis_info['priority_level']
            issue = {
                'year': year,
                'return_status': analysis_info['return_status'],
                'recommendations': analysis_info['recommendations'],
                'income_discrepancy': analysis_info['income_discrepancy'],
                'unfiled_liability': analysis_info['unfiled_liability']
            }
            if priority == 1:
                urgent_issues.append(issue)
            elif priority == 2:
                high_priority.append(issue)
            else:
                medium_priority.append(issue)
        # Display urgent issues
        if urgent_issues:
            st.error("🚨 URGENT ISSUES")
            for issue in urgent_issues:
                with st.expander(f"Tax Year {issue['year']} - URGENT", expanded=True):
                    for rec in issue['recommendations']:
                        st.write(f"• {rec}")
        # Display high priority issues
        if high_priority:
            st.warning("⚠️ HIGH PRIORITY ISSUES")
            for issue in high_priority:
                with st.expander(f"Tax Year {issue['year']} - HIGH PRIORITY"):
                    for rec in issue['recommendations']:
                        st.write(f"• {rec}")
        # Display medium priority issues
        if medium_priority:
            st.info("ℹ️ MEDIUM PRIORITY ISSUES")
            for issue in medium_priority:
                with st.expander(f"Tax Year {issue['year']} - MEDIUM PRIORITY"):
                    for rec in issue['recommendations']:
                        st.write(f"• {rec}")
        if not any([urgent_issues, high_priority, medium_priority]):
            st.success("✅ No significant issues detected")
    
    with json_tab:
        st.subheader("Complete Analysis Data (JSON)")
        st.json(analysis)

def render_comparison_tab():
    st.title("Income Comparison: Client vs Wage & Income Transcript")
    st.markdown("---")
    
    # Get client profile data (support both keys)
    client_data = st.session_state.get('client_data') or st.session_state.get('client_profile_data')
    wi_summary = st.session_state.get('wi_summary')
    at_data = st.session_state.get('at_data', [])
    
    if not client_data or not wi_summary:
        st.warning("Client profile or Wage & Income summary data not available.")
        return

    # Try to get Monthly Net from both possible structures
    monthly_net = None
    try:
        monthly_net = client_data['financial_profile']['income']['monthly_net']
    except Exception:
        pass
    if monthly_net is None:
        try:
            monthly_net = client_data['financial_profile']['income']['total'] / 12
        except Exception:
            pass
    if monthly_net is None:
        st.warning("Could not retrieve Monthly Net from client profile data.")
        return
    client_annual_income = monthly_net * 12

    # Get most recent year from WI summary
    most_recent_row = max(wi_summary, key=lambda x: int(x['Tax Year']))
    most_recent_year = str(most_recent_row['Tax Year'])
    wi_total_income = most_recent_row['Total Income']
    if isinstance(wi_total_income, str):
        wi_total_income = float(str(wi_total_income).replace("$", "").replace(",", ""))

    # Find AT data for the most recent year
    at_years_dict = {str(d.get('tax_year')): d for d in at_data if d.get('tax_year')}
    at_for_year = at_years_dict.get(most_recent_year)
    at_agi = None
    if at_for_year:
        at_agi = at_for_year.get('adjusted_gross_income')
        if at_agi is not None and isinstance(at_agi, str):
            try:
                at_agi = float(at_agi.replace("$", "").replace(",", ""))
            except Exception:
                at_agi = None

    # Decide which transcript value to use
    if at_agi is not None and at_agi > 0:
        transcript_income = at_agi
        transcript_label = "Transcript AGI (from AT)"
    else:
        transcript_income = wi_total_income
        transcript_label = "Transcript Total Income (from WI)"

    # Calculate percentage difference
    if transcript_income == 0:
        percent_diff = float('inf')
    else:
        percent_diff = ((client_annual_income - transcript_income) / transcript_income) * 100

    # Create tabs for the comparison
    comparison_tab, json_tab = st.tabs(["📊 Comparison", "🔧 JSON Data"])
    
    with comparison_tab:
        # Display results
        st.subheader(f"Most Recent Year: {most_recent_year}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Client Annual Net (Self-Reported)", f"${client_annual_income:,.2f}")
        with col2:
            st.metric(transcript_label, f"${transcript_income:,.2f}")
        with col3:
            st.metric("% Difference", f"{percent_diff:.2f}%")
        # Optionally show both AT AGI and WI Total if both exist
        if at_agi is not None and at_agi > 0:
            st.caption(f"AT AGI: ${at_agi:,.2f}")
        st.caption(f"WI Total Income: ${wi_total_income:,.2f}")
        st.markdown("---")
        st.write("This comparison shows how close the client's self-reported income is to the IRS Wage & Income transcript or Account Transcript AGI for the most recent year.")
    
    with json_tab:
        st.subheader("🔧 Comparison Data (JSON)")
        
        # Prepare comparison data for JSON display
        comparison_data = {
            "comparison_info": {
                "most_recent_year": most_recent_year,
                "client_annual_income": client_annual_income,
                "wi_total_income": wi_total_income,
                "at_agi": at_agi,
                "transcript_income_used": transcript_income,
                "transcript_source": transcript_label,
                "percentage_difference": percent_diff
            },
            "client_data": client_data,
            "wi_summary": wi_summary,
            "at_data": at_data
        }
        
        st.json(comparison_data)

def render_login_interface():
    """Render the login interface for TPS authentication"""
    st.title("🔐 TPS Authentication")
    st.markdown("---")
    
    # Check if already authenticated and not expired
    cookies, user_agent, message = load_cookies_from_file()
    expired = False
    if message and ("hour" in message and ("old" in message or "expired" in message)):
        expired = True
    
    if cookies and user_agent and not expired:
        st.success("✅ Already authenticated with TPS!")
        st.info(f"Last login: {message}")
        # Show cookie info
        with st.expander("🔧 Cookie Information"):
            try:
                if os.path.exists("logiqs-cookies.json"):
                    with open("logiqs-cookies.json", 'r') as f:
                        cookie_data = json.load(f)
                    timestamp = datetime.fromisoformat(cookie_data['timestamp'])
                    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Cookie Age", f"{age_hours:.1f} hours")
                    with col2:
                        st.metric("Cookie Count", len(cookie_data.get('cookies', [])))
                    with col3:
                        st.metric("Status", "Valid" if age_hours < 12 else "Expired")
                    st.write("**Cookie Names:**")
                    cookie_names = [c['name'] for c in cookie_data.get('cookies', [])]
                    st.write(", ".join(cookie_names))
                elif os.path.exists("tps_cookies.json"):
                    with open("tps_cookies.json", 'r') as f:
                        cookie_data = json.load(f)
                    timestamp = datetime.fromisoformat(cookie_data['timestamp'])
                    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Cookie Age", f"{age_hours:.1f} hours")
                    with col2:
                        st.metric("Cookie Count", cookie_data.get('cookie_count', 'N/A'))
                    with col3:
                        st.metric("Status", "Valid" if age_hours < 12 else "Expired")
                    st.write("**Cookie Names:**")
                    st.write(", ".join(cookie_data.get('cookie_names', [])))
            except Exception as e:
                st.error(f"Error reading cookie info: {e}")
        if st.button("🔄 Refresh Authentication"):
            st.info("Refreshing authentication...")
            success = refresh_tps_authentication()
            if success:
                st.success("✅ Authentication refreshed successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to refresh authentication")
        return True
    # If cookies are missing or expired, show the login form
    st.subheader("Enter your TPS credentials")
    log_lines = []
    def st_log_callback(msg):
        log_lines.append(msg)
        st.session_state['tps_login_log'] = '\n'.join(log_lines)
    with st.form("tps_login_form"):
        username = st.text_input("Username/Email", key="tps_username")
        password = st.text_input("Password", type="password", key="tps_password")
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("🔐 Login to TPS")
        with col2:
            test_button = st.form_submit_button("🧪 Test Connection")
        if submit_button:
            if not username or not password:
                st.error("❌ Please enter both username and password")
                return False
            with st.spinner("🔐 Authenticating with TPS..."):
                log_lines.clear()
                placeholder = st.empty()
                def stream_log(msg):
                    log_lines.append(msg)
                    placeholder.code('\n'.join(log_lines), language='text')
                success, logs = authenticate_and_sync_cookies(username, password, headless=True, slow_mo=1000, st_log_callback=stream_log)
                placeholder.code('\n'.join(log_lines), language='text')
                if success:
                    st.success("✅ Authentication successful!")
                    st.info("You can now use all TPS features in the app.")
                    st.rerun()
                else:
                    st.error("❌ Authentication failed. Please check your credentials.")
                    return False
        elif test_button:
            st.info("🧪 Testing TPS connection...")
            test_result = test_tps_connection()
            if test_result:
                st.success("✅ TPS site is accessible")
            else:
                st.error("❌ Cannot connect to TPS site")
    # Show log output if present
    if 'tps_login_log' in st.session_state and st.session_state['tps_login_log']:
        with st.expander("Authentication Log"):
            st.code(st.session_state['tps_login_log'], language='text')
    return False

def authenticate_and_sync_cookies(username, password, headless=True, slow_mo=1000, st_log_callback=None):
    import os
    import json
    from datetime import datetime
    from playwright.sync_api import sync_playwright
    LOGIQS_URL = 'https://tps.logiqs.com'
    COOKIES_FILE = 'logiqs-cookies.json'
    logs = []
    def log(msg):
        print(msg)
        logs.append(msg)
        if st_log_callback:
            st_log_callback(msg)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
        try:
            context = browser.new_context()
            page = context.new_page()
            log('🌐 Navigating to Logiqs login page...')
            page.goto(LOGIQS_URL)
            # Wait for page to load completely
            page.wait_for_load_state('networkidle', timeout=15000)
            log('📝 Looking for login form elements...')
            # Try different possible selectors for username/email field
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]', 
                '#username',
                '#email',
                'input[type="email"]',
                'input[placeholder*="username" i]',
                'input[placeholder*="email" i]',
                '#txtUsername2'  # Keep the original selector as fallback
            ]
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = page.locator(selector).first
                    if username_field.is_visible(timeout=2000):
                        log(f'✅ Found username field with selector: {selector}')
                        break
                except:
                    continue
            if not username_field:
                log('❌ Could not find username/email input field')
                log('🔍 Available input fields on page:')
                try:
                    inputs = page.locator('input').all()
                    for i, inp in enumerate(inputs[:10]):  # Show first 10 inputs
                        try:
                            input_type = inp.get_attribute('type') or 'text'
                            input_name = inp.get_attribute('name') or 'no-name'
                            input_id = inp.get_attribute('id') or 'no-id'
                            log(f'   Input {i+1}: type="{input_type}", name="{input_name}", id="{input_id}"')
                        except:
                            log(f'   Input {i+1}: <error reading attributes>')
                except:
                    log('   Could not inspect input fields')
                return False, logs
            username_field.fill(username)
            # Find and fill password field
            password_selectors = [
                'input[name="password"]',
                '#password',
                'input[type="password"]',
                'input[placeholder*="password" i]',
                '#txtPassword2'  # Keep the original selector as fallback
            ]
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = page.locator(selector).first
                    if password_field.is_visible(timeout=2000):
                        log(f'✅ Found password field with selector: {selector}')
                        break
                except:
                    continue
            if not password_field:
                log('❌ Could not find password input field')
                return False, logs
            password_field.fill(password)
            # Find and click login button
            login_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                '.login-button',
                '#login-button',
                '[data-testid="login-button"]',
                '#btnLogin2'  # Keep the original selector as fallback
            ]
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = page.locator(selector).first
                    if login_button.is_visible(timeout=2000):
                        log(f'✅ Found login button with selector: {selector}')
                        break
                except:
                    continue
            if not login_button:
                log('❌ Could not find login button')
                log('🔍 Available buttons on page:')
                try:
                    buttons = page.locator('button').all()
                    for i, btn in enumerate(buttons[:10]):  # Show first 10 buttons
                        try:
                            button_text = btn.text_content() or 'no-text'
                            button_type = btn.get_attribute('type') or 'button'
                            log(f'   Button {i+1}: text="{button_text}", type="{button_type}"')
                        except:
                            log(f'   Button {i+1}: <error reading attributes>')
                except:
                    log('   Could not inspect buttons')
                return False, logs
            log('🔑 Clicking login button...')
            login_button.click()
            # Wait for successful login (look for dashboard, user menu, or redirect)
            log('⏳ Waiting for successful authentication...')
            try:
                # Wait for either successful login indicators or error messages
                # Use a timeout and check for success/error conditions
                page.wait_for_timeout(5000)  # Wait a bit for the page to respond
                # Check if we're still on login page (error case)
                current_url = page.url
                if 'login' in current_url or 'signin' in current_url:
                    # Check for error messages
                    error_selectors = ['.error', '.alert-error', '.login-error', '[data-testid="error"]']
                    error_found = False
                    for selector in error_selectors:
                        try:
                            error_element = page.locator(selector).first
                            if error_element.is_visible(timeout=1000):
                                error_text = error_element.text_content()
                                log(f'❌ Login failed: {error_text}')
                                error_found = True
                                break
                        except:
                            continue
                    if not error_found:
                        log('❌ Login failed: Still on login page after submission')
                    return False, logs
                # Check for success indicators
                success_selectors = ['.dashboard', '.user-menu', '.profile', '[data-testid="dashboard"]', '.welcome', '.user-name', '.account-menu']
                success_found = False
                for selector in success_selectors:
                    try:
                        success_element = page.locator(selector).first
                        if success_element.is_visible(timeout=1000):
                            log('✅ Successfully authenticated!')
                            success_found = True
                            break
                    except:
                        continue
                if not success_found:
                    log('⚠️  Could not detect success indicators, but proceeding...')
            except Exception as error:
                log(f'❌ Error during authentication: {str(error)}')
                return False, logs
            # Wait a bit more to ensure all cookies are set
            page.wait_for_timeout(3000)
            log('🍪 Extracting cookies...')
            cookies = context.cookies()
            cookies_data = {
                'timestamp': datetime.now().isoformat(),
                'url': LOGIQS_URL,
                'cookies': cookies
            }
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies_data, f, indent=2)
            log(f'💾 Cookies saved to {COOKIES_FILE}')
            log(f'📊 Found {len(cookies)} cookies:')
            for cookie in cookies:
                value_preview = cookie["value"][:20] + '...' if len(cookie["value"]) > 20 else cookie["value"]
                log(f'   - {cookie["name"]}: {value_preview}')
            log('🧪 Testing access to protected content...')
            try:
                page.goto(f'{LOGIQS_URL}/dashboard', wait_until='networkidle')
                log('✅ Successfully accessed protected content')
            except Exception as error:
                log('⚠️  Could not access dashboard, but cookies are saved')
            log('\n🎉 Authentication and cookie sync completed successfully!')
            log(f'📁 Cookies file: {os.path.abspath(COOKIES_FILE)}')
            log('💡 You can now use these cookies in your API requests')
            return True, logs
        except Exception as error:
            log(f'❌ Error during authentication: {str(error)}')
            return False, logs
        finally:
            browser.close()

def test_tps_connection() -> bool:
    """Test if TPS site is accessible"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://tps.logiqs.com/Login.aspx", timeout=10000)
            title = page.title()
            browser.close()
            return "Login" in title or "TPS" in title
    except:
        return False

def refresh_tps_authentication() -> bool:
    """Refresh TPS authentication using the Streamlit login interface"""
    st.info("Please use the '🔐 TPS Login' tab to refresh your authentication.")
    return False

def main():
    st.set_page_config(
        page_title="IRS Transcript Parser",
        page_icon="📊",
        layout="wide"
    )

    # Initialize session state
    if 'case_id' not in st.session_state:
        st.session_state['case_id'] = ''
    if 'wi_data' not in st.session_state:
        st.session_state['wi_data'] = {}
    if 'at_data' not in st.session_state:
        st.session_state['at_data'] = []
    if 'client_data' not in st.session_state:
        st.session_state['client_data'] = None

    # --- Recent/Test Case IDs for quick selection ---
    recent_cases = [
        '732334',
        '772078',
        '864274',
        '884562',
        '909511',
        '923478',
        '960159',
        '1063234',
        '1111606',
        '106379',
        '1110004',
        '44944',
        '697391',
        '901733',
        '750248',
        '1037050',
        '1064152',
        '1011490',
        '654986',
        '1029024',
    ]
    st.sidebar.markdown("**Quick Select Case ID**")
    selected_case = st.sidebar.selectbox(
        "Choose a recent/test case:",
        ["(None)"] + recent_cases,
        index=0
    )
    if selected_case != "(None)":
        st.session_state['case_id'] = selected_case

    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Radio button for page selection
    page = st.sidebar.radio(
        "Choose a page:",
        ["🏠 Home", "🔐 TPS Login", "📄 WI Parser", "📊 AT Parser", "📋 ROA Parser", "📝 TRT Parser", "📊 Comprehensive Analysis", "📋 Client Profile", "⚙️ Settings", "📊 Comparison"],
        index=0
    )

    # Render content based on selected page
    if page == "🏠 Home":
        render_home()
    elif page == "🔐 TPS Login":
        render_login_interface()
    elif page == "📄 WI Parser":
        render_wi_parser()
    elif page == "📊 AT Parser":
        render_at_parser()
    elif page == "📋 ROA Parser":
        render_roa_parser()
    elif page == "📝 TRT Parser":
        render_trt_parser()
    elif page == "📊 Comprehensive Analysis":
        render_comprehensive_analysis()
    elif page == "📋 Client Profile":
        render_client_profile_tab()
    elif page == "⚙️ Settings":
        render_settings()
    elif page == "📊 Comparison":
        render_comparison_tab()

if __name__ == "__main__":
    main()
