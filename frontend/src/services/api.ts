import { LoginCredentials, AuthResponse, AuthStatus } from '../types/auth.types';
import { ParserResponse } from '../types/parser.types';

// Mock API service for development without backend
const mockDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Auth API
export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    await mockDelay(1000); // Simulate network delay
    
    // Mock successful login
    if (credentials.username && credentials.password) {
      return {
        success: true,
        message: 'Login successful',
        token: 'mock-jwt-token',
        user: {
          id: 1,
          username: credentials.username,
          email: `${credentials.username}@example.com`,
        }
      };
    }
    
    throw new Error('Invalid credentials');
  },

  getStatus: async (): Promise<AuthStatus> => {
    await mockDelay(500);
    
    // Mock authenticated status
    return {
      authenticated: true,
      user: {
        id: 1,
        username: 'demo_user',
        email: 'demo@example.com',
      },
      timestamp: new Date().toISOString(),
    };
  },

  testConnection: async (): Promise<AuthStatus> => {
    await mockDelay(800);
    
    return {
      authenticated: true,
      user: {
        id: 1,
        username: 'demo_user',
        email: 'demo@example.com',
      },
      timestamp: new Date().toISOString(),
    };
  },

  refresh: async (): Promise<AuthResponse> => {
    await mockDelay(500);
    
    return {
      success: true,
      message: 'Token refreshed',
      token: 'mock-refreshed-jwt-token',
      user: {
        id: 1,
        username: 'demo_user',
        email: 'demo@example.com',
      }
    };
  },
};

// Parser API
export const parserAPI = {
  parseWI: async (file: File): Promise<ParserResponse> => {
    await mockDelay(2000); // Simulate parsing time
    
    return {
      success: true,
      message: 'WI parsing completed',
      data: {
        '2023': [
          {
            Form: 'W-2',
            Category: 'Non-SE',
            Income: 55000,
            Withholding: 8000,
            Owner: 'TP',
            SourceFile: file.name,
            Label: 'Acme Corp'
          }
        ]
      },
      summary: [
        {
          'Tax Year': '2023',
          'Number of Forms': 1,
          'SE Income': 0,
          'SE Withholding': 0,
          'Non-SE Income': 55000,
          'Non-SE Withholding': 8000,
          'Other Income': 0,
          'Other Withholding': 0,
          'Total Income': 55000,
          'Estimated AGI': 55000,
          'Total Withholding': 8000
        }
      ]
    };
  },

  parseAT: async (file: File): Promise<ParserResponse> => {
    await mockDelay(2000);
    
    return {
      success: true,
      message: 'AT parsing completed',
      data: {
        '2023': [
          {
            Form: 'W-2',
            Category: 'Non-SE',
            Income: 75000,
            Withholding: 11000,
            Owner: 'TP',
            SourceFile: file.name,
            Label: 'Advanced Tech Corp'
          }
        ]
      },
      summary: [
        {
          'Tax Year': '2023',
          'Number of Forms': 1,
          'SE Income': 0,
          'SE Withholding': 0,
          'Non-SE Income': 75000,
          'Non-SE Withholding': 11000,
          'Other Income': 0,
          'Other Withholding': 0,
          'Total Income': 75000,
          'Estimated AGI': 75000,
          'Total Withholding': 11000
        }
      ]
    };
  },

  parseROA: async (file: File): Promise<ParserResponse> => {
    await mockDelay(2000);
    
    return {
      success: true,
      message: 'ROA parsing completed',
      data: {
        '2023': [
          {
            Form: 'W-2',
            Category: 'Non-SE',
            Income: 85000,
            Withholding: 12500,
            Owner: 'TP',
            SourceFile: file.name,
            Label: 'Record of Account Corp'
          }
        ]
      },
      summary: [
        {
          'Tax Year': '2023',
          'Number of Forms': 1,
          'SE Income': 0,
          'SE Withholding': 0,
          'Non-SE Income': 85000,
          'Non-SE Withholding': 12500,
          'Other Income': 0,
          'Other Withholding': 0,
          'Total Income': 85000,
          'Estimated AGI': 85000,
          'Total Withholding': 12500
        }
      ]
    };
  },

  parseTRT: async (file: File): Promise<ParserResponse> => {
    await mockDelay(2000);
    
    return {
      success: true,
      message: 'TRT parsing completed',
      data: {
        '2023': [
          {
            Form: 'W-2',
            Category: 'Non-SE',
            Income: 65000,
            Withholding: 9500,
            Owner: 'TP',
            SourceFile: file.name,
            Label: 'Tech Solutions Inc'
          }
        ]
      },
      summary: [
        {
          'Tax Year': '2023',
          'Number of Forms': 1,
          'SE Income': 0,
          'SE Withholding': 0,
          'Non-SE Income': 65000,
          'Non-SE Withholding': 9500,
          'Other Income': 0,
          'Other Withholding': 0,
          'Total Income': 65000,
          'Estimated AGI': 65000,
          'Total Withholding': 9500
        }
      ]
    };
  },
};

// Analysis API
export const analysisAPI = {
  getComprehensiveAnalysis: async (data: any) => {
    await mockDelay(1500);
    
    return {
      success: true,
      analysis: {
        totalIncome: 150000,
        totalWithholding: 25000,
        estimatedTax: 33000,
        projectedRefund: 8000,
        recommendations: [
          'Consider increasing retirement contributions',
          'Review itemized deductions',
          'Check for additional tax credits'
        ]
      }
    };
  },

  compareDocuments: async (data: any) => {
    await mockDelay(1200);
    
    return {
      success: true,
      comparison: {
        differences: [
          'Income variance: $5,000',
          'Withholding variance: $1,200'
        ],
        recommendations: [
          'Verify all income sources are reported',
          'Check withholding calculations'
        ]
      }
    };
  },

  getTaxSummary: async () => {
    await mockDelay(800);
    
    return {
      success: true,
      summary: {
        totalIncome: 150000,
        totalWithholding: 25000,
        estimatedTax: 33000,
        projectedRefund: 8000
      }
    };
  },

  getRecommendations: async (data: any) => {
    await mockDelay(1000);
    
    return {
      success: true,
      recommendations: [
        'Consider increasing retirement contributions',
        'Review itemized deductions',
        'Check for additional tax credits',
        'Verify all income sources are reported'
      ]
    };
  },
};

// Health check
export const healthAPI = {
  check: async () => {
    await mockDelay(300);
    
    return {
      success: true,
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0'
    };
  },
};

// Default export for compatibility
const api = {
  get: async (url: string) => ({ data: {} }),
  post: async (url: string, data: any) => ({ data: {} }),
  put: async (url: string, data: any) => ({ data: {} }),
  delete: async (url: string) => ({ data: {} }),
};

export default api; 