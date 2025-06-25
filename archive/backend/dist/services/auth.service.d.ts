import { LoginCredentials, AuthResponse, AuthStatus } from '../types/auth.types';
export declare class AuthService {
    private static instance;
    private browser;
    private cookies;
    private userAgent;
    private timestamp;
    private constructor();
    static getInstance(): AuthService;
    authenticate(credentials: LoginCredentials): Promise<AuthResponse>;
    testConnection(): Promise<AuthStatus>;
    refreshAuthentication(): Promise<AuthResponse>;
    getAuthStatus(): AuthStatus;
    private saveCookies;
    private loadCookies;
    private calculateAgeHours;
}
//# sourceMappingURL=auth.service.d.ts.map