import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/Common/Card';

const dataSamples = [
  {
    key: 'wi',
    label: 'WI Parser',
    json: {
      "2023": [
        {
          "formName": "W-2",
          "payer": "Acme Corp",
          "income": 55000,
          "withholding": 8000,
          "category": "Non-SE",
          "owner": "TP"
        },
        {
          "formName": "1099-INT",
          "payer": "Big Bank",
          "income": 120,
          "withholding": 0,
          "category": "Neither",
          "owner": "TP"
        }
      ]
    }
  },
  {
    key: 'at',
    label: 'AT Parser',
    json: {
      "2023": {
        "transactions": [
          {
            "date": "2023-04-15",
            "code": "150",
            "description": "Return Filed",
            "amount": 0,
            "type": "debit"
          },
          {
            "date": "2023-06-01",
            "code": "806",
            "description": "Withholding Credit",
            "amount": 8000,
            "type": "credit"
          }
        ],
        "summary": {
          "totalCredits": 8000,
          "totalDebits": 0,
          "balance": 8000
        }
      }
    }
  },
  {
    key: 'comprehensive',
    label: 'Comprehensive Analysis',
    json: {
      "caseId": "CASE-2024-001",
      "clientInfo": {
        "name": "John A. Smith",
        "ssn": "***-**-1234",
        "filingStatus": "Single"
      },
      "documents": {
        "wi": true,
        "at": true,
        "roa": true,
        "trt": true
      },
      "summary": {
        "totalIncome": 75000,
        "totalWithholding": 12000,
        "totalTax": 11000,
        "refund": 1000,
        "balance": 0
      },
      "recommendations": [
        "Review withholding for next year.",
        "Consider estimated payments if self-employed."
      ],
      "processingTime": 1200
    }
  },
  {
    key: 'client',
    label: 'Client Profile',
    json: {
      "id": "CLI001",
      "name": "John A. Smith",
      "ssn": "***-**-1234",
      "filingStatus": "Single",
      "address": {
        "street": "123 Main Street",
        "city": "Anytown",
        "state": "CA",
        "zip": "90210"
      },
      "contact": {
        "phone": "(555) 123-4567",
        "email": "john.smith@email.com"
      },
      "caseInfo": {
        "caseId": "CASE-2024-001",
        "status": "active",
        "assignedTo": "Sarah Johnson",
        "createdAt": "2024-01-15",
        "lastUpdated": "2024-01-20"
      },
      "documents": {
        "wi": { "count": 3, "lastUploaded": "2024-01-18" },
        "at": { "count": 1, "lastUploaded": "2024-01-19" },
        "roa": { "count": 2, "lastUploaded": "2024-01-17" },
        "trt": { "count": 1, "lastUploaded": "2024-01-20" }
      },
      "financialSummary": {
        "totalIncome": 75000,
        "totalWithholding": 12000,
        "totalTax": 11000,
        "refund": 1000,
        "balance": 0
      }
    }
  },
  {
    key: 'comparison',
    label: 'Comparison',
    json: {
      "document1": {
        "type": "WI",
        "name": "Wage & Income 2023",
        "date": "2024-01-15"
      },
      "document2": {
        "type": "AT",
        "name": "Account Transcript 2023",
        "date": "2024-01-18"
      },
      "summary": {
        "totalFields": 25,
        "matchingFields": 18,
        "mismatchedFields": 4,
        "missingFields": 2,
        "additionalFields": 1
      },
      "differences": [
        {
          "field": "Total Income",
          "value1": "$75,000",
          "value2": "$72,500",
          "type": "mismatch",
          "category": "financial"
        },
        {
          "field": "Federal Withholding",
          "value1": "$12,000",
          "value2": "$11,500",
          "type": "mismatch",
          "category": "tax"
        }
      ],
      "recommendations": [
        "Verify income discrepancy with client",
        "Check withholding calculations"
      ]
    }
  }
];

export default function Data() {
  const [selected, setSelected] = useState('wi');
  const current = dataSamples.find(d => d.key === selected);

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Data Samples</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-6 mb-4">
            {dataSamples.map(d => (
              <label key={d.key} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="data-sample"
                  value={d.key}
                  checked={selected === d.key}
                  onChange={() => setSelected(d.key)}
                  className="form-radio text-blue-600"
                />
                <span>{d.label}</span>
              </label>
            ))}
          </div>
          <pre className="bg-gray-900 text-green-200 rounded p-4 text-xs overflow-x-auto">
            {JSON.stringify(current?.json, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
} 