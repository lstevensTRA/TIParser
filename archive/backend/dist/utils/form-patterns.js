"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.formPatterns = void 0;
exports.toFloat = toFloat;
// Migrated from full_form_patterns.py
exports.formPatterns = {
    // 1099-MISC Form
    '1099-MISC': {
        pattern: /Form 1099-MISC/,
        category: 'SE', // Self-Employment
        fields: {
            // Income Fields
            'Non-Employee Compensation': /Non[- ]?Employee[- ]?Compensation[:\s]*\$?([\d,.]+)/,
            'Medical Payments': /Medical[- ]?Payments[:\s]*\$?([\d,.]+)/,
            'Fishing Income': /Fishing[- ]?Income[:\s]*\$?([\d,.]+)/,
            'Rents': /Rents[:\s]*\$?([\d,.]+)/,
            'Royalties': /Royalties[:\s]*\$?([\d,.]+)/,
            'Attorney Fees': /Attorney[- ]?Fees[:\s]*\$?([\d,.]+)/,
            'Other Income': /Other[- ]?Income[:\s]*\$?([\d,.]+)/,
            'Substitute for Dividends': /Substitute[- ]?Payments[- ]?for[- ]?Dividends[:\s]*\$?([\d,.]+)/,
            'Excess Golden Parachute': /Excess[- ]?Golden[- ]?Parachute[:\s]*\$?([\d,.]+)/,
            'Crop Insurance': /Crop[- ]?Insurance[:\s]*\$?([\d,.]+)/,
            'Foreign Tax Paid': /Foreign[- ]?Tax[- ]?Paid[:\s]*\$?([\d,.]+)/,
            'Section 409A Deferrals': /Section[- ]?409A[- ]?Deferrals[:\s]*\$?([\d,.]+)/,
            'Section 409A Income': /Section[- ]?409A[- ]?Income[:\s]*\$?([\d,.]+)/,
            'Direct Sales Indicator': /Direct[- ]?Sales[- ]?Indicator[:\s]*([A-Za-z ]+)/,
            'FATCA Filing Requirement': /FATCA[- ]?Filing[- ]?Requirement[:\s]*([A-Za-z ]+)/,
            'Second Notice Indicator': /Second[- ]?Notice[- ]?Indicator[:\s]*([A-Za-z ]+)/,
            // Withholdings
            'Federal Withholding': /Federal[\s,]*income[\s,]*tax[\s,]*withheld[:\s]*\$?([\d,.]+)/,
            'Tax Withheld': /Tax[- ]?Withheld[:\s]*\$?([\d,.]+)/
        },
        identifiers: {
            'FIN': /Payer's Federal Identification Number \(FIN\):\s*([\d\-]+)/,
            'Payer': /Payer:\s*([A-Z0-9 &.,\-]+)/
        },
        calculation: {
            Income: (fields) => {
                return (parseFloat(fields['Non-Employee Compensation'] || '0') +
                    parseFloat(fields['Medical Payments'] || '0') +
                    parseFloat(fields['Fishing Income'] || '0') +
                    parseFloat(fields['Rents'] || '0') +
                    parseFloat(fields['Royalties'] || '0') +
                    parseFloat(fields['Attorney Fees'] || '0') +
                    parseFloat(fields['Other Income'] || '0') +
                    parseFloat(fields['Substitute for Dividends'] || '0'));
            },
            Withholding: (fields) => {
                return (parseFloat(fields['Federal Withholding'] || '0') +
                    parseFloat(fields['Tax Withheld'] || '0'));
            }
        }
    },
    // 1099-NEC Form
    '1099-NEC': {
        pattern: /Form 1099-NEC/,
        category: 'SE', // Self-Employment
        fields: {
            // Income Fields
            'Non-Employee Compensation': /Non[- ]?Employee[- ]?Compensation[:\s]*\$?([\d,.]+)/,
            // Withholdings
            'Federal Withholding': /Federal[\s,]*income[\s,]*tax[\s,]*withheld[:\s]*\$?([\d,.]+)/
        },
        identifiers: {
            'FIN': /Payer's Federal Identification Number \(FIN\):\s*([\d\-]+)/,
            'Payer': /Payer:\s*([A-Z0-9 &.,\-]+)/
        },
        calculation: {
            Income: (fields) => {
                return parseFloat(fields['Non-Employee Compensation'] || '0');
            },
            Withholding: (fields) => {
                return parseFloat(fields['Federal Withholding'] || '0');
            }
        }
    },
    // 1099-K Form
    '1099-K': {
        pattern: /Form 1099-K/,
        category: 'SE', // Self-Employment
        fields: {
            // Income Fields
            'Gross Amount': /Gross amount of payment card\/third party transactions[:\s]*\$([\d,.]+)/,
            // Withholdings
            'Federal Withholding': /Federal income tax withheld[:\s]*\$([\d,.]+)/
        },
        identifiers: {
            'FIN': /Payer's Federal Identification Number \(FIN\):\s*([\d\-]+)/,
            'Payer': /Payer:\s*([A-Z0-9 &.,\-]+)/
        },
        calculation: {
            Income: (fields) => {
                return parseFloat(fields['Gross Amount'] || '0');
            },
            Withholding: (fields) => {
                return parseFloat(fields['Federal Withholding'] || '0');
            }
        }
    },
    // 1099-PATR Form
    '1099-PATR': {
        pattern: /Form 1099-PATR/,
        category: 'SE', // Self-Employment
        fields: {
            // Income Fields
            'Patronage Dividends': /Patronage dividends[:\s]*\$([\d,.]+)/,
            'Non-Patronage Distribution': /Non-patronage distribution[:\s]*\$([\d,.]+)/,
            'Retained Allocations': /Retained allocations[:\s]*\$([\d,.]+)/,
            'Redemption Amount': /Redemption amount[:\s]*\$([\d,.]+)/,
            // Withholdings
            'Federal Withholding': /Tax withheld[:\s]*\$([\d,.]+)/
        },
        identifiers: {
            'FIN': /Payer's Federal Identification Number \(FIN\):\s*([\d\-]+)/,
            'Payer': /Payer:\s*([A-Z0-9 &.,\-]+)/
        },
        calculation: {
            Income: (fields) => {
                return (parseFloat(fields['Patronage Dividends'] || '0') +
                    parseFloat(fields['Non-Patronage Distribution'] || '0') +
                    parseFloat(fields['Retained Allocations'] || '0') +
                    parseFloat(fields['Redemption Amount'] || '0'));
            },
            Withholding: (fields) => {
                return parseFloat(fields['Federal Withholding'] || '0');
            }
        }
    },
    // 1042-S Form
    '1042-S': {
        pattern: /Form 1042-S/,
        category: 'Neither', // Not SE or Non-SE
        fields: {
            // Income Fields
            'Gross Income': /Gross income[:\s]*\$([\d,.]+)/,
            // Withholdings
            'Federal Withholding': /U\.S\. federal tax withheld[:\s]*\$([\d,.]+)/
        },
        calculation: {
            Income: (fields) => {
                return parseFloat(fields['Gross Income'] || '0');
            },
            Withholding: (fields) => {
                return parseFloat(fields['Federal Withholding'] || '0');
            }
        }
    },
    // K-1 (Form 1065)
    'K-1 (Form 1065)': {
        pattern: /Schedule K-1 \(Form 1065\)/,
        category: 'SE', // Self-Employment
        fields: {
            // Income Fields
            'Royalties': /Royalties[:\s]*\$([\d,.]+)/,
            'Ordinary Income K-1': /Ordinary income[:\s]*\$([\d,.]+)/,
            'Real Estate': /Real estate[:\s]*\$([\d,.]+)/,
            'Other Rental': /Other rental[:\s]*\$([\d,.]+)/,
            'Guaranteed Payments': /Guaranteed payments[:\s]*\$([\d,.]+)/,
            // Non-Income Fields
            'Section 179 Expenses': /Section 179 expenses[:\s]*\$([\d,.]+)/,
            'Nonrecourse Beginning': /Nonrecourse beginning[:\s]*\$([\d,.]+)/,
            'Qualified Nonrecourse Beginning': /Qualified nonrecourse beginning[:\s]*\$([\d,.]+)/
        },
        calculation: {
            Income: (fields) => {
                return (parseFloat(fields['Royalties'] || '0') +
                    parseFloat(fields['Ordinary Income K-1'] || '0') +
                    parseFloat(fields['Real Estate'] || '0') +
                    parseFloat(fields['Other Rental'] || '0') +
                    parseFloat(fields['Guaranteed Payments'] || '0'));
            },
            Withholding: (fields) => 0 // No withholdings specified
        }
    },
    // K-1 (Form 1041)
    'K-1 (Form 1041)': {
        pattern: /Schedule K-1 \(Form 1041\)/,
        category: 'Neither', // Not SE or Non-SE
        fields: {
            // Income Fields
            'Net Rental Real Estate Income': /Net rental real estate income[:\s]*\$([\d,.]+)/,
            'Other Rental Income': /Other rental income[:\s]*\$([\d,.]+)/,
            // Withholdings
            'Federal Withholding': null // Explicitly stated as "None"
        },
        calculation: {
            Income: (fields) => {
                return (parseFloat(fields['Net Rental Real Estate Income'] || '0') +
                    parseFloat(fields['Other Rental Income'] || '0'));
            },
            Withholding: (fields) => 0 // No withholdings specified
        }
    },
    // W-2 Form
    'W-2': {
        pattern: /Form W-2/,
        category: 'Non-SE',
        fields: {
            'Wages': /Wages, tips, other compensation[:\s]*\$([\d,.]+)/,
            'Federal Withholding': /Federal income tax withheld[:\s]*\$([\d,.]+)/,
            'Social Security Wages': /Social security wages[:\s]*\$([\d,.]+)/,
            'Social Security Tax': /Social security tax withheld[:\s]*\$([\d,.]+)/,
            'Medicare Wages': /Medicare wages and tips[:\s]*\$([\d,.]+)/,
            'Medicare Tax': /Medicare tax withheld[:\s]*\$([\d,.]+)/
        },
        identifiers: {
            'Employer': /Employer's name, address, and ZIP code[:\s]*([A-Z0-9 &.,\-]+)/,
            'EIN': /Employer identification number \(EIN\)[:\s]*([\d\-]+)/
        },
        calculation: {
            Income: (fields) => {
                return parseFloat(fields['Wages'] || '0');
            },
            Withholding: (fields) => {
                return parseFloat(fields['Federal Withholding'] || '0');
            }
        }
    },
    // 1099-INT Form
    '1099-INT': {
        pattern: /Form 1099-INT/,
        category: 'Non-SE',
        fields: {
            'Interest Income': /Interest income[:\s]*\$([\d,.]+)/,
            'Federal Withholding': /Federal income tax withheld[:\s]*\$([\d,.]+)/
        },
        identifiers: {
            'FIN': /Payer's Federal Identification Number \(FIN\):\s*([\d\-]+)/,
            'Payer': /Payer:\s*([A-Z0-9 &.,\-]+)/
        },
        calculation: {
            Income: (fields) => {
                return parseFloat(fields['Interest Income'] || '0');
            },
            Withholding: (fields) => {
                return parseFloat(fields['Federal Withholding'] || '0');
            }
        }
    },
    // 1099-DIV Form
    '1099-DIV': {
        pattern: /Form 1099-DIV/,
        category: 'Non-SE',
        fields: {
            'Total Ordinary Dividends': /Total ordinary dividends[:\s]*\$([\d,.]+)/,
            'Qualified Dividends': /Qualified dividends[:\s]*\$([\d,.]+)/,
            'Federal Withholding': /Federal income tax withheld[:\s]*\$([\d,.]+)/
        },
        identifiers: {
            'FIN': /Payer's Federal Identification Number \(FIN\):\s*([\d\-]+)/,
            'Payer': /Payer:\s*([A-Z0-9 &.,\-]+)/
        },
        calculation: {
            Income: (fields) => {
                return parseFloat(fields['Total Ordinary Dividends'] || '0');
            },
            Withholding: (fields) => {
                return parseFloat(fields['Federal Withholding'] || '0');
            }
        }
    }
};
// Helper function to convert string to float
function toFloat(val) {
    if (typeof val === 'number')
        return val;
    try {
        return parseFloat(val.replace(/,/g, ''));
    }
    catch {
        return 0.0;
    }
}
//# sourceMappingURL=form-patterns.js.map