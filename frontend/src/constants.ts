import {
  Activity,
  Bot,
  Boxes,
  Cable,
  FileScan,
  Files,
  LayoutDashboard,
  Library,
  Search,
  Sparkles,
} from "lucide-react";
import type { AppMode } from "./api";

export interface ModuleCard {
  id: string;
  name: string;
  badge: string;
  summary: string;
  prompt: string;
}

export interface AccentStatus {
  label: string;
  value: string;
  prompt: string;
  targetMode: AppMode;
  icon: typeof LayoutDashboard;
}

export const NAV_ITEMS: Array<{
  id: AppMode;
  label: string;
  shortLabel: string;
  icon: typeof LayoutDashboard;
}> = [
  { id: "overview", label: "总览中枢", shortLabel: "总览", icon: LayoutDashboard },
  { id: "documents", label: "文档接入", shortLabel: "文档", icon: Files },
  { id: "retrieval", label: "混合检索", shortLabel: "检索", icon: Search },
  { id: "report", label: "报告生成", shortLabel: "报告", icon: Library },
  { id: "analysis", label: "分析执行", shortLabel: "分析", icon: FileScan },
  { id: "integration", label: "内容统合", shortLabel: "统合", icon: Cable },
  { id: "installer", label: "开源安装器", shortLabel: "安装", icon: Boxes },
  { id: "orchestrator", label: "主编排代理", shortLabel: "编排", icon: Bot },
  { id: "health", label: "系统健康", shortLabel: "健康", icon: Activity },
];

export const MODULE_GROUPS = ["全部模块", "接口层", "AI 编排", "外部工具"] as const;

export const MODULE_CARDS: ModuleCard[] = [
  {
    id: "ingestion",
    name: "文档接入与解析",
    badge: "接口层",
    summary: "上传、多标签归档、深度解析链路。",
    prompt: "先上传文件并完成解析，后续检索、分析和报告都会复用这批文档。",
  },
  {
    id: "retrieval",
    name: "混合检索引擎",
    badge: "接口层",
    summary: "向量语义与关键词结果融合召回。",
    prompt: "用自然语言提问，结合标签和日期过滤，可以更快定位目标证据。",
  },
  {
    id: "report",
    name: "统合报告生成",
    badge: "AI 编排",
    summary: "跨文档摘要与结构化章节输出。",
    prompt: "适合沉淀项目综述、人物画像和销售分析等可直接交付的文本结果。",
  },
  {
    id: "analysis",
    name: "分析执行栈",
    badge: "AI 编排",
    summary: "面向任务的多文档分析执行。",
    prompt: "先勾选已解析文档，再写清问题或目标，系统会返回摘要、统计和图表建议。",
  },
  {
    id: "integration",
    name: "内容统合器",
    badge: "接口层",
    summary: "将多份内容压缩为单一合并产物。",
    prompt: "适合把多篇材料合并成一份供审阅、归档或二次报告使用的正文。",
  },
  {
    id: "installer",
    name: "GitHub 开源安装器",
    badge: "外部工具",
    summary: "检索仓库并接入为 TeamMindHub 工具。",
    prompt: "输入 GitHub 检索词后即可筛选候选仓库，并把合适工具接入当前工作台。",
  },
  {
    id: "orchestrator",
    name: "主编排代理",
    badge: "AI 编排",
    summary: "任务规划、调度与结果回写。",
    prompt: "适合多步骤任务，把检索、分析、报告和工具调用交给主代理统一编排。",
  },
  {
    id: "health",
    name: "运行时观测台",
    badge: "接口层",
    summary: "查看向量库、解析器与代理后端状态。",
    prompt: "遇到接口异常或结果不稳定时，先来这里确认运行后端、工具和解析链路是否正常。",
  },
];

export const REPORT_TYPES = [
  { value: "project_summary", label: "项目综述" },
  { value: "person_profile", label: "人物画像" },
  { value: "sales_analysis", label: "销售分析" },
];

export const QUICK_HINTS = [
  "先在文档接入页上传源文件，再进入检索、分析和报告页复用同一批文档。",
  "编排代理适合复杂自然语言任务，报告生成适合结构化输出。",
  "安装器可将新的开源仓库纳入工具目录，并在系统健康页确认是否接入成功。",
];

export const HERO_CHIPS = ["深度解析", "混合检索", "多代理编排", "本地优先"] as const;

export const ACCENT_STATUSES: AccentStatus[] = [
  {
    label: "知识工作台",
    value: "进入总览",
    prompt: "回到总览页，快速查看模块布局、核心指标和最近接入的文档。",
    targetMode: "overview",
    icon: Sparkles,
  },
  {
    label: "画布结构",
    value: "查看模块",
    prompt: "聚焦当前工作台的模块结构，快速切到文档、检索、报告或分析页。",
    targetMode: "overview",
    icon: LayoutDashboard,
  },
  {
    label: "交互焦点",
    value: "运行状态",
    prompt: "跳到系统健康页，检查后端、工具数量和当前运行链路是否可用。",
    targetMode: "health",
    icon: Bot,
  },
];
