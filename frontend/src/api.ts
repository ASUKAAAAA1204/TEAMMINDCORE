import type { DesktopBridge } from "./desktop";

export type AppMode =
  | "overview"
  | "documents"
  | "retrieval"
  | "report"
  | "analysis"
  | "integration"
  | "installer"
  | "orchestrator"
  | "health";

export interface HealthResponse {
  status: string;
  database: string;
  main_orchestrator: string;
  available_agents: string[];
  vector_store_backend: string;
  deep_parser_enabled: boolean;
  deep_parser_backends: string[];
  ragflow_enabled: boolean;
  mineru_enabled: boolean;
  llamaindex_enabled: boolean;
  langgraph_enabled: boolean;
  retrieval_backend: string;
  orchestrator_backend: string;
  task_planning_backend: string;
  analysis_generation_backend: string;
  report_generation_backend: string;
}

export interface ToolSchema {
  name: string;
  description: string;
  parameters: {
    type: string;
    properties: Record<string, { type: string }>;
  };
}

export interface ToolsResponse {
  tools: ToolSchema[];
}

export interface DocumentSummary {
  id: string;
  filename: string;
  upload_time: string;
  parse_status: string;
  metadata: Record<string, unknown>;
  tags: string[];
}

export interface DocumentListResponse {
  total: number;
  page: number;
  page_size: number;
  documents: DocumentSummary[];
}

export interface UploadResponse {
  document_ids: string[];
  status: string;
  progress: number;
  message: string;
}

export interface DeleteResponse {
  success: boolean;
  message: string;
}

export interface SearchResult {
  text: string;
  score: number;
  document_id: string;
  metadata: Record<string, unknown>;
}

export interface SearchResponse {
  results: SearchResult[];
  total_found: number;
}

export interface ReportSection {
  section: string;
  content: string;
  sources: string[];
}

export interface ReportResponse {
  title: string;
  sections: ReportSection[];
  overall_summary: string;
  sources_count: number;
  generated_at: string;
}

export interface AnalysisResponse {
  task_id: string;
  results: Record<string, unknown>;
}

export interface MergeResponse {
  merged_content: string;
  total_length: number;
  source_count: number;
}

export interface InstallerSearchResult {
  name: string;
  url: string;
  stars: number;
  description: string;
  readme_summary: string;
  license: string;
}

export interface InstallerSearchResponse {
  total: number;
  results: InstallerSearchResult[];
}

export interface InstallResponse {
  success: boolean;
  tool_name: string;
  installed_path: string;
  message: string;
}

export interface OrchestratorResponse {
  task_id: string;
  status: string;
  main_agent: string;
  trace: Array<Record<string, unknown>>;
  result: Record<string, unknown>;
  executed_at: string;
  parameters: Record<string, unknown>;
  planning_backend: string;
}

type DesktopMethod = keyof DesktopBridge;
const DESKTOP_BRIDGE_TIMEOUT_MS = 10_000;

