import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './Card';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'green' | 'blue' | 'red' | 'purple' | 'gray';
  size?: 'sm' | 'md' | 'lg';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  color = 'gray',
  size = 'md'
}) => {
  const colorClasses = {
    green: 'text-green-600',
    blue: 'text-blue-600',
    red: 'text-red-600',
    purple: 'text-purple-600',
    gray: 'text-gray-600'
  };

  const sizeClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl'
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-center">
          <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
          <p className={`font-bold ${colorClasses[color]} ${sizeClasses[size]}`}>
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center justify-center mt-2">
              <span className={`text-xs font-medium ${
                trend.isPositive ? 'text-green-600' : 'text-red-600'
              }`}>
                {trend.isPositive ? '↗' : '↘'} {Math.abs(trend.value)}%
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

interface ProgressBarProps {
  label: string;
  value: number;
  max: number;
  color?: 'blue' | 'green' | 'red' | 'yellow';
  showPercentage?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  label,
  value,
  max,
  color = 'blue',
  showPercentage = true
}) => {
  const percentage = (value / max) * 100;
  
  const colorClasses = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    red: 'bg-red-600',
    yellow: 'bg-yellow-600'
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        {showPercentage && (
          <span className="text-sm text-gray-500">{percentage.toFixed(1)}%</span>
        )}
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full ${colorClasses[color]}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

interface ComparisonTableProps {
  title: string;
  data: Array<{
    field: string;
    value1: any;
    value2: any;
    type: 'match' | 'mismatch' | 'missing' | 'additional';
  }>;
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({ title, data }) => {
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'mismatch': return 'bg-red-100 text-red-800';
      case 'missing': return 'bg-yellow-100 text-yellow-800';
      case 'additional': return 'bg-blue-100 text-blue-800';
      default: return 'bg-green-100 text-green-800';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {data.map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <p className="font-medium text-gray-900">{item.field}</p>
                <div className="flex space-x-4 text-sm text-gray-600">
                  <span>Value 1: {item.value1 || 'N/A'}</span>
                  <span>Value 2: {item.value2 || 'N/A'}</span>
                </div>
              </div>
              <span className={`px-2 py-1 rounded text-xs font-medium ${getTypeColor(item.type)}`}>
                {item.type}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

interface RecommendationCardProps {
  recommendation: {
    id: string;
    category: 'tax' | 'filing' | 'documentation' | 'compliance';
    priority: 'high' | 'medium' | 'low';
    title: string;
    description: string;
    action: string;
  };
  onAction?: (id: string) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ 
  recommendation, 
  onAction 
}) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'tax': return '💰';
      case 'filing': return '📋';
      case 'documentation': return '📄';
      case 'compliance': return '⚠️';
      default: return '📊';
    }
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start space-x-4">
          <div className="text-2xl">{getCategoryIcon(recommendation.category)}</div>
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">{recommendation.title}</h3>
              <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(recommendation.priority)}`}>
                {recommendation.priority}
              </span>
            </div>
            <p className="text-gray-600 mb-3">{recommendation.description}</p>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 capitalize">{recommendation.category}</span>
              {onAction && (
                <button
                  onClick={() => onAction(recommendation.id)}
                  className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                >
                  {recommendation.action}
                </button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

interface DataTableProps {
  title: string;
  headers: string[];
  data: any[][];
  emptyMessage?: string;
}

export const DataTable: React.FC<DataTableProps> = ({ 
  title, 
  headers, 
  data, 
  emptyMessage = "No data available" 
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {headers.map((header, index) => (
                    <th
                      key={index}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {row.map((cell, cellIndex) => (
                      <td
                        key={cellIndex}
                        className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                      >
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-600">{emptyMessage}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  message = "Loading...", 
  size = 'md' 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  return (
    <div className="flex items-center justify-center py-8">
      <div className="text-center">
        <div className={`animate-spin rounded-full border-b-2 border-blue-500 mx-auto ${sizeClasses[size]}`}></div>
        <p className="mt-2 text-gray-600">{message}</p>
      </div>
    </div>
  );
};

interface EmptyStateProps {
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  icon?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ 
  title, 
  description, 
  action, 
  icon = '📊' 
}) => {
  return (
    <Card>
      <CardContent className="text-center py-8">
        <div className="text-4xl mb-4">{icon}</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600 mb-4">{description}</p>
        {action && (
          <button
            onClick={action.onClick}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {action.label}
          </button>
        )}
      </CardContent>
    </Card>
  );
}; 