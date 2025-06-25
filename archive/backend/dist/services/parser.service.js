"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ParserService = void 0;
const pdf_utils_1 = require("../utils/pdf.utils");
const form_patterns_1 = require("../utils/form-patterns");
class ParserService {
    /**
     * Parse WI (Wage & Income) documents
     */
    static async parseWIDocument(file) {
        const startTime = Date.now();
        try {
            console.log(`📄 Parsing WI document: ${file.originalname}`);
            // Extract text from PDF
            const text = await pdf_utils_1.PDFUtils.extractTextFromPDF(file.buffer);
            if (!text || text.length < 100) {
                return {
                    success: false,
                    message: 'Unable to extract readable text from PDF',
                    filename: file.originalname
                };
            }
            // Extract form data
            const wiData = this.extractFormData(text, file.originalname);
            const processingTime = Date.now() - startTime;
            return {
                success: true,
                data: wiData,
                message: 'WI document parsed successfully',
                filename: file.originalname,
                processingTime
            };
        }
        catch (error) {
            console.error('❌ WI parsing error:', error);
            return {
                success: false,
                message: `WI parsing failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
                filename: file.originalname
            };
        }
    }
    /**
     * Extract form data from text (migrated from Python extract_form_data)
     */
    static extractFormData(text, filename, taxYear, filingStatus = 'Single', combinedIncome = 0) {
        const wiData = {};
        const outputBuffer = [];
        const writeOut = (msg) => {
            outputBuffer.push(msg);
            console.log(msg);
        };
        writeOut(`\n=== Processing ${filename || 'document'} ===`);
        // Extract header info
        const headerInfo = pdf_utils_1.PDFUtils.extractHeaderInfo(text);
        const detectedTaxYear = taxYear || headerInfo.taxYear;
        const detectedFilingStatus = headerInfo.filingStatus || filingStatus;
        writeOut(`Detected Tax Year: ${detectedTaxYear || 'Unknown'}`);
        writeOut(`Detected Filing Status: ${detectedFilingStatus}`);
        // Process each form pattern
        for (const [formName, formConfig] of Object.entries(form_patterns_1.formPatterns)) {
            if (formConfig.pattern.test(text)) {
                writeOut(`\n--- Found ${formName} ---`);
                const formData = {
                    formName,
                    category: formConfig.category
                };
                // Extract field values
                for (const [fieldName, pattern] of Object.entries(formConfig.fields)) {
                    if (pattern) {
                        const match = text.match(pattern);
                        if (match && match[1]) {
                            const value = (0, form_patterns_1.toFloat)(match[1]);
                            formData[fieldName] = value;
                            writeOut(`${fieldName}: $${value.toFixed(2)}`);
                        }
                    }
                }
                // Extract identifiers (if they exist)
                if ('identifiers' in formConfig && formConfig.identifiers) {
                    for (const [identifierName, pattern] of Object.entries(formConfig.identifiers)) {
                        if (pattern) {
                            const match = text.match(pattern);
                            if (match && match[1]) {
                                formData[identifierName] = match[1].trim();
                                writeOut(`${identifierName}: ${formData[identifierName]}`);
                            }
                        }
                    }
                }
                // Calculate totals using the form's calculation functions
                if (formConfig.calculation) {
                    formData.Income = formConfig.calculation.Income(formData);
                    formData.Withholding = formConfig.calculation.Withholding(formData);
                    writeOut(`Total Income: $${formData.Income.toFixed(2)}`);
                    writeOut(`Total Withholding: $${formData.Withholding.toFixed(2)}`);
                }
                // Add owner designation based on filename
                if (filename) {
                    formData.Owner = this.extractOwnerFromFilename(filename);
                }
                // Group by tax year
                const year = detectedTaxYear || 'Unknown';
                if (!wiData[year]) {
                    wiData[year] = [];
                }
                wiData[year].push(formData);
            }
        }
        // Generate summary
        for (const [year, forms] of Object.entries(wiData)) {
            const totalIncome = forms.reduce((sum, form) => sum + (form.Income || 0), 0);
            const totalWithholding = forms.reduce((sum, form) => sum + (form.Withholding || 0), 0);
            writeOut(`\n=== ${year} Summary ===`);
            writeOut(`Total Forms: ${forms.length}`);
            writeOut(`Total Income: $${totalIncome.toFixed(2)}`);
            writeOut(`Total Withholding: $${totalWithholding.toFixed(2)}`);
        }
        return wiData;
    }
    /**
     * Extract owner designation from filename (migrated from TPSParser)
     */
    static extractOwnerFromFilename(filename) {
        if (!filename) {
            return 'TP'; // Default to taxpayer
        }
        // Clean filename and convert to uppercase for matching
        const cleanFilename = filename.toUpperCase().trim();
        // Check for spouse designation first (more specific)
        if (/\bS\b/.test(cleanFilename) || /\bSPOUSE\b/.test(cleanFilename)) {
            return 'S';
        }
        // Check for taxpayer designation
        if (/\bTP\b/.test(cleanFilename)) {
            return 'TP';
        }
        // Check for combined/joint designation
        if (/\b(COMBINED|JOINT)\b/.test(cleanFilename)) {
            return null; // Indicates joint filing data
        }
        // Default to taxpayer if no designation found
        return 'TP';
    }
    /**
     * Extract full form snippet for debugging
     */
    static extractFullFormSnippet(formName, text, startPos, filename) {
        const formPattern = form_patterns_1.formPatterns[formName];
        if (!formPattern)
            return '';
        const match = text.match(formPattern.pattern);
        if (!match)
            return '';
        const start = match.index || 0;
        const end = Math.min(start + 2000, text.length); // Get 2000 characters after form start
        return text.substring(start, end);
    }
    /**
     * Get transaction alerts (migrated from get_transaction_alerts)
     */
    static getTransactionAlerts(transactions) {
        const alerts = [];
        for (const transaction of transactions) {
            const code = transaction.code;
            const amount = Math.abs(transaction.amount);
            // Check for specific transaction codes
            if (code === '150' && amount > 10000) {
                alerts.push(`Large refund issued: $${amount.toFixed(2)} (Code: ${code})`);
            }
            if (code === '290' && amount > 5000) {
                alerts.push(`Large additional tax assessed: $${amount.toFixed(2)} (Code: ${code})`);
            }
            if (code === '971' && amount > 1000) {
                alerts.push(`Notice issued: $${amount.toFixed(2)} (Code: ${code})`);
            }
            // Check for unusual patterns
            if (amount > 50000) {
                alerts.push(`Unusually large transaction: $${amount.toFixed(2)} (Code: ${code})`);
            }
        }
        return alerts;
    }
}
exports.ParserService = ParserService;
//# sourceMappingURL=parser.service.js.map