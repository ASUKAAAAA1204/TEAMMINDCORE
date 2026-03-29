import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  Bot,
  CheckCheck,
  Database,
  Filter,
  Network,
  RefreshCcw,
  ShieldCheck,
  Wrench,
} from "lucide-react";
import type {
  AnalysisResponse,
  AppMode,
  DocumentSummary,
  HealthResponse,
  InstallResponse,
  InstallerSearchResult,
  MergeResponse,
  OrchestratorResponse,
  ReportResponse,
  SearchResponse,
  ToolsResponse,
} from "./api";
import {
  deleteDocument,
  executeAnalysis,
  fetchDocuments,
  fetchHealth,
  fetchTools,
  generateReport,
  installRepository,
  mergeDocuments,
  runOrchestrator,
  runRetrieval,
  searchRepositories,
  uploadDocuments,
} from "./api";
import { ACCENT_STATUSES, MODULE_CARDS, MODULE_GROUPS, NAV_ITEMS, type AccentStatus } from "./constants";
import { AnalysisPanel } from "./panels/AnalysisPanel";
import { DocumentsPanel } from "./panels/DocumentsPanel";
import { HealthPanel } from "./panels/HealthPanel";
import { InstallerPanel } from "./panels/InstallerPanel";
import { IntegrationPanel } from "./panels/IntegrationPanel";
import { OrchestratorPanel } from "./panels/OrchestratorPanel";
import { OverviewPanel } from "./panels/OverviewPanel";
import { ReportPanel } from "./panels/ReportPanel";
import { RetrievalPanel } from "./panels/RetrievalPanel";
import { FlashIcon, type FlashMessage, type FlashTone, StatusPill, splitTags } from "./shared";

const MODE_COPY: Record<AppMode, { eyebrow: string; description: string }> = {
  overview: { eyebrow: "工作总览", description: "从这里进入各个模块，查看当前文档、工具和系统状态。" },
  documents: { eyebrow: "文档接入", description: "上传文件、补充标签并完成解析，为后续流程准备证据材料。" },
  retrieval: { eyebrow: "混合检索", description: "把语义检索和关键词召回放在同一界面核对证据。" },
  report: { eyebrow: "结构化报告", description: "基于知识库自动生成章节化报告，适合沉淀对外交付文本。" },
  analysis: { eyebrow: "任务分析", description: "围绕选中文档执行问题分析，并提炼统计、摘要和图表建议。" },
  integration: { eyebrow: "内容统合", description: "把多份材料压缩成一个统一产物，供报告或审阅继续使用。" },
  installer: { eyebrow: "工具接入", description: "把 GitHub 开源仓库转化为可接入的 TeamMindHub 工具能力。" },
  orchestrator: { eyebrow: "主代理编排", description: "由主编排代理统一调度检索、报告、分析和安装流程。" },
  health: { eyebrow: "运行健康", description: "检查解析器、向量库、代理后端与工具模式的运行状态。" },
};

function mapModuleToMode(moduleId: string): AppMode {
  switch (moduleId) {
    case "ingestion":
      return "documents";
    case "retrieval":
      return "retrieval";
    case "report":
      return "report";
    case "analysis":
      return "analysis";
    case "integration":
      return "integration";
    case "installer":
      return "installer";
    case "orchestrator":
      return "orchestrator";
    default:
      return "health";
  }
}

