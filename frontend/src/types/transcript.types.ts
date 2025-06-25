export interface TranscriptFile {
  index: number;
  filename: string;
  case_document_id: number;
  owner: string;
}

export interface WITranscriptsResponse {
  case_id: string;
  transcript_type: string;
  total_files: number;
  files: TranscriptFile[];
} 