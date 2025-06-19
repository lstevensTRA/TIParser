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
import requests
import xml.etree.ElementTree as ET
from client_profile import render_client_profile

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
    """Load cookies from the tps_cookies.json file"""
    if not os.path.exists(COOKIE_FILE):
        logger.warning("Cookie file not found")
        return None, None
    
    try:
        with open(COOKIE_FILE, 'r') as f:
            cookie_data = json.load(f)
            
        # If we have cookies and user agent, return them regardless of timestamp
        if cookie_data.get('cookies') and cookie_data.get('user_agent'):
            # Try to check timestamp if available, but don't fail if it's not
            try:
                timestamp = datetime.fromisoformat(cookie_data['timestamp'])
                age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                if age_hours > 12:
                    logger.warning("Cookies are older than 12 hours but will try to use them")
            except (KeyError, ValueError):
                logger.warning("No timestamp found in cookie file but will try to use cookies")
                
            return cookie_data['cookies'], cookie_data['user_agent']
            
        logger.warning("Cookie file exists but missing required data")
        return None, None
        
    except Exception as e:
        logger.warning(f"Error reading cookie file: {str(e)}")
        return None, None

def get_wi_files(case_id: str) -> list:
    """
    Get list of WI files associated with a case.
    """
    cookies, user_agent = load_cookies_from_file()
    if not cookies:
        st.error("Authentication required. Please ensure cookies are valid.")
        st.info("Please run the cookie extraction script to refresh your cookies.")
        st.info("1. Run: python3 extract_tps_cookies.py")
        st.info("2. Log in to the TPS site in the opened browser window.")
        st.info("3. After logging in, press Enter in the terminal window.")
        st.info("4. Refresh this page.")
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
                st.info("Please run the cookie extraction script to refresh your cookies.")
                st.info("1. Run: python3 extract_tps_cookies.py")
                st.info("2. Log in to the TPS site in the opened browser window.")
                st.info("3. After logging in, press Enter in the terminal window.")
                st.info("4. Refresh this page.")
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

            # Check for WI in the filename
            if "WI" in name:
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
    cookies, user_agent = load_cookies_from_file()
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
    """Extract text from PDF bytes using PyPDF2, then pdfplumber as fallback."""
    import PyPDF2
    text = ""
    used_method = None
    
    # Try PyPDF2 first
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        page_texts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            page_texts.append(page_text)
        text = "\n".join(page_texts)
        if text and len(text.strip()) > 50:
            used_method = "PyPDF2"
            logger.info("Successfully extracted text using PyPDF2")
            return text
    except Exception as e:
        logger.warning(f"PyPDF2 failed: {e}")
    
    # Try pdfplumber next
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_texts = []
            for page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                page_texts.append(page_text)
            text = "\n".join(page_texts)
        if text and len(text.strip()) > 50:
            used_method = "pdfplumber"
            logger.info("Successfully extracted text using pdfplumber")
            return text
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")
    
    logger.warning("Could not extract text from PDF")
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

