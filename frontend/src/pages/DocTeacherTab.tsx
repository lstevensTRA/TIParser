import React, { useState } from 'react';

// Mock data for demonstration
const mockTranscripts = [
  {
    name: 'WI-2023-ClientA.txt',
    type: 'WI',
    content: `1. SE Income: 35000\n2. W-2 Income: 85000\n3. Total Income: 120000\n4. Withholding: 12500\n5. 1099-DIV: 800\n6. 1099-INT: 0`,
    parsed: {
      'SE Income': 35000,
      'W-2 Income': 85000,
      'Total Income': 120000,
      'Withholding': 12500,
      '1099-DIV': 800,
      // '1099-INT' is missing (simulate a miss)
    },
    expectedFields: [
      'SE Income',
      'W-2 Income',
      'Total Income',
      'Withholding',
      '1099-DIV',
      '1099-INT',
    ],
  },
  {
    name: 'AT-2022-ClientB.txt',
    type: 'AT',
    content: `1. SE Income: 42000\n2. W-2 Income: 90000\n3. Total Income: 132000\n4. Withholding: 15000\n5. 1099-DIV: 1200`,
    parsed: {
      'SE Income': 42000,
      'W-2 Income': 90000,
      'Total Income': 132000,
      'Withholding': 15000,
      '1099-DIV': 1200,
      // '1099-INT' is missing
    },
    expectedFields: [
      'SE Income',
      'W-2 Income',
      'Total Income',
      'Withholding',
      '1099-DIV',
      '1099-INT',
    ],
  },
];

const regexConfig = {
  'SE Income': 'SE Income: (\\d+)',
  'W-2 Income': 'W-2 Income: (\\d+)',
  'Total Income': 'Total Income: (\\d+)',
  'Withholding': 'Withholding: (\\d+)',
  '1099-DIV': '1099-DIV: (\\d+)',
  '1099-INT': '1099-INT: (\\d+)',
};

function generateRegexFromSelection(line: string, selected: string) {
  // Only replace the selected value in the actual line
  const isNumber = /^\d+$/.test(selected.trim());
  const escaped = selected.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const group = isNumber ? '(\\d+)' : '(.+?)';
  // Replace only the first occurrence of the selected value in the line
  return line.replace(new RegExp(escaped), group);
}