async function request<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    let detail = `请求失败: ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload?.detail?.message ?? payload?.message ?? JSON.stringify(payload);
    } catch {
      const text = await response.text();
      if (text) {
        detail = text;
      }
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

async function invokeDesktop<T>(method: DesktopMethod, payload?: unknown): Promise<T> {
  const bridge = await waitForDesktopBridge();
  const target = bridge[method] as (argument?: unknown) => Promise<unknown>;
  return (await target(payload)) as T;
}

function isDesktopRuntime() {
  return typeof window !== "undefined" && typeof window.pywebview !== "undefined";
}

async function waitForDesktopBridge(): Promise<DesktopBridge> {
  if (window.pywebview?.api) {
    return window.pywebview.api;
  }
  await new Promise<void>((resolve, reject) => {
    let settled = false;

    const cleanup = (timeoutId: number, pollId: number) => {
      window.clearTimeout(timeoutId);
      window.clearInterval(pollId);
      window.removeEventListener("pywebviewready", onReady);
    };

    const tryResolve = (timeoutId: number, pollId: number) => {
      if (!window.pywebview?.api || settled) {
        return;
      }
      settled = true;
      cleanup(timeoutId, pollId);
      resolve();
    };

    const onReady = () => tryResolve(timeoutId, pollId);
    const timeoutId = window.setTimeout(() => {
      if (settled) {
        return;
      }
      settled = true;
      cleanup(timeoutId, pollId);
      reject(new Error("desktop bridge initialization timed out"));
    }, DESKTOP_BRIDGE_TIMEOUT_MS);
    const pollId = window.setInterval(() => tryResolve(timeoutId, pollId), 50);

    window.addEventListener("pywebviewready", onReady);
    tryResolve(timeoutId, pollId);
  });
  if (!window.pywebview?.api) {
    throw new Error("desktop bridge is not available");
  }
  return window.pywebview.api;
}

async function serializeFormData(formData: FormData): Promise<Record<string, unknown>> {
  const payload: Record<string, unknown> = {
    files: [] as Array<Record<string, string>>,
  };
  for (const [key, value] of formData.entries()) {
    if (key === "files" && value instanceof File) {
      const fileEntries = payload.files as Array<Record<string, string>>;
      fileEntries.push({
        name: value.name,
        content_base64: await fileToBase64(value),
      });
      continue;
    }
    if (typeof value === "string") {
      payload[key] = value;
    }
  }
  return payload;
}

async function fileToBase64(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

export function fetchHealth() {
  if (isDesktopRuntime()) {
    return invokeDesktop<HealthResponse>("fetch_health");
  }
  return request<HealthResponse>("/health");
}

export function fetchTools() {
  if (isDesktopRuntime()) {
    return invokeDesktop<ToolsResponse>("fetch_tools");
  }
  return request<ToolsResponse>("/tools");
}

export function fetchDocuments(params: URLSearchParams) {
  if (isDesktopRuntime()) {
    return invokeDesktop<DocumentListResponse>("fetch_documents", {
      page: Number(params.get("page") || "1"),
      page_size: Number(params.get("page_size") || "100"),
      team_id: params.get("team_id"),
      keyword: params.get("keyword"),
      status: params.get("status"),
      tags: params.getAll("tags").length > 0 ? params.getAll("tags") : splitCsv(params.get("tags")),
    });
  }
  return request<DocumentListResponse>(`/ingestion/documents?${params.toString()}`);
}

export async function uploadDocuments(formData: FormData) {
  if (isDesktopRuntime()) {
    return invokeDesktop<UploadResponse>("upload_documents", await serializeFormData(formData));
  }
  return request<UploadResponse>("/ingestion/upload", {
    method: "POST",
    body: formData,
  });
}

export function deleteDocument(documentId: string) {
  if (isDesktopRuntime()) {
    return invokeDesktop<DeleteResponse>("delete_document", documentId);
  }
  return request<DeleteResponse>(`/ingestion/${documentId}`, {
    method: "DELETE",
  });
}

export function runRetrieval(payload: Record<string, unknown>) {
  if (isDesktopRuntime()) {
    return invokeDesktop<SearchResponse>("run_retrieval", payload);
  }
  return request<SearchResponse>("/retrieval/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function generateReport(payload: Record<string, unknown>) {
  if (isDesktopRuntime()) {
    return invokeDesktop<ReportResponse>("generate_report", payload);
  }
  return request<ReportResponse>("/report/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function executeAnalysis(payload: Record<string, unknown>) {
  if (isDesktopRuntime()) {
    return invokeDesktop<AnalysisResponse>("execute_analysis", payload);
  }
  return request<AnalysisResponse>("/analysis/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function mergeDocuments(payload: Record<string, unknown>) {
  if (isDesktopRuntime()) {
    return invokeDesktop<MergeResponse>("merge_documents", payload);
  }
  return request<MergeResponse>("/integration/merge", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function searchRepositories(payload: Record<string, unknown>) {
  if (isDesktopRuntime()) {
    return invokeDesktop<InstallerSearchResponse>("search_repositories", payload);
  }
  return request<InstallerSearchResponse>("/installer/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function installRepository(payload: Record<string, unknown>) {
  if (isDesktopRuntime()) {
    return invokeDesktop<InstallResponse>("install_repository", payload);
  }
  return request<InstallResponse>("/installer/install", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function runOrchestrator(payload: Record<string, unknown>) {
  if (isDesktopRuntime()) {
    return invokeDesktop<OrchestratorResponse>("run_orchestrator", payload);
  }
  return request<OrchestratorResponse>("/orchestrator/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function splitCsv(value: string | null) {
  if (!value) {
    return [];
  }
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
