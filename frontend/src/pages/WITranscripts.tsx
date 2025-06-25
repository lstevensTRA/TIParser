import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getWITranscripts } from '../services/transcriptService';

export default function WITranscripts() {
  const [caseId, setCaseId] = useState('54820');
  const { data, isLoading, error } = useQuery(['wiTranscripts', caseId], () => getWITranscripts(caseId), {
    enabled: !!caseId,
  });

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">WI Transcripts</h1>
      <div className="mb-4">
        <label className="mr-2 font-semibold">Case ID:</label>
        <input
          value={caseId}
          onChange={e => setCaseId(e.target.value)}
          className="border px-2 py-1 rounded"
        />
      </div>
      {isLoading && <div>Loading...</div>}
      {error && <div className="text-red-600">Error loading transcripts</div>}
      {data && (
        <table className="min-w-full bg-white border">
          <thead>
            <tr>
              <th className="px-4 py-2 border">Filename</th>
              <th className="px-4 py-2 border">Owner</th>
              <th className="px-4 py-2 border">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.data.files.map(file => (
              <tr key={file.case_document_id}>
                <td className="border px-4 py-2">{file.filename}</td>
                <td className="border px-4 py-2">{file.owner}</td>
                <td className="border px-4 py-2">
                  <button className="bg-blue-600 text-white px-3 py-1 rounded">View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
} 