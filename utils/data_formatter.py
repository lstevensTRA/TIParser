"""
Data formatting utilities for client profile
This is a NEW file - do not modify existing formatters
"""

from typing import Dict, Any
import re

class ClientDataFormatter:
    """Format and organize raw API data for display"""
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """Format phone number to (XXX) XXX-XXXX"""
        if not phone:
            return "N/A"
        
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return phone or "N/A"
    
    @staticmethod
    def format_ssn(ssn: str) -> str:
        """Format SSN to XXX-XX-XXXX"""
        if not ssn:
            return "N/A"
        
        digits = re.sub(r'\D', '', ssn)
        if len(digits) == 9:
            return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
        return ssn
    
    @staticmethod
    def format_currency(amount: Any) -> str:
        """Format amount as currency"""
        try:
            value = float(amount) if amount else 0
            return f"${value:,.2f}"
        except (ValueError, TypeError):
            return "$0.00"
    
    @staticmethod
    def format_address(raw_data: Dict) -> Dict[str, str]:
        """Format address components"""
        return {
            'street': raw_data.get('Address', ''),
            'apt': raw_data.get('AptNo', ''),
            'city': raw_data.get('City', ''),
            'state': raw_data.get('State', ''),
            'zip': raw_data.get('Zip', ''),
            'full_address': f"{raw_data.get('Address', '')} {raw_data.get('AptNo', '')}".strip()
        }
    
    @staticmethod
    def organize_client_data(raw_data: Dict) -> Dict:
        """
        Organize raw API data into structured format
        
        Returns organized data with sections:
        - client_info
        - contact_info  
        - financial_profile
        - tax_info
        - case_management
        """
        formatter = ClientDataFormatter()
        misc_data = raw_data.get('MiscXML', {})
        
        return {
            'client_info': {
                'case_id': raw_data.get('CaseID'),
                'full_name': f"{raw_data.get('FirstName', '')} {raw_data.get('MiddleName', '')} {raw_data.get('LastName', '')}".strip(),
                'first_name': raw_data.get('FirstName', ''),
                'middle_name': raw_data.get('MiddleName', ''),
                'last_name': raw_data.get('LastName', ''),
                'ssn': formatter.format_ssn(raw_data.get('SSN')),
                'ein': raw_data.get('EIN', ''),
                'marital_status': raw_data.get('MartialStatus', 'N/A'),
                'business_name': raw_data.get('BusinessName', ''),
                'business_type': raw_data.get('BusinessType', ''),
                'business_address': raw_data.get('BusinessAddress', '')
            },
            'contact_info': {
                'primary_phone': formatter.format_phone(raw_data.get('CellPhone')),
                'home_phone': formatter.format_phone(raw_data.get('HomePhone')),
                'work_phone': formatter.format_phone(raw_data.get('WorkPhone')),
                'email': raw_data.get('Email', 'N/A'),
                'address': formatter.format_address(raw_data),
                'sms_permitted': raw_data.get('SMSPermitted', False),
                'best_time_to_call': raw_data.get('BestTimeToCall', 'N/A')
            },
            'tax_info': {
                'total_liability': float(raw_data.get('TaxLiability', 0)),
                'years_owed': [year.strip() for year in raw_data.get('OweTaxestoFederal', '').split(',') if year.strip()],
                'unfiled_years': [year.strip() for year in raw_data.get('UnfiledTaxestoFederal', '').split(',') if year.strip()],
                'status_id': raw_data.get('StatusID'),
                'status_name': raw_data.get('StatusName', 'Unknown'),
                'tax_type': raw_data.get('TAX_RELIEF_TAX_TYPE', 'PERSONAL')
            },
            'financial_profile': formatter._organize_financial_data(misc_data, raw_data),
            'case_management': {
                'sale_date': raw_data.get('SaleDate'),
                'created_date': raw_data.get('CreatedDate'),
                'modified_date': raw_data.get('ModifiedDate'),
                'days_in_status': raw_data.get('DaysInStatus', 0),
                'source_name': raw_data.get('SourceName', 'N/A'),
                'team': {
                    'set_officer': raw_data.get('SetOfficer'),
                    'case_advocate': raw_data.get('CaseAdvocate'),
                    'tax_pro': raw_data.get('TaxPro'),
                    'tax_preparer': raw_data.get('TaxPreparer'),
                    'ti_agent': raw_data.get('TIAgent'),
                    'offer_analyst': raw_data.get('OfferAnalyst'),
                    'team_name': raw_data.get('TeamName', '').strip()
                }
            },
            'raw_data': raw_data  # Keep for debugging/reference
        }
    
    def _organize_financial_data(self, misc_data: Dict, raw_data: Dict) -> Dict:
        """Organize financial data from MiscXML and other fields"""
        return {
            'income': {
                'taxpayer_net': float(raw_data.get('ClientDetailNetIncom', 0)),
                'taxpayer_gross': float(raw_data.get('ClientDetailGrossIncom', 0)),
                'spouse_net': float(raw_data.get('SpouseDetailNetIncom', 0)),
                'spouse_gross': float(raw_data.get('SpouseDetailGrossIncom', 0)),
                'monthly_gross': float(misc_data.get('IncomeGrossM', 0)),
                'monthly_net': float(misc_data.get('Income_Net', 0)),
                'other_sources': {
                    'business': float(misc_data.get('Income_Business', 0)),
                    'pension': float(misc_data.get('Income_Pension', 0)),
                    'rental': float(misc_data.get('Income_RentalGross', 0)),
                    'interest': float(misc_data.get('Income_Interest', 0)),
                    'alimony': float(misc_data.get('Income_Alimony', 0)),
                    'child_support': float(misc_data.get('Income_ChildSupport', 0)),
                    'distributions': float(misc_data.get('Income_Distributions', 0))
                }
            },
            'expenses': self._organize_expenses(misc_data),
            'assets': self._organize_assets(misc_data),
            'business': self._organize_business_data(misc_data),
            'family': {
                'household_size': int(misc_data.get('ClientDetailHousehold', 0)),
                'members_under_65': int(misc_data.get('FamilyMembersUnder65', 0)),
                'members_over_65': int(misc_data.get('FamilyMembersOver65', 0)),
                'dependents': misc_data.get('NumberOfDependents', ''),
                'vehicle_count': int(misc_data.get('VehicleCount', 0))
            }
        }
    
    def _organize_expenses(self, misc_data: Dict) -> Dict:
        """Organize expense data"""
        return {
            'monthly_expenses': {
                'housekeeping': float(misc_data.get('Expense_HouseKeeping', 0)),
                'apparel': float(misc_data.get('Expense_Apparel', 0)),
                'personal_care': float(misc_data.get('Expense_PersonalCare', 0)),
                'food_misc': float(misc_data.get('Expense_FoodMisc', 0)),
                'transportation': float(misc_data.get('Expense_PublicTransportation', 0)),
                'prescription': float(misc_data.get('Expense_Prescription', 0)),
                'copay': float(misc_data.get('Expense_Copay', 0)),
                'taxes': float(misc_data.get('Expense_Taxes', 0)),
                'other_1': float(misc_data.get('Expense_Other1', 0)),
                'other_1_desc': misc_data.get('Expense_Other1S', ''),
                'other_2': float(misc_data.get('Expense_Other2', 0)),
                'other_2_desc': misc_data.get('Expense_Other2S', ''),
                'other_3': float(misc_data.get('Expense_Other3', 0)),
                'other_3_desc': misc_data.get('Expense_Other3S', '')
            },
            'total_allowable': float(misc_data.get('ExpenseTotalAllowable', 0))
        }
    
    def _organize_assets(self, misc_data: Dict) -> Dict:
        """Organize asset data"""
        return {
            'cash_on_hand': float(misc_data.get('CashOnHand', 0)),
            'total_net_realizable': float(misc_data.get('TotalNetRealizableValue', 0)),
            'retirement': float(misc_data.get('EE_Asset_Retirement', 0)),
            'real_estate': {
                'quick_sale': float(misc_data.get('EE_Asset_QSRealEstate', 0))
            },
            'vehicles': {
                'vehicle_1_qs': float(misc_data.get('EE_Asset_QSVehicle1', 0)),
                'vehicle_2_qs': float(misc_data.get('EE_Asset_QSVehicle2', 0)),
                'vehicle_3_qs': float(misc_data.get('EE_Asset_QSVehicle3', 0)),
                'vehicle_4_qs': float(misc_data.get('EE_Asset_QSVehicle4', 0))
            },
            'investments': float(misc_data.get('EE_Asset_QSInvestments', 0)),
            'life_insurance': float(misc_data.get('EE_Asset_QSLifeInsurance', 0)),
            'personal_effects': float(misc_data.get('EE_Asset_QSEffects', 0)),
            'other_assets': float(misc_data.get('EE_Asset_QSOther', 0)),
            'business_assets': {
                'cash': float(misc_data.get('EE_Asset_BizCash', 0)),
                'bank_accounts': float(misc_data.get('EE_Asset_BizBankAccounts', 0)),
                'receivables': float(misc_data.get('EE_Asset_BizReceivables', 0)),
                'properties': float(misc_data.get('EE_Asset_BizProperties', 0)),
                'tools': float(misc_data.get('EE_Asset_BizTools', 0)),
                'other': float(misc_data.get('EE_Asset_BizOther', 0))
            }
        }
    
    def _organize_business_data(self, misc_data: Dict) -> Dict:
        """Organize business income and expense data"""
        return {
            'income': {
                'gross_receipts': float(misc_data.get('BizIncome_GrossReceipts', 0)),
                'gross_rental': float(misc_data.get('BizIncome_GrossRental', 0)),
                'interest': float(misc_data.get('BizIncome_Interest', 0)),
                'dividends': float(misc_data.get('BizIncome_Dividends', 0)),
                'cash': float(misc_data.get('BizIncome_Cash', 0)),
                'total': float(misc_data.get('BizIncome_Total', 0))
            },
            'expenses': {
                'materials': float(misc_data.get('BizExpense_Materials', 0)),
                'inventory': float(misc_data.get('BizExpense_Inventory', 0)),
                'wages': float(misc_data.get('BizExpense_Wages', 0)),
                'rent': float(misc_data.get('BizExpense_Rent', 0)),
                'supplies': float(misc_data.get('BizExpense_Supplies', 0)),
                'vehicle_gas': float(misc_data.get('BizExpense_VehicleGas', 0)),
                'vehicle_repairs': float(misc_data.get('BizExpense_VehicleRepairs', 0)),
                'insurance': float(misc_data.get('BizExpense_Insurance', 0)),
                'taxes': float(misc_data.get('BizExpense_Taxes', 0)),
                'utilities': float(misc_data.get('BizExpense_Utilities', 0)),
                'total': float(misc_data.get('BizExpense_Total', 0))
            }
        } 