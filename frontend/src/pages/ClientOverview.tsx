import React from 'react';

export default function ClientOverview() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold mb-4">Client Overview</h1>
      {/* Transcript Upload/Selection */}
      <div className="bg-white p-6 rounded shadow border space-y-4">
        <h2 className="text-xl font-semibold mb-2">Transcript Upload</h2>
        <input type="file" className="mb-2" />
        <button className="bg-blue-600 text-white px-4 py-2 rounded">Upload</button>
      </div>
      {/* Situation Overview */}
      <div className="bg-white p-6 rounded shadow border space-y-4">
        <h2 className="text-xl font-semibold mb-2">Situation Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-blue-50 p-4 rounded">
            <div className="text-gray-500">Total Income</div>
            <div className="text-2xl font-bold">$75,000</div>
          </div>
          <div className="bg-blue-50 p-4 rounded">
            <div className="text-gray-500">Tax Owed</div>
            <div className="text-2xl font-bold">$11,000</div>
          </div>
          <div className="bg-blue-50 p-4 rounded">
            <div className="text-gray-500">Refund</div>
            <div className="text-2xl font-bold">$1,000</div>
          </div>
        </div>
      </div>
      {/* Recommended Services */}
      <div className="bg-white p-6 rounded shadow border space-y-4">
        <h2 className="text-xl font-semibold mb-2">Recommended Services</h2>
        <ul className="space-y-2">
          <li className="border-b pb-2">
            <div className="font-semibold">Tax Return Filing</div>
            <div className="text-gray-600 text-sm">Recommended due to self-employment income.</div>
            <div className="text-blue-700 font-bold">$450</div>
          </li>
          <li className="border-b pb-2">
            <div className="font-semibold">Tax Resolution Services</div>
            <div className="text-gray-600 text-sm">Critical issues found in transcript.</div>
            <div className="text-blue-700 font-bold">$750</div>
          </li>
        </ul>
      </div>
      {/* Invoice Generation */}
      <div className="bg-white p-6 rounded shadow border space-y-4">
        <h2 className="text-xl font-semibold mb-2">Invoice</h2>
        <div className="flex items-center space-x-4">
          <div className="text-lg font-bold">Total: $1,200</div>
          <button className="bg-green-600 text-white px-4 py-2 rounded">Download PDF</button>
        </div>
      </div>
    </div>
  );
} 