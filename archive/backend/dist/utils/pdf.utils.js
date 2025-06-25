"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.PDFUtils = void 0;
// @ts-ignore
const pdf = require('pdf-parse');
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const child_process_1 = require("child_process");
class PDFUtils {
    /**
     * Extract text from PDF buffer
     */
    static async extractTextFromPDF(pdfBuffer) {
        try {
            console.log('📄 Extracting text from PDF...');
            // Try direct PDF parsing first
            const data = await pdf(pdfBuffer);
            let text = data.text;
            // Check if text is readable
            if (this.isTextReadable(text)) {
                console.log('✅ PDF text extraction successful');
                return text;
            }
            // If text is not readable, try OCR
            console.log('🔍 Text not readable, attempting OCR...');
            const ocrText = await this.extractTextWithOCR(pdfBuffer);
            if (this.isTextReadable(ocrText)) {
                console.log('✅ OCR text extraction successful');
                return ocrText;
            }
            console.log('⚠️ Both PDF parsing and OCR failed');
            return text || ocrText || '';
        }
        catch (error) {
            console.error('❌ PDF processing error:', error);
            throw new Error(`PDF processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    /**
     * Check if extracted text is readable
     */
    static isTextReadable(text) {
        if (!text || text.length < 100) {
            return false;
        }
        // Check for common IRS form patterns
        const formPatterns = [
            /Form\s+\d{4}/i,
            /Internal\s+Revenue\s+Service/i,
            /Tax\s+Year/i,
            /\$\d+\.?\d*/,
            /\d{2}\/\d{2}\/\d{4}/
        ];
        const matches = formPatterns.filter(pattern => pattern.test(text));
        return matches.length >= 2;
    }
    /**
     * Extract text using OCR (Tesseract)
     */
    static async extractTextWithOCR(pdfBuffer) {
        return new Promise((resolve, reject) => {
            // Convert PDF to images first
            const tempDir = path.join(process.cwd(), 'temp');
            if (!fs.existsSync(tempDir)) {
                fs.mkdirSync(tempDir, { recursive: true });
            }
            const tempPdfPath = path.join(tempDir, `temp_${Date.now()}.pdf`);
            fs.writeFileSync(tempPdfPath, pdfBuffer);
            // Use pdf2image to convert PDF to images
            const pdf2image = (0, child_process_1.spawn)('pdf2image', ['-png', tempPdfPath, path.join(tempDir, 'page')]);
            pdf2image.on('close', async (code) => {
                if (code !== 0) {
                    fs.unlinkSync(tempPdfPath);
                    reject(new Error('Failed to convert PDF to images'));
                    return;
                }
                try {
                    // Find generated image files
                    const files = fs.readdirSync(tempDir).filter(f => f.startsWith('page') && f.endsWith('.png'));
                    if (files.length === 0) {
                        fs.unlinkSync(tempPdfPath);
                        reject(new Error('No images generated from PDF'));
                        return;
                    }
                    // Extract text from each image using Tesseract
                    const ocrPromises = files.map(file => {
                        return new Promise((resolveOCR, rejectOCR) => {
                            const imagePath = path.join(tempDir, file);
                            const tesseract = (0, child_process_1.spawn)('tesseract', [imagePath, 'stdout']);
                            let output = '';
                            tesseract.stdout.on('data', (data) => {
                                output += data.toString();
                            });
                            tesseract.on('close', (code) => {
                                fs.unlinkSync(imagePath);
                                if (code === 0) {
                                    resolveOCR(output);
                                }
                                else {
                                    rejectOCR(new Error(`OCR failed for ${file}`));
                                }
                            });
                        });
                    });
                    const ocrResults = await Promise.all(ocrPromises);
                    const combinedText = ocrResults.join('\n');
                    // Clean up
                    fs.unlinkSync(tempPdfPath);
                    resolve(combinedText);
                }
                catch (error) {
                    fs.unlinkSync(tempPdfPath);
                    reject(error);
                }
            });
        });
    }
    /**
     * Extract header information from text
     */
    static extractHeaderInfo(text) {
        const taxYearMatch = text.match(/Tax\s+Year[:\s]*(\d{4})/i);
        const filingStatusMatch = text.match(/Filing\s+Status[:\s]*([A-Za-z\s]+)/i);
        return {
            taxYear: taxYearMatch ? taxYearMatch[1] : undefined,
            filingStatus: filingStatusMatch ? filingStatusMatch[1].trim() : undefined
        };
    }
}
exports.PDFUtils = PDFUtils;
//# sourceMappingURL=pdf.utils.js.map