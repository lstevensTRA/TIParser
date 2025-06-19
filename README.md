# IRS Transcript Parser

A Streamlit application for parsing and analyzing various IRS transcripts including:
- Wage & Income (WI) Transcripts
- Account Transcripts (AT)
- Record of Account (ROA)
- Tax Return Transcripts (TRT)

## Features

- **Multi-Document Support**: Parse multiple transcript types
- **Automated Data Extraction**: Extract key information from PDFs
- **Tax Year Analysis**: View data across multiple tax years
- **Income Summaries**: Detailed breakdowns of different income types
- **Tax Projections**: Basic tax liability projections

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up cookie authentication:
```bash
python3 extract_tps_cookies.py
```

3. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Enter your Case ID on the home page
2. Navigate to the appropriate parser tab
3. View extracted data in the Summary Table
4. Check detailed extraction info in other tabs

## Security Note

This application requires TPS authentication cookies to function. Never share your cookie file or commit it to version control. # TI_parse
