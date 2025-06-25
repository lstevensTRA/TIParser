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
exports.AuthService = void 0;
const playwright_1 = require("playwright");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class AuthService {
    constructor() {
        this.browser = null;
        this.cookies = null;
        this.userAgent = null;
        this.timestamp = null;
    }
    static getInstance() {
        if (!AuthService.instance) {
            AuthService.instance = new AuthService();
        }
        return AuthService.instance;
    }
    async authenticate(credentials) {
        try {
            console.log('🔐 Starting TPS authentication...');
            // Launch browser
            this.browser = await playwright_1.chromium.launch({
                headless: true,
                slowMo: 1000
            });
            const context = await this.browser.newContext({
                userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            });
            const page = await context.newPage();
            // Navigate to login page
            await page.goto('https://tps.logiqs.com/Login.aspx');
            // Wait for login form
            await page.waitForSelector('#txtUsername', { timeout: 10000 });
            // Fill login form
            await page.fill('#txtUsername', credentials.username);
            await page.fill('#txtPassword', credentials.password);
            // Click login button
            await page.click('#btnLogin');
            // Wait for navigation
            await page.waitForLoadState('networkidle');
            // Check if login was successful
            const currentUrl = page.url();
            if (currentUrl.includes('Login.aspx') || currentUrl.includes('default.aspx')) {
                await this.browser.close();
                return {
                    success: false,
                    message: 'Login failed - invalid credentials or login page still showing'
                };
            }
            // Get cookies
            const cookies = await context.cookies();
            const cookieString = cookies.map(c => `${c.name}=${c.value}`).join('; ');
            // Use default user agent
            const userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
            // Save cookies
            this.cookies = cookieString;
            this.userAgent = userAgent;
            this.timestamp = new Date().toISOString();
            // Save to file
            await this.saveCookies(cookieString, userAgent, this.timestamp);
            await this.browser.close();
            console.log('✅ TPS authentication successful');
            return {
                success: true,
                message: 'Authentication successful',
                cookies: cookieString,
                userAgent: userAgent,
                timestamp: this.timestamp
            };
        }
        catch (error) {
            console.error('❌ Authentication error:', error);
            if (this.browser) {
                await this.browser.close();
            }
            return {
                success: false,
                message: `Authentication failed: ${error instanceof Error ? error.message : 'Unknown error'}`
            };
        }
    }
    async testConnection() {
        try {
            const cookies = await this.loadCookies();
            if (!cookies) {
                return {
                    authenticated: false,
                    message: 'No cookies found - authentication required'
                };
            }
            // Test with a simple API call
            const response = await fetch('https://tps.logiqs.com/API/Document/gridBind?caseid=test&type=grid', {
                headers: {
                    'Cookie': cookies.cookies,
                    'User-Agent': cookies.userAgent
                }
            });
            if (response.status === 302) {
                const location = response.headers.get('Location') || '';
                if (location.includes('login') || location.includes('default.aspx')) {
                    return {
                        authenticated: false,
                        message: 'Session expired - re-authentication required'
                    };
                }
            }
            return {
                authenticated: true,
                message: 'Connection test successful',
                timestamp: cookies.timestamp,
                ageHours: this.calculateAgeHours(cookies.timestamp)
            };
        }
        catch (error) {
            return {
                authenticated: false,
                message: `Connection test failed: ${error instanceof Error ? error.message : 'Unknown error'}`
            };
        }
    }
    async refreshAuthentication() {
        // For now, just return current status
        // In a real implementation, you might want to refresh the session
        const status = await this.testConnection();
        if (status.authenticated) {
            return {
                success: true,
                message: 'Authentication is still valid',
                cookies: this.cookies || undefined,
                userAgent: this.userAgent || undefined,
                timestamp: this.timestamp || undefined
            };
        }
        else {
            return {
                success: false,
                message: 'Authentication expired - re-login required'
            };
        }
    }
    getAuthStatus() {
        if (!this.cookies || !this.timestamp) {
            return {
                authenticated: false,
                message: 'No authentication data found'
            };
        }
        const ageHours = this.calculateAgeHours(this.timestamp);
        return {
            authenticated: true,
            message: `Authenticated (${ageHours.toFixed(1)} hours old)`,
            timestamp: this.timestamp,
            ageHours: ageHours
        };
    }
    async saveCookies(cookies, userAgent, timestamp) {
        const cookieData = {
            cookies,
            userAgent,
            timestamp
        };
        const cookiePath = path.join(process.cwd(), '..', 'logiqs-cookies.json');
        await fs.promises.writeFile(cookiePath, JSON.stringify(cookieData, null, 2));
    }
    async loadCookies() {
        try {
            const cookiePath = path.join(process.cwd(), '..', 'logiqs-cookies.json');
            const data = await fs.promises.readFile(cookiePath, 'utf8');
            return JSON.parse(data);
        }
        catch (error) {
            return null;
        }
    }
    calculateAgeHours(timestamp) {
        const now = new Date();
        const cookieTime = new Date(timestamp);
        return (now.getTime() - cookieTime.getTime()) / (1000 * 60 * 60);
    }
}
exports.AuthService = AuthService;
//# sourceMappingURL=auth.service.js.map