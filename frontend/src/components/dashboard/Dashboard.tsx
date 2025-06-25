import React, { useState } from 'react';
import { fetchComprehensiveAnalysis } from '../../services/analysisService';

const Dashboard: React.FC = () => {
  const [caseId, setCaseId] = useState('');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchComprehensiveAnalysis(caseId);
      setData(result);
    } catch (err: any) {
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <h2 className="text-3xl font-bold mb-4">TI Parser Dashboard</h2>
      <div className="bg-white rounded-lg shadow p-6 max-w-md mx-auto">
        <input
          type="text"
          className="input-field mb-2"
          placeholder="Enter Case ID"
          value={caseId}
          onChange={e => setCaseId(e.target.value)}
        />
        <button
          className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700 transition"
          disabled={!caseId || loading}
          onClick={handleFetch}
        >
          {loading ? 'Loading...' : 'Fetch & Analyze'}
        </button>
        {error && <div className="text-red-600 mt-2">{error}</div>}
      </div>
      {data && (
        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <pre className="text-xs overflow-x-auto">{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default Dashboard; 