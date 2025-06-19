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

    # Use the cookie string directly as a header
    cookie_header = cookies if isinstance(cookies, str) else ""

    url = f"https://tps.logiqs.com/API/Document/gridBind?caseid={case_id}&type=grid"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "User-Agent": user_agent,
        "Cookie": cookie_header
    }

    try:
        st.write("🔍 Fetching documents...")
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
    results = {}
    logger.info("Starting form pattern matching")
    def write_out(msg):
        if output_buffer is not None:
            output_buffer.write(msg + "\n")
        else:
            st.write(msg)
    write_out("🔍 **Form Pattern Matching:**")
    for form_name, pattern_info in form_patterns.items():
        logger.info(f"Processing form: {form_name}")
        matches = list(re.finditer(pattern_info['pattern'], text, re.IGNORECASE))
        if not matches:
            write_out(f"\n📋 **Form {form_name}:**")
            write_out(f"- ❌ No match found for pattern")
            logger.info(f"Form {form_name}: No pattern match found")
            continue
        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            form_text = text[start:end]
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
            if form_name == 'W-2':
                label_str = f" (EIN: {unique_id}, Employer: {unique_label})"
            elif form_name == '1099-INT':
                label_str = f" (FIN: {unique_id}, Payer: {unique_label})"
            elif form_name.startswith('1099') and unique_label:
                label_str = f", Payer: {unique_label}"
            else:
                label_str = ""
            write_out(f"\n📋 **Form {form_name} #{idx+1}{label_str}:**")
            logger.info(f"Form {form_name} #{idx+1}: {label_str}")
            write_out(f"- ✅ Pattern matched successfully")
            logger.info(f"Form {form_name} #{idx+1}: Pattern matched successfully")
            year = tax_year
            write_out(f"- 📅 Year: {year}")
            logger.info(f"Form {form_name} #{idx+1}: Using tax year {year}")
            fields_data = {}
            write_out(f"- 📊 Field Extraction:")
            logger.info(f"Form {form_name} #{idx+1}: Starting field extraction")
            for field_name, regex in pattern_info['fields'].items():
                if regex:
                    field_match = re.search(regex, form_text, re.IGNORECASE)
                    if field_match:
                        value = to_float(field_match.group(1))
                        fields_data[field_name] = value
                        write_out(f"  - {field_name}: {value}")
                        logger.info(f"Form {form_name} #{idx+1}: Field {field_name} = {value}")
                        logger.info(f"Matched text for {field_name}: {field_match.group(0)}")
                    else:
                        write_out(f"  - {field_name}: No match found")
                        logger.info(f"Form {form_name} #{idx+1}: Field {field_name} - No match found")
            if not fields_data:
                write_out(f"⚠️ Form {form_name} matched but no fields were captured")
                logger.warning(f"Form {form_name} #{idx+1}: Pattern matched but no fields captured")
            calc = pattern_info['calculation']
            income = calc['Income'](fields_data, filing_status, combined_income) if 'filing_status' in calc['Income'].__code__.co_varnames else calc['Income'](fields_data)
            withholding = calc['Withholding'](fields_data) if callable(calc.get('Withholding')) else 0
            category = pattern_info.get('category', 'Neither')
            write_out(f"- 💰 Calculated Values:")
            write_out(f"  - Income: {income}")
            write_out(f"  - Withholding: {withholding}")
            write_out(f"  - Category: {category}")
            logger.info(f"Form {form_name} #{idx+1}: Calculated values - Income: {income}, Withholding: {withholding}, Category: {category}")
            if year not in results:
                results[year] = []
            results[year].append({
                'Form': form_name,
                'UniqueID': unique_id if unique_id else None,
                'Label': unique_label if unique_label else None,
                'Income': income,
                'Withholding': withholding,
                'Category': category,
                'Fields': fields_data
            })
    logger.info("Form processing completed")
    return results

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
        st.session_state['case_id'] = case_id
        st.success(f"✅ Case ID set to: {case_id}")
        
        # Document type detection
        if cookies:  # Only try to detect documents if we have cookies
            st.write("🔍 Checking for available documents...")
            
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
            
            if not any([wi_files, at_files, roa_files, trt_files]):
                st.warning("No documents found for this case ID")
        else:
            st.info("Please ensure you have valid cookies before checking for documents.")

