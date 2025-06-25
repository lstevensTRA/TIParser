import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Common/Card';
import { Button } from '../components/Common/Button';
import { DataTable, LoadingSpinner, EmptyState } from '../components/Common/DataDisplay';

interface ATForm {
  Form: string;
  Category: 'SE' | 'Non-SE' | 'Neither';
  Income: number;
  Withholding: number;
  Owner: 'TP' | 'S' | 'Joint';
  SourceFile: string;
  Label?: string;
  Payer?: string;
}

interface ATSummary {
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

interface ATFormMatching {
  filename: string;
  owner: string;
  ssn: string;
  tax_period: string;
  form_matches: Array<{
    form_name: string;
    matched: boolean;
  }>;
}

export default function ATParser() {
  const [activeTab, setActiveTab] = useState<'summary' | 'critical' | 'projection' | 'json' | 'matching' | 'logs'>('summary');
  const [summaryView, setSummaryView] = useState<'combined' | 'separated'>('combined');
  const [isLoading, setIsLoading] = useState(false);
  const [atData, setAtData] = useState<{ [year: string]: ATForm[] }>({});
  const [atSummary, setAtSummary] = useState<ATSummary[]>([]);
  const [formMatching, setFormMatching] = useState<ATFormMatching[]>([]);
  const [logs, setLogs] = useState<string>('');

  useEffect(() => {
    // Simulate loading AT data
    setTimeout(() => {
      const mockData = {
        '2023': [
          {
            Form: 'W-2',
            Category: 'Non-SE',
            Income: 75000,
            Withholding: 11000,
            Owner: 'TP',
            SourceFile: 'AT_2023_TP.pdf',
            Label: 'Advanced Tech Corp'
          },
          {
            Form: '1099-NEC',
            Category: 'SE',
            Income: 25000,
            Withholding: 0,
            Owner: 'TP',
            SourceFile: 'AT_2023_TP.pdf',
            Label: 'Consulting Services'
          },
          {
            Form: '1099-DIV',
            Category: 'Neither',
            Income: 500,
            Withholding: 0,
            Owner: 'TP',
            SourceFile: 'AT_2023_TP.pdf',
            Label: 'Investment Fund'
          }
        ],
        '2022': [
          {
            Form: 'W-2',
            Category: 'Non-SE',
            Income: 68000,
            Withholding: 9800,
            Owner: 'TP',
            SourceFile: 'AT_2022_TP.pdf',
            Label: 'Advanced Tech Corp'
          },
          {
            Form: '1099-NEC',
            Category: 'SE',
            Income: 18000,
            Withholding: 0,
            Owner: 'TP',
            SourceFile: 'AT_2022_TP.pdf',
            Label: 'Consulting Services'
          }
        ]
      };

      const mockSummary: ATSummary[] = [
        {
          'Tax Year': '2023',
          'Number of Forms': 3,
          'SE Income': 25000,
          'SE Withholding': 0,
          'Non-SE Income': 75000,
          'Non-SE Withholding': 11000,
          'Other Income': 500,
          'Other Withholding': 0,
          'Total Income': 100500,
          'Estimated AGI': 100500,
          'Total Withholding': 11000
        },
        {
          'Tax Year': '2022',
          'Number of Forms': 2,
          'SE Income': 18000,
          'SE Withholding': 0,
          'Non-SE Income': 68000,
          'Non-SE Withholding': 9800,
          'Other Income': 0,
          'Other Withholding': 0,
          'Total Income': 86000,
          'Estimated AGI': 86000,
          'Total Withholding': 9800
        }
      ];

      const mockFormMatching: ATFormMatching[] = [
        {
          filename: 'AT_2023_TP.pdf',
          owner: 'TP',
          ssn: '***-**-9012',
          tax_period: '2023',
          form_matches: [
            { form_name: 'W-2', matched: true },
            { form_name: '1099-NEC', matched: true },
            { form_name: '1099-DIV', matched: true },
            { form_name: '1099-INT', matched: false }
          ]
        }
      ];

      setAtData(mockData);
      setAtSummary(mockSummary);
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
    const yearForms = atData[year] || [];
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

      {atSummary.length > 0 ? (
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
                    {atSummary.map((row, index) => (
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
                {atSummary.map((row, index) => {
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
                {atSummary.map((row, index) => {
                  const year = row['Tax Year'];
                  const yearForms = atData[year] || [];
                  
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
                                }, {} as { [key: string]: ATForm[] })
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
          title="No AT Data"
          description="No AT data extracted. Please process a case ID first."
          icon="📝"
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
            {atSummary.map((row, index) => {
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

  const renderJsonTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">JSON Data</h3>
      
      <Card>
        <CardHeader>
          <CardTitle>AT Data</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-900 text-green-200 rounded p-4 text-xs overflow-x-auto">
            {JSON.stringify(atData, null, 2)}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Summary Data</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-900 text-green-200 rounded p-4 text-xs overflow-x-auto">
            {JSON.stringify(atSummary, null, 2)}
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
    return <LoadingSpinner message="Loading AT Parser data..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">AT Parser</h1>
        <p className="mt-2 text-gray-600">
          Account Transcript parsing and analysis
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'summary', label: 'Summary', icon: '📊' },
            { id: 'critical', label: 'Critical Issues', icon: '⚠️' },
            { id: 'projection', label: 'Tax Projection', icon: '💰' },
            { id: 'json', label: 'JSON', icon: '📄' },
            { id: 'matching', label: 'Form Matching', icon: '🔍' },
            { id: 'logs', label: 'Logs', icon: '📝' }
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
      {activeTab === 'json' && renderJsonTab()}
      {activeTab === 'matching' && renderMatchingTab()}
      {activeTab === 'logs' && renderLogsTab()}
    </div>
  );
} 