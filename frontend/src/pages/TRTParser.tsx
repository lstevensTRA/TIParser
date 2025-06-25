import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Common/Card';
import { Button } from '../components/Common/Button';
import { DataTable, LoadingSpinner, EmptyState } from '../components/Common/DataDisplay';

interface TRTForm {
  Form: string;
  Category: 'SE' | 'Non-SE' | 'Neither';
  Income: number;
  Withholding: number;
  Owner: 'TP' | 'S' | 'Joint';
  SourceFile: string;
  Label?: string;
  Payer?: string;
}

interface TRTSummary {
  'Tax Year': string;
  'Number of Forms': number;
  'SE Income': number;
  'SE Withholding': number;
  'Non-SE Income': number;
  'Non-SE Withholding': number;
  'Other Income': number;
  'Other Withholding': number;
  'Total Income': number;
  'Estimated AGI': number;
  'Total Withholding': number;
}

interface OwnerBreakdown {
  taxpayer: { income: number; withholding: number };
  spouse: { income: number; withholding: number };
  joint: { income: number; withholding: number };
  combined: { income: number; withholding: number };
}

interface TRTFormMatching {
  filename: string;
  owner: string;
  ssn: string;
  tax_period: string;
  form_matches: Array<{
    form_name: string;
    matched: boolean;
  }>;
}

interface TaxEfficiencyMetrics {
  effectiveTaxRate: number;
  withholdingEfficiency: number;
  seTaxBurden: number;
  taxOptimizationScore: number;
  incomeStabilityScore: number;
  yearOverYearGrowth: number;
  projectedTaxLiability: number;
  withholdingAdequacy: number;
  serviceOpportunities: string[];
  recommendations: string[];
}

