export type {
  SecurityIssue,
  ProjectSummary,
  WorkflowData,
  MemoryData,
  AnalysisResponse,
  WorkflowResponse,
  MemoryResponse,
  MockResponse,
  ChatResponse,
  ChatSource,
  StatusResponse,
  UploadResponse,
} from './api';

/** Frontend display shape for issue cards */
export interface DisplayIssue {
  id: string;
  type: string;
  label: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  filePath: string;
  lineNumber: number;
  snippet?: string;
  explanation?: string;
  fix?: string;
}

/** Maps backend SecurityIssue → DisplayIssue */
export function toDisplayIssue(
  raw: import('./api').SecurityIssue,
  index: number
): DisplayIssue {
  return {
    id:          `${raw.file_path}:${raw.line_number}:${index}`,
    type:        raw.type,
    label:       raw.type_label || raw.type.replace(/_/g, ' '),
    severity:    raw.severity as DisplayIssue['severity'],
    filePath:    raw.file_path,
    lineNumber:  raw.line_number,
    snippet:     raw.code_snippet,
    explanation: raw.explanation,
    fix:         raw.fix_suggestion,
  };
}