def render_wi_parser():
    """Render the WI Transcript Parser page"""
    st.title("WI Transcript Parser")
    
    # Get case_id from session state
    case_id = st.session_state.get('case_id', None)
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return

    # Set up Streamlit tabs
    main_tab, detail_tab, log_tab, tax_tab = st.tabs(["Summary Table", "Detailed Extraction", "Logs", "Tax Projection"])

    # Set up a string buffer for logs
    import io as _io
    log_buffer = _io.StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    log_handler.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    # Set up a string buffer for detailed extraction
    detail_buffer = _io.StringIO()

    wi_files = get_wi_files(case_id)
    if wi_files:
        with main_tab:
            st.write(f"Found {len(wi_files)} WI documents. Parsing all...")
            all_results = {}
            for wi_file in wi_files:
                pdf_bytes = download_file(wi_file["CaseDocumentID"], case_id)
                if pdf_bytes:
                    text = extract_text_from_pdf(pdf_bytes)
                    if text:
                        ssn, tax_periods, tax_year = extract_header_info(text)
                        # Write extraction info to detail_buffer in a more concise format
                        detail_buffer.write(f"Processing: {wi_file['FileName']}\n")
                        detail_buffer.write(f"SSN: {ssn} | Tax Period: {', '.join(tax_periods) if tax_periods else 'None'}\n")
                        detail_buffer.write("-" * 50 + "\n")
                        # Pass buffer to extract_form_data
                        data = extract_form_data(text, form_patterns, tax_year, output_buffer=detail_buffer)
                        # Merge results by year
                        for year, forms in data.items():
                            if year not in all_results:
                                all_results[year] = []
                            all_results[year].extend(forms)

            # Aggregate yearly totals
            summary_rows = []
            for year, forms in sorted(all_results.items()):
                try:
                    year_int = int(str(year).replace(",", "").replace(" ", ""))
                except Exception:
                    year_int = year
                se_income = 0
                se_withholding = 0
                nonse_income = 0
                nonse_withholding = 0
                other_income = 0
                for form in forms:
                    cat = form.get('Category', 'Other')
                    income = form.get('Income', 0)
                    withholding = form.get('Withholding', 0)
                    if cat == 'SE':
                        se_income += income
                        se_withholding += withholding
                    elif cat == 'Non-SE':
                        nonse_income += income
                        nonse_withholding += withholding
                    else:
                        other_income += income
                summary_rows.append({
                    'Tax Year': year_int,
                    'SE Income': se_income,
                    'SE Withholding': se_withholding,
                    'Non-SE Income': nonse_income,
                    'Non-SE Withholding': nonse_withholding,
                    'Other Income': other_income
                })
            df = pd.DataFrame(summary_rows)
            df["Tax Year"] = df["Tax Year"].astype(str)
            currency_cols = ['SE Income', 'SE Withholding', 'Non-SE Income', 'Non-SE Withholding', 'Other Income']
            for col in currency_cols:
                df[col] = df[col].apply(lambda x: f"${x:,.2f}")
            st.subheader("Yearly Income & Withholding Summary")
            st.dataframe(df, use_container_width=True, hide_index=True)

        with detail_tab:
            st.subheader("Detailed Extraction Output")
            st.text(detail_buffer.getvalue())

        with log_tab:
            st.subheader("Log Output")
            st.text(log_buffer.getvalue())

        with tax_tab:
            render_tax_projection(summary_rows)
    else:
        with main_tab:
            st.warning("No WI documents found for this case ID")
        
    logger.removeHandler(log_handler)

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
        st.write("🔍 Fetching documents...")
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
    """Extract key data from AT transcript text"""
    data = {}
    
    # Extract tax period
    tax_period_match = re.search(r'TAX PERIOD:\s*([A-Za-z]+\.\s*\d{1,2},\s*\d{4})', text)
    if tax_period_match:
        # Convert "Dec. 31, 2016" to "2016"
        tax_year = tax_period_match.group(1).split(',')[-1].strip()
        data['tax_year'] = tax_year
    
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

