"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.authRoutes = void 0;
const express_1 = require("express");
const auth_service_1 = require("../services/auth.service");
const router = (0, express_1.Router)();
exports.authRoutes = router;
const authService = auth_service_1.AuthService.getInstance();
// POST /api/auth/login
router.post('/login', async (req, res) => {
    try {
        const credentials = req.body;
        if (!credentials.username || !credentials.password) {
            res.status(400).json({
                success: false,
                message: 'Username and password are required'
            });
            return;
        }
        console.log(`🔐 Login attempt for user: ${credentials.username}`);
        const result = await authService.authenticate(credentials);
        if (result.success) {
            res.json(result);
        }
        else {
            res.status(401).json(result);
        }
    }
    catch (error) {
        console.error('Login route error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error during authentication'
        });
    }
});
// GET /api/auth/status
router.get('/status', async (req, res) => {
    try {
        const status = await authService.testConnection();
        res.json(status);
    }
    catch (error) {
        console.error('Status check error:', error);
        res.status(500).json({
            authenticated: false,
            message: 'Error checking authentication status'
        });
    }
});
// POST /api/auth/test
router.post('/test', async (req, res) => {
    try {
        const status = await authService.testConnection();
        res.json(status);
    }
    catch (error) {
        console.error('Connection test error:', error);
        res.status(500).json({
            authenticated: false,
            message: 'Error testing TPS connection'
        });
    }
});
// POST /api/auth/refresh
router.post('/refresh', async (req, res) => {
    try {
        const result = await authService.refreshAuthentication();
        if (result.success) {
            res.json(result);
        }
        else {
            res.status(401).json(result);
        }
    }
    catch (error) {
        console.error('Refresh error:', error);
        res.status(500).json({
            success: false,
            message: 'Error refreshing authentication'
        });
    }
});
//# sourceMappingURL=auth.js.map