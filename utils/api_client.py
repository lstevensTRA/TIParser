"""
Client Profile Tab - Complete implementation
This is a NEW file - do not modify existing page files
"""

import streamlit as st
import requests
from typing import Dict, Optional
from config.api_config import get_client_api_url, CLIENT_API_CONFIG
from utils.data_formatter import ClientDataFormatter
from utils.tp_s_parser import TPSParser

class ClientAPIClient:
    """Handle all client profile API interactions"""
    
    def __init__(self):
        self.timeout = CLIENT_API_CONFIG["timeout"]
        self.retry_attempts = CLIENT_API_CONFIG["retry_attempts"]
    
    def fetch_client_data(self, case_id: str) -> Optional[Dict]:
        """
        Fetch client data from API
        
        Args:
            case_id: The case ID to fetch data for
            
        Returns:
            Dict with client data or None if error
        """
        if not self.validate_case_id(case_id):
            st.error("❌ Please enter a valid Case ID")
            return None

        url = get_client_api_url(case_id)
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('status') != 'success':
                    st.error(f"API Error: {data.get('message', 'Unknown error')}")
                    return None
                
                return data.get('data')
                
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    st.error(f"Failed to fetch client data after {self.retry_attempts} attempts: {str(e)}")
                    return None
                st.warning(f"Attempt {attempt + 1} failed, retrying...")
        
        return None
    
    def validate_case_id(self, case_id: str) -> bool:
        """Validate case ID format"""
        if not case_id or not case_id.strip():
            return False
        
        # Add any specific validation rules for case IDs
        try:
            int(case_id)  # Assuming case IDs are numeric
            return True
        except ValueError:
            return False

def render_client_profile_tab():
    """Main function to render the client profile tab"""
    st.header("📋 Client Profile")

    # Get case_id from session state
    case_id = st.session_state.get('case_id', None)
    if not case_id:
        st.warning("Please enter a Case ID on the Home tab first.")
        return

    # Initialize API client and formatter
    api_client = ClientAPIClient()
    formatter = ClientDataFormatter()

    # Check if data needs to be re-fetched
    if case_id != st.session_state.get('client_profile_case_id'):
        with st.spinner("Fetching client data..."):
            raw_data = api_client.fetch_client_data(case_id)
            if raw_data:
                organized_data = formatter.organize_client_data(raw_data)
                st.session_state['client_profile_data'] = organized_data
                st.session_state['client_profile_case_id'] = case_id
                st.success("✅ Client data loaded successfully!")
            else:
                st.error("❌ Failed to load client data for the current Case ID.")
                # Clear old data if new fetch fails
                if 'client_profile_data' in st.session_state:
                    del st.session_state['client_profile_data']
                if 'client_profile_case_id' in st.session_state:
                    del st.session_state['client_profile_case_id']

    # Display client profile if data exists
    if 'client_profile_data' in st.session_state and st.session_state.get('client_profile_case_id') == case_id:
        display_client_profile(st.session_state['client_profile_data'])
    elif case_id:
        st.info("Data for the current Case ID could not be loaded.")

def display_client_profile(client_data: dict):
    """Display the complete client profile"""
    
    # Header Section
    display_client_header(client_data)
    
    st.divider()
    
    # Main Content Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "💰 Financial Profile", 
        "🏛️ Tax Information",
        "👥 Case Management", 
        "📋 Detailed Data"
    ])
    
    with tab1:
        display_overview_tab(client_data)
    
    with tab2:
        display_financial_tab(client_data)
    
    with tab3:
        display_tax_info_tab(client_data)
    
    with tab4:
        display_case_management_tab(client_data)
    
    with tab5:
        display_detailed_data_tab(client_data)

def display_client_header(client_data: dict):
    """Display header with key client information"""
    client_info = client_data['client_info']
    tax_info = client_data['tax_info']
    
    # Main header row
    col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
    
    with col1:
        st.title(f"👤 {client_info['full_name']}")
        st.caption(f"Case ID: {client_info['case_id']} | SSN: {client_info['ssn']}")
    
    with col2:
        st.metric(
            "Total Liability", 
            ClientDataFormatter.format_currency(tax_info['total_liability'])
        )
    
    with col3:
        years_count = len(tax_info['years_owed']) + len(tax_info['unfiled_years'])
        st.metric("Tax Years", str(years_count))
    
    with col4:
        # Status with color coding
        status = tax_info['status_name']
        if 'Pending' in status:
            st.warning(f"⏳ {status}")
        elif 'Active' in status or 'Preparation' in status:
            st.info(f"🔄 {status}")
        else:
            st.success(f"✅ {status}")