def extract_form_data(text, form_patterns, tax_year, filing_status='Single', combined_income=0, output_buffer=None):
    """Extract form data from text using patterns"""
    results = {}
    
    def write_out(msg):
        """Write to both logger and output buffer if provided"""
        logger.info(msg)
        if output_buffer:
            output_buffer.write(msg + "\n")
    
    write_out("Starting form pattern matching")
    
    # Process each form type
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
            
            # Format label string
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
            
            # Extract fields
            fields_data = {}
            write_out("Starting field extraction")
            for field_name, regex in pattern_info['fields'].items():
                if regex:
                    field_match = re.search(regex, form_text, re.IGNORECASE)
                    if field_match:
                        value = to_float(field_match.group(1))
                        fields_data[field_name] = value
                        write_out(f"Field {field_name} = {value}")
                        write_out(f"Matched text for {field_name}: {field_match.group(0)}")
                    else:
                        write_out(f"Field {field_name} - No match found")
            
            if not fields_data:
                write_out(f"Form {form_name} matched but no fields were captured")
                continue
            
            # Calculate income and withholding using the form's calculation rules
            calc = pattern_info['calculation']
            income = calc['Income'](fields_data, filing_status, combined_income) if 'filing_status' in calc['Income'].__code__.co_varnames else calc['Income'](fields_data)
            withholding = calc['Withholding'](fields_data) if callable(calc.get('Withholding')) else 0
            category = pattern_info.get('category', 'Neither')
            
            write_out(f"Calculated values - Income: {income}, Withholding: {withholding}, Category: {category}")
            
            # Store results
            if tax_year not in results:
                results[tax_year] = []
            
            results[tax_year].append({
                'Form': form_name,
                'UniqueID': unique_id if unique_id else None,
                'Label': unique_label if unique_label else None,
                'Income': income,
                'Withholding': withholding,
                'Category': category,
                'Fields': fields_data
            })
    
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
    cookies, user_agent = load_cookies_from_file()
    if not cookies:
        st.warning("⚠️ No valid cookies found. Please run the cookie extraction script to refresh your cookies.")
        st.info("Steps to refresh cookies:")
        st.markdown("""
        1. Run: `python3 extract_tps_cookies.py`
        2. Log in to the TPS site in the opened browser window.
        3. After logging in, press Enter in the terminal window.
        4. Refresh this page.
        """)
        st.info("Note: If you've manually added cookies to tps_cookies.json, you can try using the parsers, but you may need to refresh cookies if authentication fails.")
    
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
        
        for idx, wi_file in enumerate(wi_files):
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing file: {wi_file['FileName']}")
            logger.info(f"{'='*50}\n")
            
            # Extract owner from filename
            owner = extract_owner_from_filename(wi_file['FileName'])
            logger.info(f"Extracted owner from filename '{wi_file['FileName']}': {owner}")
            
            pdf_bytes = download_file(wi_file["CaseDocumentID"], case_id)
            if pdf_bytes:
                text = extract_text_from_pdf(pdf_bytes)
                if text:
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
                    
                    # Process forms
                    forms_data = extract_form_data(text, form_patterns, tax_year, output_buffer=log_buffer)
                    if forms_data:
                        # forms_data is a dictionary with tax years as keys
                        for year, year_forms in forms_data.items():
                            if year not in all_data:
                                all_data[year] = []
                            
                            # Add owner information to each form
                            for form in year_forms:
                                form['Owner'] = owner
                                logger.info(f"Added Owner={owner} to form {form['Form']}")
                            
                            all_data[year].extend(year_forms)
            
            # Update progress bar
            progress_bar.progress((idx + 1) / total_files)
    
    # Store results in session state
    st.session_state['wi_data'] = all_data
    st.session_state['wi_log'] = log_buffer.getvalue()
    st.session_state['wi_form_matching'] = form_matching_results
    
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
    summary_tab, tax_projection_tab, json_tab, form_matching_tab, log_tab = st.tabs([
        "Summary", "Tax Projection", "JSON", "Form Matching", "Logs"
    ])

    with summary_tab:
        st.subheader("Income Summary")
        if st.session_state['wi_summary']:
            df = pd.DataFrame(st.session_state['wi_summary'])
            
            # Calculate detailed TP/SP totals for each year
            detailed_totals = {}
            for year in df['Tax Year']:
                year_forms = st.session_state['wi_data'].get(int(year), [])
                
                # Initialize structure for this year
                detailed_totals[year] = {
                    'TP': {'SE': 0, 'SE_Withholding': 0, 'Non-SE': 0, 'Non-SE_Withholding': 0, 'Other': 0, 'Other_Withholding': 0},
                    'SP': {'SE': 0, 'SE_Withholding': 0, 'Non-SE': 0, 'Non-SE_Withholding': 0, 'Other': 0, 'Other_Withholding': 0}
                }
                
                # Calculate totals by owner and category
                for form in year_forms:
                    owner = form.get('Owner', 'TP')
                    if owner not in ['TP', 'S']:  # Skip joint forms for this breakdown
                        continue
                        
                    owner_key = 'TP' if owner == 'TP' else 'SP' if owner == 'S' else None
                    if not owner_key:
                        continue
                        
                    category = form.get('Category', 'Neither')
                    income = form.get('Income', 0)
                    withholding = form.get('Withholding', 0)
                    
                    if category == 'SE':
                        detailed_totals[year][owner_key]['SE'] += income
                        detailed_totals[year][owner_key]['SE_Withholding'] += withholding
                    elif category == 'Non-SE':
                        detailed_totals[year][owner_key]['Non-SE'] += income
                        detailed_totals[year][owner_key]['Non-SE_Withholding'] += withholding
                    else:  # Neither category goes to Other
                        detailed_totals[year][owner_key]['Other'] += income
                        detailed_totals[year][owner_key]['Other_Withholding'] += withholding
            
            # Check if we have any SP data
            has_sp = any(
                sum(totals['SP'][key] for key in ['SE', 'Non-SE', 'Other']) > 0 
                for totals in detailed_totals.values()
            )
            
            # Add TP columns
            df['TP SE Income'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['TP']['SE'])
            df['TP SE Withholding'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['TP']['SE_Withholding'])
            df['TP Non-SE Income'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['TP']['Non-SE'])
            df['TP Non-SE Withholding'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['TP']['Non-SE_Withholding'])
            df['TP Other Income'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['TP']['Other'])
            df['TP Other Withholding'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['TP']['Other_Withholding'])
            df['TP Total Income'] = df.apply(lambda x: x['TP SE Income'] + x['TP Non-SE Income'] + x['TP Other Income'], axis=1)
            df['TP Total Withholding'] = df.apply(lambda x: x['TP SE Withholding'] + x['TP Non-SE Withholding'] + x['TP Other Withholding'], axis=1)
            
            # Add SP columns if spouse data exists
            if has_sp:
                df['SP SE Income'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['SP']['SE'])
                df['SP SE Withholding'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['SP']['SE_Withholding'])
                df['SP Non-SE Income'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['SP']['Non-SE'])
                df['SP Non-SE Withholding'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['SP']['Non-SE_Withholding'])
                df['SP Other Income'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['SP']['Other'])
                df['SP Other Withholding'] = df['Tax Year'].apply(lambda x: detailed_totals[x]['SP']['Other_Withholding'])
                df['SP Total Income'] = df.apply(lambda x: x['SP SE Income'] + x['SP Non-SE Income'] + x['SP Other Income'], axis=1)
                df['SP Total Withholding'] = df.apply(lambda x: x['SP SE Withholding'] + x['SP Non-SE Withholding'] + x['SP Other Withholding'], axis=1)
            
            # Format currency columns for display
            display_df = df.copy()
            
            # Define column order
            columns = ['Tax Year', 'Number of Forms']
            
            # TP columns
            tp_cols = [
                'TP SE Income', 'TP SE Withholding',
                'TP Non-SE Income', 'TP Non-SE Withholding',
                'TP Other Income', 'TP Other Withholding',
                'TP Total Income', 'TP Total Withholding'
            ]
            columns.extend(tp_cols)
            
            # SP columns if they exist
            if has_sp:
                sp_cols = [
                    'SP SE Income', 'SP SE Withholding',
                    'SP Non-SE Income', 'SP Non-SE Withholding',
                    'SP Other Income', 'SP Other Withholding',
                    'SP Total Income', 'SP Total Withholding'
                ]
                columns.extend(sp_cols)
            
            # Total columns
            total_cols = ['Total Income', 'Total Withholding']
            columns.extend(total_cols)
            
            # Format all currency columns
            currency_cols = [col for col in columns if any(x in col for x in ['Income', 'Withholding'])]
            for col in currency_cols:
                display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
            
            # Display the table with the specified column order
            st.table(display_df[columns])
            
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
                    
                    # Display TP/SP breakdown
                    st.markdown("---")
                    st.markdown("**Income by Owner**")
                    cols = st.columns(3 if has_sp else 2)
                    
                    # Always show TP (it's the default)
                    with cols[0]:
                        st.markdown("**Taxpayer**")
                        st.metric("Income", f"${detailed_totals[year]['TP']['SE'] + detailed_totals[year]['TP']['Non-SE'] + detailed_totals[year]['TP']['Other']:,.2f}")
                        st.metric("Withholding", f"${detailed_totals[year]['TP']['SE_Withholding'] + detailed_totals[year]['TP']['Non-SE_Withholding'] + detailed_totals[year]['TP']['Other_Withholding']:,.2f}")
                    
                    col_idx = 1
                    if has_sp:
                        with cols[col_idx]:
                            st.markdown("**Spouse**")
                            st.metric("Income", f"${detailed_totals[year]['SP']['SE'] + detailed_totals[year]['SP']['Non-SE'] + detailed_totals[year]['SP']['Other']:,.2f}")
                            st.metric("Withholding", f"${detailed_totals[year]['SP']['SE_Withholding'] + detailed_totals[year]['SP']['Non-SE_Withholding'] + detailed_totals[year]['SP']['Other_Withholding']:,.2f}")
                        col_idx += 1
                    
                    with cols[col_idx]:
                        st.markdown("**Joint**")
                        joint_income = row['Total Income'] - (
                            detailed_totals[year]['TP']['SE'] + detailed_totals[year]['TP']['Non-SE'] + detailed_totals[year]['TP']['Other'] +
                            detailed_totals[year]['SP']['SE'] + detailed_totals[year]['SP']['Non-SE'] + detailed_totals[year]['SP']['Other']
                        )
                        joint_withholding = row['Total Withholding'] - (
                            detailed_totals[year]['TP']['SE_Withholding'] + detailed_totals[year]['TP']['Non-SE_Withholding'] + detailed_totals[year]['TP']['Other_Withholding'] +
                            detailed_totals[year]['SP']['SE_Withholding'] + detailed_totals[year]['SP']['Non-SE_Withholding'] + detailed_totals[year]['SP']['Other_Withholding']
                        )
                        st.metric("Income", f"${joint_income:,.2f}")
                        st.metric("Withholding", f"${joint_withholding:,.2f}")
                    
                    # Display forms breakdown with owner information
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
                                
                                # Format the form display
                                form_label = f"{form_type}"
                                if label:
                                    form_label += f" - {label}"
                                
                                st.markdown(f"• {form_label} ({category}): ${income:,.2f}")
                                fcol1, fcol2 = st.columns(2)
                                with fcol1:
                                    st.write(f"Income: ${income:,.2f}")
                                with fcol2:
                                    st.write(f"Withholding: ${withholding:,.2f}")
                                st.markdown("---")
        else:
            st.info("📝 No Wage & Income data extracted")
    
    with tax_projection_tab:
        render_tax_projection(st.session_state['wi_projection'])
        
    with json_tab:
        st.subheader("Parsed WI Data (JSON)")
        st.json(st.session_state['wi_data'])
        
    with form_matching_tab:
        st.subheader("Form Pattern Matching")
        st.write(f"Found {len(st.session_state['wi_form_matching'])} WI documents.")
        
        # Display form matching results
        for result in st.session_state['wi_form_matching']:
            st.markdown(f"**Processing: {result['filename']}**")
            if result.get('owner'):
                st.text(f"Owner: {result['owner']}")
            if result['ssn'] and result['tax_period']:
                st.text(f"SSN: {result['ssn']} | Tax Period: {result['tax_period']}")
                st.text("-" * 50)
            
            st.text("🔍 Form Pattern Matching:")
            for match in result['form_matches']:
                st.text(f"📋 {match['form_name']}:")
                if match['matched']:
                    st.text("✅ Match found")
                else:
                    st.text("❌ No match found")
            st.markdown("---")
        
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
    cookies, user_agent = load_cookies_from_file()
    if not cookies:
        st.error("Authentication required. Please ensure cookies are valid.")
        st.info("Please run the cookie extraction script to refresh your cookies.")
        st.info("1. Run: python3 extract_tps_cookies.py")
        st.info("2. Log in to the TPS site in the opened browser window.")
        st.info("3. After logging in, press Enter in the terminal window.")
        st.info("4. Refresh this page.")
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
                st.info("Please run the cookie extraction script to refresh your cookies.")
                st.info("1. Run: python3 extract_tps_cookies.py")
                st.info("2. Log in to the TPS site in the opened browser window.")
                st.info("3. After logging in, press Enter in the terminal window.")
                st.info("4. Refresh this page.")
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
    """Extract transaction data from AT transcript text"""
    # Find the transactions section
    transactions_match = re.search(r'TRANSACTIONS\s*\n.*?\n(.*?)(?=\n\s*\n|$)', text, re.DOTALL)
    if not transactions_match:
        return []
    
    transactions_text = transactions_match.group(1)
    
    # Parse each transaction line
    # Pattern matches: CODE, EXPLANATION, DATE, AMOUNT
    transaction_pattern = r'(\d{3})(.*?)(\d{2}-\d{2}-\d{4})\s*\$?([-\d,.]+|-)'
    transactions = []
    
    for match in re.finditer(transaction_pattern, transactions_text):
        code = match.group(1)
        description = match.group(2).strip()
        date = match.group(3)
        amount_str = match.group(4)
        
        # Handle amount parsing
        try:
            if amount_str == '-':
                amount = 0.0  # Convert dash to zero
            else:
                amount = float(amount_str.replace(',', ''))
        except ValueError:
            logger.warning(f"Could not parse amount '{amount_str}' for transaction code {code}")
            amount = 0.0
        
        # Interpret the transaction using our codes database
        interpreted = interpret_transaction(code, description, date, amount)
        if interpreted:
            transactions.append(interpreted)
    
    return transactions

