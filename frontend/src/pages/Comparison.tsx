import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Common/Card';
import { Button } from '../components/Common/Button';
import { DataTable, LoadingSpinner, EmptyState } from '../components/Common/DataDisplay';

interface ClientData {
  financial_profile: {
    income: {
      monthly_net?: number;
      total?: number;
    };
  };
}

interface WISummary {
  'Tax Year': string;
  'Total Income': number;
}

interface ATData {
  tax_year: string;
  adjusted_gross_income?: number;
}

interface ComparisonData {
  most_recent_year: string;
  client_annual_income: number;
  wi_total_income: number;
  at_agi?: number;
  transcript_income_used: number;
  transcript_source: string;
  percentage_difference: number;
}

interface HumanAnalysis {
  id: string;
  category: string;
  finding: string;
  recommendation: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'in-progress' | 'resolved';
  notes?: string;
  dateAdded: string;
}

interface ComputerAnalysis {
  category: string;
  automatedFinding: string;
  confidence: number;
  dataSource: string;
}

interface Discrepancy {
  id: string;
  category: string;
  humanFinding: string;
  computerFinding: string;
  difference: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'reviewing' | 'resolved';
  resolution?: string;
}

interface Invoice {
  id: string;
  service: string;
  amount: number;
  description: string;
  date: string;
  status: 'draft' | 'sent' | 'paid';
}

