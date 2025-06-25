import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Common/Card';
import { Button } from '../components/Common/Button';
import { MetricCard, DataTable, LoadingSpinner, EmptyState } from '../components/Common/DataDisplay';

interface ClientInfo {
  id: string;
  name: string;
  ssn: string;
  filingStatus: string;
  address: {
    street: string;
    city: string;
    state: string;
    zip: string;
  };
  contact: {
    phone: string;
    email: string;
  };
  caseInfo: {
    caseId: string;
    status: 'active' | 'closed' | 'pending';
    assignedTo: string;
    createdAt: string;
    lastUpdated: string;
  };
  documents: {
    wi: { count: number; lastUploaded: string };
    at: { count: number; lastUploaded: string };
    roa: { count: number; lastUploaded: string };
    trt: { count: number; lastUploaded: string };
  };
  financialSummary: {
    totalIncome: number;
    totalWithholding: number;
    totalTax: number;
    refund: number;
    balance: number;
  };
}

export default function ClientProfile() {
  const [clientInfo, setClientInfo] = useState<ClientInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'documents' | 'financial' | 'expenses' | 'notes'>('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [filingMode, setFilingMode] = useState<'Single' | 'Married'>('Single');

  useEffect(() => {
    // Simulate loading client data
    setTimeout(() => {
      setClientInfo({
        id: 'CLI001',
        name: 'John A. Smith',
        ssn: '***-**-1234',
        filingStatus: 'Single',
        address: {
          street: '123 Main Street',
          city: 'Anytown',
          state: 'CA',
          zip: '90210'
        },
        contact: {
          phone: '(555) 123-4567',
          email: 'john.smith@email.com'
        },
        caseInfo: {
          caseId: 'CASE-2024-001',
          status: 'active',
          assignedTo: 'Sarah Johnson',
          createdAt: '2024-01-15',
          lastUpdated: '2024-01-20'
        },
        documents: {
          wi: { count: 3, lastUploaded: '2024-01-18' },
          at: { count: 1, lastUploaded: '2024-01-19' },
          roa: { count: 2, lastUploaded: '2024-01-17' },
          trt: { count: 1, lastUploaded: '2024-01-20' }
        },
        financialSummary: {
          totalIncome: 75000,
          totalWithholding: 12000,
          totalTax: 11000,
          refund: 1000,
          balance: 0
        }
      });
      setIsLoading(false);
    }, 1000);
  }, []);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'closed': return 'bg-gray-100 text-gray-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading client profile..." />;
  }

  if (!clientInfo) {
    return (
      <EmptyState
        title="Client Not Found"
        description="The requested client profile could not be loaded."
        action={{
          label: "Go Back",
          onClick: () => window.history.back()
        }}
        icon="👤"
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{clientInfo.name}</h1>
            <p className="mt-2 text-gray-600">
              Case ID: {clientInfo.caseInfo.caseId} • SSN: {clientInfo.ssn}
            </p>
          </div>
          <div className="flex space-x-3">
            <Button variant="outline" onClick={() => setIsEditing(!isEditing)}>
              {isEditing ? 'Cancel Edit' : 'Edit Profile'}
            </Button>
            <Button>Export Profile</Button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'documents', label: 'Documents' },
            { id: 'financial', label: 'Financial' },
            { id: 'expenses', label: 'Expenses' },
            { id: 'notes', label: 'Notes' }
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
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Income"
              value={formatCurrency(clientInfo.financialSummary.totalIncome)}
              color="green"
            />
            <MetricCard
              title="Total Withholding"
              value={formatCurrency(clientInfo.financialSummary.totalWithholding)}
              color="blue"
            />
            <MetricCard
              title="Total Tax"
              value={formatCurrency(clientInfo.financialSummary.totalTax)}
              color="red"
            />
            <MetricCard
              title="Refund"
              value={formatCurrency(clientInfo.financialSummary.refund)}
              color="green"
            />
          </div>

          {/* Client Information */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Full Name</label>
                    <p className="text-lg font-semibold">{clientInfo.name}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">SSN</label>
                    <p className="text-lg font-mono">{clientInfo.ssn}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Filing Status</label>
                    <p className="text-lg">{clientInfo.filingStatus}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Contact Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Phone</label>
                    <p className="text-lg">{clientInfo.contact.phone}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Email</label>
                    <p className="text-lg">{clientInfo.contact.email}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Address</label>
                    <p className="text-lg">
                      {clientInfo.address.street}<br />
                      {clientInfo.address.city}, {clientInfo.address.state} {clientInfo.address.zip}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Case Information */}
          <Card>
            <CardHeader>
              <CardTitle>Case Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Case ID</label>
                  <p className="text-lg font-semibold">{clientInfo.caseInfo.caseId}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Status</label>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(clientInfo.caseInfo.status)}`}>
                    {clientInfo.caseInfo.status}
                  </span>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Assigned To</label>
                  <p className="text-lg">{clientInfo.caseInfo.assignedTo}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Created</label>
                  <p className="text-lg">{formatDate(clientInfo.caseInfo.createdAt)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'documents' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Document Summary</CardTitle>
              <CardDescription>
                Overview of all uploaded documents for this client
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-700">Wage & Income</p>
                  <p className="text-2xl font-bold text-blue-600">{clientInfo.documents.wi.count}</p>
                  <p className="text-xs text-gray-500">Last: {formatDate(clientInfo.documents.wi.lastUploaded)}</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-700">Account Transcript</p>
                  <p className="text-2xl font-bold text-green-600">{clientInfo.documents.at.count}</p>
                  <p className="text-xs text-gray-500">Last: {formatDate(clientInfo.documents.at.lastUploaded)}</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-700">Record of Account</p>
                  <p className="text-2xl font-bold text-purple-600">{clientInfo.documents.roa.count}</p>
                  <p className="text-xs text-gray-500">Last: {formatDate(clientInfo.documents.roa.lastUploaded)}</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-700">Tax Return Transcript</p>
                  <p className="text-2xl font-bold text-red-600">{clientInfo.documents.trt.count}</p>
                  <p className="text-xs text-gray-500">Last: {formatDate(clientInfo.documents.trt.lastUploaded)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <DataTable
            title="Document History"
            headers={['Document Type', 'Upload Date', 'Status', 'Actions']}
            data={[
              ['Wage & Income (W-2)', '2024-01-18', 'Processed', 'View'],
              ['Account Transcript', '2024-01-19', 'Processed', 'View'],
              ['Record of Account', '2024-01-17', 'Processed', 'View'],
              ['Tax Return Transcript', '2024-01-20', 'Processing', 'View']
            ]}
          />
        </div>
      )}

      {activeTab === 'financial' && (
        <div className="space-y-6">
          {/* Financial Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Income"
              value={formatCurrency(clientInfo.financialSummary.totalIncome)}
              color="green"
              size="lg"
            />
            <MetricCard
              title="Total Withholding"
              value={formatCurrency(clientInfo.financialSummary.totalWithholding)}
              color="blue"
              size="lg"
            />
            <MetricCard
              title="Total Tax"
              value={formatCurrency(clientInfo.financialSummary.totalTax)}
              color="red"
              size="lg"
            />
            <MetricCard
              title="Refund"
              value={formatCurrency(clientInfo.financialSummary.refund)}
              color="green"
              size="lg"
            />
          </div>

          {/* Financial Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Tax Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Effective Tax Rate</span>
                    <span className="font-semibold">
                      {((clientInfo.financialSummary.totalTax / clientInfo.financialSummary.totalIncome) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Withholding Rate</span>
                    <span className="font-semibold">
                      {((clientInfo.financialSummary.totalWithholding / clientInfo.financialSummary.totalIncome) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Net Income</span>
                    <span className="font-semibold text-green-600">
                      {formatCurrency(clientInfo.financialSummary.totalIncome - clientInfo.financialSummary.totalTax)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cash Flow</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Income</span>
                    <span className="font-semibold text-green-600">
                      +{formatCurrency(clientInfo.financialSummary.totalIncome)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Tax Withholding</span>
                    <span className="font-semibold text-red-600">
                      -{formatCurrency(clientInfo.financialSummary.totalWithholding)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Tax Liability</span>
                    <span className="font-semibold text-red-600">
                      -{formatCurrency(clientInfo.financialSummary.totalTax)}
                    </span>
                  </div>
                  <hr />
                  <div className="flex justify-between items-center font-bold">
                    <span className="text-gray-900">Net Result</span>
                    <span className={`font-bold ${clientInfo.financialSummary.refund > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {clientInfo.financialSummary.refund > 0 ? '+' : ''}{formatCurrency(clientInfo.financialSummary.refund)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'expenses' && (
        <div className="space-y-6">
          <div className="flex items-center space-x-4 mb-4">
            <span className="font-semibold">Filing Status:</span>
            <button
              className={`px-4 py-1 rounded border ${filingMode === 'Single' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
              onClick={() => setFilingMode('Single')}
            >
              Single
            </button>
            <button
              className={`px-4 py-1 rounded border ${filingMode === 'Married' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
              onClick={() => setFilingMode('Married')}
            >
              Married
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border">
              <thead>
                <tr>
                  <th className="px-4 py-2 border">Field</th>
                  <th className="px-4 py-2 border">Taxpayer</th>
                  {filingMode === 'Married' && <th className="px-4 py-2 border">Spouse</th>}
                </tr>
              </thead>
              <tbody>
                {/* Income Section */}
                <tr className="bg-blue-50">
                  <td colSpan={filingMode === 'Married' ? 3 : 2} className="font-semibold px-4 py-2">Income</td>
                </tr>
                {[
                  'Wages',
                  'Interest',
                  'Dividends',
                  'Net Business Income',
                  'Net Rental Income',
                  'Pension / Social Security',
                  'Child Support',
                  'Alimony',
                  'Other Income',
                  'Total Income',
                ].map((field) => (
                  <tr key={field}>
                    <td className="border px-4 py-2">{field}</td>
                    <td className="border px-4 py-2">$0.00</td>
                    {filingMode === 'Married' && <td className="border px-4 py-2">$0.00</td>}
                  </tr>
                ))}
                {/* Vehicle Costs Section */}
                <tr className="bg-blue-50">
                  <td colSpan={filingMode === 'Married' ? 3 : 2} className="font-semibold px-4 py-2">Vehicle Costs</td>
                </tr>
                {['Ownership', 'Operating'].map((field) => (
                  <tr key={field}>
                    <td className="border px-4 py-2">{field}</td>
                    <td className="border px-4 py-2">$0.00</td>
                    {filingMode === 'Married' && <td className="border px-4 py-2">$0.00</td>}
                  </tr>
                ))}
                {/* Health Insurance Section */}
                <tr className="bg-blue-50">
                  <td colSpan={filingMode === 'Married' ? 3 : 2} className="font-semibold px-4 py-2">Health Insurance</td>
                </tr>
                {['Premiums', 'Out-of-Pocket Costs'].map((field) => (
                  <tr key={field}>
                    <td className="border px-4 py-2">{field}</td>
                    <td className="border px-4 py-2">$0.00</td>
                    {filingMode === 'Married' && <td className="border px-4 py-2">$0.00</td>}
                  </tr>
                ))}
                {/* Court Ordered Payments Section */}
                <tr className="bg-blue-50">
                  <td colSpan={filingMode === 'Married' ? 3 : 2} className="font-semibold px-4 py-2">Court Ordered Payments</td>
                </tr>
                <tr>
                  <td className="border px-4 py-2">Payments</td>
                  <td className="border px-4 py-2">$0.00</td>
                  {filingMode === 'Married' && <td className="border px-4 py-2">$0.00</td>}
                </tr>
                {/* Child/Dependent Care Section */}
                <tr className="bg-blue-50">
                  <td colSpan={filingMode === 'Married' ? 3 : 2} className="font-semibold px-4 py-2">Child/Dependent Care</td>
                </tr>
                <tr>
                  <td className="border px-4 py-2">Care Expenses</td>
                  <td className="border px-4 py-2">$0.00</td>
                  {filingMode === 'Married' && <td className="border px-4 py-2">$0.00</td>}
                </tr>
                {/* Life Insurance Section */}
                <tr className="bg-blue-50">
                  <td colSpan={filingMode === 'Married' ? 3 : 2} className="font-semibold px-4 py-2">Life Insurance</td>
                </tr>
                <tr>
                  <td className="border px-4 py-2">Premiums</td>
                  <td className="border px-4 py-2">$0.00</td>
                  {filingMode === 'Married' && <td className="border px-4 py-2">$0.00</td>}
                </tr>
                {/* Taxes Section */}
                <tr className="bg-blue-50">
                  <td colSpan={filingMode === 'Married' ? 3 : 2} className="font-semibold px-4 py-2">Taxes</td>
                </tr>
                {['W-2 Taxes', '1099 Estimated Deposits'].map((field) => (
                  <tr key={field}>
                    <td className="border px-4 py-2">{field}</td>
                    <td className="border px-4 py-2">$0.00</td>
                    {filingMode === 'Married' && <td className="border px-4 py-2">$0.00</td>}
                  </tr>
                ))}
                {/* Other Debts Section */}
                <tr className="bg-blue-50">
                  <td colSpan={filingMode === 'Married' ? 3 : 2} className="font-semibold px-4 py-2">Other Secured Debts</td>
                </tr>
                <tr>
                  <td className="border px-4 py-2">Secured Debts</td>
                  <td className="border px-4 py-2">$0.00</td>
                  {filingMode === 'Married' && <td className="border px-4 py-2">$0.00</td>}
                </tr>
                {/* Summary Section */}
                <tr className="bg-blue-50">
                  <td colSpan={filingMode === 'Married' ? 3 : 2} className="font-semibold px-4 py-2">Summary</td>
                </tr>
                {['Total Living Expenses', 'Ability to Pay', 'Offer Amount'].map((field) => (
                  <tr key={field}>
                    <td className="border px-4 py-2">{field}</td>
                    <td className="border px-4 py-2">$0.00</td>
                    {filingMode === 'Married' && <td className="border px-4 py-2">$0.00</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'notes' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Case Notes</CardTitle>
              <CardDescription>
                Add and manage notes for this client case
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex space-x-3">
                  <textarea
                    className="flex-1 input-field"
                    rows={4}
                    placeholder="Add a new note..."
                  />
                  <Button>Add Note</Button>
                </div>
                
                <div className="space-y-3">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-gray-900">Initial client consultation completed</span>
                      <span className="text-xs text-gray-500">2024-01-15</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      Client provided all necessary documentation. Tax situation appears straightforward. 
                      Will proceed with analysis once all documents are processed.
                    </p>
                  </div>
                  
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-gray-900">Document processing completed</span>
                      <span className="text-xs text-gray-500">2024-01-20</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      All documents have been processed and analyzed. Client qualifies for standard deduction. 
                      No unusual items identified.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
} 