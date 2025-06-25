import streamlit as st
import requests
import json

def fetch_client_data(case_id: str) -> dict:
    """
    Fetch client data from API and parse into organized structure
    """
    API_KEY = "4917fa0ce4694529a9b97ead1a60c932"
    API_URL = f"https://tps.logiqs.com/publicapi/2020-02-22/cases/caseinfo?apikey={API_KEY}&CaseID={case_id}"
    
    try:
        response = requests.get(API_URL)
        response_data = response.json()
            
        if response_data.get('status') != 'success' or 'data' not in response_data:
            st.error(f"API Error: {response_data.get('message', 'Unknown error')}")
            return None
            
        raw_data = response_data['data']
        misc_data = raw_data.get('MiscXML', {})
        
        # Organize MiscXML data into structured categories
        organized_misc = organize_misc_xml_data(misc_data)
        
        return {
            'personal': {
                'name': f"{raw_data.get('FirstName', '')} {raw_data.get('MiddleName', '')} {raw_data.get('LastName', '')}".strip(),
                'ssn': format_ssn(raw_data.get('SSN')),
                'dob': raw_data.get('DOB', 'N/A'),
                'phone': format_phone(raw_data.get('CellPhone')),
                'email': raw_data.get('Email', 'N/A'),
                'address': {
                    'street': raw_data.get('Address', ''),
                    'city': raw_data.get('City', ''),
                    'state': raw_data.get('State', ''),
                    'zip': raw_data.get('Zip', '')
                }
            },
            'financial_profile': {
                'income': {
                    'taxpayer': float(misc_data.get('Income_Taxpayer', 0)),
                    'spouse': float(misc_data.get('Income_Spouse', 0)),
                    'other': float(misc_data.get('Income_Other', 0)),
                    'total': float(misc_data.get('Income_Total', 0))
                },
                'expenses': {
                    'housing': float(misc_data.get('Expense_Housing', 0)),
                    'utilities': float(misc_data.get('Expense_Utilities', 0)),
                    'food': float(misc_data.get('Expense_FoodMisc', 0)),
                    'transportation': float(misc_data.get('Expense_Transportation', 0)),
                    'personal_care': float(misc_data.get('Expense_PersonalCare', 0)),
                    'apparel': float(misc_data.get('Expense_Apparel', 0)),
                    'other': float(misc_data.get('Expense_Other', 0)),
                    'total': float(misc_data.get('Expense_Total', 0))
                },
                'assets': {
                    'cash': float(misc_data.get('Asset_Cash', 0)),
                    'retirement': float(misc_data.get('Asset_Retirement', 0)),
                    'real_estate': float(misc_data.get('Asset_RealEstate', 0)),
                    'vehicles': float(misc_data.get('Asset_Vehicles', 0)),
                    'business': float(misc_data.get('Asset_Business', 0)),
                    'total': float(misc_data.get('Asset_Total', 0))
                }
            },
            'tax_info': {
                'total_liability': float(raw_data.get('TaxLiability', 0)),
                'years_owed': raw_data.get('OweTaxestoFederal', '').split(', ') if raw_data.get('OweTaxestoFederal') else [],
                'unfiled_years': raw_data.get('UnfiledTaxestoFederal', '').split(', ') if raw_data.get('UnfiledTaxestoFederal') else [],
                'irs_status': 'Collections' if misc_data.get('TaxpayerStatusIsCollections') else 'N/A',
                'payments': {
                    'history': [],
                    'levy_status': misc_data.get('AnyLevysOnAssets', 'N/A')
                }
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
                    'modified_date': raw_data.get('ModifiedDate'),
                    'current_status': raw_data.get('StatusName'),
                    'source': raw_data.get('SourceName', 'N/A')
                }
            },
            'misc_data': organized_misc,
            'raw_data': raw_data
        }
        
    except Exception as e:
        st.error(f"Error fetching client data: {str(e)}")
        return None

