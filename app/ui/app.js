const APP_TITLE = "TeamMindHub Command Center";

const NAV_ITEMS = [
  { id: "overview", label: "总览", shortLabel: "总览", group: "核心视图" },
  { id: "documents", label: "文档接入", shortLabel: "文档", group: "知识流" },
  { id: "retrieval", label: "混合检索", shortLabel: "检索", group: "知识流" },
  { id: "report", label: "报告生成", shortLabel: "报告", group: "分析流" },
  { id: "analysis", label: "分析执行", shortLabel: "分析", group: "分析流" },
  { id: "integration", label: "内容统合", shortLabel: "统合", group: "分析流" },
  { id: "installer", label: "开源接入", shortLabel: "接入", group: "工具桥" },
  { id: "orchestrator", label: "主编排代理", shortLabel: "编排", group: "工具桥" },
  { id: "health", label: "系统健康", shortLabel: "健康", group: "核心视图" },
];

const MODULE_GROUPS = ["全部模块", "知识流", "分析流", "工具桥"];

const MODULE_CARDS = [
  {
    id: "documents",
    title: "文档接入",
    meta: "知识流",
    summary: "上传原始资料，触发深度解析，并把结构化内容放入统一知识底座。",
  },
  {
    id: "retrieval",
    title: "混合检索",
    meta: "知识流",
    summary: "融合向量召回与关键词检索，为后续报告与分析提供可追溯证据。",
  },
  {
    id: "report",
    title: "报告生成",
    meta: "分析流",
    summary: "围绕指定实体与报告类型，生成可直接审阅的结构化章节内容。",
  },
  {
    id: "analysis",
    title: "分析执行",
    meta: "分析流",
    summary: "面向选中文档执行任务分析，产出摘要、统计和图表建议。",
  },
  {
    id: "integration",
    title: "内容统合",
    meta: "分析流",
    summary: "将多份文档压缩为单一输出，为归档、复核和报告复用做准备。",
  },
  {
    id: "installer",
    title: "开源接入",
    meta: "工具桥",
    summary: "搜索 GitHub 仓库并以 TeamMindHub 工具的方式注册进当前系统。",
  },
  {
    id: "orchestrator",
    title: "主编排代理",
    meta: "工具桥",
    summary: "统一调度检索、报告、分析和安装能力，并支持实时流式追踪。",
  },
  {
    id: "health",
    title: "系统健康",
    meta: "核心视图",
    summary: "聚合向量库、解析器、主代理和工具注册表的运行状态。",
  },
];

const REPORT_TYPES = [
  { value: "project_summary", label: "项目综述" },
  { value: "person_profile", label: "人物画像" },
  { value: "sales_analysis", label: "销售分析" },
];

const INSTALLER_SUGGESTIONS = [
  "retrieval agent",
  "document parser",
  "langgraph workflow",
  "crew orchestration",
];

const QUICK_ACTIONS = [
  { mode: "documents", label: "上传资料" },
  { mode: "retrieval", label: "检索证据" },
  { mode: "analysis", label: "运行分析" },
  { mode: "installer", label: "接入开源组件" },
];

const MODE_COPY = {
  overview: {
    eyebrow: "Same-Origin UI",
    title: "生产级同源控制台",
    description: "保留模板的空间层次，但所有业务文案、交互逻辑和状态流都已重写为 TeamMindHub 原生工作台。",
  },
  documents: {
    eyebrow: "Ingestion",
    title: "文档接入与解析",
    description: "上传文件、追踪解析状态、选择证据文档，并将选中项持续带入分析与统合流程。",
  },
  retrieval: {
    eyebrow: "Hybrid Search",
    title: "混合检索",
    description: "在一个页面里完成查询、过滤、得分比较和证据审阅，减少检索到分析之间的切换成本。",
  },
  report: {
    eyebrow: "Structured Output",
    title: "报告生成",
    description: "以真实后端 schema 为基础，生成可交付的结构化报告，而不是停留在静态模板演示。",
  },
  analysis: {
    eyebrow: "Evidence Analysis",
    title: "分析执行",
    description: "围绕选中的解析文档执行分析任务，输出摘要、统计、图表描述和完整原始结果。",
  },
  integration: {
    eyebrow: "Merge Pipeline",
    title: "内容统合",
    description: "把多份资料合并为单一产物，用于报告上下文复用、审阅和知识沉淀。",
  },
  installer: {
    eyebrow: "OSS Bridge",
    title: "开源能力接入",
    description: "在不离开工作台的前提下搜索、确认并注册 GitHub 仓库，补齐工具层能力。",
  },
  orchestrator: {
    eyebrow: "Agent Routing",
    title: "主编排代理",
    description: "支持普通执行与 SSE 流式追踪两种模式，实时展示路由链路与最终结果。",
  },
  health: {
    eyebrow: "Runtime",
    title: "系统健康面板",
    description: "检查所有后端能力、安装工具以及编排后端的当前状态，方便快速诊断。",
  },
};

const STORAGE_KEYS = {
  theme: "tmh-ui-theme",
  mode: "tmh-ui-mode",
  selectedDocs: "tmh-ui-selected-documents",
};

const ANALYSIS_FORMATS = ["json", "markdown", "text"];
const MERGE_STRATEGIES = ["concatenate", "timeline", "topic"];
const MERGE_FORMATS = ["markdown", "text"];
const PARSE_MODES = ["deep", "auto", "fast"];

const app = document.getElementById("app");
const themeMedia = window.matchMedia?.("(prefers-color-scheme: dark)");

let deferredInstallPrompt = null;
let flashTimer = null;
let documentPollHandle = null;
let documentPollAttempts = 0;

const state = {
  bootstrapping: true,
  mode: readStorage(STORAGE_KEYS.mode, "overview"),
  themePreference: readStorage(STORAGE_KEYS.theme, "system"),
  mobileSidebarOpen: false,
  moduleGroup: "全部模块",
  moduleQuery: "",
  isOnline: navigator.onLine,
  canInstall: false,
  health: null,
  tools: [],
  documents: [],
  documentTotal: 0,
  flash: {
    tone: "info",
    text: "控制台已经切换到 TeamMindHub 原生语义，所有操作直接连接真实后端接口。",
  },
  selectedDocumentIds: readJsonStorage(STORAGE_KEYS.selectedDocs, []),
  uploadTeamId: "default",
  uploadTags: "",
  uploadParseMode: "deep",
  pendingFiles: [],
  uploading: false,
  docKeyword: "",
  docStatus: "all",
  docTags: "",
  documentsLoading: false,
  documentsError: "",
  retrievalQuery: "",
  retrievalTopK: 8,
  retrievalAlpha: 0.7,
  retrievalTags: "",
  retrievalDateAfter: "",
  retrievalLoading: false,
  retrievalResult: null,
  reportEntity: "",
  reportType: "project_summary",
  reportIncludeSources: true,
  reportMaxSections: 4,
  reportLoading: false,
  reportResult: null,
  analysisTask: "",
  analysisFormat: "json",
  analysisLoading: false,
  analysisResult: null,
  mergeStrategy: "concatenate",
  mergeFormat: "markdown",
  mergeLoading: false,
  mergeResult: null,
  installerQuery: "",
  installerLoading: false,
  installerResults: [],
  installerResult: null,
  installingRepo: "",
  orchestratorTask: "",
  orchestratorAgent: "",
  orchestratorMaxSteps: 10,
  orchestratorTimeout: 300,
  orchestratorStream: true,
  orchestratorLoading: false,
  orchestratorResult: null,
  orchestratorEvents: [],
};

function readStorage(key, fallback) {
  try {
    return localStorage.getItem(key) || fallback;
  } catch {
    return fallback;
  }
}

function readJsonStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeStorage(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // no-op
  }
}

function writeJsonStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // no-op
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function splitTags(raw) {
  return String(raw || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function clampInt(value, min, max, fallback) {
  const parsed = Number.parseInt(String(value), 10);
  if (Number.isNaN(parsed)) return fallback;
  return Math.min(max, Math.max(min, parsed));
}

function clampFloat(value, min, max, fallback) {
  const parsed = Number.parseFloat(String(value));
  if (Number.isNaN(parsed)) return fallback;
  return Math.min(max, Math.max(min, parsed));
}

function formatDate(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatJson(value) {
  try {
    return JSON.stringify(value ?? {}, null, 2);
  } catch {
    return String(value ?? "");
  }
}

function truncate(value, max = 280) {
  const text = String(value || "");
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

function parsedDocuments() {
  return state.documents.filter((item) => item.parse_status === "parsed");
}

function selectedDocuments() {
  const selected = new Set(state.selectedDocumentIds);
  return parsedDocuments().filter((item) => selected.has(item.id));
}

function selectionCountLabel() {
  return `${state.selectedDocumentIds.length} 份已选文档`;
}

function filteredModules() {
  const query = state.moduleQuery.trim().toLowerCase();
  return MODULE_CARDS.filter((item) => {
    const matchesGroup = state.moduleGroup === "全部模块" || state.moduleGroup === item.meta;
    const haystack = `${item.title} ${item.summary} ${item.meta}`.toLowerCase();
    const matchesQuery = !query || haystack.includes(query);
    return matchesGroup && matchesQuery;
  });
}

function activeNav() {
  return NAV_ITEMS.find((item) => item.id === state.mode) || NAV_ITEMS[0];
}

function themeOptions() {
  return {
    system: "自动",
    dark: "深色",
    light: "浅色",
  };
}

function resolveTheme() {
  if (state.themePreference === "system") {
    return themeMedia?.matches ? "dark" : "light";
  }
  return state.themePreference;
}

function applyTheme() {
  const resolvedTheme = resolveTheme();
  document.documentElement.dataset.theme = resolvedTheme;
  writeStorage(STORAGE_KEYS.theme, state.themePreference);
  const themeMeta = document.querySelector('meta[name="theme-color"]');
  if (themeMeta) {
    themeMeta.setAttribute("content", resolvedTheme === "dark" ? "#101915" : "#eff5ea");
  }
}

function cycleTheme() {
  const order = ["system", "dark", "light"];
  const currentIndex = order.indexOf(state.themePreference);
  state.themePreference = order[(currentIndex + 1) % order.length];
  applyTheme();
  setFlash("success", `界面主题已切换为${themeOptions()[state.themePreference]}。`);
  render();
}

function setMode(mode) {
  state.mode = mode;
  state.mobileSidebarOpen = false;
  writeStorage(STORAGE_KEYS.mode, mode);
  render();
}

function persistSelectedDocuments() {
  writeJsonStorage(STORAGE_KEYS.selectedDocs, state.selectedDocumentIds);
}

function setFlash(tone, text, { sticky = false } = {}) {
  state.flash = { tone, text };
  if (flashTimer) {
    window.clearTimeout(flashTimer);
  }
  if (!sticky) {
    flashTimer = window.setTimeout(() => {
      state.flash = null;
      render();
    }, 4200);
  }
  render();
}

function clearFlash() {
  state.flash = null;
  if (flashTimer) {
    window.clearTimeout(flashTimer);
  }
  render();
}

function ensureSelectedDocumentsAreValid() {
  const known = new Set(parsedDocuments().map((item) => item.id));
  state.selectedDocumentIds = state.selectedDocumentIds.filter((id) => known.has(id));
  persistSelectedDocuments();
}

function renderPill(label, tone = "neutral") {
  return `<span class="status-pill" data-tone="${tone}">${escapeHtml(label)}</span>`;
}

function renderEmpty(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function renderSkeleton(count = 3) {
  return `<div class="skeleton-grid">${Array.from({ length: count })
    .map(
      () => `
      <div class="skeleton-block">
        <div class="skeleton-stack">
          <div class="skeleton-line is-short"></div>
          <div class="skeleton-line"></div>
          <div class="skeleton-line"></div>
        </div>
      </div>`,
    )
    .join("")}</div>`;
}

function renderTopbar() {
  const copy = MODE_COPY[state.mode];
  const themeLabel = themeOptions()[state.themePreference];
  return `
    <header class="topbar">
      <div class="topbar-copy">
        <span class="eyebrow">${escapeHtml(copy.eyebrow)}</span>
        <h2>${escapeHtml(copy.title)}</h2>
        <p>${escapeHtml(copy.description)}</p>
      </div>
      <div class="topbar-actions">
        <button class="secondary-button mobile-only" type="button" data-action="toggle-sidebar">模块导航</button>
        ${renderPill(state.isOnline ? "在线" : "离线", state.isOnline ? "success" : "warning")}
        ${renderPill(selectionCountLabel())}
        ${renderPill(`${state.tools.length} 个工具`)}
        ${state.canInstall ? '<button class="secondary-button" type="button" data-action="install-pwa">安装应用</button>' : ""}
        <button class="secondary-button" type="button" data-action="theme-toggle">主题：${themeLabel}</button>
        <button class="primary-button" type="button" data-action="refresh">刷新数据</button>
      </div>
    </header>
  `;
}

function renderRail() {
  return `
    <aside class="rail" aria-label="主导航">
      <div class="rail-brand">TMH</div>
      <nav class="rail-nav">
        ${NAV_ITEMS.map(
          (item) => `
            <button
              class="rail-button"
              type="button"
              data-nav="${item.id}"
              aria-current="${item.id === state.mode ? "page" : "false"}"
            >
              ${escapeHtml(item.shortLabel)}
            </button>`,
        ).join("")}
      </nav>
      <div class="rail-status">
        <div class="status-dot"></div>
        <span class="status-label">${state.isOnline ? "runtime synced" : "offline cache ready"}</span>
      </div>
    </aside>
  `;
}

function renderSidebar() {
  const modules = filteredModules();
  return `
    <aside class="sidebar" aria-label="模块导航">
      <div class="sidebar-copy">
        <span class="eyebrow">Capability Map</span>
        <h1>${APP_TITLE}</h1>
        <p>围绕文档、检索、分析、报告、集成和编排的全链路知识工作台。</p>
      </div>
      <div class="sidebar-search">
        <label class="search-shell">
          <span aria-hidden="true">⌕</span>
          <input
            type="text"
            name="moduleQuery"
            value="${escapeHtml(state.moduleQuery)}"
            placeholder="筛选模块或能力"
            aria-label="筛选模块"
          />
        </label>
        <div class="chip-row">
          ${MODULE_GROUPS.map(
            (group) => `
              <button
                class="chip-button ${group === state.moduleGroup ? "is-active" : ""}"
                type="button"
                data-group="${group}"
              >
                ${escapeHtml(group)}
              </button>`,
          ).join("")}
        </div>
      </div>
      <div class="sidebar-modules">
        ${modules
          .map(
            (module) => `
              <button
                class="module-card ${module.id === state.mode ? "is-active" : ""}"
                type="button"
                data-mode="${module.id}"
              >
                <strong>${escapeHtml(module.title)}</strong>
                <p>${escapeHtml(module.summary)}</p>
                <span class="module-meta">${escapeHtml(module.meta)}</span>
              </button>`,
          )
          .join("")}
      </div>
      <div class="sidebar-footer">
        <article class="sidebar-stat">
          <strong>${parsedDocuments().length}</strong>
          <p class="eyebrow-copy">解析完成文档</p>
        </article>
        <article class="sidebar-stat">
          <strong>${state.health?.orchestrator_backend || "--"}</strong>
          <p class="eyebrow-copy">编排后端</p>
        </article>
        <article class="sidebar-stat">
          <strong>${resolveTheme()}</strong>
          <p class="eyebrow-copy">当前视觉主题</p>
        </article>
      </div>
    </aside>
  `;
}

function renderBanner() {
  if (!state.flash) return "";
  const labels = {
    info: "系统提示",
    success: "执行成功",
    warning: "注意",
    error: "执行失败",
  };
  return `
    <div class="flash-banner" data-tone="${state.flash.tone}" role="status" aria-live="polite">
      <div class="flash-copy">
        <strong>${labels[state.flash.tone] || "系统提示"}</strong>
        <span>${escapeHtml(state.flash.text)}</span>
      </div>
      <button class="icon-button" type="button" data-action="dismiss-flash" aria-label="关闭提示">关闭</button>
    </div>
  `;
}

function renderOverview() {
  const stats = [
    { label: "文档总量", value: state.documentTotal, hint: "已进入知识底座的资料数量" },
    { label: "解析完成", value: parsedDocuments().length, hint: "可直接参与检索和分析" },
    { label: "已选证据", value: state.selectedDocumentIds.length, hint: "将在分析与统合中复用" },
    { label: "工具模式", value: state.tools.length, hint: "包含内置能力与已安装开源工具" },
  ];

  return `
    <div class="panel-grid">
      <section class="panel panel-span-2 hero-card">
        <span class="eyebrow">UI / UX extreme polish</span>
        <h1 class="hero-title">${APP_TITLE}</h1>
        <p class="hero-copy">
          同源工作台现已具备主题切换、离线外壳缓存、骨架屏、流式编排追踪和移动端侧栏适配，
          可以直接围绕 PRD 的后端能力进行日常使用和演示。
        </p>
        <div class="chip-row">
          <span class="chip">深色 / 浅色 / 自动主题</span>
          <span class="chip">PWA 离线外壳</span>
          <span class="chip">SSE 流式追踪</span>
          <span class="chip">可访问焦点状态</span>
        </div>
        <div class="metric-grid">
          ${stats
            .map(
              (item) => `
                <article class="metric-card">
                  <span>${escapeHtml(item.label)}</span>
                  <strong>${escapeHtml(String(item.value))}</strong>
                  <small>${escapeHtml(item.hint)}</small>
                </article>`,
            )
            .join("")}
        </div>
        <div class="action-grid">
          ${QUICK_ACTIONS.map(
            (action) => `
              <button class="quick-action" type="button" data-mode="${action.mode}">
                ${escapeHtml(action.label)}
              </button>`,
          ).join("")}
        </div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <h3 class="panel-title">本轮优化重点</h3>
          <p class="panel-copy">从模板感界面转为可交付的生产级同源控制台。</p>
        </div>
        <div class="section-list">
          <article class="section-callout">
            <strong>更强交互反馈</strong>
            <span class="meta-copy">统一 loading、骨架屏、离线状态与提示条语义。</span>
          </article>
          <article class="section-callout">
            <strong>PWA 准备就绪</strong>
            <span class="meta-copy">Manifest、Service Worker、安装入口与离线壳缓存全部到位。</span>
          </article>
          <article class="section-callout">
            <strong>编排流式化</strong>
            <span class="meta-copy">利用 /orchestrator/run 的 SSE 能力显示实时 trace。</span>
          </article>
        </div>
      </section>

      <section class="panel panel-span-2">
        <div class="panel-header">
          <h3 class="panel-title">模块画布</h3>
          <p class="panel-copy">所有卡片都映射到真实后端接口，而不是静态占位交互。</p>
        </div>
        <div class="detail-grid">
          ${MODULE_CARDS.map(
            (item) => `
              <button class="detail-card" type="button" data-mode="${item.id}">
                <strong>${escapeHtml(item.title)}</strong>
                <p>${escapeHtml(item.summary)}</p>
                <span class="meta-copy">${escapeHtml(item.meta)}</span>
              </button>`,
          ).join("")}
        </div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <h3 class="panel-title">近期状态</h3>
          <p class="panel-copy">快速确认运行环境是否健康。</p>
        </div>
        <div class="section-list">
          <article class="section-card">
            <strong>编排后端</strong>
            <p>${escapeHtml(state.health?.orchestrator_backend || "--")}</p>
          </article>
          <article class="section-card">
            <strong>向量后端</strong>
            <p>${escapeHtml(state.health?.vector_store_backend || "--")}</p>
          </article>
          <article class="section-card">
            <strong>当前主题</strong>
            <p>${escapeHtml(resolveTheme())}</p>
          </article>
        </div>
      </section>
    </div>
  `;
}

function renderDocumentSection() {
  const pendingList = state.pendingFiles.length
    ? `<ul class="pending-files">${state.pendingFiles
        .map((file) => `<li>${escapeHtml(file.name)}</li>`)
        .join("")}</ul>`
    : '<p class="meta-copy">支持多文件上传，上传后会自动进入解析轮询。</p>';

  const listContent = state.documentsLoading
    ? renderSkeleton(3)
    : state.documentsError
      ? `<div class="inline-message" data-tone="error">${escapeHtml(state.documentsError)}</div>`
      : state.documents.length === 0
        ? renderEmpty("当前没有符合筛选条件的文档。")
        : `<div class="document-list">${state.documents
            .map((doc) => {
              const isChecked = state.selectedDocumentIds.includes(doc.id);
              const parserName = doc.metadata?.parser_name || "parser pending";
              return `
                <article class="document-row">
                  <input
                    type="checkbox"
                    data-toggle-doc="${doc.id}"
                    ${isChecked ? "checked" : ""}
                    ${doc.parse_status !== "parsed" ? "disabled" : ""}
                    aria-label="选择 ${escapeHtml(doc.filename)}"
                  />
                  <div class="document-main">
                    <div class="document-title-row">
                      <strong class="document-title">${escapeHtml(doc.filename)}</strong>
                      ${renderPill(doc.parse_status, doc.parse_status === "parsed" ? "success" : "warning")}
                    </div>
                    <div class="document-meta">
                      <span>${escapeHtml(doc.id)}</span>
                      <span>${escapeHtml(formatDate(doc.upload_time))}</span>
                      <span>${escapeHtml(parserName)}</span>
                    </div>
                    <div class="selection-chips">
                      ${(doc.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("") || '<span class="meta-copy">无标签</span>'}
                    </div>
                  </div>
                  <button class="ghost-button" type="button" data-delete-doc="${doc.id}">删除</button>
                </article>`;
            })
            .join("")}</div>`;

  return `
    <div class="panel-grid">
      <section class="panel">
        <div class="panel-header">
          <h3 class="panel-title">上传与解析</h3>
          <p class="panel-copy">直接映射到 `/ingestion/upload`，并针对多文件上传增加状态反馈。</p>
        </div>
        <form id="upload-form" class="form-stack">
          <label class="field">
            <span class="field-label">团队 ID</span>
            <input type="text" name="uploadTeamId" value="${escapeHtml(state.uploadTeamId)}" />
          </label>
          <label class="field">
            <span class="field-label">标签</span>
            <input
              type="text"
              name="uploadTags"
              value="${escapeHtml(state.uploadTags)}"
              placeholder="例如：PRD, 风险, 客户洞察"
            />
          </label>
          <label class="field">
            <span class="field-label">解析模式</span>
            <select name="uploadParseMode">
              ${PARSE_MODES.map(
                (mode) => `<option value="${mode}" ${mode === state.uploadParseMode ? "selected" : ""}>${mode}</option>`,
              ).join("")}
            </select>
          </label>
          <label class="upload-dropzone">
            <strong>选择待解析文件</strong>
            <span class="meta-copy">最小可见反馈与批量文件列表会即时更新。</span>
            <input type="file" name="pendingFiles" multiple />
            <span class="secondary-button">浏览文件</span>
          </label>
          ${pendingList}
          <button class="primary-button" type="submit" ${state.uploading ? "disabled" : ""}>
            ${state.uploading ? "正在提交解析任务…" : "提交解析"}
          </button>
        </form>
      </section>

      <section class="panel panel-span-2">
        <div class="panel-header">
          <h3 class="panel-title">文档库</h3>
          <p class="panel-copy">支持筛选、批量选择、轮询刷新和跨模块复用。</p>
        </div>
        <form id="document-filters-form" class="toolbar">
          <div class="split-row">
            <label class="field">
              <span class="field-label">关键字</span>
              <input type="text" name="docKeyword" value="${escapeHtml(state.docKeyword)}" placeholder="文件名或关键词" />
            </label>
            <label class="field">
              <span class="field-label">状态</span>
              <select name="docStatus">
                <option value="all" ${state.docStatus === "all" ? "selected" : ""}>全部</option>
                <option value="uploaded" ${state.docStatus === "uploaded" ? "selected" : ""}>uploaded</option>
                <option value="parsed" ${state.docStatus === "parsed" ? "selected" : ""}>parsed</option>
              </select>
            </label>
            <label class="field">
              <span class="field-label">标签</span>
              <input type="text" name="docTags" value="${escapeHtml(state.docTags)}" placeholder="逗号分隔标签" />
            </label>
          </div>
          <div class="toolbar-actions">
            <button class="secondary-button" type="submit" ${state.documentsLoading ? "disabled" : ""}>应用筛选</button>
            <button class="ghost-button" type="button" data-action="select-all-docs">全选已解析</button>
            <button class="ghost-button" type="button" data-action="clear-selected-docs">清空已选</button>
          </div>
        </form>
        ${listContent}
      </section>
    </div>
  `;
}

function renderRetrievalSection() {
  const results = state.retrievalResult?.results || [];
  return `
    <div class="panel-grid">
      <section class="panel">
        <div class="panel-header">
          <h3 class="panel-title">检索请求</h3>
          <p class="panel-copy">支持 Top K、Hybrid Alpha、标签与日期过滤，并强化前端校验。</p>
        </div>
        <form id="retrieval-form" class="form-stack">
          <label class="field">
            <span class="field-label">检索问题</span>
            <textarea name="retrievalQuery" rows="6">${escapeHtml(state.retrievalQuery)}</textarea>
          </label>
          <label class="field">
            <span class="field-label">Top K</span>
            <input type="number" min="1" max="20" name="retrievalTopK" value="${state.retrievalTopK}" />
          </label>
          <label class="field">
            <span class="field-label">Hybrid Alpha</span>
            <div class="range-row">
              <input type="range" min="0" max="1" step="0.05" name="retrievalAlpha" value="${state.retrievalAlpha}" />
              <span class="field-hint">${state.retrievalAlpha.toFixed(2)}</span>
            </div>
          </label>
          <label class="field">
            <span class="field-label">标签过滤</span>
            <input type="text" name="retrievalTags" value="${escapeHtml(state.retrievalTags)}" placeholder="例如：PRD, 风险" />
          </label>
          <label class="field">
            <span class="field-label">起始日期</span>
            <input type="date" name="retrievalDateAfter" value="${escapeHtml(state.retrievalDateAfter)}" />
          </label>
          <button class="primary-button" type="submit" ${state.retrievalLoading ? "disabled" : ""}>
            ${state.retrievalLoading ? "正在检索…" : "执行检索"}
          </button>
        </form>
      </section>

      <section class="panel panel-span-2">
        <div class="panel-header">
          <h3 class="panel-title">证据结果</h3>
          <p class="panel-copy">以得分条、元数据与内容预览的形式显示召回结果。</p>
        </div>
        ${
          state.retrievalLoading
            ? renderSkeleton(3)
            : results.length === 0
              ? renderEmpty("提交检索后，这里会展示可追溯证据结果。")
              : `<div class="result-list">${results
                  .map((item) => {
                    const width = Math.max(8, Math.min(100, Number(item.score) * 100));
                    return `
                      <article class="result-card">
                        <div class="result-head">
                          <strong>${escapeHtml(item.document_id)}</strong>
                          ${renderPill(`score ${Number(item.score).toFixed(3)}`)}
                        </div>
                        <div class="score-meter"><span style="width: ${width}%"></span></div>
                        <p>${escapeHtml(truncate(item.text, 360))}</p>
                        <div class="code-block"><pre>${escapeHtml(formatJson(item.metadata || {}))}</pre></div>
                      </article>`;
                  })
                  .join("")}</div>`
        }
      </section>
    </div>
  `;
}

function renderReportSection() {
  const result = state.reportResult;
  return `
    <div class="panel-grid">
      <section class="panel">
        <div class="panel-header">
          <h3 class="panel-title">报告配置</h3>
          <p class="panel-copy">生成 grounded 报告，且默认启用引用来源。</p>
        </div>
        <form id="report-form" class="form-stack">
          <label class="field">
            <span class="field-label">报告主体</span>
            <input type="text" name="reportEntity" value="${escapeHtml(state.reportEntity)}" placeholder="例如：TeamMindHub Q1 项目" />
          </label>
          <label class="field">
            <span class="field-label">报告类型</span>
            <select name="reportType">
              ${REPORT_TYPES.map(
                (item) => `<option value="${item.value}" ${item.value === state.reportType ? "selected" : ""}>${escapeHtml(item.label)}</option>`,
              ).join("")}
            </select>
          </label>
          <label class="field">
            <span class="field-label">最大章节数</span>
            <input type="number" min="1" max="12" name="reportMaxSections" value="${state.reportMaxSections}" />
          </label>
          <label class="toggle-row">
            <span class="field-label">包含来源</span>
            <input type="checkbox" name="reportIncludeSources" ${state.reportIncludeSources ? "checked" : ""} />
          </label>
          <button class="primary-button" type="submit" ${state.reportLoading ? "disabled" : ""}>
            ${state.reportLoading ? "正在生成报告…" : "生成报告"}
          </button>
        </form>
      </section>

      <section class="panel panel-span-2">
        <div class="panel-header">
          <h3 class="panel-title">报告结果</h3>
          <p class="panel-copy">章节化展示、来源清单与整体摘要同时保留。</p>
        </div>
        ${
          state.reportLoading
            ? renderSkeleton(3)
            : !result
              ? renderEmpty("填写实体后即可生成结构化报告。")
              : `
                <div class="section-list">
                  <article class="section-card">
                    <div class="result-head">
                      <strong>${escapeHtml(result.title)}</strong>
                      ${renderPill(`${result.sources_count} 个来源`, "success")}
                    </div>
                    <p>${escapeHtml(result.overall_summary)}</p>
                    <span class="meta-copy">${escapeHtml(formatDate(result.generated_at))}</span>
                  </article>
                  ${result.sections
                    .map(
                      (section) => `
                        <article class="section-card">
                          <div class="result-head">
                            <strong>${escapeHtml(section.section)}</strong>
                            ${renderPill(`${section.sources.length} 个引用`)}
                          </div>
                          <p>${escapeHtml(section.content)}</p>
                          <div class="selection-chips">
                            ${section.sources.map((source) => `<span class="selection-chip">${escapeHtml(source)}</span>`).join("")}
                          </div>
                        </article>`,
                    )
                    .join("")}
                </div>`
        }
      </section>
    </div>
  `;
}

function renderAnalysisSection() {
  const result = state.analysisResult;
  return `
    <div class="panel-grid">
      <section class="panel">
        <div class="panel-header">
          <h3 class="panel-title">分析任务</h3>
          <p class="panel-copy">从已选解析文档出发，输出摘要、统计和完整原始结果。</p>
        </div>
        <form id="analysis-form" class="form-stack">
          <label class="field">
            <span class="field-label">分析任务</span>
            <textarea name="analysisTask" rows="6">${escapeHtml(state.analysisTask)}</textarea>
          </label>
          <label class="field">
            <span class="field-label">输出格式</span>
            <select name="analysisFormat">
              ${ANALYSIS_FORMATS.map(
                (item) => `<option value="${item}" ${item === state.analysisFormat ? "selected" : ""}>${item}</option>`,
              ).join("")}
            </select>
          </label>
          <div class="section-callout">
            <strong>当前证据集</strong>
            <div class="selection-chips">
              ${selectedDocuments().map((doc) => `<span class="selection-chip">${escapeHtml(doc.filename)}</span>`).join("") || '<span class="meta-copy">尚未选择解析完成的文档。</span>'}
            </div>
          </div>
          <button class="primary-button" type="submit" ${state.analysisLoading ? "disabled" : ""}>
            ${state.analysisLoading ? "正在执行分析…" : "执行分析"}
          </button>
        </form>
      </section>

      <section class="panel panel-span-2">
        <div class="panel-header">
          <h3 class="panel-title">分析结果</h3>
          <p class="panel-copy">摘要与原始结果分层展示，便于继续处理或复制到外部系统。</p>
        </div>
        ${
          state.analysisLoading
            ? renderSkeleton(3)
            : !result
              ? renderEmpty("选择文档并提交任务后，这里会展示分析结果。")
              : `
                <div class="detail-grid">
                  <article class="section-card">
                    <div class="result-head">
                      <strong>${escapeHtml(result.task_id)}</strong>
                      ${renderPill(state.analysisFormat)}
                    </div>
                    <p>${escapeHtml(String(result.results?.summary || "暂无摘要"))}</p>
                  </article>
                  <article class="section-card">
                    <div class="result-head">
                      <strong>图表描述</strong>
                      ${renderPill("Chart")}
                    </div>
                    <p>${escapeHtml(String(result.results?.chart_description || "暂无图表建议"))}</p>
                  </article>
                </div>
                <div class="code-block"><pre>${escapeHtml(formatJson(result.results || {}))}</pre></div>`
        }
      </section>
    </div>
  `;
}

function renderIntegrationSection() {
  const result = state.mergeResult;
  return `
    <div class="panel-grid">
      <section class="panel">
        <div class="panel-header">
          <h3 class="panel-title">统合策略</h3>
          <p class="panel-copy">将已选文档组合成单一产物，适合报告上游或审阅复用。</p>
        </div>
        <form id="integration-form" class="form-stack">
          <label class="field">
            <span class="field-label">策略</span>
            <select name="mergeStrategy">
              ${MERGE_STRATEGIES.map(
                (item) => `<option value="${item}" ${item === state.mergeStrategy ? "selected" : ""}>${item}</option>`,
              ).join("")}
            </select>
          </label>
          <label class="field">
            <span class="field-label">输出格式</span>
            <select name="mergeFormat">
              ${MERGE_FORMATS.map(
                (item) => `<option value="${item}" ${item === state.mergeFormat ? "selected" : ""}>${item}</option>`,
              ).join("")}
            </select>
          </label>
          <div class="section-callout">
            <strong>当前证据集</strong>
            <div class="selection-chips">
              ${selectedDocuments().map((doc) => `<span class="selection-chip">${escapeHtml(doc.filename)}</span>`).join("") || '<span class="meta-copy">尚未选择解析完成的文档。</span>'}
            </div>
          </div>
          <button class="primary-button" type="submit" ${state.mergeLoading ? "disabled" : ""}>
            ${state.mergeLoading ? "正在统合…" : "生成统合产物"}
          </button>
        </form>
      </section>

      <section class="panel panel-span-2">
        <div class="panel-header">
          <h3 class="panel-title">统合结果</h3>
          <p class="panel-copy">完整保留文本内容和可复制操作，方便后续进入报告或外部工作流。</p>
        </div>
        ${
          state.mergeLoading
            ? renderSkeleton(2)
            : !result
              ? renderEmpty("选择至少一份文档后即可生成统合结果。")
              : `
                <article class="section-card">
                  <div class="result-head">
                    <strong>合并完成</strong>
                    ${renderPill(`${result.source_count} 份来源`, "success")}
                  </div>
                  <p>输出总长度 ${result.total_length} 字符。</p>
                  <div class="inline-actions">
                    <button class="secondary-button" type="button" data-copy="${escapeHtml(result.merged_content)}">复制全文</button>
                  </div>
                </article>
                <div class="code-block"><pre>${escapeHtml(result.merged_content)}</pre></div>`
        }
      </section>
    </div>
  `;
}

function renderInstallerSection() {
  return `
    <div class="panel-grid">
      <section class="panel">
        <div class="panel-header">
          <h3 class="panel-title">仓库搜索</h3>
          <p class="panel-copy">搜索 GitHub 开源项目，并在确认后注册为 TeamMindHub 工具。</p>
        </div>
        <form id="installer-form" class="form-stack">
          <label class="field">
            <span class="field-label">搜索关键字</span>
            <input type="text" name="installerQuery" value="${escapeHtml(state.installerQuery)}" placeholder="例如：langgraph workflow" />
          </label>
          <div class="chip-row">
            ${INSTALLER_SUGGESTIONS.map(
              (item) => `
                <button class="chip-button" type="button" data-suggestion="${item}">
                  ${escapeHtml(item)}
                </button>`,
            ).join("")}
          </div>
          <button class="primary-button" type="submit" ${state.installerLoading ? "disabled" : ""}>
            ${state.installerLoading ? "正在搜索…" : "搜索 GitHub 仓库"}
          </button>
        </form>
        ${
          state.installerResult
            ? `
              <article class="section-callout">
                <strong>${escapeHtml(state.installerResult.tool_name)}</strong>
                <span class="meta-copy">${escapeHtml(state.installerResult.message)}</span>
                <span class="meta-copy">${escapeHtml(state.installerResult.installed_path)}</span>
              </article>`
            : ""
        }
      </section>

      <section class="panel panel-span-2">
        <div class="panel-header">
          <h3 class="panel-title">候选仓库</h3>
          <p class="panel-copy">强化加载反馈、按钮防抖和安装确认，避免重复提交。</p>
        </div>
        ${
          state.installerLoading
            ? renderSkeleton(3)
            : state.installerResults.length === 0
              ? renderEmpty("输入查询后，这里会显示候选仓库列表。")
              : `<div class="tool-list">${state.installerResults
                  .map(
                    (item) => `
                      <article class="tool-card">
                        <div class="tool-head">
                          <strong>${escapeHtml(item.name)}</strong>
                          ${renderPill(`${item.stars} stars`)}
                        </div>
                        <p>${escapeHtml(item.description || item.readme_summary || "暂无描述")}</p>
                        <div class="document-meta">
                          <span>${escapeHtml(item.license || "未知许可")}</span>
                          <a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">查看仓库</a>
                        </div>
                        <button
                          class="secondary-button"
                          type="button"
                          data-install-repo="${escapeHtml(item.url)}"
                          ${state.installingRepo === item.url ? "disabled" : ""}
                        >
                          ${state.installingRepo === item.url ? "正在接入…" : "接入 TeamMindHub"}
                        </button>
                      </article>`,
                  )
                  .join("")}</div>`
        }
      </section>
    </div>
  `;
}

function renderOrchestratorSection() {
  const agents = state.health?.available_agents || [];
  return `
    <div class="panel-grid">
      <section class="panel">
        <div class="panel-header">
          <h3 class="panel-title">主代理任务</h3>
          <p class="panel-copy">支持普通执行与流式执行两种模式，流式模式会实时刷新 trace。</p>
        </div>
        <form id="orchestrator-form" class="form-stack">
          <label class="field">
            <span class="field-label">主代理</span>
            <select name="orchestratorAgent">
              ${agents.map((agent) => `<option value="${escapeHtml(agent)}" ${agent === state.orchestratorAgent ? "selected" : ""}>${escapeHtml(agent)}</option>`).join("")}
            </select>
          </label>
          <label class="field">
            <span class="field-label">任务描述</span>
            <textarea name="orchestratorTask" rows="7">${escapeHtml(state.orchestratorTask)}</textarea>
          </label>
          <div class="split-row">
            <label class="field">
              <span class="field-label">Max Steps</span>
              <input type="number" min="1" max="50" name="orchestratorMaxSteps" value="${state.orchestratorMaxSteps}" />
            </label>
            <label class="field">
              <span class="field-label">Timeout</span>
              <input type="number" min="30" max="1200" name="orchestratorTimeout" value="${state.orchestratorTimeout}" />
            </label>
          </div>
          <label class="toggle-row">
            <span class="field-label">实时流式追踪</span>
            <input type="checkbox" name="orchestratorStream" ${state.orchestratorStream ? "checked" : ""} />
          </label>
          <button class="primary-button" type="submit" ${state.orchestratorLoading ? "disabled" : ""}>
            ${state.orchestratorLoading ? "正在调度…" : "调度主代理"}
          </button>
        </form>
      </section>

      <section class="panel panel-span-2">
        <div class="panel-header">
          <h3 class="panel-title">执行追踪</h3>
          <p class="panel-copy">流式模式下会先显示 trace，再在末尾写入完整结果。</p>
        </div>
        ${
          state.orchestratorLoading && state.orchestratorEvents.length === 0
            ? renderSkeleton(2)
            : state.orchestratorEvents.length === 0 && !state.orchestratorResult
              ? renderEmpty("提交主代理任务后，实时 trace 会显示在这里。")
              : `
                <div class="trace-list">
                  ${state.orchestratorEvents
                    .map(
                      (event, index) => `
                        <article class="trace-card">
                          <div class="trace-head">
                            <strong>${escapeHtml(event.event === "result" ? "最终结果" : "Trace Event")}</strong>
                            ${renderPill(event.event)}
                          </div>
                          ${
                            event.event === "trace"
                              ? `
                                <div class="trace-row">
                                  <div class="trace-step">${index + 1}</div>
                                  <div class="trace-content">
                                    <strong>${escapeHtml(String(event.data.action || "step"))}</strong>
                                    <span>${escapeHtml(String(event.data.timestamp || "--"))}</span>
                                  </div>
                                </div>`
                              : `<div class="code-block"><pre>${escapeHtml(formatJson(event.data || {}))}</pre></div>`
                          }
                        </article>`,
                    )
                    .join("")}
                  ${
                    state.orchestratorResult
                      ? `
                        <article class="section-card">
                          <div class="result-head">
                            <strong>${escapeHtml(state.orchestratorResult.main_agent)}</strong>
                            ${renderPill(state.orchestratorResult.status, "success")}
                          </div>
                          <p>规划后端：${escapeHtml(state.orchestratorResult.planning_backend)}</p>
                          <div class="code-block"><pre>${escapeHtml(formatJson(state.orchestratorResult.result || {}))}</pre></div>
                        </article>`
                      : ""
                  }
                </div>`
        }
      </section>
    </div>
  `;
}

function renderHealthSection() {
  const health = state.health || {};
  const metrics = [
    ["向量后端", health.vector_store_backend || "--"],
    ["检索后端", health.retrieval_backend || "--"],
    ["编排后端", health.orchestrator_backend || "--"],
    ["任务规划", health.task_planning_backend || "--"],
    ["分析生成", health.analysis_generation_backend || "--"],
    ["报告生成", health.report_generation_backend || "--"],
  ];
  return `
    <div class="panel-grid">
      <section class="panel panel-span-2">
        <div class="panel-header">
          <h3 class="panel-title">运行指标</h3>
          <p class="panel-copy">基于 `/health` 实时渲染，保留所有关键后端字段。</p>
        </div>
        ${
          state.bootstrapping && !state.health
            ? renderSkeleton(3)
            : `<div class="health-grid">${metrics
                .map(
                  ([label, value]) => `
                    <article class="metric-card">
                      <span>${escapeHtml(label)}</span>
                      <strong>${escapeHtml(String(value))}</strong>
                      <small>runtime status</small>
                    </article>`,
                )
                .join("")}</div>`
        }
      </section>

      <section class="panel">
        <div class="panel-header">
          <h3 class="panel-title">能力开关</h3>
          <p class="panel-copy">便于确认 PRD 所需开源组件当前启停情况。</p>
        </div>
        <div class="section-list">
          <article class="section-card"><strong>Deep Parse</strong><p>${escapeHtml((health.deep_parser_backends || []).join(", ") || "disabled")}</p></article>
          <article class="section-card"><strong>LangGraph</strong><p>${health.langgraph_enabled ? "enabled" : "disabled"}</p></article>
          <article class="section-card"><strong>LlamaIndex</strong><p>${health.llamaindex_enabled ? "enabled" : "disabled"}</p></article>
          <article class="section-card"><strong>RAGFlow</strong><p>${health.ragflow_enabled ? "enabled" : "disabled"}</p></article>
        </div>
      </section>

      <section class="panel panel-span-2">
        <div class="panel-header">
          <h3 class="panel-title">工具注册表</h3>
          <p class="panel-copy">内置 schema 与已安装工具统一出现在这里。</p>
        </div>
        ${
          state.bootstrapping && state.tools.length === 0
            ? renderSkeleton(2)
            : state.tools.length === 0
              ? renderEmpty("当前还没有可展示的工具 schema。")
              : `<div class="tool-list">${state.tools
                  .map(
                    (tool) => `
                      <article class="tool-card">
                        <div class="tool-head">
                          <strong>${escapeHtml(tool.name)}</strong>
                          ${renderPill(`${Object.keys(tool.parameters?.properties || {}).length} 个参数`)}
                        </div>
                        <p>${escapeHtml(tool.description)}</p>
                      </article>`,
                  )
                  .join("")}</div>`
        }
      </section>
    </div>
  `;
}

function renderContent() {
  switch (state.mode) {
    case "documents":
      return renderDocumentSection();
    case "retrieval":
      return renderRetrievalSection();
    case "report":
      return renderReportSection();
    case "analysis":
      return renderAnalysisSection();
    case "integration":
      return renderIntegrationSection();
    case "installer":
      return renderInstallerSection();
    case "orchestrator":
      return renderOrchestratorSection();
    case "health":
      return renderHealthSection();
    default:
      return renderOverview();
  }
}

function renderStatusBar() {
  return `
    <footer class="workspace-status">
      <span><strong>当前模块</strong> ${escapeHtml(activeNav().label)}</span>
      <span><strong>解析文档</strong> ${parsedDocuments().length}</span>
      <span><strong>已选证据</strong> ${state.selectedDocumentIds.length}</span>
      <span><strong>主代理</strong> ${escapeHtml(state.orchestratorAgent || state.health?.main_orchestrator || "--")}</span>
      <span><strong>向量后端</strong> ${escapeHtml(state.health?.vector_store_backend || "--")}</span>
      <span><strong>主题</strong> ${escapeHtml(resolveTheme())}</span>
      <span class="inline-actions"><span class="status-dot"></span>${state.isOnline ? "same-origin online" : "offline shell available"}</span>
    </footer>
  `;
}

function render() {
  app.innerHTML = `
    <div class="app-shell ${state.mobileSidebarOpen ? "is-sidebar-open" : ""}">
      ${renderRail()}
      ${renderSidebar()}
      <section class="workspace">
        ${renderTopbar()}
        <main id="main-content" class="workspace-main">
          ${renderBanner()}
          ${renderContent()}
        </main>
        ${renderStatusBar()}
      </section>
      <button class="backdrop-scrim" type="button" data-action="close-sidebar" aria-label="关闭侧栏"></button>
    </div>
  `;
}

async function api(path, options = {}) {
  const controller = new AbortController();
  const timeout = options.timeout ?? 30000;
  const timeoutId = window.setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(path, {
      ...options,
      signal: controller.signal,
      headers: {
        ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...(options.headers || {}),
      },
    });

    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      const message =
        typeof payload === "string"
          ? payload
          : payload?.detail?.message || payload?.detail || payload?.message || `请求失败: ${response.status}`;
      throw new Error(String(message));
    }

    return payload;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("请求超时，请稍后重试。");
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function streamSse(path, payload, onEvent) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `请求失败: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const normalized = buffer.replaceAll("\r", "");
    const chunks = normalized.split("\n\n");
    buffer = chunks.pop() || "";

    for (const chunk of chunks) {
      if (!chunk.trim()) continue;
      let eventName = "message";
      let eventData = "";
      for (const line of chunk.split("\n")) {
        if (line.startsWith("event:")) {
          eventName = line.slice(6).trim();
        }
        if (line.startsWith("data:")) {
          eventData += line.slice(5).trim();
        }
      }
      onEvent({
        event: eventName,
        data: eventData ? JSON.parse(eventData) : null,
      });
    }

    if (done) {
      break;
    }
  }
}

async function loadHealth() {
  const payload = await api("/health", { timeout: 8000 });
  state.health = payload;
  if (!state.orchestratorAgent && Array.isArray(payload.available_agents) && payload.available_agents.length > 0) {
    state.orchestratorAgent = payload.available_agents[0];
  }
}

async function loadTools() {
  const payload = await api("/tools", { timeout: 8000 });
  state.tools = payload.tools || [];
}

function stopDocumentPolling() {
  if (documentPollHandle) {
    window.clearTimeout(documentPollHandle);
    documentPollHandle = null;
  }
  documentPollAttempts = 0;
}

function scheduleDocumentPolling() {
  if (documentPollHandle || documentPollAttempts >= 6) {
    return;
  }
  documentPollAttempts += 1;
  documentPollHandle = window.setTimeout(async () => {
    documentPollHandle = null;
    await loadDocuments({ silent: true });
  }, 2800);
}

async function loadDocuments({ silent = false } = {}) {
  state.documentsLoading = true;
  if (!silent) {
    render();
  }
  try {
    const params = new URLSearchParams({
      page: "1",
      page_size: "100",
    });
    if (state.docKeyword.trim()) params.set("keyword", state.docKeyword.trim());
    if (state.docStatus !== "all") params.set("status", state.docStatus);
    if (state.docTags.trim()) params.set("tags", state.docTags.trim());
    const payload = await api(`/ingestion/documents?${params.toString()}`, { timeout: 8000 });
    state.documents = payload.documents || [];
    state.documentTotal = payload.total || 0;
    state.documentsError = "";
    ensureSelectedDocumentsAreValid();
    if (state.documents.some((item) => item.parse_status !== "parsed")) {
      scheduleDocumentPolling();
    } else {
      stopDocumentPolling();
    }
  } catch (error) {
    state.documentsError = error.message || "无法读取文档列表。";
  } finally {
    state.documentsLoading = false;
    render();
  }
}

async function refreshAll({ announce = false } = {}) {
  if (!state.bootstrapping) {
    setFlash("info", "正在同步后端状态与控制台数据…", { sticky: true });
  }
  try {
    await Promise.all([loadHealth(), loadTools(), loadDocuments({ silent: true })]);
    state.bootstrapping = false;
    if (announce) {
      setFlash("success", "健康状态、工具注册表与文档列表已刷新。");
    } else {
      render();
    }
  } catch (error) {
    state.bootstrapping = false;
    setFlash("error", error.message || "刷新失败。", { sticky: true });
  }
}

async function handleUpload() {
  if (state.uploading) return;
  if (state.pendingFiles.length === 0) {
    setFlash("error", "请先选择至少一份文档。", { sticky: true });
    return;
  }
  state.uploading = true;
  render();
  try {
    const formData = new FormData();
    for (const file of state.pendingFiles) {
      formData.append("files", file);
    }
    formData.append("team_id", state.uploadTeamId.trim() || "default");
    if (state.uploadTags.trim()) formData.append("tags", state.uploadTags.trim());
    formData.append("parse_mode", state.uploadParseMode);
    const payload = await api("/ingestion/upload", {
      method: "POST",
      body: formData,
      headers: {},
      timeout: 60000,
    });
    state.pendingFiles = [];
    setFlash("success", payload.message || "解析任务已提交。");
    await loadDocuments();
  } catch (error) {
    setFlash("error", error.message || "上传失败。", { sticky: true });
  } finally {
    state.uploading = false;
    render();
  }
}

async function handleRetrieval() {
  if (!state.retrievalQuery.trim()) {
    setFlash("error", "请输入检索问题。", { sticky: true });
    return;
  }
  state.retrievalLoading = true;
  render();
  try {
    state.retrievalResult = await api("/retrieval/search", {
      method: "POST",
      body: JSON.stringify({
        query: state.retrievalQuery.trim(),
        top_k: clampInt(state.retrievalTopK, 1, 20, 8),
        hybrid_alpha: clampFloat(state.retrievalAlpha, 0, 1, 0.7),
        filters: {
          tags: splitTags(state.retrievalTags),
          date_after: state.retrievalDateAfter || null,
        },
      }),
    });
    setFlash("success", `检索完成，返回 ${state.retrievalResult.total_found} 条结果。`);
  } catch (error) {
    setFlash("error", error.message || "检索失败。", { sticky: true });
  } finally {
    state.retrievalLoading = false;
    render();
  }
}

async function handleReport() {
  if (!state.reportEntity.trim()) {
    setFlash("error", "请输入报告主体。", { sticky: true });
    return;
  }
  state.reportLoading = true;
  render();
  try {
    state.reportResult = await api("/report/generate", {
      method: "POST",
      body: JSON.stringify({
        entity: state.reportEntity.trim(),
        report_type: state.reportType,
        include_sources: state.reportIncludeSources,
        max_sections: clampInt(state.reportMaxSections, 1, 12, 4),
      }),
    });
    setFlash("success", `报告生成完成，共 ${state.reportResult.sections.length} 个章节。`);
  } catch (error) {
    setFlash("error", error.message || "报告生成失败。", { sticky: true });
  } finally {
    state.reportLoading = false;
    render();
  }
}

async function handleAnalysis() {
  if (!state.analysisTask.trim()) {
    setFlash("error", "请输入分析任务。", { sticky: true });
    return;
  }
  if (state.selectedDocumentIds.length === 0) {
    setFlash("error", "请先选择至少一份解析完成的文档。", { sticky: true });
    return;
  }
  state.analysisLoading = true;
  render();
  try {
    state.analysisResult = await api("/analysis/execute", {
      method: "POST",
      body: JSON.stringify({
        task: state.analysisTask.trim(),
        document_ids: state.selectedDocumentIds,
        output_format: state.analysisFormat,
      }),
    });
    setFlash("success", "分析任务执行完成。");
  } catch (error) {
    setFlash("error", error.message || "分析执行失败。", { sticky: true });
  } finally {
    state.analysisLoading = false;
    render();
  }
}

async function handleIntegration() {
  if (state.selectedDocumentIds.length === 0) {
    setFlash("error", "统合前请先选择至少一份文档。", { sticky: true });
    return;
  }
  state.mergeLoading = true;
  render();
  try {
    state.mergeResult = await api("/integration/merge", {
      method: "POST",
      body: JSON.stringify({
        document_ids: state.selectedDocumentIds,
        rule: {
          strategy: state.mergeStrategy,
          format: state.mergeFormat,
        },
      }),
    });
    setFlash("success", `统合完成，共处理 ${state.mergeResult.source_count} 份文档。`);
  } catch (error) {
    setFlash("error", error.message || "统合失败。", { sticky: true });
  } finally {
    state.mergeLoading = false;
    render();
  }
}

async function handleInstallerSearch() {
  if (!state.installerQuery.trim()) {
    setFlash("error", "请输入 GitHub 搜索关键字。", { sticky: true });
    return;
  }
  state.installerLoading = true;
  render();
  try {
    const payload = await api("/installer/search", {
      method: "POST",
      body: JSON.stringify({ query: state.installerQuery.trim() }),
    });
    state.installerResults = payload.results || [];
    setFlash("success", `已找到 ${payload.total} 个候选仓库。`);
  } catch (error) {
    setFlash("error", error.message || "搜索仓库失败。", { sticky: true });
  } finally {
    state.installerLoading = false;
    render();
  }
}

async function handleInstallerInstall(repoUrl) {
  if (state.installingRepo) return;
  const confirmed = window.confirm(`将把 ${repoUrl} 接入 TeamMindHub，是否继续？`);
  if (!confirmed) return;
  state.installingRepo = repoUrl;
  render();
  try {
    state.installerResult = await api("/installer/install", {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl, confirm: true }),
      timeout: 60000,
    });
    await loadTools();
    setFlash("success", state.installerResult.message || "仓库接入完成。");
  } catch (error) {
    setFlash("error", error.message || "仓库接入失败。", { sticky: true });
  } finally {
    state.installingRepo = "";
    render();
  }
}

async function handleOrchestrator() {
  if (!state.orchestratorTask.trim()) {
    setFlash("error", "请输入要交给主代理的任务。", { sticky: true });
    return;
  }
  state.orchestratorLoading = true;
  state.orchestratorEvents = [];
  state.orchestratorResult = null;
  render();
  const payload = {
    main_agent: state.orchestratorAgent || null,
    task: state.orchestratorTask.trim(),
    parameters: {
      max_steps: clampInt(state.orchestratorMaxSteps, 1, 50, 10),
      timeout: clampInt(state.orchestratorTimeout, 30, 1200, 300),
      stream: state.orchestratorStream,
    },
  };
  try {
    if (state.orchestratorStream) {
      await streamSse("/orchestrator/run", payload, (event) => {
        state.orchestratorEvents.push(event);
        if (event.event === "result") {
          state.orchestratorResult = event.data;
        }
        render();
      });
      setFlash("success", "主代理流式执行完成。");
    } else {
      state.orchestratorResult = await api("/orchestrator/run", {
        method: "POST",
        body: JSON.stringify(payload),
        timeout: 60000,
      });
      setFlash("success", `主代理执行完成，状态为 ${state.orchestratorResult.status}。`);
    }
  } catch (error) {
    setFlash("error", error.message || "主代理执行失败。", { sticky: true });
  } finally {
    state.orchestratorLoading = false;
    render();
  }
}

async function deleteDocument(documentId) {
  const confirmed = window.confirm("删除后将移除该文档及其索引，是否继续？");
  if (!confirmed) return;
  try {
    const payload = await api(`/ingestion/${documentId}`, {
      method: "DELETE",
      headers: {},
    });
    setFlash("success", payload.message || "文档已删除。");
    await loadDocuments();
  } catch (error) {
    setFlash("error", error.message || "删除失败。", { sticky: true });
  }
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    setFlash("success", "内容已复制到剪贴板。");
  } catch {
    setFlash("error", "复制失败，请手动复制。", { sticky: true });
  }
}

async function promptInstall() {
  if (!deferredInstallPrompt) return;
  await deferredInstallPrompt.prompt();
  const choice = await deferredInstallPrompt.userChoice;
  if (choice.outcome === "accepted") {
    setFlash("success", "PWA 安装已确认。");
  } else {
    setFlash("warning", "已取消安装应用。");
  }
  deferredInstallPrompt = null;
  state.canInstall = false;
  render();
}

function updateStateFromField(target) {
  const { name, value, checked, files, type } = target;
  if (!name) return;

  switch (name) {
    case "moduleQuery":
      state.moduleQuery = value;
      break;
    case "uploadTeamId":
      state.uploadTeamId = value;
      break;
    case "uploadTags":
      state.uploadTags = value;
      break;
    case "uploadParseMode":
      state.uploadParseMode = value;
      break;
    case "pendingFiles":
      state.pendingFiles = Array.from(files || []);
      break;
    case "docKeyword":
      state.docKeyword = value;
      break;
    case "docStatus":
      state.docStatus = value;
      break;
    case "docTags":
      state.docTags = value;
      break;
    case "retrievalQuery":
      state.retrievalQuery = value;
      break;
    case "retrievalTopK":
      state.retrievalTopK = clampInt(value, 1, 20, 8);
      break;
    case "retrievalAlpha":
      state.retrievalAlpha = clampFloat(value, 0, 1, 0.7);
      break;
    case "retrievalTags":
      state.retrievalTags = value;
      break;
    case "retrievalDateAfter":
      state.retrievalDateAfter = value;
      break;
    case "reportEntity":
      state.reportEntity = value;
      break;
    case "reportType":
      state.reportType = value;
      break;
    case "reportIncludeSources":
      state.reportIncludeSources = checked;
      break;
    case "reportMaxSections":
      state.reportMaxSections = clampInt(value, 1, 12, 4);
      break;
    case "analysisTask":
      state.analysisTask = value;
      break;
    case "analysisFormat":
      state.analysisFormat = value;
      break;
    case "mergeStrategy":
      state.mergeStrategy = value;
      break;
    case "mergeFormat":
      state.mergeFormat = value;
      break;
    case "installerQuery":
      state.installerQuery = value;
      break;
    case "orchestratorAgent":
      state.orchestratorAgent = value;
      break;
    case "orchestratorTask":
      state.orchestratorTask = value;
      break;
    case "orchestratorMaxSteps":
      state.orchestratorMaxSteps = clampInt(value, 1, 50, 10);
      break;
    case "orchestratorTimeout":
      state.orchestratorTimeout = clampInt(value, 30, 1200, 300);
      break;
    case "orchestratorStream":
      state.orchestratorStream = type === "checkbox" ? checked : Boolean(value);
      break;
    default:
      break;
  }
}

function handleClick(event) {
  const nav = event.target.closest("[data-nav]");
  if (nav) {
    setMode(nav.dataset.nav);
    return;
  }

  const modeTrigger = event.target.closest("[data-mode]");
  if (modeTrigger) {
    setMode(modeTrigger.dataset.mode);
    return;
  }

  const group = event.target.closest("[data-group]");
  if (group) {
    state.moduleGroup = group.dataset.group;
    render();
    return;
  }

  const action = event.target.closest("[data-action]");
  if (action) {
    switch (action.dataset.action) {
      case "refresh":
        void refreshAll({ announce: true });
        return;
      case "theme-toggle":
        cycleTheme();
        return;
      case "dismiss-flash":
        clearFlash();
        return;
      case "toggle-sidebar":
        state.mobileSidebarOpen = !state.mobileSidebarOpen;
        render();
        return;
      case "close-sidebar":
        state.mobileSidebarOpen = false;
        render();
        return;
      case "select-all-docs":
        state.selectedDocumentIds = parsedDocuments().map((item) => item.id);
        persistSelectedDocuments();
        render();
        return;
      case "clear-selected-docs":
        state.selectedDocumentIds = [];
        persistSelectedDocuments();
        render();
        return;
      case "install-pwa":
        void promptInstall();
        return;
      default:
        break;
    }
  }

  const deleteButton = event.target.closest("[data-delete-doc]");
  if (deleteButton) {
    void deleteDocument(deleteButton.dataset.deleteDoc);
    return;
  }

  const installButton = event.target.closest("[data-install-repo]");
  if (installButton) {
    void handleInstallerInstall(installButton.dataset.installRepo);
    return;
  }

  const suggestion = event.target.closest("[data-suggestion]");
  if (suggestion) {
    state.installerQuery = suggestion.dataset.suggestion || "";
    render();
    return;
  }

  const copyButton = event.target.closest("[data-copy]");
  if (copyButton) {
    void copyToClipboard(copyButton.dataset.copy || "");
  }
}

function handleChange(event) {
  const toggle = event.target.closest("[data-toggle-doc]");
  if (toggle) {
    const documentId = toggle.dataset.toggleDoc;
    state.selectedDocumentIds = toggle.checked
      ? Array.from(new Set([...state.selectedDocumentIds, documentId]))
      : state.selectedDocumentIds.filter((item) => item !== documentId);
    persistSelectedDocuments();
    render();
    return;
  }

  updateStateFromField(event.target);
  render();
}

function handleInput(event) {
  updateStateFromField(event.target);
  render();
}

function handleSubmit(event) {
  event.preventDefault();
  switch (event.target.id) {
    case "upload-form":
      void handleUpload();
      break;
    case "document-filters-form":
      void loadDocuments();
      break;
    case "retrieval-form":
      void handleRetrieval();
      break;
    case "report-form":
      void handleReport();
      break;
    case "analysis-form":
      void handleAnalysis();
      break;
    case "integration-form":
      void handleIntegration();
      break;
    case "installer-form":
      void handleInstallerSearch();
      break;
    case "orchestrator-form":
      void handleOrchestrator();
      break;
    default:
      break;
  }
}

app.addEventListener("click", handleClick);
app.addEventListener("change", handleChange);
app.addEventListener("input", handleInput);
app.addEventListener("submit", handleSubmit);

window.addEventListener("online", () => {
  state.isOnline = true;
  setFlash("success", "网络已恢复，控制台可以继续同步。");
});

window.addEventListener("offline", () => {
  state.isOnline = false;
  setFlash("warning", "当前处于离线状态，已回退到离线外壳。", { sticky: true });
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  state.canInstall = true;
  render();
});

window.addEventListener("appinstalled", () => {
  deferredInstallPrompt = null;
  state.canInstall = false;
  setFlash("success", "TeamMindHub 已安装为桌面应用。");
});

themeMedia?.addEventListener("change", () => {
  if (state.themePreference === "system") {
    applyTheme();
    render();
  }
});

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  try {
    await navigator.serviceWorker.register("./sw.js", { scope: "./" });
  } catch {
    // best effort only
  }
}

async function bootstrap() {
  applyTheme();
  render();
  await Promise.all([registerServiceWorker(), refreshAll({ announce: false })]);
}

void bootstrap();