def extract_at_data(text):
    """Extract data from Account Transcript text"""
    data = {}
    transactions = []
    
    # Extract tax year - improved pattern matching
    year_match = re.search(r'TAX PERIOD:\s*Dec\.\s*31,\s*(\d{4})', text, re.IGNORECASE)
    if year_match:
        year = year_match.group(1)
        data['tax_year'] = format_year(year)
        logger.info(f"Found tax year from TAX PERIOD: {data['tax_year']}")
    else:
        # Try alternative patterns if the main one doesn't work
        year_match = re.search(r'Tax Period:\s*Dec\.\s*(\d{4})|Tax Period:\s*(\d{4})|TAX PERIOD:\s*(\d{4})', text, re.IGNORECASE)
        if year_match:
            year = year_match.group(1) or year_match.group(2) or year_match.group(3)
            data['tax_year'] = format_year(year)
            logger.info(f"Found tax year from alternative pattern: {data['tax_year']}")
        else:
            # Try to extract year from filename or other patterns
            year_match = re.search(r'(\d{4})', text)
            if year_match:
                data['tax_year'] = format_year(year_match.group(1))
                logger.info(f"Found tax year from fallback pattern: {data['tax_year']}")
            else:
                logger.warning("No tax year found")
                data['tax_year'] = 'Unknown'
    
    # Extract SSN (Taxpayer ID)
    ssn_match = re.search(r'TAXPAYER IDENTIFICATION NUMBER:\s*([\dX-]+)', text)
    if ssn_match:
        data['ssn'] = ssn_match.group(1)
    
    # Extract financial data
    financial_patterns = {
        'account_balance': r'ACCOUNT BALANCE:[\s]*[\$]?([\d,\.]+)',
        'accrued_interest': r'ACCRUED INTEREST:[\s]*[\$]?([\d,\.]+)',
        'accrued_penalty': r'ACCRUED PENALTY:[\s]*[\$]?([\d,\.]+)',
        'total_balance': r'ACCOUNT BALANCE PLUS ACCRUALS.*?:[\s]*[\$]?([\d,\.]+)',
        'adjusted_gross_income': r'ADJUSTED GROSS INCOME:[\s]*[\$]?([\d,\.]+)',
        'taxable_income': r'TAXABLE INCOME:[\s]*[\$]?([\d,\.]+)',
        'tax_per_return': r'TAX PER RETURN:[\s]*[\$]?([\d,\.]+)',
        'se_tax_taxpayer': r'SE TAXABLE INCOME TAXPAYER:[\s]*[\$]?([\d,\.]+)',
        'se_tax_spouse': r'SE TAXABLE INCOME SPOUSE:[\s]*[\$]?([\d,\.]+)',
        'total_se_tax': r'TOTAL SELF EMPLOYMENT TAX:[\s]*[\$]?([\d,\.]+)'
    }
    
    for key, pattern in financial_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)  # Added case-insensitive matching
        if match:
            try:
                # Convert string amount to float, removing commas
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
    filing_match = re.search(r'FILING STATUS:\s*([^,\n]+)', text)
    if filing_match:
        data['filing_status'] = filing_match.group(1).strip()
    
    # Extract processing date - more flexible pattern
    processing_match = re.search(r'PROCESSING DATE\s*([A-Z][a-z]+\.?\s+\d{1,2},?\s*\d{4})', text)
    if processing_match:
        data['processing_date'] = processing_match.group(1)
        logger.info(f"Found processing date: {data['processing_date']}")
    else:
        # Try alternative date format
        alt_processing_match = re.search(r'PROCESSING DATE\s*([A-Z][a-z]+\.?\s+\d{1,2}\s+\d{4})', text)
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
                    # Log the complete raw text
                    logger.info("Complete extracted text from PDF:")
                    logger.info("-" * 50)
                    logger.info(text)
                    logger.info("-" * 50)
                    
                    data = extract_at_data(text)
                    if data:
                        all_data.append(data)
            
            # Update progress bar
            progress_bar.progress((idx + 1) / total_files)
    
    # Store results in session state
    st.session_state['at_data'] = all_data
    st.session_state['at_log'] = log_buffer.getvalue()
    
    # Process alerts
    all_alerts = []
    for year_data in all_data:
        if 'transactions' in year_data:
            alerts = get_transaction_alerts(year_data['transactions'])
            all_alerts.extend(alerts)
    st.session_state['at_alerts'] = all_alerts
    
    # Clean up logging
    logger.removeHandler(log_handler)
    log_buffer.close()