def organize_misc_xml_data(misc_data: dict) -> dict:
    """
    Organize MiscXML data into structured categories
    """
    organized = {
        'expenses': {},
        'assets': {},
        'liabilities': {},
        'business': {},
        'other': {}
    }
    
    # Organize expenses - using actual field names from API response
    expense_fields = {
        'Expense_HouseKeeping': 'Housing',
        'Expense_Apparel': 'Clothing',
        'Expense_PersonalCare': 'Personal Care',
        'Expense_FoodMisc': 'Food',
        'Expense_PublicTransportation': 'Transportation',
        'Expense_Prescription': 'Prescription Drugs',
        'Expense_Copay': 'Medical Copays',
        'Expense_Taxes': 'Taxes',
        'Expense_Other1': 'Other Expenses',
        'Expense_Other2': 'Other Expenses 2',
        'Expense_Other3': 'Other Expenses 3',
        'Expense_Other4': 'Other Expenses 4',
        'Expense_Other5': 'Other Expenses 5',
        'Expense_Other6': 'Other Expenses 6'
    }
    
    for field, category in expense_fields.items():
        value = float(misc_data.get(field, 0))
        if value > 0:
            if category not in organized['expenses']:
                organized['expenses'][category] = 0
            organized['expenses'][category] += value
    
    # Organize assets - using actual field names from API response
    asset_fields = {
        'EE_Asset_Retirement': 'Retirement',
        'EE_Asset_QSRealEstate': 'Real Estate',
        'EE_Asset_QSVehicle1': 'Vehicle 1',
        'EE_Asset_QSVehicle2': 'Vehicle 2',
        'EE_Asset_QSVehicle3': 'Vehicle 3',
        'EE_Asset_QSVehicle4': 'Vehicle 4',
        'EE_Asset_QSEffects': 'Personal Effects',
        'EE_Asset_QSInvestments': 'Investments',
        'EE_Asset_QSLifeInsurance': 'Life Insurance',
        'EE_Asset_QSOther': 'Other Assets',
        'CashOnHand': 'Cash on Hand',
        'EE_Asset_BizCash': 'Business Cash',
        'EE_Asset_BizBankAccounts': 'Business Bank Accounts',
        'EE_Asset_BizReceivables': 'Business Receivables',
        'EE_Asset_BizProperties': 'Business Properties',
        'EE_Asset_BizTools': 'Business Tools',
        'EE_Asset_BizOther': 'Other Business Assets'
    }
    
    for field, category in asset_fields.items():
        value = float(misc_data.get(field, 0))
        if value > 0:
            organized['assets'][category] = value
    
    # Organize liabilities - using actual field names from API response
    liability_fields = {
        'CarPayment': 'Car Payment',
        'CreditCardDebt': 'Credit Card Debt',
        'CarInsurance': 'Car Insurance',
        'CardPayments': 'Card Payments',
        'HomeEquity': 'Home Equity',
        'CarEquity': 'Car Equity',
        'AvailableCash': 'Available Cash',
        'CanRaiseFunds': 'Can Raise Funds'
    }
    
    for field, category in liability_fields.items():
        value = misc_data.get(field, '')
        if value and value != '0' and value != '0.00':
            organized['liabilities'][category] = value
    
    # Organize business information - using actual field names from API response
    business_fields = {
        'BizIncome_GrossReceipts': 'Gross Receipts',
        'BizIncome_GrossRental': 'Gross Rental',
        'BizIncome_Interest': 'Business Interest',
        'BizIncome_Dividends': 'Business Dividends',
        'BizIncome_Cash': 'Business Cash',
        'BizIncome_Total': 'Total Business Income',
        'BizExpense_Materials': 'Materials',
        'BizExpense_Inventory': 'Inventory',
        'BizExpense_Wages': 'Wages',
        'BizExpense_Rent': 'Business Rent',
        'BizExpense_Supplies': 'Supplies',
        'BizExpense_VehicleGas': 'Vehicle Gas',
        'BizExpense_VehicleRepairs': 'Vehicle Repairs',
        'BizExpense_Insurance': 'Business Insurance',
        'BizExpense_Taxes': 'Business Taxes',
        'BizExpense_Total': 'Total Business Expenses'
    }
    
    for field, category in business_fields.items():
        value = float(misc_data.get(field, 0))
        if value > 0:
            organized['business'][category] = value
    
    # Add other miscellaneous fields - using actual field names from API response
    other_fields = {
        'Income_Net': 'Net Income',
        'IncomeDeductions': 'Income Deductions',
        'TotalNetRealizableValue': 'Total Net Realizable Value',
        'FamilyMembersUnder65': 'Family Members Under 65',
        'FamilyMembersOver65': 'Family Members Over 65',
        'VehicleCount': 'Vehicle Count',
        'CreditScore': 'Credit Score',
        'Credit': 'Credit Available',
        'IncomeGrossM': 'Gross Monthly Income',
        'IncomeSpouseM': 'Spouse Monthly Income',
        'Income_Personal_Net': 'Personal Net Income',
        'ExpenseTotalAllowable': 'Total Allowable Expenses',
        'ClientDetailHousehold': 'Household Size',
        'ClientDetailNetIncom': 'Client Net Income',
        'SpouseDetailNetIncom': 'Spouse Net Income'
    }
    
    for field, category in other_fields.items():
        value = misc_data.get(field, '')
        if value and value != '0' and value != '0.00':
            organized['other'][category] = value
    
    return organized