export default function Comparison() {
  const [activeTab, setActiveTab] = useState<'comparison' | 'analysis' | 'discrepancies' | 'invoices' | 'json'>('comparison');
  const [isLoading, setIsLoading] = useState(false);
  const [clientData, setClientData] = useState<ClientData | null>(null);
  const [wiSummary, setWiSummary] = useState<WISummary[]>([]);
  const [atData, setAtData] = useState<ATData[]>([]);
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [humanAnalysis, setHumanAnalysis] = useState<HumanAnalysis[]>([]);
  const [computerAnalysis, setComputerAnalysis] = useState<ComputerAnalysis[]>([]);
  const [discrepancies, setDiscrepancies] = useState<Discrepancy[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [showAddAnalysis, setShowAddAnalysis] = useState(false);
  const [newAnalysis, setNewAnalysis] = useState({
    category: '',
    finding: '',
    recommendation: '',
    priority: 'medium' as const,
    notes: ''
  });

  useEffect(() => {
    // Simulate loading comparison data
    setTimeout(() => {
      const mockClientData: ClientData = {
        financial_profile: {
          income: {
            monthly_net: 6500, // $6,500 monthly net
          }
        }
      };

      const mockWISummary: WISummary[] = [
        {
          'Tax Year': '2023',
          'Total Income': 85000
        },
        {
          'Tax Year': '2022',
          'Total Income': 78000
        }
      ];

      const mockATData: ATData[] = [
        {
          tax_year: '2023',
          adjusted_gross_income: 82000
        },
        {
          tax_year: '2022',
          adjusted_gross_income: 75000
        }
      ];

      const mockHumanAnalysis: HumanAnalysis[] = [
        {
          id: '1',
          category: 'Income Reporting',
          finding: 'Client underreported SE income by $5,000',
          recommendation: 'File amended return for 2023',
          priority: 'high',
          status: 'pending',
          notes: 'Client admitted to missing 1099-NEC',
          dateAdded: '2024-01-15'
        },
        {
          id: '2',
          category: 'Withholding',
          finding: 'Insufficient withholding for SE income',
          recommendation: 'Implement quarterly payments',
          priority: 'medium',
          status: 'in-progress',
          notes: 'Client agreed to quarterly payments',
          dateAdded: '2024-01-16'
        },
        {
          id: '3',
          category: 'Business Structure',
          finding: 'S-Corp election could save $3,000 annually',
          recommendation: 'Evaluate S-Corp conversion',
          priority: 'medium',
          status: 'pending',
          dateAdded: '2024-01-17'
        }
      ];

      const mockComputerAnalysis: ComputerAnalysis[] = [
        {
          category: 'Income Reporting',
          automatedFinding: 'SE income detected: $30,000',
          confidence: 95,
          dataSource: 'ROA Parser'
        },
        {
          category: 'Withholding',
          automatedFinding: 'Withholding adequacy: 85%',
          confidence: 88,
          dataSource: 'TRT Parser'
        },
        {
          category: 'Tax Efficiency',
          automatedFinding: 'Effective tax rate: 12.5%',
          confidence: 92,
          dataSource: 'Combined Analysis'
        }
      ];

      const mockDiscrepancies: Discrepancy[] = [
        {
          id: '1',
          category: 'Income Reporting',
          humanFinding: 'Underreported SE income by $5,000',
          computerFinding: 'SE income: $30,000 (complete)',
          difference: 'Human analysis found missing income not in transcripts',
          priority: 'high',
          status: 'open'
        },
        {
          id: '2',
          category: 'Withholding',
          humanFinding: 'Insufficient withholding for SE income',
          computerFinding: 'Withholding adequacy: 85%',
          difference: 'Computer analysis doesn\'t account for SE tax burden',
          priority: 'medium',
          status: 'reviewing'
        }
      ];

      const mockInvoices: Invoice[] = [
        {
          id: 'INV-001',
          service: 'Tax Return Filing (2023)',
          amount: 450,
          description: 'Complete tax return preparation with SE income optimization',
          date: '2024-01-15',
          status: 'sent'
        },
        {
          id: 'INV-002',
          service: 'Tax Resolution Services',
          amount: 750,
          description: 'Comprehensive tax situation analysis and resolution',
          date: '2024-01-16',
          status: 'draft'
        },
        {
          id: 'INV-003',
          service: 'Business Structure Analysis',
          amount: 300,
          description: 'S-Corp election evaluation and implementation',
          date: '2024-01-17',
          status: 'draft'
        }
      ];

      setClientData(mockClientData);
      setWiSummary(mockWISummary);
      setAtData(mockATData);

      // Calculate comparison data
      const clientAnnualIncome = mockClientData.financial_profile.income.monthly_net! * 12;
      const mostRecentYear = '2023';
      const wiTotalIncome = mockWISummary.find(row => row['Tax Year'] === mostRecentYear)?.['Total Income'] || 0;
      const atAgi = mockATData.find(d => d.tax_year === mostRecentYear)?.adjusted_gross_income;

      // Decide which transcript value to use
      let transcriptIncome: number;
      let transcriptSource: string;
      
      if (atAgi && atAgi > 0) {
        transcriptIncome = atAgi;
        transcriptSource = 'Transcript AGI (from AT)';
      } else {
        transcriptIncome = wiTotalIncome;
        transcriptSource = 'Transcript Total Income (from WI)';
      }

      // Calculate percentage difference
      const percentDiff = transcriptIncome === 0 ? Infinity : 
        ((clientAnnualIncome - transcriptIncome) / transcriptIncome) * 100;

      const comparison: ComparisonData = {
        most_recent_year: mostRecentYear,
        client_annual_income: clientAnnualIncome,
        wi_total_income: wiTotalIncome,
        at_agi: atAgi,
        transcript_income_used: transcriptIncome,
        transcript_source: transcriptSource,
        percentage_difference: percentDiff
      };

      setComparisonData(comparison);
      setHumanAnalysis(mockHumanAnalysis);
      setComputerAnalysis(mockComputerAnalysis);
      setDiscrepancies(mockDiscrepancies);
      setInvoices(mockInvoices);
    }, 1000);
  }, []);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercentage = (percent: number) => {
    if (percent === Infinity) return '∞%';
    return `${percent.toFixed(2)}%`;
  };

  const getDifferenceColor = (percent: number) => {
    if (percent === Infinity) return 'text-red-600';
    const absPercent = Math.abs(percent);
    if (absPercent <= 5) return 'text-green-600';
    if (absPercent <= 15) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'resolved': return 'bg-green-100 text-green-800';
      case 'in-progress': return 'bg-blue-100 text-blue-800';
      case 'reviewing': return 'bg-yellow-100 text-yellow-800';
      case 'open': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleAddAnalysis = () => {
    if (!newAnalysis.category || !newAnalysis.finding || !newAnalysis.recommendation) return;
    
    const analysis: HumanAnalysis = {
      id: Date.now().toString(),
      category: newAnalysis.category,
      finding: newAnalysis.finding,
      recommendation: newAnalysis.recommendation,
      priority: newAnalysis.priority,
      status: 'pending',
      notes: newAnalysis.notes,
      dateAdded: new Date().toISOString().split('T')[0]
    };

    setHumanAnalysis(prev => [...prev, analysis]);
    setNewAnalysis({
      category: '',
      finding: '',
      recommendation: '',
      priority: 'medium',
      notes: ''
    });
    setShowAddAnalysis(false);
  };

  const renderComparisonTab = () => (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Income Comparison</h1>
        <p className="mt-2 text-gray-600">
          Client vs Wage & Income Transcript
        </p>
      </div>

      {!clientData || !wiSummary || !comparisonData ? (
        <EmptyState
          title="No Comparison Data Available"
          description="Client profile or Wage & Income summary data not available. Please process a case ID first."
        />
      ) : (
        <div className="space-y-6">
          {/* Main Comparison Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Income Comparison Analysis</CardTitle>
              <CardDescription>
                Most Recent Year: {comparisonData.most_recent_year}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <h3 className="text-sm font-medium text-blue-900 mb-2">
                    Client Annual Net (Self-Reported)
                  </h3>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatCurrency(comparisonData.client_annual_income)}
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    Monthly: {formatCurrency(comparisonData.client_annual_income / 12)}
                  </p>
                </div>

                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <h3 className="text-sm font-medium text-green-900 mb-2">
                    {comparisonData.transcript_source}
                  </h3>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(comparisonData.transcript_income_used)}
                  </p>
                </div>

                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <h3 className="text-sm font-medium text-purple-900 mb-2">
                    % Difference
                  </h3>
                  <p className={`text-2xl font-bold ${getDifferenceColor(comparisonData.percentage_difference)}`}>
                    {formatPercentage(comparisonData.percentage_difference)}
                  </p>
                  <p className="text-xs text-purple-600 mt-1">
                    {comparisonData.percentage_difference > 0 ? 'Client Higher' : 'Transcript Higher'}
                  </p>
                </div>
              </div>

              {/* Additional Income Sources */}
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                {comparisonData.at_agi && comparisonData.at_agi > 0 && (
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-1">AT AGI</h4>
                    <p className="text-lg font-semibold text-gray-700">
                      {formatCurrency(comparisonData.at_agi)}
                    </p>
                  </div>
                )}
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-1">WI Total Income</h4>
                  <p className="text-lg font-semibold text-gray-700">
                    {formatCurrency(comparisonData.wi_total_income)}
                  </p>
                </div>
              </div>

              {/* Analysis Description */}
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-900 mb-2">Analysis</h4>
                <p className="text-blue-800 text-sm">
                  This comparison shows how close the client's self-reported income is to the IRS Wage & Income transcript or Account Transcript AGI for the most recent year.
                </p>
                {comparisonData.percentage_difference !== Infinity && (
                  <div className="mt-3">
                    <p className="text-blue-800 text-sm">
                      <strong>Interpretation:</strong> {
                        Math.abs(comparisonData.percentage_difference) <= 5 ? 
                          '✅ Excellent match - Client reporting appears accurate' :
                        Math.abs(comparisonData.percentage_difference) <= 15 ? 
                          '⚠️ Moderate variance - Review for discrepancies' :
                          '❌ Significant variance - Requires investigation'
                      }
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );

  const renderTraVsAiTab = () => {
    // Example mock data for demonstration
    const traTI = {
      'SE Income': 35000,
      'W-2 Income': 85000,
      'Total Income': 120000,
      'Withholding': 12500,
      '1099-DIV': 800,
      '1099-INT': 0
    };
    const aiTI = {
      'SE Income': 30000,
      'W-2 Income': 85000,
      'Total Income': 115800,
      'Withholding': 12500,
      '1099-DIV': 800,
      '1099-INT': 250
    };
    const fields = Object.keys({ ...traTI, ...aiTI });
    let matchCount = 0;
    let mismatchCount = 0;
    const rows = fields.map((field) => {
      const human = traTI[field] ?? '—';
      const ai = aiTI[field] ?? '—';
      const match = human === ai;
      if (match) matchCount++; else mismatchCount++;
      return { field, human, ai, match };
    });

    return (
      <div className="space-y-6">
        <div className="border-b border-gray-200 pb-4">
          <h1 className="text-3xl font-bold text-gray-900">TRA TI vs AI TI</h1>
          <p className="mt-2 text-gray-600">
            Compare Tax Resolution Analyst's Tax Interpretation (TRA TI) with AI Tax Interpretation (AI TI)
          </p>
        </div>
        <div className="flex items-center space-x-8 mb-4">
          <span className="text-green-700 font-semibold">Matches: {matchCount}</span>
          <span className="text-red-700 font-semibold">Mismatches: {mismatchCount}</span>
        </div>
        <div className="overflow-x-auto">
          <div className="min-w-full">
            {/* Header Row for side-by-side panels */}
            <div className="grid grid-cols-3 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase">
              <div className="px-6 py-3 text-center border-r border-gray-200">TRA TI (Human)</div>
              <div className="px-6 py-3 text-center">Result</div>
              <div className="px-6 py-3 text-center border-l border-gray-200">AI TI (Computer)</div>
            </div>
            {/* Data Rows */}
            {rows.map((row, idx) => (
              <div key={idx} className="grid grid-cols-3 border-b border-gray-100 items-center">
                {/* TRA TI Value */}
                <div className="px-6 py-4 whitespace-nowrap text-sm text-center bg-white border-r border-gray-100">
                  <div className="font-medium text-gray-900">{row.field}</div>
                  <div className="mt-1 text-gray-700">{row.human}</div>
                </div>
                {/* Match/Mismatch Badge */}
                <div className="px-6 py-4 whitespace-nowrap text-sm text-center">
                  {row.match ? (
                    <span className="bg-green-100 text-green-800 font-semibold px-2 py-1 rounded">Match</span>
                  ) : (
                    <span className="bg-red-100 text-red-800 font-semibold px-2 py-1 rounded">Mismatch</span>
                  )}
                </div>
                {/* AI TI Value */}
                <div className="px-6 py-4 whitespace-nowrap text-sm text-center bg-white border-l border-gray-100">
                  <div className="font-medium text-gray-900">{row.field}</div>
                  <div className="mt-1 text-gray-700">{row.ai}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderDiscrepanciesTab = () => (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Discrepancies & Resolution</h1>
        <p className="mt-2 text-gray-600">
          Track differences between human and computer analysis
        </p>
      </div>

      <div className="space-y-4">
        {discrepancies.map((discrepancy) => (
          <Card key={discrepancy.id} className="border-l-4 border-l-orange-500">
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{discrepancy.category}</h3>
                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getPriorityColor(discrepancy.priority)}`}>
                  {discrepancy.priority.toUpperCase()}
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">Human Finding</h4>
                  <p className="text-sm text-gray-600">{discrepancy.humanFinding}</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">Computer Finding</h4>
                  <p className="text-sm text-gray-600">{discrepancy.computerFinding}</p>
                </div>
              </div>
              
              <div className="mb-4">
                <h4 className="font-medium text-gray-900 mb-1">Difference</h4>
                <p className="text-sm text-gray-600">{discrepancy.difference}</p>
              </div>
              
              {discrepancy.resolution && (
                <div className="mb-4 p-3 bg-green-50 rounded">
                  <h4 className="font-medium text-green-900 mb-1">Resolution</h4>
                  <p className="text-sm text-green-800">{discrepancy.resolution}</p>
                </div>
              )}
              
              <div className="flex justify-between items-center">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(discrepancy.status)}`}>
                  {discrepancy.status}
                </span>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  Update Status
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderInvoicesTab = () => (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Service Invoices</h1>
        <p className="mt-2 text-gray-600">
          Track actual services invoiced and AI-suggested services
        </p>
      </div>

      {/* Side by side tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Actual TRA Services Table */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Actual TRA Services</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {invoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{invoice.service}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{invoice.description}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${invoice.amount.toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`font-semibold px-2 py-1 rounded ${
                        invoice.status === 'paid' ? 'bg-green-100 text-green-800' :
                        invoice.status === 'sent' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {invoice.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Suggested Services Table */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">AI Suggested Services</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Suggested Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Why Suggested</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {/* Example mock AI suggestions */}
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Tax Return Filing (2023)</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Complete tax return preparation with SE income optimization</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">$450.00</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">SE income detected</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Tax Resolution Services</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Comprehensive tax situation analysis and resolution</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">$750.00</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Critical issues found</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Business Structure Analysis</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">S-Corp election evaluation and implementation</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">$300.00</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">SE income &gt; $25,000</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Bookkeeping Services</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Monthly bookkeeping for small business</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">$200.00</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Multiple 1099s detected</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );

  const renderJsonTab = () => (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Comparison Data (JSON)</h1>
        <p className="mt-2 text-gray-600">
          Raw comparison data for debugging and analysis
        </p>
      </div>

      {!comparisonData ? (
        <EmptyState
          title="No Comparison Data"
          description="No comparison data available to display."
        />
      ) : (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Complete Analysis Data</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-gray-900 text-green-200 rounded p-4 text-xs overflow-x-auto">
                {JSON.stringify({
                  comparison_info: comparisonData,
                  human_analysis: humanAnalysis,
                  computer_analysis: computerAnalysis,
                  discrepancies: discrepancies,
                  invoices: invoices,
                  client_data: clientData,
                  wi_summary: wiSummary,
                  at_data: atData
                }, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );

  if (isLoading) {
    return <LoadingSpinner message="Loading comparison data..." />;
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'comparison', label: 'Income Comparison' },
            { id: 'analysis', label: 'TRA TI vs AI TI' },
            { id: 'discrepancies', label: 'Discrepancies' },
            { id: 'invoices', label: 'Invoices' },
            { id: 'json', label: 'JSON Data' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'comparison' && renderComparisonTab()}
      {activeTab === 'analysis' && renderTraVsAiTab()}
      {activeTab === 'discrepancies' && renderDiscrepanciesTab()}
      {activeTab === 'invoices' && renderInvoicesTab()}
      {activeTab === 'json' && renderJsonTab()}
    </div>
  );
} 