def render_at_parser():
    """Render the AT Parser page (Account Transcript)"""
    st.title("AT Parser")
    
    # Get case_id from session state
    case_id = st.session_state.get('case_id', None)
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return

    # Check if we have data
    if 'at_data' not in st.session_state:
        st.warning("No Account Transcript data available. Please process a case ID first.")
        return

    # Set up Streamlit tabs
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
        
        # Create summary rows for all years
        summary_rows = []
        for data in at_data:
            # Use tax_year if available, otherwise use a default
            tax_year = data.get('tax_year', 'Unknown')
            if tax_year == 'Unknown':
                # Try to extract year from processing date or other fields
                processing_date = data.get('processing_date', '')
                if processing_date:
                    year_match = re.search(r'(\d{4})', processing_date)
                    if year_match:
                        tax_year = format_year(year_match.group(1))
            
            row = {
                'Tax Year': format_year(tax_year),
                'Return Filed': 'Yes' if any(
                    trans.get('code') in ['150', '976'] 
                    for trans in data.get('transactions', [])
                ) else 'No',
                'Filing Status': data.get('filing_status', 'Unknown'),
                'Current Balance': data.get('account_balance', 0),
                'Processing Date': data.get('processing_date', 'Unknown'),
                'AGI': data.get('adjusted_gross_income', 0),
                'Taxable Income': data.get('taxable_income', 0),
                'Tax Per Return': data.get('tax_per_return', 0)
            }
            summary_rows.append(row)
        
        if summary_rows:
            df = pd.DataFrame(summary_rows)
            # Format currency columns
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
    cookies, user_agent = load_cookies_from_file()
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
    cookies, user_agent = load_cookies_from_file()
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
    cookies, user_agent = load_cookies_from_file()
    if cookies:
        st.success("✅ Valid cookies found")
    else:
        st.error("❌ No valid cookies found")
        st.info("To refresh cookies:")
        st.code("python3 extract_tps_cookies.py")
    
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

def extract_owner_from_filename(filename: str) -> str:
    """
    Extract TP/S designation from filename
    Returns: "TP", "S", or None (for joint/combined)
    
    Examples:
        "WI 19 TP" → "TP"
        "WI S 19" → "S"  
        "WI 19" → "TP" (default)
        "WI 19 COMBINED" → None (joint)
    """
    if not filename:
        return "TP"  # Default to taxpayer
    
    filename_upper = filename.upper()
    
    # Check for explicit spouse designation
    if any(pattern in filename_upper for pattern in [" S ", " SPOUSE", "_S_", "_SPOUSE_"]):
        return "S"
    
    # Check for explicit taxpayer designation
    if any(pattern in filename_upper for pattern in [" TP ", " TAXPAYER", "_TP_", "_TAXPAYER_"]):
        return "TP"
    
    # Check for combined/joint designation
    if any(pattern in filename_upper for pattern in [" COMBINED", " JOINT", "_COMBINED_", "_JOINT_"]):
        return None
    
    # Default to taxpayer if no clear designation
    return "TP"

def aggregate_income_by_owner(forms: list) -> dict:
    """
    Calculate totals for TP, S, joint, and combined income/withholding
    
    Args:
        forms: List of form dictionaries with Owner field
        
    Returns:
        Dictionary with breakdown by owner type
    """
    totals = {
        "taxpayer": {
            "total_income": 0,
            "total_withholding": 0,
            "w2_income": 0,
            "se_income": 0
        },
        "spouse": {
            "total_income": 0,
            "total_withholding": 0,
            "w2_income": 0,
            "se_income": 0
        },
        "joint": {
            "total_income": 0,
            "total_withholding": 0
        },
        "combined": {
            "total_income": 0,
            "total_withholding": 0,
            "w2_income": 0,
            "se_income": 0
        }
    }
    
    for form in forms:
        owner = form.get('Owner', 'TP')  # Default to TP if no owner specified
        income = form.get('Income', 0)
        withholding = form.get('Withholding', 0)
        category = form.get('Category', 'Neither')
        form_type = form.get('Form', '')
        
        # Add to combined totals
        totals["combined"]["total_income"] += income
        totals["combined"]["total_withholding"] += withholding
        
        # Categorize by form type
        if form_type == "W-2":
            totals["combined"]["w2_income"] += income
        if category == "SE":
            totals["combined"]["se_income"] += income
        
        # Add to specific owner totals
        if owner == "TP":
            totals["taxpayer"]["total_income"] += income
            totals["taxpayer"]["total_withholding"] += withholding
            if form_type == "W-2":
                totals["taxpayer"]["w2_income"] += income
            if category == "SE":
                totals["taxpayer"]["se_income"] += income
        elif owner == "S":
            totals["spouse"]["total_income"] += income
            totals["spouse"]["total_withholding"] += withholding
            if form_type == "W-2":
                totals["spouse"]["w2_income"] += income
            if category == "SE":
                totals["spouse"]["se_income"] += income
        else:  # None or joint
            totals["joint"]["total_income"] += income
            totals["joint"]["total_withholding"] += withholding
    
    return totals

