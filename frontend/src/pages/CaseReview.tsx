import React, { useState } from 'react';

const mockCases = [
  { id: 'CASE-2023-001', client: 'John Smith' },
  { id: 'CASE-2023-002', client: 'Jane Doe' },
];

const mockActual = {
  values: {
    'Total Income': 75000,
    'Tax Owed': 11000,
    'Refund': 1000,
  },
  services: ['Tax Return Filing', 'Tax Resolution Services'],
  invoice: 1200,
};

const mockSuggested = {
  values: {
    'Total Income': 75000,
    'Tax Owed': 12000,
    'Refund': 900,
  },
  services: ['Tax Return Filing'],
  invoice: 450,
};

export default function CaseReview() {
  const [selectedCase, setSelectedCase] = useState(mockCases[0].id);
  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold mb-4">Case Review</h1>
      {/* Case Selector */}
      <div className="bg-white p-6 rounded shadow border flex items-center space-x-4">
        <label className="font-semibold">Select Case:</label>
        <select
          value={selectedCase}
          onChange={e => setSelectedCase(e.target.value)}
          className="border px-2 py-1 rounded"
        >
          {mockCases.map(c => (
            <option key={c.id} value={c.id}>{c.client} ({c.id})</option>
          ))}
        </select>
      </div>
      {/* Side-by-side Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Actual (Human) */}
        <div className="bg-white p-6 rounded shadow border">
          <h2 className="text-xl font-semibold mb-4">Actual (Human)</h2>
          <div className="space-y-2">
            {Object.entries(mockActual.values).map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span>{k}</span>
                <span>{v}</span>
              </div>
            ))}
          </div>
          <div className="mt-4">
            <div className="font-semibold mb-1">Services</div>
            <ul className="list-disc ml-6 text-gray-700">
              {mockActual.services.map(s => <li key={s}>{s}</li>)}
            </ul>
          </div>
          <div className="mt-4 font-bold">Invoice: ${mockActual.invoice}</div>
        </div>
        {/* System Suggested (AI/Regex) */}
        <div className="bg-white p-6 rounded shadow border">
          <h2 className="text-xl font-semibold mb-4">System Suggested (AI/Regex)</h2>
          <div className="space-y-2">
            {Object.entries(mockSuggested.values).map(([k, v]) => (
              <div key={k} className={`flex justify-between ${mockActual.values[k] !== v ? 'bg-red-50' : ''}`}>
                <span>{k}</span>
                <span>{v}</span>
              </div>
            ))}
          </div>
          <div className="mt-4">
            <div className="font-semibold mb-1">Services</div>
            <ul className="list-disc ml-6 text-gray-700">
              {mockSuggested.services.map(s => <li key={s} className={mockActual.services.includes(s) ? '' : 'bg-yellow-100'}>{s}</li>)}
            </ul>
          </div>
          <div className={`mt-4 font-bold ${mockActual.invoice !== mockSuggested.invoice ? 'bg-red-100' : ''}`}>Invoice: ${mockSuggested.invoice}</div>
        </div>
      </div>
    </div>
  );
} 