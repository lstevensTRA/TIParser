import api from './api';

export const fetchComprehensiveAnalysis = async (caseId: string) => {
  const response = await api.get(`/analysis/${caseId}/comprehensive`);
  return response.data;
}; 