export default function App() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [mode, setMode] = useState<AppMode>("overview");
  const [moduleGroup, setModuleGroup] = useState<(typeof MODULE_GROUPS)[number]>("全部模块");
  const [moduleQuery, setModuleQuery] = useState("");
  const [flash, setFlash] = useState<FlashMessage>({
    tone: "neutral",
    text: "界面已从模板语义重映射到 TeamMindHub，所有操作都直连真实后端接口。",
  });

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [tools, setTools] = useState<ToolsResponse["tools"]>([]);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [documentTotal, setDocumentTotal] = useState(0);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);

  const [docKeyword, setDocKeyword] = useState("");
  const [docStatus, setDocStatus] = useState("all");
  const [docTags, setDocTags] = useState("");
  const [uploadTeamId, setUploadTeamId] = useState("default");
  const [uploadTags, setUploadTags] = useState("");
  const [uploadParseMode, setUploadParseMode] = useState("deep");
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);

  const [retrievalQuery, setRetrievalQuery] = useState("");
  const [retrievalTopK, setRetrievalTopK] = useState(8);
  const [retrievalAlpha, setRetrievalAlpha] = useState(0.7);
  const [retrievalTags, setRetrievalTags] = useState("");
  const [retrievalDate, setRetrievalDate] = useState("");
  const [retrievalResult, setRetrievalResult] = useState<SearchResponse | null>(null);
  const [retrievalLoading, setRetrievalLoading] = useState(false);

  const [reportEntity, setReportEntity] = useState("");
  const [reportType, setReportType] = useState("project_summary");
  const [reportIncludeSources, setReportIncludeSources] = useState(true);
  const [reportMaxSections, setReportMaxSections] = useState(4);
  const [reportResult, setReportResult] = useState<ReportResponse | null>(null);
  const [reportLoading, setReportLoading] = useState(false);

  const [analysisTask, setAnalysisTask] = useState("");
  const [analysisFormat, setAnalysisFormat] = useState("json");
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  const [mergeStrategy, setMergeStrategy] = useState("concatenate");
  const [mergeFormat, setMergeFormat] = useState("markdown");
  const [mergeResult, setMergeResult] = useState<MergeResponse | null>(null);
  const [mergeLoading, setMergeLoading] = useState(false);

  const [installerQuery, setInstallerQuery] = useState("");
  const [installerResults, setInstallerResults] = useState<InstallerSearchResult[]>([]);
  const [installerLoading, setInstallerLoading] = useState(false);
  const [installingRepo, setInstallingRepo] = useState<string | null>(null);
  const [installResult, setInstallResult] = useState<InstallResponse | null>(null);

  const [orchestratorTask, setOrchestratorTask] = useState("");
  const [orchestratorAgent, setOrchestratorAgent] = useState("");
  const [orchestratorMaxSteps, setOrchestratorMaxSteps] = useState(10);
  const [orchestratorTimeout, setOrchestratorTimeout] = useState(300);
  const [orchestratorResult, setOrchestratorResult] = useState<OrchestratorResponse | null>(null);
  const [orchestratorLoading, setOrchestratorLoading] = useState(false);

  const updateFlash = useCallback((tone: FlashTone, text: string) => setFlash({ tone, text }), []);

  const loadHealth = useCallback(async () => {
    const payload = await fetchHealth();
    setHealth(payload);
    if (!orchestratorAgent && payload.available_agents.length > 0) {
      setOrchestratorAgent(payload.available_agents[0]);
    }
  }, [orchestratorAgent]);

  const loadTools = useCallback(async () => {
    const payload = await fetchTools();
    setTools(payload.tools);
  }, []);

  const loadDocuments = useCallback(async () => {
    setDocumentsLoading(true);
    setDocumentsError(null);
    try {
      const params = new URLSearchParams({ page: "1", page_size: "100" });
      if (docKeyword.trim()) params.set("keyword", docKeyword.trim());
      if (docStatus !== "all") params.set("status", docStatus);
      if (docTags.trim()) params.set("tags", docTags.trim());
      const payload = await fetchDocuments(params);
      setDocuments(payload.documents);
      setDocumentTotal(payload.total);
      setSelectedDocumentIds((prev) => prev.filter((id) => payload.documents.some((doc) => doc.id === id)));
    } catch (error) {
      const detail = error instanceof Error ? error.message : "无法读取文档列表。";
      setDocumentsError(detail);
      updateFlash("error", detail);
    } finally {
      setDocumentsLoading(false);
    }
  }, [docKeyword, docStatus, docTags, updateFlash]);

  const refreshAll = useCallback(async () => {
    try {
      await Promise.all([loadHealth(), loadTools(), loadDocuments()]);
      updateFlash("success", "后端状态、文档列表与工具模式已刷新。");
    } catch (error) {
      const detail = error instanceof Error ? error.message : "刷新失败。";
      updateFlash("error", detail);
    }
  }, [loadDocuments, loadHealth, loadTools, updateFlash]);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  const parsedDocuments = useMemo(() => documents.filter((document) => document.parse_status === "parsed"), [documents]);
  const selectedDocuments = useMemo(
    () => parsedDocuments.filter((document) => selectedDocumentIds.includes(document.id)),
    [parsedDocuments, selectedDocumentIds],
  );
  const activeMode = useMemo(() => NAV_ITEMS.find((item) => item.id === mode) ?? NAV_ITEMS[0], [mode]);
  const filteredModules = useMemo(
    () =>
      MODULE_CARDS.filter((module) => {
        const matchesGroup = moduleGroup === "全部模块" || module.badge === moduleGroup;
        const matchesQuery =
          !moduleQuery.trim() || module.name.includes(moduleQuery.trim()) || module.summary.includes(moduleQuery.trim());
        return matchesGroup && matchesQuery;
      }),
    [moduleGroup, moduleQuery],
  );
  const dashboardStats = [
    { label: "已接入文档", value: String(documentTotal), helper: "知识源总量" },
    { label: "解析完成", value: String(parsedDocuments.length), helper: "可直接参与检索和分析" },
    { label: "已选文档", value: String(selectedDocumentIds.length), helper: "供分析与统合复用" },
    { label: "工具模式", value: String(tools.length), helper: "安装器接入的工具视图" },
  ];

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => setPendingFiles(Array.from(event.target.files ?? []));
  const toggleDocumentSelection = (documentId: string) =>
    setSelectedDocumentIds((prev) => (prev.includes(documentId) ? prev.filter((item) => item !== documentId) : [...prev, documentId]));
  const openModuleFromCard = (moduleId: string) => setMode(mapModuleToMode(moduleId));
  const handleStatusCardClick = useCallback(
    (item: AccentStatus) => {
      setMode(item.targetMode);
      updateFlash("neutral", item.prompt);
    },
    [updateFlash],
  );

  async function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pendingFiles.length === 0) return updateFlash("error", "请先选择至少一个文档。");
    const formData = new FormData();
    pendingFiles.forEach((file) => formData.append("files", file));
    formData.append("team_id", uploadTeamId || "default");
    if (uploadTags.trim()) formData.append("tags", uploadTags.trim());
    formData.append("parse_mode", uploadParseMode);
    setUploading(true);
    try {
      const payload = await uploadDocuments(formData);
      setPendingFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = "";
      updateFlash("success", payload.message);
      await loadDocuments();
      [1200, 3600, 7200].forEach((delay) => window.setTimeout(() => void loadDocuments(), delay));
    } catch (error) {
      updateFlash("error", error instanceof Error ? error.message : "上传失败。");
    } finally {
      setUploading(false);
    }
  }

  async function handleDeleteDocument(documentId: string) {
    if (!window.confirm("删除后将移除该文档及其本地索引，是否继续？")) return;
    try {
      const payload = await deleteDocument(documentId);
      updateFlash("success", payload.message);
      await loadDocuments();
    } catch (error) {
      updateFlash("error", error instanceof Error ? error.message : "删除失败。");
    }
  }

  async function handleRetrieval(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!retrievalQuery.trim()) return updateFlash("error", "请输入检索问题。");
    setRetrievalLoading(true);
    try {
      const payload = await runRetrieval({
        query: retrievalQuery.trim(),
        top_k: retrievalTopK,
        hybrid_alpha: retrievalAlpha,
        filters: { tags: splitTags(retrievalTags), date_after: retrievalDate || null },
      });
      setRetrievalResult(payload);
      updateFlash("success", `检索完成，返回 ${payload.total_found} 条结果。`);
    } catch (error) {
      updateFlash("error", error instanceof Error ? error.message : "检索失败。");
    } finally {
      setRetrievalLoading(false);
    }
  }

  async function handleReport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!reportEntity.trim()) return updateFlash("error", "请输入报告主体。");
    setReportLoading(true);
    try {
      const payload = await generateReport({
        entity: reportEntity.trim(),
        report_type: reportType,
        include_sources: reportIncludeSources,
        max_sections: reportMaxSections,
      });
      setReportResult(payload);
      updateFlash("success", `报告已生成，共 ${payload.sections.length} 个章节。`);
    } catch (error) {
      updateFlash("error", error instanceof Error ? error.message : "报告生成失败。");
    } finally {
      setReportLoading(false);
    }
  }

  async function handleAnalysis(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!analysisTask.trim()) return updateFlash("error", "请输入分析任务。");
    if (selectedDocumentIds.length === 0) return updateFlash("error", "请至少选择一份解析完成的文档。");
    setAnalysisLoading(true);
    try {
      const payload = await executeAnalysis({ task: analysisTask.trim(), document_ids: selectedDocumentIds, output_format: analysisFormat });
      setAnalysisResult(payload);
      updateFlash("success", "分析任务已执行完成。");
    } catch (error) {
      updateFlash("error", error instanceof Error ? error.message : "分析执行失败。");
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function handleMerge(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedDocumentIds.length === 0) return updateFlash("error", "统合前请先选择至少一份文档。");
    setMergeLoading(true);
    try {
      const payload = await mergeDocuments({ document_ids: selectedDocumentIds, rule: { strategy: mergeStrategy, format: mergeFormat } });
      setMergeResult(payload);
      updateFlash("success", `已统合 ${payload.source_count} 份文档。`);
    } catch (error) {
      updateFlash("error", error instanceof Error ? error.message : "内容统合失败。");
    } finally {
      setMergeLoading(false);
    }
  }

  async function handleInstallerSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!installerQuery.trim()) return updateFlash("error", "请输入 GitHub 开源检索词。");
    setInstallerLoading(true);
    try {
      const payload = await searchRepositories({ query: installerQuery.trim() });
      setInstallerResults(payload.results);
      updateFlash("success", `已找到 ${payload.total} 个候选仓库。`);
    } catch (error) {
      updateFlash("error", error instanceof Error ? error.message : "仓库检索失败。");
    } finally {
      setInstallerLoading(false);
    }
  }

  async function handleInstall(repoUrl: string) {
    if (!window.confirm(`将把 ${repoUrl} 接入 TeamMindHub，是否继续？`)) return;
    setInstallingRepo(repoUrl);
    try {
      const payload = await installRepository({ repo_url: repoUrl, confirm: true });
      setInstallResult(payload);
      updateFlash("success", payload.message);
      await loadTools();
    } catch (error) {
      updateFlash("error", error instanceof Error ? error.message : "安装失败。");
    } finally {
      setInstallingRepo(null);
    }
  }

  async function handleOrchestrator(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!orchestratorTask.trim()) return updateFlash("error", "请输入要交给主代理的任务。");
    setOrchestratorLoading(true);
    try {
      const payload = await runOrchestrator({
        main_agent: orchestratorAgent || null,
        task: orchestratorTask.trim(),
        parameters: { max_steps: orchestratorMaxSteps, timeout: orchestratorTimeout, stream: false },
      });
      setOrchestratorResult(payload);
      updateFlash("success", `主代理已完成路由，状态为 ${payload.status}。`);
    } catch (error) {
      updateFlash("error", error instanceof Error ? error.message : "主代理执行失败。");
    } finally {
      setOrchestratorLoading(false);
    }
  }

  return (
    <div className="app-frame">
      <aside className="icon-rail">
        <div className="rail-logo">TM</div>
        <nav className="rail-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.id} type="button" title={item.label} className={`rail-button ${item.id === mode ? "is-active" : ""}`} onClick={() => setMode(item.id)}>
                <Icon size={18} />
              </button>
            );
          })}
        </nav>
      </aside>
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="eyebrow">TeamMindHub</span>
          <h1>能力地图</h1>
          <p>模板结构保留，业务语义全部替换为知识接入、检索、分析、统合和代理编排。</p>
        </div>
        <label className="search-shell">
          <Filter size={14} />
          <input value={moduleQuery} onChange={(event) => setModuleQuery(event.target.value)} placeholder="筛选模块" />
        </label>
        <div className="chip-row">
          {MODULE_GROUPS.map((group) => (
            <button key={group} type="button" className={`chip-button ${moduleGroup === group ? "is-selected" : ""}`} onClick={() => setModuleGroup(group)}>
              {group}
            </button>
          ))}
        </div>
        <div className="module-list">
          {filteredModules.map((module) => (
            <button
              key={module.id}
              type="button"
              className={`module-item ${mapModuleToMode(module.id) === mode ? "is-current" : ""}`}
              onClick={() => setMode(mapModuleToMode(module.id))}
              title={module.prompt}
            >
              <div className="module-copy">
                <strong>{module.name}</strong>
                <p>{module.summary}</p>
                <small className="module-hint">{module.prompt}</small>
              </div>
              <span>{module.badge}</span>
            </button>
          ))}
        </div>
        <div className="sidebar-footer">
          {ACCENT_STATUSES.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                type="button"
                className="sidebar-status sidebar-status-button"
                onClick={() => handleStatusCardClick(item)}
                title={item.prompt}
              >
                <Icon size={16} />
                <div>
                  <strong>{item.value}</strong>
                  <span>{item.label}</span>
                </div>
              </button>
            );
          })}
        </div>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div><span className="eyebrow">{MODE_COPY[mode].eyebrow}</span><div className="topbar-title"><h2>{activeMode.label}</h2><p>{MODE_COPY[mode].description}</p></div></div>
          <div className="topbar-actions">
            <StatusPill icon={health?.status === "ok" ? CheckCheck : AlertTriangle} text={health?.status === "ok" ? "后端已连接" : "后端待连接"} />
            <StatusPill icon={Database} text={`${parsedDocuments.length} 份已解析`} />
            <StatusPill icon={ShieldCheck} text={`${tools.length} 个工具`} />
            <button type="button" className="secondary-button" onClick={() => void refreshAll()}><RefreshCcw size={15} />刷新</button>
          </div>
        </header>
        <section className="workspace-content">
          <article className={`flash-banner flash-${flash.tone}`}><FlashIcon tone={flash.tone} /><span>{flash.text}</span></article>
          {mode === "overview" && <OverviewPanel dashboardStats={dashboardStats} documents={documents} onOpenModule={openModuleFromCard} onOpenStatus={handleStatusCardClick} />}
          {mode === "documents" && <DocumentsPanel uploadTeamId={uploadTeamId} uploadTags={uploadTags} uploadParseMode={uploadParseMode} pendingFiles={pendingFiles} uploading={uploading} docKeyword={docKeyword} docStatus={docStatus} docTags={docTags} documents={documents} documentsLoading={documentsLoading} documentsError={documentsError} selectedDocumentIds={selectedDocumentIds} fileInputRef={fileInputRef} onUploadTeamIdChange={setUploadTeamId} onUploadTagsChange={setUploadTags} onUploadParseModeChange={setUploadParseMode} onFileChange={handleFileChange} onUpload={handleUpload} onDocKeywordChange={setDocKeyword} onDocStatusChange={setDocStatus} onDocTagsChange={setDocTags} onToggleDocument={toggleDocumentSelection} onDeleteDocument={handleDeleteDocument} />}
          {mode === "retrieval" && <RetrievalPanel retrievalQuery={retrievalQuery} retrievalTopK={retrievalTopK} retrievalAlpha={retrievalAlpha} retrievalTags={retrievalTags} retrievalDate={retrievalDate} retrievalLoading={retrievalLoading} retrievalResult={retrievalResult} onQueryChange={setRetrievalQuery} onTopKChange={setRetrievalTopK} onAlphaChange={setRetrievalAlpha} onTagsChange={setRetrievalTags} onDateChange={setRetrievalDate} onSubmit={handleRetrieval} />}
          {mode === "report" && <ReportPanel reportEntity={reportEntity} reportType={reportType} reportIncludeSources={reportIncludeSources} reportMaxSections={reportMaxSections} reportLoading={reportLoading} reportResult={reportResult} onEntityChange={setReportEntity} onTypeChange={setReportType} onIncludeSourcesChange={setReportIncludeSources} onMaxSectionsChange={setReportMaxSections} onSubmit={handleReport} />}
          {mode === "analysis" && <AnalysisPanel analysisTask={analysisTask} analysisFormat={analysisFormat} analysisLoading={analysisLoading} analysisResult={analysisResult} parsedDocuments={parsedDocuments} selectedDocumentIds={selectedDocumentIds} onTaskChange={setAnalysisTask} onFormatChange={setAnalysisFormat} onToggleDocument={toggleDocumentSelection} onSubmit={handleAnalysis} />}
          {mode === "integration" && <IntegrationPanel mergeStrategy={mergeStrategy} mergeFormat={mergeFormat} mergeLoading={mergeLoading} mergeResult={mergeResult} selectedDocuments={selectedDocuments} onStrategyChange={setMergeStrategy} onFormatChange={setMergeFormat} onSubmit={handleMerge} />}
          {mode === "installer" && <InstallerPanel installerQuery={installerQuery} installerLoading={installerLoading} installerResults={installerResults} installingRepo={installingRepo} installResult={installResult} onQueryChange={setInstallerQuery} onSubmit={handleInstallerSearch} onInstall={handleInstall} />}
          {mode === "orchestrator" && <OrchestratorPanel orchestratorTask={orchestratorTask} orchestratorAgent={orchestratorAgent} orchestratorMaxSteps={orchestratorMaxSteps} orchestratorTimeout={orchestratorTimeout} orchestratorLoading={orchestratorLoading} orchestratorResult={orchestratorResult} availableAgents={health?.available_agents ?? []} onTaskChange={setOrchestratorTask} onAgentChange={setOrchestratorAgent} onMaxStepsChange={setOrchestratorMaxSteps} onTimeoutChange={setOrchestratorTimeout} onSubmit={handleOrchestrator} />}
          {mode === "health" && <HealthPanel health={health} tools={tools} />}
        </section>
        <footer className="status-bar">
          <span>当前模块：{activeMode.shortLabel}</span><span>已选文档：{selectedDocumentIds.length}</span><span>可用代理：{health?.available_agents.length ?? 0}</span><span>向量后端：{health?.vector_store_backend ?? "待连接"}</span><span>编排后端：{health?.orchestrator_backend ?? "待连接"}</span>
          <span className="status-bar-end">{health ? <Network size={13} /> : <Bot size={13} />}{health ? "运行状态已同步" : "等待后端连接"}</span>
        </footer>
      </main>
    </div>
  );
}
