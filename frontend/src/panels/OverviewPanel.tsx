import { ArrowRight } from "lucide-react";
import type { DocumentSummary } from "../api";
import type { AccentStatus } from "../constants";
import { ACCENT_STATUSES, HERO_CHIPS, MODULE_CARDS } from "../constants";
import { EmptyState, SectionHeading } from "../shared";

export function OverviewPanel(props: {
  dashboardStats: Array<{ label: string; value: string; helper: string }>;
  documents: DocumentSummary[];
  onOpenModule: (moduleId: string) => void;
  onOpenStatus: (item: AccentStatus) => void;
}) {
  return (
    <div className="content-grid">
      <section className="panel panel-span-2 hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">工作总览</span>
          <h2>TeamMindHub 指挥总览</h2>
          <p>保留模板的深色导航与节点画布骨架，同时把所有语义重建为 TeamMindHub 的知识工作流。</p>
        </div>
        <div className="chip-row">
          {HERO_CHIPS.map((chip) => (
            <span key={chip} className="chip">
              {chip}
            </span>
          ))}
        </div>
        <div className="stats-grid">
          {props.dashboardStats.map((item) => (
            <article key={item.label} className="metric-card">
              <span>{item.label}</span>
              <strong>{item.value}</strong>
              <small>{item.helper}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <SectionHeading
          title="快速入口"
          description="这三张卡片现在可点击，用来快速跳转到最常用的视图。"
          hint="如果你不确定下一步做什么，可以先点“运行状态”检查当前后端与工具可用性。"
        />
        <div className="sidebar-footer">
          {ACCENT_STATUSES.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                type="button"
                className="sidebar-status sidebar-status-button"
                onClick={() => props.onOpenStatus(item)}
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
      </section>

      <section className="panel panel-span-2">
        <SectionHeading
          title="模块画布"
          description="按 TeamMindHub 的真实能力重组后的工作模块。"
          hint="每张卡片都附带一句提示，帮你判断这个模块最适合处理什么任务。"
        />
        <div className="node-board">
          {MODULE_CARDS.map((module) => (
            <button key={module.id} type="button" className="node-card" onClick={() => props.onOpenModule(module.id)}>
              <span className="node-badge">{module.badge}</span>
              <strong>{module.name}</strong>
              <p>{module.summary}</p>
              <small className="node-hint">{module.prompt}</small>
              <span className="node-link">
                进入模块
                <ArrowRight size={14} />
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="panel">
        <SectionHeading
          title="最新文档"
          description="最近进入工作台的知识源。"
          hint="如果这里为空，先去“文档接入”模块上传并完成解析。"
        />
        <div className="activity-list">
          {props.documents.slice(0, 5).map((document) => (
            <article key={document.id} className="activity-row">
              <div>
                <strong>{document.filename}</strong>
                <p>{document.id}</p>
              </div>
              <span className={`status-badge status-${document.parse_status}`}>{document.parse_status}</span>
            </article>
          ))}
          {props.documents.length === 0 && <EmptyState text="还没有已接入的文档。" />}
        </div>
      </section>
    </div>
  );
}