def render_at_parser():
    """Render the AT Parser page (Account Transcript)"""
    st.title("AT Parser")
    
    # Get case_id from session state
    case_id = st.session_state.get('case_id', None)
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return

    # Set up Streamlit tabs
    summary_tab, transactions_tab, log_tab = st.tabs(["Summary", "Transactions", "Logs"])

    # Set up a string buffer for logs
    import io as _io
    log_buffer = _io.StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    log_handler.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    at_files = get_at_files(case_id)
    if at_files:
        # Store all extracted data
        all_years_data = []
        all_transactions = []
        
        for at_file in at_files:
            logger.info(f"Processing file: {at_file['FileName']}")
            pdf_bytes = download_file(at_file["CaseDocumentID"], case_id)
            if pdf_bytes:
                text = extract_text_from_pdf(pdf_bytes)
                if text:
                    data = extract_at_data(text)
                    if data and 'tax_year' in data:
                        all_years_data.append(data)
                        if 'transactions' in data:
                            # Add tax year to each transaction for reference
                            for trans in data['transactions']:
                                trans['tax_year'] = data['tax_year']
                            all_transactions.extend(data['transactions'])
        
        with summary_tab:
            if all_years_data:
                # Create DataFrame for summary
                df = pd.DataFrame(all_years_data)
                # Sort by tax year
                df['tax_year'] = pd.to_numeric(df['tax_year'])
                df = df.sort_values('tax_year')
                
                # Format currency columns
                currency_cols = [
                    'account_balance', 'accrued_interest', 'accrued_penalty', 
                    'total_balance', 'adjusted_gross_income', 'taxable_income',
                    'tax_per_return', 'se_tax_taxpayer', 'se_tax_spouse', 'total_se_tax'
                ]
                
                # Create display DataFrame with formatted currency
                display_df = df.copy()
                for col in currency_cols:
                    display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
                
                # Rename columns for display
                column_names = {
                    'tax_year': 'Tax Year',
                    'account_balance': 'Account Balance',
                    'accrued_interest': 'Accrued Interest',
                    'accrued_penalty': 'Accrued Penalty',
                    'total_balance': 'Total Balance',
                    'adjusted_gross_income': 'AGI',
                    'taxable_income': 'Taxable Income',
                    'tax_per_return': 'Tax Per Return',
                    'se_tax_taxpayer': 'SE Tax (Taxpayer)',
                    'se_tax_spouse': 'SE Tax (Spouse)',
                    'total_se_tax': 'Total SE Tax',
                    'filing_status': 'Filing Status'
                }
                display_df = display_df.rename(columns=column_names)
                
                # Display the summary table
                st.subheader("Account Transcript Summary")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        with transactions_tab:
            if all_transactions:
                st.subheader("Transactions")
                # Create DataFrame for transactions
                trans_df = pd.DataFrame(all_transactions)
                # Sort by date
                trans_df['date'] = pd.to_datetime(trans_df['date'])
                trans_df = trans_df.sort_values(['tax_year', 'date'])
                
                # Format amount as currency
                trans_df['amount'] = trans_df['amount'].apply(lambda x: f"${x:,.2f}")
                
                # Rename columns for display
                trans_df = trans_df.rename(columns={
                    'tax_year': 'Tax Year',
                    'code': 'Code',
                    'meaning': 'Meaning',
                    'description': 'Description',
                    'date': 'Date',
                    'amount': 'Amount'
                })
                
                # Reorder columns
                trans_df = trans_df[['Tax Year', 'Date', 'Code', 'Meaning', 'Description', 'Amount']]
                
                # Display the transactions table
                st.dataframe(trans_df, use_container_width=True, hide_index=True)
            else:
                st.info("No transactions found in the documents.")
        
        with log_tab:
            st.subheader("Log Output")
            for at_file in at_files:
                logger.info(f"Processing file: {at_file['FileName']}")
                pdf_bytes = download_file(at_file["CaseDocumentID"], case_id)
                if pdf_bytes:
                    text = extract_text_from_pdf(pdf_bytes)
                    if text:
                        logger.info("Successfully extracted text from PDF")
                        logger.info("Raw text content:")
                        logger.info("-" * 50)
                        logger.info(text)
                        logger.info("-" * 50)
                    else:
                        logger.warning(f"Failed to extract text from {at_file['FileName']}")
                else:
                    logger.error(f"Failed to download {at_file['FileName']}")
            st.text(log_buffer.getvalue())
    else:
        with summary_tab:
            st.warning("No AT documents found for this case ID")

    # Clean up logging handler
    logger.removeHandler(log_handler)

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
        st.write("🔍 Fetching documents...")
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
        st.write("🔍 Fetching documents...")
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
    """)

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="IRS Transcript Parser",
        page_icon="📊",
        layout="wide"
    )

    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Radio button for page selection
    page = st.sidebar.radio(
        "Choose a page:",
        ["🏠 Home", "📄 WI Parser", "📊 AT Parser", "📋 ROA Parser", "📝 TRT Parser", "⚙️ Settings"],
        index=0
    )

    # Render content based on selected page
    if page == "🏠 Home":
        render_home()
    elif page == "📄 WI Parser":
        render_wi_parser()
    elif page == "📊 AT Parser":
        render_at_parser()
    elif page == "📋 ROA Parser":
        render_roa_parser()
    elif page == "📝 TRT Parser":
        render_trt_parser()
    elif page == "⚙️ Settings":
        render_settings()

if __name__ == "__main__":
    main()
