import axios from 'axios';
import type { WITranscriptsResponse } from '../types/transcript.types';
import { paths } from '../types/openapi';

const API_BASE = import.meta.env.VITE_API_BASE;

type WIAnalysisResponse = paths['/wi/{case_id}']['get']['responses']['200']['content']['application/json'];

export const getWITranscripts = (caseId: string) =>
  axios.get<WITranscriptsResponse>(`${API_BASE}/transcripts/wi/${caseId}`);

export const getWIAnalysis = (caseId: string) =>
  axios.get<WIAnalysisResponse>(`${API_BASE}/wi/${caseId}`); 