import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Common/Card';
import { Button } from '../components/Common/Button';
import { analysisAPI } from '../services/api';

interface TaxSummary {
  totalIncome: number;
  totalWithholding: number;
  totalTax: number;
  refund: number;
  balance: number;
  effectiveTaxRate: number;
  withholdingRate: number;
}

interface Recommendation {
  id: string;
  category: 'tax' | 'filing' | 'documentation' | 'compliance';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action: string;
}

interface ComparisonResult {
  document1: string;
  document2: string;
  differences: {
    field: string;
    value1: any;
    value2: any;
    type: 'mismatch' | 'missing' | 'additional';
  }[];
  summary: string;
}

export default function Analysis() {
  const [activeTab, setActiveTab] = useState<'summary' | 'comparison' | 'recommendations'>('summary');
  const [isLoading, setIsLoading] = useState(false);
  const [taxSummary, setTaxSummary] = useState<TaxSummary | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [selectedDocuments, setSelectedDocuments] = useState<{ doc1: string; doc2: string }>({
    doc1: '',
    doc2: ''
  });

  useEffect(() => {
    loadTaxSummary();
    loadRecommendations();
  }, []);

  const loadTaxSummary = async () => {
    setIsLoading(true);
    try {
      const summary = await analysisAPI.getTaxSummary();
      setTaxSummary(summary);
    } catch (error) {
      console.error('Failed to load tax summary:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadRecommendations = async () => {
    try {
      const recs = await analysisAPI.getRecommendations({});
      setRecommendations(recs);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  };

  const handleCompareDocuments = async () => {
    if (!selectedDocuments.doc1 || !selectedDocuments.doc2) return;
    
    setIsLoading(true);
    try {
      const result = await analysisAPI.compareDocuments({
        document1: selectedDocuments.doc1,
        document2: selectedDocuments.doc2
      });
      setComparisonResult(result);
    } catch (error) {
      console.error('Failed to compare documents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'tax': return '💰';
      case 'filing': return '📋';
      case 'documentation': return '📄';
      case 'compliance': return '⚠️';
      default: return '📊';
    }
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">📊 Comprehensive Analysis</h1>
        <p className="mt-2 text-gray-600">
          Generate comprehensive tax analysis and recommendations
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'summary', label: 'Tax Summary', icon: '📊' },
            { id: 'comparison', label: 'Document Comparison', icon: '🔍' },
            { id: 'recommendations', label: 'Recommendations', icon: '💡' }
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
      {activeTab === 'summary' && (
        <div className="space-y-6">
          {isLoading ? (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading tax summary...</p>
                </div>
              </CardContent>
            </Card>
          ) : taxSummary ? (
            <>
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                  <CardContent className="p-6">
                    <div className="text-center">
                      <p className="text-sm font-medium text-gray-500">Total Income</p>
                      <p className="text-2xl font-bold text-green-600">
                        {formatCurrency(taxSummary.totalIncome)}
                      </p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="text-center">
                      <p className="text-sm font-medium text-gray-500">Total Withholding</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {formatCurrency(taxSummary.totalWithholding)}
                      </p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="text-center">
                      <p className="text-sm font-medium text-gray-500">Total Tax</p>
                      <p className="text-2xl font-bold text-red-600">
                        {formatCurrency(taxSummary.totalTax)}
                      </p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="text-center">
                      <p className="text-sm font-medium text-gray-500">Refund/Balance</p>
                      <p className={`text-2xl font-bold ${taxSummary.refund > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(taxSummary.refund)}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Detailed Analysis */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Tax Rates Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Effective Tax Rate</span>
                        <span className="font-semibold">{formatPercentage(taxSummary.effectiveTaxRate)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Withholding Rate</span>
                        <span className="font-semibold">{formatPercentage(taxSummary.withholdingRate)}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${taxSummary.effectiveTaxRate * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Cash Flow Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Income vs Tax</span>
                        <span className={`font-semibold ${taxSummary.totalIncome > taxSummary.totalTax ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(taxSummary.totalIncome - taxSummary.totalTax)}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Withholding vs Tax</span>
                        <span className={`font-semibold ${taxSummary.totalWithholding > taxSummary.totalTax ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(taxSummary.totalWithholding - taxSummary.totalTax)}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-gray-600">No tax summary data available</p>
                <Button onClick={loadTaxSummary} className="mt-4">
                  Load Tax Summary
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'comparison' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Document Comparison</CardTitle>
              <CardDescription>
                Compare two documents to identify differences and discrepancies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      First Document
                    </label>
                    <select
                      value={selectedDocuments.doc1}
                      onChange={(e) => setSelectedDocuments(prev => ({ ...prev, doc1: e.target.value }))}
                      className="input-field w-full"
                    >
                      <option value="">Select document...</option>
                      <option value="wi">Wage & Income (W-2)</option>
                      <option value="at">Account Transcript</option>
                      <option value="roa">Record of Account</option>
                      <option value="trt">Tax Return Transcript</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Second Document
                    </label>
                    <select
                      value={selectedDocuments.doc2}
                      onChange={(e) => setSelectedDocuments(prev => ({ ...prev, doc2: e.target.value }))}
                      className="input-field w-full"
                    >
                      <option value="">Select document...</option>
                      <option value="wi">Wage & Income (W-2)</option>
                      <option value="at">Account Transcript</option>
                      <option value="roa">Record of Account</option>
                      <option value="trt">Tax Return Transcript</option>
                    </select>
                  </div>
                </div>
                <Button 
                  onClick={handleCompareDocuments}
                  disabled={!selectedDocuments.doc1 || !selectedDocuments.doc2 || isLoading}
                  className="w-full"
                >
                  {isLoading ? 'Comparing...' : 'Compare Documents'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {comparisonResult && (
            <Card>
              <CardHeader>
                <CardTitle>Comparison Results</CardTitle>
                <CardDescription>
                  {comparisonResult.summary}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {comparisonResult.differences.length > 0 ? (
                  <div className="space-y-3">
                    {comparisonResult.differences.map((diff, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{diff.field}</p>
                          <div className="flex space-x-4 text-sm text-gray-600">
                            <span>Doc 1: {diff.value1 || 'N/A'}</span>
                            <span>Doc 2: {diff.value2 || 'N/A'}</span>
                          </div>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          diff.type === 'mismatch' ? 'bg-red-100 text-red-800' :
                          diff.type === 'missing' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {diff.type}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-gray-600 py-4">
                    No differences found between the selected documents.
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'recommendations' && (
        <div className="space-y-6">
          {recommendations.length > 0 ? (
            <div className="space-y-4">
              {recommendations.map((rec) => (
                <Card key={rec.id}>
                  <CardContent className="p-6">
                    <div className="flex items-start space-x-4">
                      <div className="text-2xl">{getCategoryIcon(rec.category)}</div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">{rec.title}</h3>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(rec.priority)}`}>
                            {rec.priority}
                          </span>
                        </div>
                        <p className="text-gray-600 mb-3">{rec.description}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-500 capitalize">{rec.category}</span>
                          <Button variant="outline" size="sm">
                            {rec.action}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-gray-600">No recommendations available</p>
                <Button onClick={loadRecommendations} className="mt-4">
                  Load Recommendations
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
} 