def detect_missing_spouse_data(forms: list, filing_status: str) -> dict:
    """
    Identify if spouse data is missing when expected
    
    Args:
        forms: List of form dictionaries
        filing_status: Filing status from AT data
        
    Returns:
        Dictionary with missing data analysis
    """
    analysis = {
        "taxpayer_has_income": False,
        "spouse_has_income": False,
        "missing_spouse_data": False,
        "missing_taxpayer_data": False,
        "recommendations": []
    }
    
    # Check what income exists
    for form in forms:
        owner = form.get('Owner', 'TP')
        if owner == "TP" and form.get('Income', 0) > 0:
            analysis["taxpayer_has_income"] = True
        elif owner == "S" and form.get('Income', 0) > 0:
            analysis["spouse_has_income"] = True
    
    # Analyze based on filing status
    if filing_status in ["Married Filing Jointly", "Married Filing Separately"]:
        if analysis["taxpayer_has_income"] and not analysis["spouse_has_income"]:
            analysis["missing_spouse_data"] = True
            analysis["recommendations"].append("Spouse income data appears to be missing")
        elif not analysis["taxpayer_has_income"] and analysis["spouse_has_income"]:
            analysis["missing_taxpayer_data"] = True
            analysis["recommendations"].append("Taxpayer income data appears to be missing")
        elif not analysis["taxpayer_has_income"] and not analysis["spouse_has_income"]:
            analysis["recommendations"].append("No income data found for either taxpayer or spouse")
    else:
        # Single filing - only taxpayer should have income
        if not analysis["taxpayer_has_income"]:
            analysis["missing_taxpayer_data"] = True
            analysis["recommendations"].append("No taxpayer income data found")
    
    return analysis