def display_overview_tab(client_data: dict):
    """Display overview information"""
    client_info = client_data['client_info']
    contact_info = client_data['contact_info']
    financial = client_data['financial_profile']
    tax_info = client_data['tax_info']
    
    # Three column layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📞 Contact Information")
        st.write(f"**Primary Phone:** {contact_info['primary_phone']}")
        st.write(f"**Home Phone:** {contact_info['home_phone']}")
        st.write(f"**Work Phone:** {contact_info['work_phone']}")
        st.write(f"**Email:** {contact_info['email']}")
        st.write(f"**SMS Permitted:** {'✅ Yes' if contact_info['sms_permitted'] else '❌ No'}")
        st.write(f"**Best Time to Call:** {contact_info['best_time_to_call']}")
        
        st.subheader("🏠 Address")
        address = contact_info['address']
        st.write(f"**Street:** {address['full_address']}")
        st.write(f"**City:** {address['city']}")
        st.write(f"**State:** {address['state']}")
        st.write(f"**ZIP:** {address['zip']}")
    
    with col2:
        st.subheader("👥 Personal Information")
        st.write(f"**Marital Status:** {client_info['marital_status']}")
        
        if client_info['business_name']:
            st.write(f"**Business Name:** {client_info['business_name']}")
            st.write(f"**Business Type:** {client_info['business_type']}")
        
        family = financial['family']
        if family['household_size']:
            st.write(f"**Household Size:** {family['household_size']}")
            st.write(f"**Members Under 65:** {family['members_under_65']}")
            st.write(f"**Members Over 65:** {family['members_over_65']}")
            st.write(f"**Vehicles:** {family['vehicle_count']}")
    
    with col3:
        st.subheader("💰 Financial Summary")
        income = financial['income']
        st.metric("Taxpayer Income", ClientDataFormatter.format_currency(income['taxpayer_net']))
        st.metric("Spouse Income", ClientDataFormatter.format_currency(income['spouse_net']))
        st.metric("Monthly Net", ClientDataFormatter.format_currency(income['monthly_net']))
        
        st.subheader("🏛️ Tax Summary")
        st.metric("Total Liability", ClientDataFormatter.format_currency(tax_info['total_liability']))
        
        if tax_info['years_owed']:
            st.write("**Years Owed:**")
            st.write(", ".join(tax_info['years_owed']))
        
        if tax_info['unfiled_years']:
            st.write("**Unfiled Years:**")
            st.write(", ".join(tax_info['unfiled_years']))

def display_financial_tab(client_data: dict):
    """Display detailed financial information"""
    financial = client_data['financial_profile']
    formatter = ClientDataFormatter()
    
    # Income Section
    st.subheader("💰 Income Analysis")
    income = financial['income']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Taxpayer Net", formatter.format_currency(income['taxpayer_net']))
    with col2:
        st.metric("Spouse Net", formatter.format_currency(income['spouse_net']))
    with col3:
        st.metric("Monthly Gross", formatter.format_currency(income['monthly_gross']))
    with col4:
        st.metric("Monthly Net", formatter.format_currency(income['monthly_net']))
    
    # Other Income Sources
    if any(income['other_sources'].values()):
        st.subheader("🔄 Other Income Sources")
        col1, col2 = st.columns(2)
        
        with col1:
            for source, amount in income['other_sources'].items():
                if amount > 0:
                    st.write(f"**{source.title()}:** {formatter.format_currency(amount)}")
    
    # Monthly Expenses
    st.subheader("📊 Monthly Expenses")
    expenses = financial['expenses']['monthly_expenses']
    
    col1, col2 = st.columns(2)
    with col1:
        for expense, amount in expenses.items():
            if amount > 0 and not expense.endswith('_desc'):
                desc = expenses.get(f"{expense}_desc", "")
                label = expense.replace('_', ' ').title()
                if desc:
                    label += f" ({desc})"
                st.write(f"**{label}:** {formatter.format_currency(amount)}")
    
    with col2:
        total_expenses = sum(v for k, v in expenses.items() if not k.endswith('_desc') and isinstance(v, (int, float)))
        st.metric("Total Monthly Expenses", formatter.format_currency(total_expenses))
        st.metric("IRS Allowable Total", formatter.format_currency(financial['expenses']['total_allowable']))
    
    # Assets Summary
    st.subheader("🏦 Assets Summary")
    assets = financial['assets']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cash on Hand", formatter.format_currency(assets['cash_on_hand']))
        st.metric("Retirement", formatter.format_currency(assets['retirement']))
        st.metric("Investments", formatter.format_currency(assets['investments']))
    
    with col2:
        st.metric("Real Estate (QS)", formatter.format_currency(assets['real_estate']['quick_sale']))
        st.metric("Life Insurance", formatter.format_currency(assets['life_insurance']))
        st.metric("Personal Effects", formatter.format_currency(assets['personal_effects']))
    
    with col3:
        total_vehicles = sum(assets['vehicles'].values())
        st.metric("Vehicles Total", formatter.format_currency(total_vehicles))
        st.metric("Other Assets", formatter.format_currency(assets['other_assets']))
        st.metric("Total Net Realizable", formatter.format_currency(assets['total_net_realizable']))

