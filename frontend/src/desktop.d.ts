export interface DesktopBridge {
  fetch_health(): Promise<unknown>;
  fetch_tools(): Promise<unknown>;
  fetch_documents(payload?: Record<string, unknown>): Promise<unknown>;
  upload_documents(payload: Record<string, unknown>): Promise<unknown>;
  delete_document(documentId: string): Promise<unknown>;
  run_retrieval(payload: Record<string, unknown>): Promise<unknown>;
  generate_report(payload: Record<string, unknown>): Promise<unknown>;
  execute_analysis(payload: Record<string, unknown>): Promise<unknown>;
  merge_documents(payload: Record<string, unknown>): Promise<unknown>;
  search_repositories(payload: Record<string, unknown>): Promise<unknown>;
  install_repository(payload: Record<string, unknown>): Promise<unknown>;
  run_orchestrator(payload: Record<string, unknown>): Promise<unknown>;
  stream_orchestrator(payload: Record<string, unknown>): Promise<unknown>;
  reveal_data_directory(): Promise<string>;
}

declare global {
  interface Window {
    pywebview?: {
      api?: DesktopBridge;
    };
  }
}

export {};
