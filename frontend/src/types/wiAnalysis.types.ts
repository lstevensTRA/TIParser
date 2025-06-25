export interface WIYearSummary {
  number_of_forms: number;
  se_income: number;
  se_withholding: number;
  non_se_income: number;
  non_se_withholding: number;
  other_income: number;
  other_withholding: number;
  total_income: number;
  total_withholding: number;
  estimated_agi: number;
}

export interface WIOverallTotals {
  total_se_income: number;
  total_non_se_income: number;
  total_other_income: number;
  total_income: number;
  estimated_agi: number;
}

export interface WISummary {
  total_years: number;
  years_analyzed: string[];
  total_forms: number;
  by_year: Record<string, WIYearSummary>;
  overall_totals: WIOverallTotals;
}

export interface WIFormDetail {
  Form: string;
  UniqueID: string | null;
  Label: string | null;
  Income: number;
  Withholding: number;
  Category: 'SE' | 'Non-SE' | 'Neither';
  Fields: Record<string, any>;
  PayerBlurb: string;
  Owner: 'TP' | 'S' | 'Joint';
  SourceFile: string;
  Payer?: string;
}

// Alias for consistency with WIParser component
export type WIForm = WIFormDetail;

export interface WIAnalysisResponse {
  summary: WISummary;
  [year: string]: WIFormDetail[] | WISummary;
} 