def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"

def format_phone(phone: str) -> str:
    """Format phone number"""
    if not phone:
        return "N/A"
    # Remove all non-digits
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone

def format_ssn(ssn: str) -> str:
    """Format SSN with dashes"""
    if not ssn:
        return "N/A"
    # Remove all non-digits
    digits = ''.join(filter(str.isdigit, ssn))
    if len(digits) == 9:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    return ssn

def display_client_header(client_data: dict):
    """Display the header section with key client identifiers"""
    if not client_data:
        return
        
    client_info = client_data['personal']
    tax_info = client_data['tax_info']
    
    # Get case_id from session state
    case_id = st.session_state.get('case_id', 'N/A')
    
    # Header with key info
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.title(client_info['name'])
        st.caption(f"Case ID: {case_id}")
    
    with col2:
        st.metric("SSN", client_info['ssn'])
    
    with col3:
        status_color = {
            'Active': 'green',
            'Pending': 'orange',
            'Inactive': 'red'
        }.get(client_info.get('status', 'Unknown'), 'gray')
        
        st.markdown(
            f"<div style='background-color: {status_color}; padding: 10px; "
            f"border-radius: 5px; color: white; text-align: center;'>"
            f"Status: {client_info.get('status', 'Unknown')}</div>",
            unsafe_allow_html=True
        )
    
    with col4:
        st.metric("Total Tax Liability", format_currency(tax_info['total_liability']))

