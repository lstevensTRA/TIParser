export declare const formPatterns: {
    '1099-MISC': {
        pattern: RegExp;
        category: string;
        fields: {
            'Non-Employee Compensation': RegExp;
            'Medical Payments': RegExp;
            'Fishing Income': RegExp;
            Rents: RegExp;
            Royalties: RegExp;
            'Attorney Fees': RegExp;
            'Other Income': RegExp;
            'Substitute for Dividends': RegExp;
            'Excess Golden Parachute': RegExp;
            'Crop Insurance': RegExp;
            'Foreign Tax Paid': RegExp;
            'Section 409A Deferrals': RegExp;
            'Section 409A Income': RegExp;
            'Direct Sales Indicator': RegExp;
            'FATCA Filing Requirement': RegExp;
            'Second Notice Indicator': RegExp;
            'Federal Withholding': RegExp;
            'Tax Withheld': RegExp;
        };
        identifiers: {
            FIN: RegExp;
            Payer: RegExp;
        };
        calculation: {
            Income: (fields: any) => number;
            Withholding: (fields: any) => number;
        };
    };
    '1099-NEC': {
        pattern: RegExp;
        category: string;
        fields: {
            'Non-Employee Compensation': RegExp;
            'Federal Withholding': RegExp;
        };
        identifiers: {
            FIN: RegExp;
            Payer: RegExp;
        };
        calculation: {
            Income: (fields: any) => number;
            Withholding: (fields: any) => number;
        };
    };
    '1099-K': {
        pattern: RegExp;
        category: string;
        fields: {
            'Gross Amount': RegExp;
            'Federal Withholding': RegExp;
        };
        identifiers: {
            FIN: RegExp;
            Payer: RegExp;
        };
        calculation: {
            Income: (fields: any) => number;
            Withholding: (fields: any) => number;
        };
    };
    '1099-PATR': {
        pattern: RegExp;
        category: string;
        fields: {
            'Patronage Dividends': RegExp;
            'Non-Patronage Distribution': RegExp;
            'Retained Allocations': RegExp;
            'Redemption Amount': RegExp;
            'Federal Withholding': RegExp;
        };
        identifiers: {
            FIN: RegExp;
            Payer: RegExp;
        };
        calculation: {
            Income: (fields: any) => number;
            Withholding: (fields: any) => number;
        };
    };
    '1042-S': {
        pattern: RegExp;
        category: string;
        fields: {
            'Gross Income': RegExp;
            'Federal Withholding': RegExp;
        };
        calculation: {
            Income: (fields: any) => number;
            Withholding: (fields: any) => number;
        };
    };
    'K-1 (Form 1065)': {
        pattern: RegExp;
        category: string;
        fields: {
            Royalties: RegExp;
            'Ordinary Income K-1': RegExp;
            'Real Estate': RegExp;
            'Other Rental': RegExp;
            'Guaranteed Payments': RegExp;
            'Section 179 Expenses': RegExp;
            'Nonrecourse Beginning': RegExp;
            'Qualified Nonrecourse Beginning': RegExp;
        };
        calculation: {
            Income: (fields: any) => number;
            Withholding: (fields: any) => number;
        };
    };
    'K-1 (Form 1041)': {
        pattern: RegExp;
        category: string;
        fields: {
            'Net Rental Real Estate Income': RegExp;
            'Other Rental Income': RegExp;
            'Federal Withholding': null;
        };
        calculation: {
            Income: (fields: any) => number;
            Withholding: (fields: any) => number;
        };
    };
    'W-2': {
        pattern: RegExp;
        category: string;
        fields: {
            Wages: RegExp;
            'Federal Withholding': RegExp;
            'Social Security Wages': RegExp;
            'Social Security Tax': RegExp;
            'Medicare Wages': RegExp;
            'Medicare Tax': RegExp;
        };
        identifiers: {
            Employer: RegExp;
            EIN: RegExp;
        };
        calculation: {
            Income: (fields: any) => number;
            Withholding: (fields: any) => number;
        };
    };
    '1099-INT': {
        pattern: RegExp;
        category: string;
        fields: {
            'Interest Income': RegExp;
            'Federal Withholding': RegExp;
        };
        identifiers: {
            FIN: RegExp;
            Payer: RegExp;
        };
        calculation: {
            Income: (fields: any) => number;
            Withholding: (fields: any) => number;
        };
    };
    '1099-DIV': {
        pattern: RegExp;
        category: string;
        fields: {
            'Total Ordinary Dividends': RegExp;
            'Qualified Dividends': RegExp;
            'Federal Withholding': RegExp;
        };
        identifiers: {
            FIN: RegExp;
            Payer: RegExp;
        };
        calculation: {
            Income: (fields: any) => number;
            Withholding: (fields: any) => number;
        };
    };
};
export declare function toFloat(val: string | number): number;
//# sourceMappingURL=form-patterns.d.ts.map