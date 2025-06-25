import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getWIAnalysis } from '../services/transcriptService';

export default function WIAnalysis() {
  const { caseId } = useParams<{ caseId: string }>();
  const { data, isLoading, error } = useQuery(
    ['wiAnalysis', caseId],
    () => getWIAnalysis(caseId!),
    { enabled: !!caseId }
  );

  if (!caseId) return <div>No case ID provided.</div>;
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div className="text-red-600">Error loading analysis</div>;

  const summary = data?.data.summary;

  return (
    <div className="max-w-3xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">WI Analysis for Case {caseId}</h1>
      {summary && (
        <div>
          <h2 className="text-xl font-semibold mb-2">Summary</h2>
          <div>Total Years: {summary.total_years}</div>
          <div>Total Forms: {summary.total_forms}</div>
          <div>Years Analyzed: {summary.years_analyzed.join(', ')}</div>
          <h3 className="mt-4 font-semibold">Overall Totals</h3>
          <pre className="bg-gray-100 p-2 rounded">{JSON.stringify(summary.overall_totals, null, 2)}</pre>
        </div>
      )}
    </div>
  );
} 