def display_client_overview(client_data: dict):
    """Display the client overview section"""
    if not client_data:
        return
        
    client_info = client_data['personal']
    tax_info = client_data['tax_info']
    financial = client_data['financial_profile']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Contact Information")
        st.write(f"**Phone:** {client_info['phone']}")
        st.write(f"**Email:** {client_info['email']}")
        
        st.subheader("Address")
        address = client_info['address']
        st.write(f"**Street:** {address['street']}")
        st.write(f"**City:** {address['city']}")
        st.write(f"**State:** {address['state']}")
        st.write(f"**ZIP:** {address['zip']}")
    
    with col2:
        st.subheader("Tax Information")
        st.write(f"**Total Liability:** {format_currency(tax_info['total_liability'])}")
        st.write("**Years Owed:**")
        st.write(", ".join(tax_info['years_owed']) if tax_info['years_owed'] else "None")
        st.write("**Unfiled Years:**")
        st.write(", ".join(tax_info['unfiled_years']) if tax_info['unfiled_years'] else "None")
        st.write(f"**IRS Status:** {tax_info['irs_status']}")
        
        st.subheader("Case Management")
        case_mgmt = client_data['case_management']
        timeline = case_mgmt['timeline']
        st.write(f"**Created Date:** {timeline['created_date']}")
        st.write(f"**Current Status:** {timeline['current_status']}")
    
    with col3:
        st.subheader("Income Summary")
        income = financial['income']
        st.write(f"**Taxpayer Income:** {format_currency(income['taxpayer'])}")
        st.write(f"**Spouse Income:** {format_currency(income['spouse'])}")
        st.write(f"**Total Net Income:** {format_currency(income['total'])}")
        
        st.subheader("Expenses Summary")
        expenses = financial['expenses']
        st.write(f"**Total Monthly Expenses:** {format_currency(expenses['total'])}")
        
        st.subheader("Assets Summary")
        assets = financial['assets']
        st.write(f"**Total Assets:** {format_currency(assets['total'])}")

def display_financial_profile(client_data: dict):
    """Display the financial profile section"""
    if not client_data:
        return
        
    financial = client_data['financial_profile']
    
    # Income Section
    st.subheader("Income Information")
    income = financial['income']
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Taxpayer Income", format_currency(income['taxpayer']))
    with col2:
        st.metric("Spouse Income", format_currency(income['spouse']))
    with col3:
        st.metric("Total Net Income", format_currency(income['total']))
    
    # Monthly Expenses
    st.subheader("Monthly Expenses")
    expenses = financial['expenses']
    if expenses:
        col1, col2 = st.columns(2)
        with col1:
            expense_categories = ['housing', 'utilities', 'food', 'transportation', 'personal_care', 'apparel', 'other']
            for category in expense_categories:
                if expenses.get(category, 0) > 0:
                    st.write(f"**{category.title()}:** {format_currency(expenses[category])}")
        with col2:
            st.metric("Total Monthly Expenses", format_currency(expenses['total']))
    else:
        st.write("No expense data available")
    
    # Assets Summary
    st.subheader("Assets")
    assets = financial['assets']
    if assets:
        col1, col2 = st.columns(2)
        with col1:
            asset_categories = ['cash', 'retirement', 'real_estate', 'vehicles', 'business']
            for category in asset_categories:
                if assets.get(category, 0) > 0:
                    st.write(f"**{category.title()}:** {format_currency(assets[category])}")
        with col2:
            st.metric("Total Assets", format_currency(assets['total']))
    else:
        st.write("No asset data available")
    
    # Additional Misc Data
    if 'misc_data' in client_data and client_data['misc_data']:
        st.subheader("Additional Financial Information")
        misc = client_data['misc_data']
        
        if misc.get('expenses'):
            st.write("**Additional Expenses:**")
            for category, amount in misc['expenses'].items():
                st.write(f"- {category}: {format_currency(amount)}")
        
        if misc.get('assets'):
            st.write("**Additional Assets:**")
            for category, amount in misc['assets'].items():
                st.write(f"- {category}: {format_currency(amount)}")
        
        if misc.get('liabilities'):
            st.write("**Liabilities:**")
            for category, value in misc['liabilities'].items():
                st.write(f"- {category}: {value}")
        
        if misc.get('other'):
            st.write("**Other Information:**")
            for category, value in misc['other'].items():
                st.write(f"- {category}: {value}")

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
        st.write(", ".join(tax_info['years_owed']) if tax_info['years_owed'] else "None")
        st.write("**Unfiled Years:**")
        st.write(", ".join(tax_info['unfiled_years']) if tax_info['unfiled_years'] else "None")
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
    """Display case management information"""
    if not client_data:
        return
        
    case_mgmt = client_data['case_management']
    
    st.subheader("Case Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Team Assignment**")
        team = case_mgmt['team']
        st.write(f"Revenue Officer: {team['officer']}")
        st.write(f"Case Advocate: {team['advocate']}")
        st.write(f"Tax Preparer: {team['preparer']}")
        st.write(f"TI Agent: {team['ti_agent']}")
        st.write(f"Team: {team['team']}")
    
    with col2:
        st.write("**Timeline**")
        timeline = case_mgmt['timeline']
        st.write(f"Sale Date: {timeline['sale_date']}")
        st.write(f"Created: {timeline['created_date']}")
        st.write(f"Modified: {timeline['modified_date']}")
        st.write(f"Current Status: {timeline['current_status']}")
        st.write(f"Source: {timeline['source']}")

