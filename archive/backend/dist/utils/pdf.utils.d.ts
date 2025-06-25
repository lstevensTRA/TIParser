export declare class PDFUtils {
    /**
     * Extract text from PDF buffer
     */
    static extractTextFromPDF(pdfBuffer: Buffer): Promise<string>;
    /**
     * Check if extracted text is readable
     */
    private static isTextReadable;
    /**
     * Extract text using OCR (Tesseract)
     */
    private static extractTextWithOCR;
    /**
     * Extract header information from text
     */
    static extractHeaderInfo(text: string): {
        taxYear?: string;
        filingStatus?: string;
    };
}
//# sourceMappingURL=pdf.utils.d.ts.map