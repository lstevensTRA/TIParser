import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Common/Card';
import { Button } from '../components/Common/Button';
import { LoadingSpinner, EmptyState } from '../components/Common/DataDisplay';

interface TaxSituation {
  clientName: string;
  caseId: string;
  taxYears: string[];
  totalIncome: number;
  effectiveTaxRate: number;
  withholdingAdequacy: number;
  seIncome: number;
  criticalIssues: number;
  priorityLevel: 'low' | 'medium' | 'high' | 'critical';
  lastUpdated: string;
}

interface ServiceRecommendation {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  estimatedHours: number;
  basePrice: number;
  urgency: 'immediate' | 'soon' | 'planning';
  category: 'filing' | 'amendment' | 'planning' | 'resolution';
}

interface ActionItem {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  dueDate?: string;
  status: 'pending' | 'in-progress' | 'completed';
  assignedTo?: string;
}

interface QuickMetrics {
  totalIncome: number;
  effectiveTaxRate: number;
  withholdingAdequacy: number;
  seTaxBurden: number;
  yearOverYearGrowth: number;
  taxOptimizationScore: number;
}

export default function Home() {
  const [isLoading, setIsLoading] = useState(true);
  const [taxSituation, setTaxSituation] = useState<TaxSituation | null>(null);
  const [serviceRecommendations, setServiceRecommendations] = useState<ServiceRecommendation[]>([]);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [quickMetrics, setQuickMetrics] = useState<QuickMetrics | null>(null);
  const [activeView, setActiveView] = useState<'overview' | 'services' | 'actions' | 'analysis'>('overview');

  useEffect(() => {
    // Simulate loading comprehensive client data
    setTimeout(() => {
      const mockTaxSituation: TaxSituation = {
        clientName: 'John Smith',
        caseId: 'CASE-2024-001',
        taxYears: ['2023', '2022', '2021'],
        totalIncome: 115800,
        effectiveTaxRate: 12.5,
        withholdingAdequacy: 85,
        seIncome: 30000,
        criticalIssues: 3,
        priorityLevel: 'high',
        lastUpdated: '2024-01-15'
      };

      const mockServices: ServiceRecommendation[] = [
        {
          id: 'tax-filing-2023',
          title: '2023 Tax Return Filing',
          description: 'Complete tax return preparation with SE income optimization',
          priority: 'high',
          estimatedHours: 3,
          basePrice: 450,
          urgency: 'immediate',
          category: 'filing'
        },
        {
          id: 'withholding-adjustment',
          title: 'Withholding Optimization',
          description: 'Adjust W-4 and implement quarterly payments for SE income',
          priority: 'medium',
          estimatedHours: 1.5,
          basePrice: 200,
          urgency: 'soon',
          category: 'planning'
        },
        {
          id: 'business-structure',
          title: 'Business Structure Analysis',
          description: 'Evaluate S-Corp election for $30K SE income',
          priority: 'medium',
          estimatedHours: 2,
          basePrice: 300,
          urgency: 'planning',
          category: 'planning'
        },
        {
          id: 'resolution-fee',
          title: 'Tax Resolution Services',
          description: 'Comprehensive tax situation analysis and resolution',
          priority: 'high',
          estimatedHours: 5,
          basePrice: 750,
          urgency: 'immediate',
          category: 'resolution'
        }
      ];

      const mockActions: ActionItem[] = [
        {
          id: 'gather-docs',
          title: 'Gather Missing Documents',
          description: 'Collect 1099-NEC forms and business expense records',
          priority: 'high',
          dueDate: '2024-01-25',
          status: 'pending',
          assignedTo: 'Client'
        },
        {
          id: 'adjust-withholding',
          title: 'Adjust W-4 Withholding',
          description: 'Update W-4 to increase withholding by $200/month',
          priority: 'medium',
          dueDate: '2024-02-01',
          status: 'pending',
          assignedTo: 'Client'
        },
        {
          id: 'quarterly-payments',
          title: 'Set Up Quarterly Payments',
          description: 'Establish quarterly estimated tax payments for SE income',
          priority: 'high',
          dueDate: '2024-04-15',
          status: 'pending',
          assignedTo: 'Tax Preparer'
        }
      ];

      const mockMetrics: QuickMetrics = {
        totalIncome: 115800,
        effectiveTaxRate: 12.5,
        withholdingAdequacy: 85,
        seTaxBurden: 15.3,
        yearOverYearGrowth: 14.6,
        taxOptimizationScore: 72
      };

      setTaxSituation(mockTaxSituation);
      setServiceRecommendations(mockServices);
      setActionItems(mockActions);
      setQuickMetrics(mockMetrics);
      setIsLoading(false);
    }, 1500);
  }, []);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
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

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '📋';
      case 'low': return '✅';
      default: return '📄';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'immediate': return 'text-red-600';
      case 'soon': return 'text-orange-600';
      case 'planning': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const renderOverview = () => (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-blue-700 rounded-lg p-6 text-white">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold">{taxSituation?.clientName}</h1>
            <div className="mt-1 text-blue-100 text-sm">
              Case ID: {taxSituation?.caseId} &nbsp;|&nbsp; Last Updated: {taxSituation?.lastUpdated}
            </div>
          </div>
          <div>
            <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
              taxSituation?.priorityLevel === 'critical' ? 'bg-red-100 text-red-700' :
              taxSituation?.priorityLevel === 'high' ? 'bg-yellow-100 text-yellow-800' :
              taxSituation?.priorityLevel === 'medium' ? 'bg-blue-100 text-blue-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {taxSituation?.priorityLevel?.toUpperCase()} PRIORITY
            </span>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-700">
              {formatCurrency(quickMetrics?.totalIncome || 0)}
            </p>
            <p className="text-sm text-gray-600">Total Income (2023)</p>
            <p className="text-xs text-gray-500 mt-1">
              {quickMetrics?.yearOverYearGrowth && quickMetrics.yearOverYearGrowth > 10 ? 'Growing' : 'Stable'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className={`text-2xl font-bold ${quickMetrics?.effectiveTaxRate && quickMetrics.effectiveTaxRate < 15 ? 'text-green-600' : 'text-orange-500'}`}> 
              {quickMetrics?.effectiveTaxRate?.toFixed(1)}%
            </p>
            <p className="text-sm text-gray-600">Effective Tax Rate</p>
            <p className="text-xs text-gray-500 mt-1">
              {quickMetrics?.effectiveTaxRate && quickMetrics.effectiveTaxRate < 15 ? 'Excellent' : 'Review'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className={`text-2xl font-bold ${quickMetrics?.withholdingAdequacy && quickMetrics.withholdingAdequacy >= 90 ? 'text-green-600' : 'text-orange-500'}`}> 
              {quickMetrics?.withholdingAdequacy?.toFixed(0)}%
            </p>
            <p className="text-sm text-gray-600">Withholding Adequacy</p>
            <p className="text-xs text-gray-500 mt-1">
              {quickMetrics?.withholdingAdequacy && quickMetrics.withholdingAdequacy >= 90 ? 'Adequate' : 'Low'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className={`text-2xl font-bold ${quickMetrics?.taxOptimizationScore && quickMetrics.taxOptimizationScore >= 80 ? 'text-purple-600' : 'text-orange-500'}`}> 
              {quickMetrics?.taxOptimizationScore?.toFixed(0)}
            </p>
            <p className="text-sm text-gray-600">Optimization Score</p>
            <p className="text-xs text-gray-500 mt-1">
              {quickMetrics?.taxOptimizationScore && quickMetrics.taxOptimizationScore >= 80 ? 'Good' : 'Opportunity'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Tax Situation Summary</CardTitle>
          <CardDescription>
            Comprehensive overview of client's tax position
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Key Findings</h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-blue-50 rounded">
                  <span className="text-sm text-blue-900">Self-Employment Income</span>
                  <span className="font-semibold text-blue-900">{formatCurrency(taxSituation?.seIncome || 0)}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-900">Critical Issues Found</span>
                  <span className="font-semibold text-gray-900">{taxSituation?.criticalIssues}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-900">Tax Years Analyzed</span>
                  <span className="font-semibold text-gray-900">{taxSituation?.taxYears?.join(', ')}</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Immediate Concerns</h4>
              <div className="space-y-2">
                {quickMetrics?.withholdingAdequacy && quickMetrics.withholdingAdequacy < 90 && (
                  <div className="p-2 bg-red-50 rounded text-red-800 text-sm">
                    Insufficient withholding detected
                  </div>
                )}
                {taxSituation?.seIncome && taxSituation.seIncome > 0 && (
                  <div className="p-2 bg-yellow-50 rounded text-yellow-800 text-sm">
                    Self-employment tax planning needed
                  </div>
                )}
                {quickMetrics?.yearOverYearGrowth && quickMetrics.yearOverYearGrowth > 10 && (
                  <div className="p-2 bg-blue-50 rounded text-blue-800 text-sm">
                    Strong income growth requires planning
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button 
          onClick={() => setActiveView('services')}
          className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold"
        >
          View Services
        </Button>
        <Button 
          onClick={() => setActiveView('actions')}
          className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold"
        >
          Action Items
        </Button>
        <Button 
          onClick={() => setActiveView('analysis')}
          className="w-full bg-purple-700 hover:bg-purple-800 text-white font-semibold"
        >
          Detailed Analysis
        </Button>
      </div>
    </div>
  );

  const renderServices = () => (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Service Recommendations</h1>
        <p className="mt-2 text-gray-600">
          Recommended services with pricing and urgency
        </p>
      </div>

      <div className="space-y-4">
        {serviceRecommendations.map((service) => (
          <Card key={service.id} className="border-l-4 border-l-blue-500">
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{service.title}</h3>
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getPriorityColor(service.priority)}`}>
                      {getPriorityIcon(service.priority)} {service.priority.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-gray-600 mb-3">{service.description}</p>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>⏱️ {service.estimatedHours} hours</span>
                    <span className={`${getUrgencyColor(service.urgency)}`}>
                      {service.urgency === 'immediate' ? '🚨 Immediate' : 
                       service.urgency === 'soon' ? '⏰ Soon' : '📅 Planning'}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(service.basePrice)}</p>
                  <Button className="mt-2 bg-blue-600 hover:bg-blue-700">
                    Add to Proposal
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Total Estimate */}
      <Card className="bg-gray-50">
        <CardContent className="p-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Total Estimated Services</h3>
              <p className="text-sm text-gray-600">
                {serviceRecommendations.length} services recommended
              </p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-gray-900">
                {formatCurrency(serviceRecommendations.reduce((sum, service) => sum + service.basePrice, 0))}
              </p>
              <p className="text-sm text-gray-600">
                {serviceRecommendations.reduce((sum, service) => sum + service.estimatedHours, 0)} total hours
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderActions = () => (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Action Items</h1>
        <p className="mt-2 text-gray-600">
          Tasks and next steps for client and tax preparer
        </p>
      </div>

      <div className="space-y-4">
        {actionItems.map((action) => (
          <Card key={action.id} className="border-l-4 border-l-green-500">
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{action.title}</h3>
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getPriorityColor(action.priority)}`}>
                      {getPriorityIcon(action.priority)} {action.priority.toUpperCase()}
                    </span>
                    {action.dueDate && (
                      <span className="text-xs text-gray-500">
                        Due: {action.dueDate}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-600 mb-3">{action.description}</p>
                  {action.assignedTo && (
                    <p className="text-sm text-gray-500">Assigned to: {action.assignedTo}</p>
                  )}
                </div>
                <div className="text-right">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    action.status === 'completed' ? 'bg-green-100 text-green-800' :
                    action.status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {action.status === 'completed' ? '✅ Completed' :
                     action.status === 'in-progress' ? '🔄 In Progress' : '⏳ Pending'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderAnalysis = () => (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Detailed Tax Analysis</h1>
        <p className="mt-2 text-gray-600">
          Comprehensive breakdown of tax situation and recommendations
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Income Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Income (2023)</span>
                <span className="font-semibold">{formatCurrency(quickMetrics?.totalIncome || 0)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Self-Employment Income</span>
                <span className="font-semibold">{formatCurrency(taxSituation?.seIncome || 0)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Year-over-Year Growth</span>
                <span className="font-semibold">{quickMetrics?.yearOverYearGrowth?.toFixed(1)}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tax Efficiency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Effective Tax Rate</span>
                <span className="font-semibold">{quickMetrics?.effectiveTaxRate?.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Withholding Adequacy</span>
                <span className="font-semibold">{quickMetrics?.withholdingAdequacy?.toFixed(0)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Tax Optimization Score</span>
                <span className="font-semibold">{quickMetrics?.taxOptimizationScore?.toFixed(0)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recommendations Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="p-3 bg-blue-50 rounded">
              <h4 className="font-semibold text-blue-900 mb-1">Immediate Actions Required</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• File 2023 tax return with SE income optimization</li>
                <li>• Adjust W-4 withholding to prevent underpayment</li>
                <li>• Set up quarterly estimated tax payments</li>
              </ul>
            </div>
            <div className="p-3 bg-green-50 rounded">
              <h4 className="font-semibold text-green-900 mb-1">Planning Opportunities</h4>
              <ul className="text-sm text-green-800 space-y-1">
                <li>• Evaluate S-Corp election for tax savings</li>
                <li>• Implement retirement plan contributions</li>
                <li>• Review business expense deductions</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  if (isLoading) {
    return <LoadingSpinner message="Loading client dashboard..." />;
  }

  if (!taxSituation) {
    return (
      <EmptyState
        title="No Client Data Available"
        description="Please select a client or process a case ID to view the dashboard."
        icon="👤"
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'services', label: 'Services' },
            { id: 'actions', label: 'Actions' },
            { id: 'analysis', label: 'Analysis' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeView === tab.id
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
      {activeView === 'overview' && renderOverview()}
      {activeView === 'services' && renderServices()}
      {activeView === 'actions' && renderActions()}
      {activeView === 'analysis' && renderAnalysis()}
    </div>
  );
} 