export interface FormData {
  formName: string;
  payer?: string;
  fin?: string;
  income: number;
  withholding: number;
  category: 'SE' | 'Non-SE' | 'Neither';
  owner?: 'TP' | 'S' | 'Joint';
  [key: string]: any;
}

export interface WIData {
  [year: string]: FormData[];
}

export interface ATTransaction {
  date: string;
  code: string;
  description: string;
  amount: number;
  type: 'credit' | 'debit';
}

export interface ATData {
  [year: string]: {
    transactions: ATTransaction[];
    summary: {
      totalCredits: number;
      totalDebits: number;
      balance: number;
    };
  };
}

export interface ROAData {
  [year: string]: {
    forms: FormData[];
    summary: {
      totalIncome: number;
      totalWithholding: number;
    };
  };
}

export interface TRTData {
  [year: string]: {
    forms: FormData[];
    filingStatus: string;
    summary: {
      totalIncome: number;
      totalTax: number;
      refund: number;
    };
  };
}

export interface ParserResponse {
  success: boolean;
  data?: WIData | ATData | ROAData | TRTData;
  message: string;
  filename?: string;
  processingTime?: number;
}

export interface FileUpload {
  file: File;
  type: 'wi' | 'at' | 'roa' | 'trt';
} 