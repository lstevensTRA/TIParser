"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.parserRoutes = void 0;
const express_1 = require("express");
const multer_1 = __importDefault(require("multer"));
const parser_service_1 = require("../services/parser.service");
const router = (0, express_1.Router)();
exports.parserRoutes = router;
// Configure multer for file uploads
const upload = (0, multer_1.default)({
    storage: multer_1.default.memoryStorage(),
    limits: {
        fileSize: 50 * 1024 * 1024, // 50MB limit
    },
    fileFilter: (req, file, cb) => {
        // Accept PDF files only
        if (file.mimetype === 'application/pdf') {
            cb(null, true);
        }
        else {
            cb(new Error('Only PDF files are allowed'));
        }
    }
});
// POST /api/parse/wi - Parse WI (Wage & Income) documents
router.post('/wi', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            res.status(400).json({
                success: false,
                message: 'No file uploaded'
            });
            return;
        }
        const file = {
            fieldname: req.file.fieldname,
            originalname: req.file.originalname,
            encoding: req.file.encoding,
            mimetype: req.file.mimetype,
            buffer: req.file.buffer,
            size: req.file.size
        };
        console.log(`📄 Processing WI file: ${file.originalname}`);
        const result = await parser_service_1.ParserService.parseWIDocument(file);
        if (result.success) {
            res.json(result);
        }
        else {
            res.status(400).json(result);
        }
    }
    catch (error) {
        console.error('WI parsing route error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error during WI parsing'
        });
    }
});
// POST /api/parse/at - Parse AT (Account Transcript) documents
router.post('/at', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            res.status(400).json({
                success: false,
                message: 'No file uploaded'
            });
            return;
        }
        const file = {
            fieldname: req.file.fieldname,
            originalname: req.file.originalname,
            encoding: req.file.encoding,
            mimetype: req.file.mimetype,
            buffer: req.file.buffer,
            size: req.file.size
        };
        console.log(`📄 Processing AT file: ${file.originalname}`);
        // TODO: Implement AT parsing logic
        const result = {
            success: true,
            message: 'AT parsing not yet implemented',
            filename: file.originalname,
            processingTime: 0
        };
        res.json(result);
    }
    catch (error) {
        console.error('AT parsing route error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error during AT parsing'
        });
    }
});
// POST /api/parse/roa - Parse ROA (Record of Account) documents
router.post('/roa', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            res.status(400).json({
                success: false,
                message: 'No file uploaded'
            });
            return;
        }
        const file = {
            fieldname: req.file.fieldname,
            originalname: req.file.originalname,
            encoding: req.file.encoding,
            mimetype: req.file.mimetype,
            buffer: req.file.buffer,
            size: req.file.size
        };
        console.log(`📄 Processing ROA file: ${file.originalname}`);
        // TODO: Implement ROA parsing logic
        const result = {
            success: true,
            message: 'ROA parsing not yet implemented',
            filename: file.originalname,
            processingTime: 0
        };
        res.json(result);
    }
    catch (error) {
        console.error('ROA parsing route error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error during ROA parsing'
        });
    }
});
// POST /api/parse/trt - Parse TRT (Tax Return Transcript) documents
router.post('/trt', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            res.status(400).json({
                success: false,
                message: 'No file uploaded'
            });
            return;
        }
        const file = {
            fieldname: req.file.fieldname,
            originalname: req.file.originalname,
            encoding: req.file.encoding,
            mimetype: req.file.mimetype,
            buffer: req.file.buffer,
            size: req.file.size
        };
        console.log(`📄 Processing TRT file: ${file.originalname}`);
        // TODO: Implement TRT parsing logic
        const result = {
            success: true,
            message: 'TRT parsing not yet implemented',
            filename: file.originalname,
            processingTime: 0
        };
        res.json(result);
    }
    catch (error) {
        console.error('TRT parsing route error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error during TRT parsing'
        });
    }
});
// Error handling middleware for multer
router.use((error, req, res, next) => {
    if (error instanceof multer_1.default.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            res.status(400).json({
                success: false,
                message: 'File too large. Maximum size is 50MB.'
            });
            return;
        }
    }
    if (error.message === 'Only PDF files are allowed') {
        res.status(400).json({
            success: false,
            message: 'Only PDF files are allowed'
        });
        return;
    }
    next(error);
});
//# sourceMappingURL=parsers.js.map