def display_detailed_financials(client_data: dict):
    """Display the detailed financials section"""
    if not client_data:
        return
    
    financial = client_data['financial_profile']
    misc_data = client_data['misc_data']
    
    # Business Information
    if misc_data.get('business'):
        st.subheader("Business Information")
        business = misc_data['business']
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Business Income**")
            income_fields = ['Gross Receipts', 'Gross Rental', 'Business Interest', 'Business Dividends', 'Business Cash', 'Total Business Income']
            for field in income_fields:
                if field in business:
                    st.write(f"{field}: {format_currency(business[field])}")
        with col2:
            st.write("**Business Expenses**")
            expense_fields = ['Materials', 'Inventory', 'Wages', 'Business Rent', 'Supplies', 'Vehicle Gas', 'Vehicle Repairs', 'Business Insurance', 'Business Taxes', 'Total Business Expenses']
            for field in expense_fields:
                if field in business:
                    st.write(f"{field}: {format_currency(business[field])}")
    
    # Detailed Assets
    if misc_data.get('assets'):
        st.subheader("Detailed Assets")
        assets = misc_data['assets']
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Personal Assets**")
            personal_assets = ['Retirement', 'Real Estate', 'Vehicle 1', 'Vehicle 2', 'Vehicle 3', 'Vehicle 4', 'Personal Effects', 'Investments', 'Life Insurance', 'Other Assets', 'Cash on Hand']
            for asset in personal_assets:
                if asset in assets:
                    st.write(f"{asset}: {format_currency(assets[asset])}")
        with col2:
            st.write("**Business Assets**")
            business_assets = ['Business Cash', 'Business Bank Accounts', 'Business Receivables', 'Business Properties', 'Business Tools', 'Other Business Assets']
            for asset in business_assets:
                if asset in assets:
                    st.write(f"{asset}: {format_currency(assets[asset])}")
    
    # Other Financial Information
    if misc_data.get('other'):
        st.subheader("Other Financial Information")
        other = misc_data['other']
        col1, col2 = st.columns(2)
        with col1:
            for key, value in other.items():
                if key not in ['Family Members Under 65', 'Family Members Over 65', 'Vehicle Count']:
                    st.write(f"**{key}:** {value}")
        with col2:
            if 'Family Members Under 65' in other:
                st.write(f"**Family Members Under 65:** {other['Family Members Under 65']}")
            if 'Family Members Over 65' in other:
                st.write(f"**Family Members Over 65:** {other['Family Members Over 65']}")
            if 'Vehicle Count' in other:
                st.write(f"**Vehicle Count:** {other['Vehicle Count']}")
    
    # Raw MiscXML Data (collapsible)
    with st.expander("Raw MiscXML Data"):
        st.json(client_data['raw_data'].get('MiscXML', {}))

def render_client_profile():
    """Main function to render the client profile tab"""
    st.header("Client Profile")
    
    # Get case ID from session state
    case_id = st.session_state.get('case_id')
    
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return
    
    # Fetch client data
    client_data = fetch_client_data(case_id)
    
    if not client_data:
        st.error("Failed to load client data.")
        return
    
    # Display client header
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
    
    # Show raw data in expander
    with st.expander("Raw API Data"):
        st.json(client_data['raw_data']) 