def display_tax_info_tab(client_data: dict):
    """Display tax-specific information"""
    tax_info = client_data['tax_info']
    formatter = ClientDataFormatter()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏛️ Tax Liability Overview")
        st.metric("Total Liability", formatter.format_currency(tax_info['total_liability']))
        st.write(f"**Tax Type:** {tax_info['tax_type']}")
        st.write(f"**Status ID:** {tax_info['status_id']}")
        
        if tax_info['years_owed']:
            st.write("**Years with Taxes Owed:**")
            for year in tax_info['years_owed']:
                st.write(f"• {year}")
    
    with col2:
        if tax_info['unfiled_years']:
            st.subheader("📋 Unfiled Years")
            for year in tax_info['unfiled_years']:
                st.warning(f"⚠️ {year} - Return Not Filed")
        else:
            st.success("✅ All required returns appear to be filed")
        
        st.subheader("📄 Current Status")
        st.info(tax_info['status_name'])

def display_case_management_tab(client_data: dict):
    """Display case management information"""
    case_mgmt = client_data['case_management']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 Team Assignments")
        team = case_mgmt['team']
        
        assignments = [
            ("Set Officer", team['set_officer']),
            ("Case Advocate", team['case_advocate']),
            ("Tax Preparer", team['tax_preparer']),
            ("TI Agent", team['ti_agent']),
            ("Offer Analyst", team['offer_analyst']),
            ("Team", team['team_name'])
        ]
        
        for role, person in assignments:
            if person:
                st.write(f"**{role}:** {person}")
    
    with col2:
        st.subheader("📅 Timeline")
        st.write(f"**Sale Date:** {case_mgmt['sale_date']}")
        st.write(f"**Created:** {case_mgmt['created_date']}")
        st.write(f"**Last Modified:** {case_mgmt['modified_date']}")
        st.write(f"**Days in Status:** {case_mgmt['days_in_status']}")
        st.write(f"**Source:** {case_mgmt['source_name']}")

def display_detailed_data_tab(client_data: dict):
    """Display detailed/raw data for advanced users"""
    st.subheader("🔍 Business Income & Expenses")
    
    business = client_data['financial_profile']['business']
    formatter = ClientDataFormatter()
    
    if any(business['income'].values()) or any(business['expenses'].values()):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Business Income**")
            for category, amount in business['income'].items():
                if amount > 0:
                    st.write(f"• {category.replace('_', ' ').title()}: {formatter.format_currency(amount)}")
        
        with col2:
            st.write("**Business Expenses**")
            for category, amount in business['expenses'].items():
                if amount > 0:
                    st.write(f"• {category.replace('_', ' ').title()}: {formatter.format_currency(amount)}")
    else:
        st.info("No business income or expenses reported")
    
    # Raw data viewer
    with st.expander("🔧 Raw API Data (For Debugging)"):
        st.json(client_data['raw_data'])

# Integration function for main app
def add_client_profile_to_main_app():
    """
    Add this function call to your main app.py navigation
    
    Example integration in app.py:
    
    if selected_tab == "Client Profile":
        from pages.client_profile import render_client_profile_tab
        render_client_profile_tab()
    """
    pass

# For testing purposes
if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Client Profile")
    render_client_profile_tab() 