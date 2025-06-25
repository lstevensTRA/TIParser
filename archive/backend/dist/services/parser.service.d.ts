import { ParserResponse, FileUpload } from '../types/parser.types';
export declare class ParserService {
    /**
     * Parse WI (Wage & Income) documents
     */
    static parseWIDocument(file: FileUpload): Promise<ParserResponse>;
    /**
     * Extract form data from text (migrated from Python extract_form_data)
     */
    private static extractFormData;
    /**
     * Extract owner designation from filename (migrated from TPSParser)
     */
    private static extractOwnerFromFilename;
    /**
     * Extract full form snippet for debugging
     */
    private static extractFullFormSnippet;
    /**
     * Get transaction alerts (migrated from get_transaction_alerts)
     */
    static getTransactionAlerts(transactions: any[]): string[];
}
//# sourceMappingURL=parser.service.d.ts.map