export default function DocTeacherTab() {
  const [selectedTranscriptIdx, setSelectedTranscriptIdx] = useState(0);
  const transcript = mockTranscripts[selectedTranscriptIdx];
  const [selectedField, setSelectedField] = useState(transcript.expectedFields[0]);
  const [regex, setRegex] = useState(regexConfig[selectedField]);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [selectedText, setSelectedText] = useState('');
  const [selectedLine, setSelectedLine] = useState('');
  const [highlightedLineIdx, setHighlightedLineIdx] = useState<number | null>(null);

  // Update regex when field or transcript changes
  React.useEffect(() => {
    setRegex(regexConfig[selectedField]);
    setTestResult(null);
  }, [selectedField, selectedTranscriptIdx]);

  // Simulate test
  const handleTest = () => {
    try {
      const re = new RegExp(regex);
      const match = transcript.content.match(re);
      setTestResult(match ? match[1] : 'No match');
    } catch (e) {
      setTestResult('Invalid regex');
    }
  };

  // Simulate save (would call backend in real app)
  const handleSave = () => {
    // POST /api/regex-update { field, regex }
    alert(`Saved regex for ${selectedField}: ${regex}`);
  };

  // Find missed fields
  const missedFields = transcript.expectedFields.filter(
    (field) => !(field in transcript.parsed)
  );

  // Handler for selection in transcript
  const handleTranscriptSelect = (e: React.SyntheticEvent<HTMLPreElement>) => {
    const selection = window.getSelection();
    if (selection && selection.toString()) {
      const selected = selection.toString();
      // Find the line and its index containing the selection using anchorNode
      let anchorNode = selection.anchorNode;
      while (anchorNode && anchorNode.nodeType !== 3) { // 3 = TEXT_NODE
        anchorNode = anchorNode.firstChild;
      }
      const transcriptLines = transcript.content.split('\n');
      let lineIdx = null;
      let line = '';
      // Fallback: find the first line containing the selection
      for (let i = 0; i < transcriptLines.length; i++) {
        if (transcriptLines[i].includes(selected)) {
          lineIdx = i;
          line = transcriptLines[i];
          break;
        }
      }
      setSelectedText(selected);
      setSelectedLine(line);
      setHighlightedLineIdx(lineIdx);
      // Generate regex and set it
      if (selected && line) {
        setRegex(generateRegexFromSelection(line, selected));
        setTestResult(null);
      }
    } else {
      setHighlightedLineIdx(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Transcript Selector */}
      <div className="flex items-center space-x-4">
        <label className="font-semibold">Select Transcript:</label>
        <select
          value={selectedTranscriptIdx}
          onChange={e => {
            setSelectedTranscriptIdx(Number(e.target.value));
            setSelectedField(mockTranscripts[Number(e.target.value)].expectedFields[0]);
            setHighlightedLineIdx(null);
          }}
          className="border px-2 py-1 rounded"
        >
          {mockTranscripts.map((t, idx) => (
            <option key={t.name} value={idx}>{t.name}</option>
          ))}
        </select>
      </div>
      {/* Side-by-side view */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Raw Transcript */}
        <div>
          <h2 className="font-bold mb-2">Raw Transcript</h2>
          <pre
            className="bg-gray-100 p-4 rounded h-96 overflow-auto text-sm border cursor-text"
            onMouseUp={handleTranscriptSelect}
            title="Select a value to teach the parser"
            style={{ whiteSpace: 'pre-wrap' }}
          >
            {transcript.content.split('\n').map((line, idx) => (
              <div
                key={idx}
                style={{
                  background: highlightedLineIdx === idx ? '#DBEAFE' : undefined,
                  display: 'block',
                  width: '100%',
                }}
              >
                {line}
              </div>
            ))}
          </pre>
          <div className="text-xs text-gray-500 mt-2">
            Tip: Highlight the value you want to extract for the selected field. The regex will be generated automatically.
          </div>
        </div>
        {/* Parsed Output */}
        <div>
          <h2 className="font-bold mb-2">Parsed Output</h2>
          <table className="min-w-full bg-white border">
            <thead>
              <tr>
                <th className="px-4 py-2 border">Field</th>
                <th className="px-4 py-2 border">Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(transcript.parsed).map(([field, value]) => (
                <tr key={field}>
                  <td className="border px-4 py-2">{field}</td>
                  <td className="border px-4 py-2">{value}</td>
                </tr>
              ))}
              {/* Show missed fields */}
              {missedFields.map((missed) => (
                <tr key={missed} className="bg-red-50">
                  <td className="border px-4 py-2 text-red-700">{missed}</td>
                  <td className="border px-4 py-2 text-red-700">Missed</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {/* Regex Editor */}
      <div className="flex flex-wrap items-center gap-4 mt-6">
        <label className="font-semibold">Field:</label>
        <select
          value={selectedField}
          onChange={e => setSelectedField(e.target.value)}
          className="border px-2 py-1 rounded"
        >
          {transcript.expectedFields.map(field => (
            <option key={field} value={field}>{field}</option>
          ))}
        </select>
        <label className="font-semibold">Regex:</label>
        <input
          value={regex}
          onChange={e => setRegex(e.target.value)}
          className="border px-2 py-1 rounded w-96"
        />
        <button onClick={handleTest} className="bg-blue-600 text-white px-4 py-1 rounded">Test</button>
        <button onClick={handleSave} className="bg-green-600 text-white px-4 py-1 rounded">Save</button>
        {testResult && (
          <span className="ml-4">
            <b>Test Result:</b> {testResult}
          </span>
        )}
      </div>
    </div>
  );
} 