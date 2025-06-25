"""
Taxpayer/Spouse parsing logic for WI transcripts
This is a NEW file - do not modify existing transcript parsers
"""

import re
from typing import Dict, List, Optional

class TPSParser:
    """Handle Taxpayer (TP) and Spouse (S) designation parsing from filenames"""
    
    @staticmethod
    def extract_owner_from_filename(filename: str) -> str:
        """
        Extract TP/S designation from filename
        
        Args:
            filename: The uploaded file name (e.g., "WI 19 TP", "WI S 19", "WI 19")
            
        Returns:
            "TP", "S", or "TP" (default)
            
        Examples:
            "WI 19 TP" → "TP"
            "WI S 19" → "S"  
            "WI 19" → "TP" (default)
            "WI 19 COMBINED" → None (joint)
        """
        if not filename:
            return "TP"  # Default to taxpayer
        
        # Clean filename and convert to uppercase for matching
        clean_filename = filename.upper().strip()
        
        # Check for spouse designation first (more specific)
        if re.search(r'\bS\b', clean_filename) or re.search(r'\bSPOUSE\b', clean_filename):
            return "S"
        
        # Check for taxpayer designation
        if re.search(r'\bTP\b', clean_filename):
            return "TP"
        
        # Check for combined/joint designation
        if re.search(r'\b(COMBINED|JOINT)\b', clean_filename):
            return None  # Indicates joint filing data
        
        # Default to taxpayer if no designation found
        return "TP"
    
    @staticmethod
    def enhance_wi_data_with_owner(wi_data: Dict, filename: str) -> Dict:
        """
        Add Owner field to existing WI transcript data based on filename
        
        Args:
            wi_data: Existing WI transcript data structure
            filename: Source filename for owner determination
            
        Returns:
            Enhanced WI data with Owner fields added
        """
        if not wi_data:
            return wi_data
        
        owner = TPSParser.extract_owner_from_filename(filename)
        
        # Add owner designation to all forms in this file
        enhanced_data = {}
        for year, forms in wi_data.items():
            enhanced_data[year] = []
            for form in forms:
                enhanced_form = form.copy()
                enhanced_form['Owner'] = owner
                enhanced_data[year].append(enhanced_form)
        
        return enhanced_data
    
    @staticmethod
    def aggregate_income_by_owner(wi_data: Dict) -> Dict:
        """
        Calculate income totals broken down by owner (TP/S/Joint)
        
        Args:
            wi_data: WI transcript data with Owner fields
            
        Returns:
            Dictionary with totals by owner type
        """
        totals = {}
        
        for year, forms in wi_data.items():
            year_totals = {
                'taxpayer': {'income': 0, 'withholding': 0, 'se_income': 0, 'non_se_income': 0},
                'spouse': {'income': 0, 'withholding': 0, 'se_income': 0, 'non_se_income': 0},
                'joint': {'income': 0, 'withholding': 0, 'se_income': 0, 'non_se_income': 0},
                'combined': {'income': 0, 'withholding': 0, 'se_income': 0, 'non_se_income': 0}
            }
            
            for form in forms:
                owner = form.get('Owner')
                income = float(form.get('Income', 0))
                withholding = float(form.get('Withholding', 0))
                category = form.get('Category', '')
                
                # Determine which bucket to add to
                if owner == 'TP':
                    bucket = 'taxpayer'
                elif owner == 'S':
                    bucket = 'spouse'
                elif owner is None:
                    bucket = 'joint'
                else:
                    bucket = 'taxpayer'  # Default fallback
                
                # Add to appropriate bucket
                year_totals[bucket]['income'] += income
                year_totals[bucket]['withholding'] += withholding
                
                # Categorize income type
                if category == 'SE':
                    year_totals[bucket]['se_income'] += income
                elif category == 'Non-SE':
                    year_totals[bucket]['non_se_income'] += income
                
                # Always add to combined totals
                year_totals['combined']['income'] += income
                year_totals['combined']['withholding'] += withholding
                if category == 'SE':
                    year_totals['combined']['se_income'] += income
                elif category == 'Non-SE':
                    year_totals['combined']['non_se_income'] += income
            
            totals[year] = year_totals
        
        return totals
    
    @staticmethod
    def detect_missing_spouse_data(totals: Dict, filing_status: str) -> List[str]:
        """
        Identify years where spouse data might be missing
        
        Args:
            totals: Income totals by owner from aggregate_income_by_owner
            filing_status: Client's filing status
            
        Returns:
            List of recommendations for missing data
        """
        recommendations = []
        
        if filing_status not in ['Married Filing Jointly', 'Married Filing Separately']:
            return recommendations  # Not married, no spouse data expected
        
        for year, year_totals in totals.items():
            taxpayer_income = year_totals['taxpayer']['income']
            spouse_income = year_totals['spouse']['income']
            
            # Check for potential missing spouse data
            if taxpayer_income > 0 and spouse_income == 0:
                recommendations.append(
                    f"Year {year}: Consider checking for spouse income - only taxpayer income found"
                )
            elif taxpayer_income == 0 and spouse_income > 0:
                recommendations.append(
                    f"Year {year}: Consider checking for taxpayer income - only spouse income found"
                )
            elif taxpayer_income == 0 and spouse_income == 0:
                recommendations.append(
                    f"Year {year}: No income found for either spouse - verify transcript completeness"
                )
        
        return recommendations
    
    @staticmethod
    def generate_tps_analysis_summary(wi_data: Dict, filing_status: str) -> Dict:
        """
        Generate comprehensive TP/S analysis summary
        
        Args:
            wi_data: WI transcript data with Owner fields
            filing_status: Client's filing status
            
        Returns:
            Complete analysis with recommendations
        """
        totals = TPSParser.aggregate_income_by_owner(wi_data)
        missing_data_recs = TPSParser.detect_missing_spouse_data(totals, filing_status)
        
        return {
            'totals_by_year': totals,
            'filing_status': filing_status,
            'missing_data_recommendations': missing_data_recs,
            'summary_statistics': TPSParser._calculate_summary_stats(totals),
            'analysis_metadata': {
                'years_analyzed': list(totals.keys()),
                'has_taxpayer_data': any(t['taxpayer']['income'] > 0 for t in totals.values()),
                'has_spouse_data': any(t['spouse']['income'] > 0 for t in totals.values()),
                'has_joint_data': any(t['joint']['income'] > 0 for t in totals.values())
            }
        }
    
    @staticmethod
    def _calculate_summary_stats(totals: Dict) -> Dict:
        """Calculate summary statistics across all years"""
        all_years_tp_income = sum(t['taxpayer']['income'] for t in totals.values())
        all_years_sp_income = sum(t['spouse']['income'] for t in totals.values())
        all_years_joint_income = sum(t['joint']['income'] for t in totals.values())
        all_years_combined_income = sum(t['combined']['income'] for t in totals.values())
        
        return {
            'total_taxpayer_income_all_years': all_years_tp_income,
            'total_spouse_income_all_years': all_years_sp_income,
            'total_joint_income_all_years': all_years_joint_income,
            'total_combined_income_all_years': all_years_combined_income,
            'years_with_data': len(totals),
            'average_annual_combined_income': all_years_combined_income / len(totals) if totals else 0
        } 