def create_enhanced_tax_summary(wi_data: dict, at_data: list) -> dict:
    """
    Enhanced version that handles TP/S separation while preserving all existing functionality
    
    Args:
        wi_data: Dictionary with years as keys, arrays of forms as values
        at_data: List of account transcript dictionaries
        
    Returns:
        Enhanced dictionary with TP/S analysis added to existing analysis
    """
    
    def calculate_wi_totals(year_forms):
        """Calculate total income and withholding from WI forms (preserves existing logic)"""
        total_income = 0
        total_withholding = 0
        
        for form in year_forms:
            # Only count SE and Non-SE income (exclude "Neither" category) - PRESERVES EXISTING LOGIC
            if form.get('Category') in ['SE', 'Non-SE']:
                total_income += form.get('Income', 0)
                total_withholding += form.get('Withholding', 0)
        
        return total_income, total_withholding
    
    def find_at_data_for_year(year, at_data):
        """Find AT data for a specific year (preserves existing logic)"""
        for at_record in at_data:
            at_year = at_record.get('tax_year', '')
            if at_year and str(at_year).isdigit() and int(at_year) == int(year):
                return at_record
        return None
    
    def determine_filing_status(at_record):
        """Determine if return was filed based on AT transactions (preserves existing logic)"""
        if not at_record or 'transactions' not in at_record:
            return "Not Filed"
        
        # Look for transaction code 150 (Return filed) or 976 (Return filed)
        for transaction in at_record['transactions']:
            if transaction.get('code') in ['150', '976']:
                return "Filed"
        
        return "Not Filed"
    
    def calculate_simple_tax(income, filing_status="Single"):
        """Simple tax calculation for unfiled year projections (preserves existing logic)"""
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
    
    def generate_enhanced_recommendations(analysis_data, owner_analysis):
        """Generate enhanced recommendations that include TP/S specific guidance"""
        recommendations = analysis_data.get('recommendations', [])
        
        # Add TP/S specific recommendations
        if owner_analysis.get('missing_spouse_data'):
            recommendations.append("⚠️ Missing spouse income data - verify all spouse forms are included")
        
        if owner_analysis.get('missing_taxpayer_data'):
            recommendations.append("⚠️ Missing taxpayer income data - verify all taxpayer forms are included")
        
        # Add specific income breakdown recommendations
        taxpayer_income = analysis_data.get('taxpayer_income', 0)
        spouse_income = analysis_data.get('spouse_income', 0)
        
        if taxpayer_income > 0 and spouse_income == 0:
            recommendations.append("ℹ️ Only taxpayer income found - verify if spouse should have reported income")
        elif spouse_income > 0 and taxpayer_income == 0:
            recommendations.append("ℹ️ Only spouse income found - verify if taxpayer should have reported income")
        
        return recommendations
    
    # Initialize result structure
    result = {}
    
    # Get all unique years from both WI and AT data (preserves existing logic)
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
        
        # PRESERVE EXISTING LOGIC - calculate totals exactly as before
        wi_total_income, wi_total_withholding = calculate_wi_totals(year_forms)
        
        # Get AT data for this year (preserves existing logic)
        at_record = find_at_data_for_year(year_str, at_data)
        return_status = determine_filing_status(at_record)
        
        # Calculate income discrepancy (preserves existing logic)
        at_agi = at_record.get('adjusted_gross_income', 0) if at_record else 0
        income_discrepancy = wi_total_income - at_agi
        
        # Determine if amendment is needed (preserves existing logic)
        needs_amendment = False
        if return_status == "Filed" and abs(income_discrepancy) > 1000:
            needs_amendment = True
        
        # Calculate unfiled liability (UPDATED to show actual calculated amount)
        unfiled_liability = 0
        if return_status == "Not Filed" and wi_total_income > 0:
            filing_status = at_record.get('filing_status', 'Single') if at_record else 'Single'
            estimated_tax = calculate_simple_tax(wi_total_income, filing_status)
            unfiled_liability = estimated_tax - wi_total_withholding  # Show actual amount including negatives
        
        # ENHANCED: Calculate owner-specific totals
        owner_totals = aggregate_income_by_owner(year_forms)
        
        # ENHANCED: Detect missing spouse/taxpayer data
        filing_status = at_record.get('filing_status', 'Single') if at_record else 'Single'
        owner_analysis = detect_missing_spouse_data(year_forms, filing_status)
        
        # Create analysis data (preserves existing structure)
        analysis_data = {
            'income_discrepancy': income_discrepancy,
            'needs_amendment': needs_amendment,
            'unfiled_liability': unfiled_liability,
            'return_status': return_status,
            # ENHANCED: Add owner-specific data
            'taxpayer_income': owner_totals['taxpayer']['total_income'],
            'spouse_income': owner_totals['spouse']['total_income'],
            'joint_income': owner_totals['joint']['total_income'],
            'owner_analysis': owner_analysis
        }
        
        # Generate recommendations (preserves existing logic + enhanced)
        analysis_data['recommendations'] = generate_enhanced_recommendations(analysis_data, owner_analysis)
        
        # Calculate priority level (preserves existing logic)
        def calculate_priority_level(analysis_data):
            """Calculate priority level (1=urgent, 2=high, 3=medium) - PRESERVES EXISTING LOGIC"""
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
        
        analysis_data['priority_level'] = calculate_priority_level(analysis_data)
        
        # Build result structure (preserves existing structure + enhanced)
        result[year_str] = {
            'wi_data': {
                'forms': year_forms,
                'total_income': wi_total_income,  # PRESERVES EXISTING
                'total_withholding': wi_total_withholding,  # PRESERVES EXISTING
                # ENHANCED: Add owner-specific breakdowns
                'totals': owner_totals
            },
            'at_data': at_record,  # PRESERVES EXISTING
            'return_status': return_status,  # PRESERVES EXISTING
            'has_at_data': at_record is not None,  # PRESERVES EXISTING
            'analysis': analysis_data  # PRESERVES EXISTING + ENHANCED
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
    analysis = create_enhanced_tax_summary(wi_data, at_data)
    
    # Set up Streamlit tabs
    overview_tab, detailed_tab, recommendations_tab, json_tab = st.tabs([
        "Overview", "Detailed Analysis", "Recommendations", "JSON"
    ])
    
    with overview_tab:
        st.subheader("Tax Analysis Overview")
        
        # Create summary table
        summary_data = []
        for year, year_data in analysis.items():
            analysis_info = year_data['analysis']
            summary_data.append({
                'Tax Year': year,
                'Return Status': analysis_info['return_status'],
                'WI Total Income': year_data['wi_data']['total_income'],
                'AT AGI': year_data['at_data'].get('adjusted_gross_income', 0) if year_data['at_data'] else 0,
                'Income Discrepancy': analysis_info['income_discrepancy'],
                'Needs Amendment': 'Yes' if analysis_info['needs_amendment'] else 'No',
                'Unfiled Liability': analysis_info['unfiled_liability'],
                'Priority Level': analysis_info['priority_level']
            })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            
            # Format currency columns
            currency_cols = ['WI Total Income', 'AT AGI', 'Income Discrepancy', 'Unfiled Liability']
            for col in currency_cols:
                df[col] = df[col].apply(lambda x: f"${x:,.2f}")
            
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
            
            # Summary statistics
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            total_discrepancy = sum(abs(row['Income Discrepancy']) for row in summary_data)
            total_unfiled_liability = sum(row['Unfiled Liability'] for row in summary_data)
            urgent_count = sum(1 for row in summary_data if row['Priority Level'] == 1)
            filed_count = sum(1 for row in summary_data if row['Return Status'] == 'Filed')
            
            with col1:
                st.metric("Total Income Discrepancy", f"${total_discrepancy:,.2f}")
            with col2:
                st.metric("Total Unfiled Liability", f"${total_unfiled_liability:,.2f}")
            with col3:
                st.metric("Urgent Issues", urgent_count)
            with col4:
                st.metric("Returns Filed", f"{filed_count}/{len(summary_data)}")
    
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
                    
                    # Show enhanced TP/S breakdown
                    if 'totals' in year_data['wi_data']:
                        totals = year_data['wi_data']['totals']
                        st.markdown("**Income Breakdown:**")
                        st.write(f"• Taxpayer: ${totals['taxpayer']['total_income']:,.2f}")
                        st.write(f"• Spouse: ${totals['spouse']['total_income']:,.2f}")
                        st.write(f"• Joint: ${totals['joint']['total_income']:,.2f}")
                        st.write(f"• Combined: ${totals['combined']['total_income']:,.2f}")
                    
                    # Show forms breakdown with owner information
                    if year_data['wi_data']['forms']:
                        st.markdown("**Forms by Owner:**")
                        forms_by_owner = {}
                        for form in year_data['wi_data']['forms']:
                            owner = form.get('Owner', 'TP')
                            if owner not in forms_by_owner:
                                forms_by_owner[owner] = []
                            forms_by_owner[owner].append(form)
                        
                        for owner, forms in forms_by_owner.items():
                            owner_label = "Taxpayer" if owner == "TP" else "Spouse" if owner == "S" else "Joint"
                            st.write(f"**{owner_label}:**")
                            for form in forms:
                                st.write(f"  • {form['Form']}: ${form['Income']:,.2f}")
                
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
                
                # Enhanced TP/S analysis
                if 'owner_analysis' in analysis_info:
                    owner_analysis = analysis_info['owner_analysis']
                    st.markdown("**TP/S Analysis:**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        taxpayer_income = analysis_info.get('taxpayer_income', 0)
                        spouse_income = analysis_info.get('spouse_income', 0)
                        st.write(f"Taxpayer Income: ${taxpayer_income:,.2f}")
                        st.write(f"Spouse Income: ${spouse_income:,.2f}")
                    
                    with col2:
                        if owner_analysis.get('missing_spouse_data'):
                            st.warning("⚠️ Missing spouse data")
                        if owner_analysis.get('missing_taxpayer_data'):
                            st.warning("⚠️ Missing taxpayer data")
                        if not owner_analysis.get('missing_spouse_data') and not owner_analysis.get('missing_taxpayer_data'):
                            st.success("✅ TP/S data complete")
    
    with recommendations_tab:
        st.subheader("Actionable Recommendations")
        
        # Group by priority level
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

def format_currency(amount: float) -> str:
    """Format number as currency with $ and commas"""
    return f"${amount:,.2f}" if amount is not None else "N/A"

def format_phone(phone: str) -> str:
    """Format phone number as (XXX) XXX-XXXX"""
    if not phone:
        return "N/A"
    # Remove any non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone

def format_ssn(ssn: str) -> str:
    """Format SSN as XXX-XX-XXXX with masking"""
    if not ssn:
        return "N/A"
    digits = ''.join(filter(str.isdigit, ssn))
    if len(digits) == 9:
        return f"XXX-XX-{digits[-4:]}"
    return "Invalid SSN"

def parse_misc_xml(xml_str: str) -> dict:
    """Parse MiscXML string into a dictionary"""
    if not xml_str:
        return {}
    try:
        root = ET.fromstring(xml_str)
        result = {}
        for child in root:
            result[child.tag] = child.text
        return result
    except ET.ParseError:
        return {}

def fetch_client_data(case_id: str) -> dict:
    """
    Fetch client data from API and parse into organized structure
    """
    API_KEY = "4917fa0ce4694529a9b97ead1a60c932"
    API_URL = f"https://tps.logiqs.com/publicapi/2020-02-22/cases/caseinfo?apikey={API_KEY}&CaseID={case_id}"
    
    try:
        response = requests.get(API_URL, verify=False)
        response_data = response.json()
        
        if response.status_code != 200:
            st.error(f"API Error: Status Code {response.status_code}")
            st.code(response.text)
            return None
            
        if response_data.get('status') != 'success' or 'data' not in response_data:
            st.error(f"API Error: {response_data.get('message', 'Unknown error')}")
            st.code(response_data)
            return None
            
        raw_data = response_data['data']
        misc_data = raw_data.get('MiscXML', {})
        
        return {
            'client_info': {
                'name': f"{raw_data.get('FirstName', '')} {raw_data.get('MiddleName', '')} {raw_data.get('LastName', '')}".strip(),
                'case_id': case_id,
                'ssn': format_ssn(raw_data.get('SSN')),
                'status': raw_data.get('StatusName'),
                'address': {
                    'street': raw_data.get('Address', ''),
                    'city': raw_data.get('City', ''),
                    'state': raw_data.get('State', ''),
                    'zip': raw_data.get('Zip', '')
                },
                'contact': {
                    'cell': format_phone(raw_data.get('CellPhone')),
                    'home': format_phone(raw_data.get('HomePhone')),
                    'work': format_phone(raw_data.get('WorkPhone')),
                    'email': raw_data.get('Email', 'N/A'),
                    'best_time': raw_data.get('BestTimeToCall', 'N/A'),
                    'sms_permitted': raw_data.get('SMSPermitted', False)
                }
            },
            'tax_info': {
                'total_liability': float(raw_data.get('TaxLiability', 0)),
                'years_owed': raw_data.get('OweTaxestoFederal', '').split(', ') if raw_data.get('OweTaxestoFederal') else [],
                'unfiled_years': raw_data.get('UnfiledTaxestoFederal', '').split(', ') if raw_data.get('UnfiledTaxestoFederal') else []
            },
            'case_management': {
                'team': {
                    'officer': raw_data.get('SetOfficer', 'N/A'),
                    'advocate': raw_data.get('CaseAdvocate', 'N/A'),
                    'preparer': raw_data.get('TaxPreparer', 'N/A'),
                    'ti_agent': raw_data.get('TIAgent', 'N/A'),
                    'team': raw_data.get('TeamName', 'N/A').strip()
                },
                'timeline': {
                    'sale_date': raw_data.get('SaleDate'),
                    'created_date': raw_data.get('CreatedDate'),
                    'modified_date': raw_data.get('ModifiedDate')
                }
            },
            'raw_data': raw_data
        }
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.code(response.text if 'response' in locals() else str(e))
        return None

def display_client_header(client_data: dict):
    """Display the header section with key client identifiers"""
    if not client_data:
        return
        
    client_info = client_data['client_info']
    tax_info = client_data['tax_info']
    
    # Header with key info
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.title(client_info['name'])
        st.caption(f"Case ID: {client_info['case_id']}")
    
    with col2:
        st.metric("SSN", client_info['ssn'])
    
    with col3:
        status_color = {
            'Active': 'green',
            'Pending': 'orange',
            'Inactive': 'red'
        }.get(client_info['status'], 'gray')
        
        st.markdown(
            f"<div style='background-color: {status_color}; padding: 10px; "
            f"border-radius: 5px; color: white; text-align: center;'>"
            f"Status: {client_info['status']}</div>",
            unsafe_allow_html=True
        )
    
    with col4:
        st.metric("Total Tax Liability", format_currency(tax_info['total_liability']))

def display_client_overview(client_data: dict):
    """Display the client overview section"""
    if not client_data:
        return
        
    client_info = client_data['client_info']
    tax_info = client_data['tax_info']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Contact Information")
        address = client_info['address']
        st.write(f"**Address:**  \n{address['street']}  \n{address['city']}, {address['state']} {address['zip']}")
        
        contact = client_info['contact']
        st.write("**Phone Numbers:**")
        st.write(f"Cell: {contact['cell']}")
        st.write(f"Home: {contact['home']}")
        st.write(f"Work: {contact['work']}")
        
        st.write(f"**Email:** {contact['email']}")
        st.write(f"**Best Time to Call:** {contact['best_time']}")
        st.write(f"**SMS Permitted:** {'Yes' if contact['sms_permitted'] else 'No'}")
    
    with col2:
        st.subheader("Demographics")
        demo = client_info['demographics']
        st.write(f"**Marital Status:** {demo['marital_status']}")
        if demo['business_name'] != 'N/A':
            st.write(f"**Business Name:** {demo['business_name']}")
            st.write(f"**Business Type:** {demo['business_type']}")
        st.write(f"**Creation Date:** {demo['creation_date']}")
        st.write(f"**Days in Status:** {demo['days_in_status']}")
    
    with col3:
        st.subheader("Quick Stats")
        st.metric("Total Tax Liability", format_currency(tax_info['total_liability']))
        st.write("**Years Owed:**")
        st.write(", ".join(tax_info['years_owed']) if tax_info['years_owed'][0] else "None")
        st.write("**Unfiled Years:**")
        st.write(", ".join(tax_info['unfiled_years']) if tax_info['unfiled_years'][0] else "None")
        st.write(f"**Case Created:** {client_info['demographics']['creation_date']}")

def display_financial_profile(client_data: dict):
    """Display the financial profile section"""
    if not client_data:
        return
        
    financial = client_data['financial_profile']
    
    # Income Section
    st.subheader("Income Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Taxpayer Income", format_currency(financial['income']['taxpayer']))
    with col2:
        st.metric("Spouse Income", format_currency(financial['income']['spouse']))
    with col3:
        st.metric("Total Net Income", format_currency(financial['income']['total']))
    
    # Expense Breakdown
    st.subheader("Monthly Expenses")
    col1, col2 = st.columns(2)
    
    with col1:
        expenses = financial['expenses']
        st.write(f"**Housing/Utilities:** {format_currency(expenses['housing'] + expenses['utilities'])}")
        st.write(f"**Food:** {format_currency(expenses['food'])}")
        st.write(f"**Transportation:** {format_currency(expenses['transportation'])}")
        st.write(f"**Personal:** {format_currency(expenses['personal'])}")
        st.write(f"**Other:** {format_currency(expenses['other'])}")
        st.metric("Total Monthly Expenses", format_currency(expenses['total']))
    
    # Assets Summary
    with col2:
        st.subheader("Assets")
        assets = financial['assets']
        st.write(f"**Cash on Hand:** {format_currency(assets['cash'])}")
        st.write(f"**Retirement:** {format_currency(assets['retirement'])}")
        st.write(f"**Real Estate:** {format_currency(assets['real_estate'])}")
        st.write(f"**Vehicles:** {format_currency(assets['vehicles'])}")
        st.write(f"**Business Assets:** {format_currency(assets['business'])}")
        st.metric("Total Net Realizable Value", format_currency(assets['total']))

def display_tax_information(client_data: dict):
    """Display the tax information section"""
    if not client_data:
        return
        
    tax_info = client_data['tax_info']
    
    # Tax Liability Breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Tax Liability Breakdown")
        st.metric("Total Tax Liability", format_currency(tax_info['total_liability']))
        st.write("**Years with Taxes Owed:**")
        st.write(", ".join(tax_info['years_owed']) if tax_info['years_owed'][0] else "None")
        st.write("**Unfiled Years:**")
        st.write(", ".join(tax_info['unfiled_years']) if tax_info['unfiled_years'][0] else "None")
        st.write(f"**IRS Status:** {tax_info['irs_status']}")
    
    with col2:
        st.subheader("Payment Information")
        payments = tax_info['payments']
        if payments['history']:
            st.write("**Payment History:**")
            for payment in payments['history']:
                st.write(f"- {payment}")
        else:
            st.write("No payment history available")
            
        st.write(f"**Levy Status:** {payments['levy_status']}")

def display_case_management(client_data: dict):
    """Display the case management section"""
    if not client_data:
        return
        
    case_mgmt = client_data['case_management']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Team Assignments")
        team = case_mgmt['team']
        st.write(f"**Set Officer:** {team['officer']}")
        st.write(f"**Case Advocate:** {team['advocate']}")
        st.write(f"**Tax Preparer:** {team['preparer']}")
        st.write(f"**TI Agent:** {team['ti_agent']}")
        st.write(f"**Team:** {team['team']}")
    
    with col2:
        st.subheader("Case Timeline")
        timeline = case_mgmt['timeline']
        st.write(f"**Sale Date:** {timeline['sale_date']}")
        st.write(f"**Created Date:** {timeline['created_date']}")
        st.write(f"**Modified Date:** {timeline['modified_date']}")
        st.write(f"**Current Status:** {timeline['current_status']}")
        st.write(f"**Source:** {timeline['source']}")

def display_detailed_financials(client_data: dict):
    """Display the detailed financials section"""
    if not client_data:
        return
    
    financial = client_data['financial_profile']
    misc_data = client_data['misc_data']
    
    with st.expander("Detailed Income Analysis"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Income Breakdown**")
            st.write(f"Taxpayer Income: {format_currency(financial['income']['taxpayer'])}")
            st.write(f"Spouse Income: {format_currency(financial['income']['spouse'])}")
            st.write(f"Other Income: {format_currency(financial['income']['other'])}")
        with col2:
            st.write("**Income Sources**")
            for key, value in misc_data.items():
                if key.startswith('Income_'):
                    st.write(f"{key.replace('Income_', '')}: {format_currency(float(value or 0))}")
    
    with st.expander("Detailed Expense Analysis"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Monthly Expenses**")
            expenses = financial['expenses']
            for category, amount in expenses.items():
                if category != 'total':
                    st.write(f"{category.title()}: {format_currency(amount)}")
        with col2:
            st.write("**Additional Expenses**")
            for key, value in misc_data.items():
                if key.startswith('Expense_') and key not in ['Expense_Housing', 'Expense_Utilities', 'Expense_FoodMisc', 
                                                            'Expense_Transportation', 'Expense_PersonalCare', 'Expense_Apparel', 
                                                            'Expense_Other']:
                    st.write(f"{key.replace('Expense_', '')}: {format_currency(float(value or 0))}")
    
    with st.expander("Asset Details"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Asset Breakdown**")
            assets = financial['assets']
            for category, amount in assets.items():
                if category != 'total':
                    st.write(f"{category.title()}: {format_currency(amount)}")
        with col2:
            st.write("**Additional Assets**")
            for key, value in misc_data.items():
                if key.startswith('Asset_') and key not in ['Asset_Cash', 'Asset_Retirement', 'Asset_RealEstate', 
                                                          'Asset_Vehicles', 'Asset_Business']:
                    st.write(f"{key.replace('Asset_', '')}: {format_currency(float(value or 0))}")

def render_client_profile():
    """Render the client profile tab"""
    # Get case_id from session state
    case_id = st.session_state.get('case_id')
    if not case_id:
        st.warning("Please enter a Case ID first.")
        return
    
    # Fetch client data if not in session state
    if 'client_data' not in st.session_state:
        with st.spinner("Fetching client data..."):
            st.session_state.client_data = fetch_client_data(case_id)
    
    client_data = st.session_state.client_data
    if not client_data:
        st.error("Failed to load client data.")
        return
    
    # Display header
    display_client_header(client_data)
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Financial Profile", "Tax Info",
        "Case Management", "Detailed Financials"
    ])
    
    with tab1:
        display_client_overview(client_data)
    
    with tab2:
        display_financial_profile(client_data)
    
    with tab3:
        display_tax_information(client_data)
    
    with tab4:
        display_case_management(client_data)
    
    with tab5:
        display_detailed_financials(client_data)

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

    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Case ID input in sidebar
    case_id = st.sidebar.text_input("Enter Case ID", key="case_id_input")
    if case_id:
        st.session_state.case_id = case_id
        # Clear client data when case ID changes
        st.session_state.client_data = None
    
    # Radio button for page selection
    page = st.sidebar.radio(
        "Choose a page:",
        ["🏠 Home", "👤 Client Profile", "📄 WI Parser", "📊 AT Parser", "📋 ROA Parser", "📝 TRT Parser", "📈 Tax Summary", "📊 Comprehensive Analysis", "⚙️ Settings"],
        index=0
    )

    # Render content based on selected page
    if page == "🏠 Home":
        render_home()
    elif page == "👤 Client Profile":
        render_client_profile()
    elif page == "📄 WI Parser":
        render_wi_parser()
    elif page == "📊 AT Parser":
        render_at_parser()
    elif page == "📋 ROA Parser":
        render_roa_parser()
    elif page == "📝 TRT Parser":
        render_trt_parser()
    elif page == "📈 Tax Summary":
        render_tax_summary()
    elif page == "📊 Comprehensive Analysis":
        render_comprehensive_analysis()
    elif page == "⚙️ Settings":
        render_settings()

if __name__ == "__main__":
    main()
