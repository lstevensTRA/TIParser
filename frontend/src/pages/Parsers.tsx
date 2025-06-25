import React, { useState } from 'react';
import WIParser from './WIParser';
import ATParser from './ATParser';
import ROAParser from './ROAParser';
import TRTParser from './TRTParser';

const parserTabs = [
  { label: 'WI Parser', component: <WIParser /> },
  { label: 'AT Parser', component: <ATParser /> },
  { label: 'ROA Parser', component: <ROAParser /> },
  { label: 'TRT Parser', component: <TRTParser /> },
];

export default function Parsers() {
  const [activeTab, setActiveTab] = useState(0);
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex space-x-8" aria-label="Tabs">
          {parserTabs.map((tab, idx) => (
            <button
              key={tab.label}
              onClick={() => setActiveTab(idx)}
              className={`px-4 py-2 text-base font-medium border-b-2 transition-colors duration-150 focus:outline-none ${
                activeTab === idx
                  ? 'border-blue-600 text-blue-700 bg-blue-50'
                  : 'border-transparent text-gray-600 hover:text-blue-700 hover:bg-blue-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      <div>
        {parserTabs[activeTab].component}
      </div>
    </div>
  );
} 