export default function TRTParser() {
  const [activeTab, setActiveTab] = useState<'summary' | 'critical' | 'projection' | 'efficiency' | 'json' | 'matching' | 'logs'>('summary');
  const [summaryView, setSummaryView] = useState<'combined' | 'separated'>('combined');
  const [isLoading, setIsLoading] = useState(false);
  const [trtData, setTrtData] = useState<{ [year: string]: TRTForm[] }>({});
  const [trtSummary, setTrtSummary] = useState<TRTSummary[]>([]);
  const [formMatching, setFormMatching] = useState<TRTFormMatching[]>([]);
  const [logs, setLogs] = useState<string>('');
  const [taxEfficiency, setTaxEfficiency] = useState<TaxEfficiencyMetrics | null>(null);

  useEffect(() => {
    // Simulate loading TRT data
    setTimeout(() => {
      const mockData = {
        '2023': [
          {
            Form: 'W-2',
            Category: 'Non-SE',
            Income: 65000,
            Withholding: 9500,
            Owner: 'TP',
            SourceFile: 'TRT_2023_TP.pdf',
            Label: 'Tech Solutions Inc'
          },
          {
            Form: '1099-MISC',
            Category: 'SE',
            Income: 15000,
            Withholding: 0,
            Owner: 'TP',
            SourceFile: 'TRT_2023_TP.pdf',
            Label: 'Freelance Work'
          },
          {
            Form: '1099-INT',
            Category: 'Neither',
            Income: 250,
            Withholding: 0,
            Owner: 'TP',
            SourceFile: 'TRT_2023_TP.pdf',
            Label: 'Local Bank'
          }
        ],
        '2022': [
          {
            Form: 'W-2',
            Category: 'Non-SE',
            Income: 58000,
            Withholding: 8200,
            Owner: 'TP',
            SourceFile: 'TRT_2022_TP.pdf',
            Label: 'Tech Solutions Inc'
          },
          {
            Form: '1099-MISC',
            Category: 'SE',
            Income: 12000,
            Withholding: 0,
            Owner: 'TP',
            SourceFile: 'TRT_2022_TP.pdf',
            Label: 'Freelance Work'
          }
        ]
      };

      const mockSummary: TRTSummary[] = [
        {
          'Tax Year': '2023',
          'Number of Forms': 3,
          'SE Income': 15000,
          'SE Withholding': 0,
          'Non-SE Income': 65000,
          'Non-SE Withholding': 9500,
          'Other Income': 250,
          'Other Withholding': 0,
          'Total Income': 80250,
          'Estimated AGI': 80250,
          'Total Withholding': 9500
        },
        {
          'Tax Year': '2022',
          'Number of Forms': 2,
          'SE Income': 12000,
          'SE Withholding': 0,
          'Non-SE Income': 58000,
          'Non-SE Withholding': 8200,
          'Other Income': 0,
          'Other Withholding': 0,
          'Total Income': 70000,
          'Estimated AGI': 70000,
          'Total Withholding': 8200
        }
      ];

      const mockFormMatching: TRTFormMatching[] = [
        {
          filename: 'TRT_2023_TP.pdf',
          owner: 'TP',
          ssn: '***-**-5678',
          tax_period: '2023',
          form_matches: [
            { form_name: 'W-2', matched: true },
            { form_name: '1099-MISC', matched: true },
            { form_name: '1099-INT', matched: true },
            { form_name: '1099-DIV', matched: false }
          ]
        }
      ];

      // Calculate tax efficiency metrics
      const currentYear = '2023';
      const previousYear = '2022';
      const currentData = mockSummary.find(s => s['Tax Year'] === currentYear);
      const previousData = mockSummary.find(s => s['Tax Year'] === previousYear);

      if (currentData && previousData) {
        const effectiveTaxRate = (currentData['Total Withholding'] / currentData['Total Income']) * 100;
        const withholdingEfficiency = 88; // Mock calculation
        const seTaxBurden = currentData['SE Income'] > 0 ? (currentData['SE Income'] * 0.153) / currentData['SE Income'] * 100 : 0;
        const taxOptimizationScore = Math.max(0, 100 - Math.abs(effectiveTaxRate - 15)); // Target 15% effective rate
        const incomeStabilityScore = 82; // Mock calculation
        const yearOverYearGrowth = ((currentData['Total Income'] - previousData['Total Income']) / previousData['Total Income']) * 100;
        const projectedTaxLiability = currentData['Total Income'] * 0.20; // Simplified projection
        const withholdingAdequacy = (currentData['Total Withholding'] / projectedTaxLiability) * 100;

        const serviceOpportunities = [];
        if (currentData['SE Income'] > 0) serviceOpportunities.push('Self-Employment Tax Planning');
        if (withholdingAdequacy < 90) serviceOpportunities.push('Withholding Optimization');
        if (yearOverYearGrowth > 10) serviceOpportunities.push('Income Growth Planning');
        if (currentData['SE Income'] > 25000) serviceOpportunities.push('Business Structure Analysis');

        const recommendations = [];
        if (currentData['SE Income'] > 0) recommendations.push('Consider quarterly estimated tax payments');
        if (withholdingAdequacy < 90) recommendations.push('Increase withholding or make estimated payments');
        if (yearOverYearGrowth > 10) recommendations.push('Review tax planning strategies for income growth');
        if (currentData['SE Income'] > 25000) recommendations.push('Evaluate S-Corp election for tax savings');

        setTaxEfficiency({
          effectiveTaxRate,
          withholdingEfficiency,
          seTaxBurden,
          taxOptimizationScore,
          incomeStabilityScore,
          yearOverYearGrowth,
          projectedTaxLiability,
          withholdingAdequacy,
          serviceOpportunities,
          recommendations
        });
      }

      setTrtData(mockData);
      setTrtSummary(mockSummary);
      setFormMatching(mockFormMatching);
      setLogs('Processing completed successfully...\nExtracted 5 forms from 2 files.\nSelf-employment income detected.\nNo critical issues found.');
    }, 1000);
  }, []);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getOwnerBreakdown = (year: string): OwnerBreakdown => {
    const yearForms = trtData[year] || [];
    const breakdown: OwnerBreakdown = {
      taxpayer: { income: 0, withholding: 0 },
      spouse: { income: 0, withholding: 0 },
      joint: { income: 0, withholding: 0 },
      combined: { income: 0, withholding: 0 }
    };

    yearForms.forEach(form => {
      const income = form.Income || 0;
      const withholding = form.Withholding || 0;
      
      if (form.Owner === 'TP') {
        breakdown.taxpayer.income += income;
        breakdown.taxpayer.withholding += withholding;
      } else if (form.Owner === 'S') {
        breakdown.spouse.income += income;
        breakdown.spouse.withholding += withholding;
      } else if (form.Owner === 'Joint') {
        breakdown.joint.income += income;
        breakdown.joint.withholding += withholding;
      }
      
      breakdown.combined.income += income;
      breakdown.combined.withholding += withholding;
    });

    return breakdown;
  };

  const renderSummaryTab = () => (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <h3 className="text-lg font-semibold">Income Summary</h3>
        <div className="flex space-x-2">
          <label className="flex items-center space-x-2">
            <input
              type="radio"
              name="summary-view"
              value="combined"
              checked={summaryView === 'combined'}
              onChange={() => setSummaryView('combined')}
              className="form-radio"
            />
            <span>Combined</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="radio"
              name="summary-view"
              value="separated"
              checked={summaryView === 'separated'}
              onChange={() => setSummaryView('separated')}
              className="form-radio"
            />
            <span>Separated by Owner</span>
          </label>
        </div>
      </div>

      {trtSummary.length > 0 ? (
        <div className="space-y-6">
          {/* Summary Table */}
          <Card>
            <CardHeader>
              <CardTitle>Summary Table</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tax Year</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Combined Income</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Combined Withholding</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">SE Income</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">SE Withholding</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Non-SE Income</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Non-SE Withholding</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Other Income</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Other Withholding</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Income</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estimated AGI</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Withholding</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {trtSummary.map((row, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{row['Tax Year']}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['Total Income'])}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['Total Withholding'])}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['SE Income'])}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['SE Withholding'])}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['Non-SE Income'])}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['Non-SE Withholding'])}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['Other Income'])}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['Other Withholding'])}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['Total Income'])}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['Estimated AGI'])}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row['Total Withholding'])}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Owner-Based Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Owner-Based Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trtSummary.map((row, index) => {
                  const year = row['Tax Year'];
                  const breakdown = getOwnerBreakdown(year);
                  
                  return (
                    <details key={index} className="border border-gray-200 rounded-lg">
                      <summary className="px-4 py-3 bg-gray-50 cursor-pointer font-medium">
                        📊 Tax Year {year} - Owner Breakdown
                      </summary>
                      <div className="p-4">
                        <div className="grid grid-cols-4 gap-4">
                          <div>
                            <h4 className="font-semibold text-gray-900">Taxpayer</h4>
                            <p className="text-sm text-gray-600">Income: {formatCurrency(breakdown.taxpayer.income)}</p>
                            <p className="text-sm text-gray-600">Withholding: {formatCurrency(breakdown.taxpayer.withholding)}</p>
                          </div>
                          <div>
                            <h4 className="font-semibold text-gray-900">Spouse</h4>
                            <p className="text-sm text-gray-600">Income: {formatCurrency(breakdown.spouse.income)}</p>
                            <p className="text-sm text-gray-600">Withholding: {formatCurrency(breakdown.spouse.withholding)}</p>
                          </div>
                          <div>
                            <h4 className="font-semibold text-gray-900">Joint</h4>
                            <p className="text-sm text-gray-600">Income: {formatCurrency(breakdown.joint.income)}</p>
                            <p className="text-sm text-gray-600">Withholding: {formatCurrency(breakdown.joint.withholding)}</p>
                          </div>
                          <div>
                            <h4 className="font-semibold text-gray-900">Combined</h4>
                            <p className="text-sm text-gray-600">Income: {formatCurrency(breakdown.combined.income)}</p>
                            <p className="text-sm text-gray-600">Withholding: {formatCurrency(breakdown.combined.withholding)}</p>
                          </div>
                        </div>
                      </div>
                    </details>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Detailed Breakdown by Year */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Year-by-Year Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trtSummary.map((row, index) => {
                  const year = row['Tax Year'];
                  const yearForms = trtData[year] || [];
                  
                  return (
                    <details key={index} className="border border-gray-200 rounded-lg" open>
                      <summary className="px-4 py-3 bg-gray-50 cursor-pointer font-medium">
                        📅 Tax Year {year} - Detailed Breakdown
                      </summary>
                      <div className="p-4 space-y-4">
                        {/* Income Categories */}
                        <div className="grid grid-cols-3 gap-4">
                          <div className="text-center p-3 bg-blue-50 rounded-lg">
                            <h4 className="font-semibold text-blue-900">Self-Employment Income</h4>
                            <p className="text-lg font-bold text-blue-600">{formatCurrency(row['SE Income'])}</p>
                            <p className="text-sm text-blue-600">Withholding: {formatCurrency(row['SE Withholding'])}</p>
                          </div>
                          <div className="text-center p-3 bg-green-50 rounded-lg">
                            <h4 className="font-semibold text-green-900">Non-Self-Employment Income</h4>
                            <p className="text-lg font-bold text-green-600">{formatCurrency(row['Non-SE Income'])}</p>
                            <p className="text-sm text-green-600">Withholding: {formatCurrency(row['Non-SE Withholding'])}</p>
                          </div>
                          <div className="text-center p-3 bg-purple-50 rounded-lg">
                            <h4 className="font-semibold text-purple-900">Other Income</h4>
                            <p className="text-lg font-bold text-purple-600">{formatCurrency(row['Other Income'])}</p>
                            <p className="text-sm text-purple-600">Withholding: {formatCurrency(row['Other Withholding'])}</p>
                          </div>
                        </div>

                        {/* Forms Breakdown */}
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-3">Forms Breakdown</h4>
                          {yearForms.length > 0 ? (
                            <div className="space-y-3">
                              {Object.entries(
                                yearForms.reduce((acc, form) => {
                                  const owner = form.Owner;
                                  if (!acc[owner]) acc[owner] = [];
                                  acc[owner].push(form);
                                  return acc;
                                }, {} as { [key: string]: TRTForm[] })
                              ).map(([owner, forms]) => (
                                <div key={owner} className="border border-gray-200 rounded-lg p-3">
                                  <h5 className="font-medium text-gray-900 mb-2">
                                    {owner === 'TP' ? 'Taxpayer' : owner === 'S' ? 'Spouse' : 'Joint'} Forms:
                                  </h5>
                                  <div className="space-y-2">
                                    {forms.map((form, formIndex) => (
                                      <div key={formIndex} className="bg-gray-50 rounded p-2">
                                        <div className="flex items-center justify-between">
                                          <span className="font-medium">{form.Form}</span>
                                          <span className="text-sm text-gray-600">({form.Category})</span>
                                        </div>
                                        {form.Label && form.Label !== 'UNKNOWN' && (
                                          <p className="text-sm text-gray-600">Payer: {form.Label}</p>
                                        )}
                                        <div className="grid grid-cols-3 gap-2 mt-1 text-sm">
                                          <span>Income: {formatCurrency(form.Income)}</span>
                                          <span>Withholding: {formatCurrency(form.Withholding)}</span>
                                          <span>Source: {form.SourceFile}</span>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-gray-600">No forms found for this year</p>
                          )}
                        </div>
                      </div>
                    </details>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <EmptyState
          title="No TRT Data"
          description="No TRT data extracted. Please process a case ID first."
        />
      )}
    </div>
  );

  const renderCriticalTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Critical Extraction Issues & Forms to Check</h3>
      
      <Card>
        <CardHeader>
          <CardTitle>Extraction Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm">All forms extracted successfully</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm">Self-employment income detected and categorized</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span className="text-sm">SE tax calculations may be needed</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Form Matching Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {formMatching.map((file, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-3">
                <h4 className="font-medium text-gray-900 mb-2">{file.filename}</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Owner:</span> {file.owner}
                  </div>
                  <div>
                    <span className="text-gray-600">SSN:</span> {file.ssn}
                  </div>
                  <div>
                    <span className="text-gray-600">Tax Period:</span> {file.tax_period}
                  </div>
                </div>
                <div className="mt-2">
                  <h5 className="font-medium text-gray-900 mb-1">Form Matches:</h5>
                  <div className="space-y-1">
                    {file.form_matches.map((match, matchIndex) => (
                      <div key={matchIndex} className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${match.matched ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span className="text-sm">{match.form_name}: {match.matched ? 'Found' : 'Not Found'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderProjectionTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Tax Projection</h3>
      
      <Card>
        <CardHeader>
          <CardTitle>Projected Tax Calculations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {trtSummary.map((row, index) => {
              const agi = row['Estimated AGI'];
              const withholding = row['Total Withholding'];
              const seIncome = row['SE Income'];
              const estimatedTax = agi * 0.22; // Simplified tax calculation
              const seTax = seIncome * 0.153; // SE tax rate
              const totalTax = estimatedTax + seTax;
              const refund = withholding - totalTax;
              
              return (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Tax Year {row['Tax Year']}</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <p className="text-sm text-gray-600">Estimated AGI</p>
                      <p className="text-lg font-bold text-blue-600">{formatCurrency(agi)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-600">Total Withholding</p>
                      <p className="text-lg font-bold text-green-600">{formatCurrency(withholding)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-600">Income Tax</p>
                      <p className="text-lg font-bold text-red-600">{formatCurrency(estimatedTax)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-600">SE Tax</p>
                      <p className="text-lg font-bold text-orange-600">{formatCurrency(seTax)}</p>
                    </div>
                  </div>
                  <div className="mt-4 text-center">
                    <p className="text-sm text-gray-600">Projected Refund/Owed</p>
                    <p className={`text-xl font-bold ${refund >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(Math.abs(refund))} {refund >= 0 ? 'Refund' : 'Owed'}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderEfficiencyTab = () => (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Tax Efficiency Analysis</h1>
        <p className="mt-2 text-gray-600">
          Advanced tax analysis and service recommendations
        </p>
      </div>

      {!taxEfficiency ? (
        <EmptyState
          title="No Efficiency Data Available"
          description="Tax efficiency analysis requires processed TRT data."
        />
      ) : (
        <div className="space-y-6">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {taxEfficiency.effectiveTaxRate.toFixed(1)}%
                </p>
                <p className="text-sm text-gray-600">Effective Tax Rate</p>
                <p className="text-xs text-gray-500 mt-1">
                  {taxEfficiency.effectiveTaxRate < 15 ? '✅ Excellent' : '⚠️ Review'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-green-600">
                  {taxEfficiency.withholdingAdequacy.toFixed(0)}%
                </p>
                <p className="text-sm text-gray-600">Withholding Adequacy</p>
                <p className="text-xs text-gray-500 mt-1">
                  {taxEfficiency.withholdingAdequacy >= 90 ? '✅ Adequate' : '⚠️ Low'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-purple-600">
                  {taxEfficiency.taxOptimizationScore.toFixed(0)}
                </p>
                <p className="text-sm text-gray-600">Optimization Score</p>
                <p className="text-xs text-gray-500 mt-1">
                  {taxEfficiency.taxOptimizationScore >= 80 ? '✅ Good' : '📈 Opportunity'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-orange-600">
                  {taxEfficiency.yearOverYearGrowth.toFixed(1)}%
                </p>
                <p className="text-sm text-gray-600">Income Growth</p>
                <p className="text-xs text-gray-500 mt-1">
                  {taxEfficiency.yearOverYearGrowth > 10 ? '📈 Strong' : '📊 Stable'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Service Opportunities */}
          <Card>
            <CardHeader>
              <CardTitle>Service Opportunities</CardTitle>
              <CardDescription>
                Identified areas for tax planning and optimization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3">Detected Opportunities</h4>
                  <div className="space-y-2">
                    {taxEfficiency.serviceOpportunities.map((opportunity, index) => (
                      <div key={index} className="flex items-center space-x-2 p-2 bg-blue-50 rounded">
                        <span className="text-blue-500">💡</span>
                        <span className="text-sm text-blue-900">{opportunity}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-gray-900 mb-3">Recommendations</h4>
                  <div className="space-y-2">
                    {taxEfficiency.recommendations.map((rec, index) => (
                      <div key={index} className="flex items-center space-x-2 p-2 bg-green-50 rounded">
                        <span className="text-green-500">✅</span>
                        <span className="text-sm text-green-900">{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Detailed Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Tax Burden Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Effective Tax Rate</span>
                    <span className="font-semibold">{taxEfficiency.effectiveTaxRate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">SE Tax Burden</span>
                    <span className="font-semibold">{taxEfficiency.seTaxBurden.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Withholding Efficiency</span>
                    <span className="font-semibold">{taxEfficiency.withholdingEfficiency.toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Income Stability</span>
                    <span className="font-semibold">{taxEfficiency.incomeStabilityScore.toFixed(0)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Projection Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Projected Tax Liability</span>
                    <span className="font-semibold">{formatCurrency(taxEfficiency.projectedTaxLiability)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Current Withholding</span>
                    <span className="font-semibold">{formatCurrency(trtSummary.find(s => s['Tax Year'] === '2023')?.['Total Withholding'] || 0)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Shortfall/Surplus</span>
                    <span className={`font-semibold ${taxEfficiency.projectedTaxLiability > (trtSummary.find(s => s['Tax Year'] === '2023')?.['Total Withholding'] || 0) ? 'text-red-600' : 'text-green-600'}`}>
                      {formatCurrency(taxEfficiency.projectedTaxLiability - (trtSummary.find(s => s['Tax Year'] === '2023')?.['Total Withholding'] || 0))}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Year-over-Year Growth</span>
                    <span className="font-semibold">{taxEfficiency.yearOverYearGrowth.toFixed(1)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Action Items */}
          <Card>
            <CardHeader>
              <CardTitle>Recommended Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {taxEfficiency.withholdingAdequacy < 90 && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                    <h4 className="font-semibold text-yellow-900 mb-1">⚠️ Withholding Adjustment Needed</h4>
                    <p className="text-sm text-yellow-800">
                      Current withholding may be insufficient. Consider increasing W-4 withholding or making quarterly estimated payments.
                    </p>
                  </div>
                )}
                
                {taxEfficiency.seTaxBurden > 0 && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                    <h4 className="font-semibold text-blue-900 mb-1">💼 Self-Employment Planning</h4>
                    <p className="text-sm text-blue-800">
                      Self-employment income detected. Review quarterly payment requirements and potential business deductions.
                    </p>
                  </div>
                )}

                {taxEfficiency.yearOverYearGrowth > 10 && (
                  <div className="p-3 bg-green-50 border border-green-200 rounded">
                    <h4 className="font-semibold text-green-900 mb-1">📈 Income Growth Planning</h4>
                    <p className="text-sm text-green-800">
                      Strong income growth detected. Consider tax planning strategies for managing increased tax liability.
                    </p>
                  </div>
                )}

                {taxEfficiency.taxOptimizationScore < 80 && (
                  <div className="p-3 bg-purple-50 border border-purple-200 rounded">
                    <h4 className="font-semibold text-purple-900 mb-1">🎯 Tax Optimization Opportunity</h4>
                    <p className="text-sm text-purple-800">
                      Tax optimization score indicates room for improvement. Review deductions, credits, and filing strategies.
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

  const renderJsonTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">JSON Data</h3>
      
      <Card>
        <CardHeader>
          <CardTitle>TRT Data</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-900 text-green-200 rounded p-4 text-xs overflow-x-auto">
            {JSON.stringify(trtData, null, 2)}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Summary Data</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-900 text-green-200 rounded p-4 text-xs overflow-x-auto">
            {JSON.stringify(trtSummary, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );

  const renderMatchingTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Form Matching</h3>
      
      <Card>
        <CardHeader>
          <CardTitle>Form Pattern Matching Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {formMatching.map((file, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-3">{file.filename}</h4>
                <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                  <div>
                    <span className="text-gray-600">Owner:</span> {file.owner}
                  </div>
                  <div>
                    <span className="text-gray-600">SSN:</span> {file.ssn}
                  </div>
                  <div>
                    <span className="text-gray-600">Tax Period:</span> {file.tax_period}
                  </div>
                </div>
                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Pattern Matches:</h5>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {file.form_matches.map((match, matchIndex) => (
                      <div key={matchIndex} className={`p-2 rounded text-sm ${
                        match.matched ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {match.form_name}: {match.matched ? '✓' : '✗'}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderLogsTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Processing Logs</h3>
      
      <Card>
        <CardHeader>
          <CardTitle>Extraction Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-900 text-green-200 rounded p-4 text-xs overflow-x-auto whitespace-pre-wrap">
            {logs || 'No logs available'}
          </pre>
        </CardContent>
      </Card>
    </div>
  );

  if (isLoading) {
    return <LoadingSpinner message="Loading TRT Parser data..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">TRT Parser</h1>
        <p className="mt-2 text-gray-600">
          Tax Return Transcript parsing and analysis
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'summary', label: '📊 Summary', icon: '📊' },
            { id: 'critical', label: '🚨 Critical Issues', icon: '🚨' },
            { id: 'projection', label: '📈 Tax Projection', icon: '📈' },
            { id: 'efficiency', label: '🎯 Tax Efficiency', icon: '🎯' },
            { id: 'json', label: '🔧 JSON Data', icon: '🔧' },
            { id: 'matching', label: '📋 Form Matching', icon: '📋' },
            { id: 'logs', label: '📝 Logs', icon: '📝' }
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
              {tab.icon} {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'summary' && renderSummaryTab()}
      {activeTab === 'critical' && renderCriticalTab()}
      {activeTab === 'projection' && renderProjectionTab()}
      {activeTab === 'efficiency' && renderEfficiencyTab()}
      {activeTab === 'json' && renderJsonTab()}
      {activeTab === 'matching' && renderMatchingTab()}
      {activeTab === 'logs' && renderLogsTab()}
    </div>
  );
} 