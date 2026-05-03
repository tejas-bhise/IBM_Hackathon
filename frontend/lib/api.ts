import axios, { AxiosInstance, AxiosError } from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api';

// ─── Response Types ────────────────────────────────────────────────────────────

export interface UploadResponse {
  success: boolean;
  project_id: string;
  message: string;
  total_files: number;
  project_name: string;
}

export interface StatusResponse {
  success: boolean;
  project_id: string;
  status: 'ingesting' | 'processing' | 'completed' | 'error';
  pipeline_step: number;
  total_steps: number;
  percent: number;
  current_step_name: string;
  error?: string;
  project_name?: string;
}

export interface SecurityIssue {
  type: string;
  type_label: string;
  title: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  severity_rank: number;
  file_path: string;
  line_number: number;
  code_snippet?: string;
  explanation?: string;
  fix_suggestion?: string;
  context?: string;
}

export interface ProjectSummary {
  project_type: string;
  description: string;
  tech_stack: string[];
  main_modules: string[];
  data_flow: string;
  architecture_type: string;
  api_endpoints: string[];
  entry_point: string;
  security_score: number;
  grade: string;
  total_issues: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

export interface WorkflowData {
  stage: string;
  stage_label: string;
  risk_level: string;
  risk: string;
  recommended_action: string;
  confidence: number;
  security_score: number;
  grade: string;
  total_issues: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  blockers: string[];
  ai_decision: Record<string, unknown>;
  role_views: Record<string, unknown>;
}

export interface MemoryData {
  ai_summary: string;
  recent_work: string[];
  active_areas: string[];
  development_phase: string;
  last_focus: string;
  has_git_history: boolean;
  total_commits_analyzed: number;
}

export interface AnalysisResponse {
  success: boolean;
  project_id: string;
  project_name: string;
  total_files_analyzed: number;
  summary: ProjectSummary;
  issues: SecurityIssue[];
  security_issues: SecurityIssue[];
  total_issues: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  security_score: number;
  grade: string;
  memory: MemoryData;
  mock_data: Record<string, unknown>;
  workflow: WorkflowData;
}

// GET /workflow/{id} → { success, project_id, workflow: WorkflowData }
export interface WorkflowResponse {
  success: boolean;
  project_id: string;
  workflow: WorkflowData;
}

// GET /memory/{id} → flat: { recent_work, features, security, refactors }
export interface MemoryResponse {
  recent_work: string[];
  features: string[];
  security: string[];
  refactors: string[];
}

export interface MockResponse {
  success: boolean;
  [key: string]: unknown;
}

export interface ChatSource {
  file: string;
  content: string;
  score?: number;
}

// POST /chat → { success, answer, reasoning, sources, role, mode, confidence, chunks_retrieved }
export interface ChatResponse {
  success: boolean;
  answer: string;
  reasoning: string;
  sources: ChatSource[];
  role: string;
  mode: 'gemini' | 'groq' | 'fallback';
  confidence: 'high' | 'low';
  chunks_retrieved: number;
}

// ─── Error Helper ──────────────────────────────────────────────────────────────

function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const ae = error as AxiosError<{ detail?: string; message?: string }>;
    const detail = ae.response?.data?.detail ?? ae.response?.data?.message;
    if (detail) return typeof detail === 'string' ? detail : JSON.stringify(detail);
    if (ae.response?.status === 404) return 'Project not found.';
    if (ae.response?.status === 202) return 'Analysis still in progress.';
    if (ae.message) return ae.message;
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred';
}

// ─── API Client ────────────────────────────────────────────────────────────────

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 60_000,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // POST /upload — MUST be multipart/form-data (backend uses Form(), not JSON body)
  async uploadProject(githubUrl?: string, file?: File): Promise<UploadResponse> {
    const formData = new FormData();
    if (githubUrl) formData.append('github_url', githubUrl.trim());
    if (file) formData.append('file', file);

    try {
      const response = await this.client.post<UploadResponse>('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }

  async getStatus(projectId: string): Promise<StatusResponse> {
    try {
      const response = await this.client.get<StatusResponse>(`/status/${projectId}`);
      return response.data;
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }

  async getAnalysis(projectId: string): Promise<AnalysisResponse> {
    try {
      const response = await this.client.get<AnalysisResponse>(`/analysis/${projectId}`);
      return response.data;
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }

  // POST /chat — JSON body: { project_id, question, role }
  async sendChat(
    projectId: string,
    question: string,
    role: 'dev' | 'pm' | 'investor' = 'dev'
  ): Promise<ChatResponse> {
    try {
      const response = await this.client.post<ChatResponse>('/chat', {
        project_id: projectId,
        question,
        role,
      });
      return response.data;
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }

  // GET /workflow/{id} → { success, project_id, workflow: WorkflowData }
  async getWorkflow(projectId: string): Promise<WorkflowResponse> {
    try {
      const response = await this.client.get<WorkflowResponse>(`/workflow/${projectId}`);
      return response.data;
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }

  async getMock(projectId: string): Promise<MockResponse> {
    try {
      const response = await this.client.get<MockResponse>(`/mock/${projectId}`);
      return response.data;
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }

  // GET /memory/{id} → flat { recent_work, features, security, refactors }
  async getMemory(projectId: string): Promise<MemoryResponse> {
    try {
      const response = await this.client.get<MemoryResponse>(`/memory/${projectId}`);
      return response.data;
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }
}

// ─── Singleton + Convenience Exports ──────────────────────────────────────────

export const apiClient = new APIClient();

export const uploadProject = (githubUrl?: string, file?: File) =>
  apiClient.uploadProject(githubUrl, file);
export const getStatus   = (projectId: string) => apiClient.getStatus(projectId);
export const getAnalysis = (projectId: string) => apiClient.getAnalysis(projectId);
export const sendChat    = (projectId: string, question: string, role?: 'dev' | 'pm' | 'investor') =>
  apiClient.sendChat(projectId, question, role);
export const getWorkflow = (projectId: string) => apiClient.getWorkflow(projectId);
export const getMock     = (projectId: string) => apiClient.getMock(projectId);
export const getMemory   = (projectId: string) => apiClient.getMemory(projectId);
/** MemoryItem — single entry in a memory list */


/** MemoryItem — single entry in a memory list */
export interface MemoryItem {
  title?: string;
  description?: string;
  category?: string;
  timestamp?: string;
  file?: string;
  type?: string;
  line?: number;
}


/** MemoryItem — single memory entry returned by getMemory() */
export interface MemoryItem {
  title?: string;
  description?: string;
  category?: string;
  timestamp?: string;
  file?: string;
  type?: string;
  line?: number;
}
