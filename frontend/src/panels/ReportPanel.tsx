import { Layers3, LoaderCircle } from "lucide-react";
import type { ReportResponse } from "../api";
import { REPORT_TYPES } from "../constants";
import { EmptyState, SectionHeading, formatDate } from "../shared";

export function ReportPanel(props: {
  reportEntity: string;
  reportType: string;
  reportIncludeSources: boolean;
  reportMaxSections: number;
  reportLoading: boolean;
  reportResult: ReportResponse | null;
  onEntityChange: (value: string) => void;
  onTypeChange: (value: string) => void;
  onIncludeSourcesChange: (value: boolean) => void;
  onMaxSectionsChange: (value: number) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>;
}) {
  return (
    <div className="content-grid">
      <section className="panel">
        <SectionHeading
          title="报告配置"
          description="使用知识库证据自动生成结构化章节。"
          hint="如果你已经在检索页确认过证据，这里更适合做最终沉淀和可交付文本输出。"
        />
        <form className="stacked-form" onSubmit={props.onSubmit}>
          <label>
            报告主体
            <input value={props.reportEntity} onChange={(event) => props.onEntityChange(event.target.value)} />
          </label>
          <label>
            报告类型
            <select value={props.reportType} onChange={(event) => props.onTypeChange(event.target.value)}>
              {REPORT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </label>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={props.reportIncludeSources}
              onChange={(event) => props.onIncludeSourcesChange(event.target.checked)}
            />
            <span>附带来源文档 ID</span>
          </label>
          <label>
            最大章节数
            <input
              type="range"
              min={1}
              max={8}
              value={props.reportMaxSections}
              onChange={(event) => props.onMaxSectionsChange(Number(event.target.value))}
            />
            <span className="field-hint">{props.reportMaxSections}</span>
          </label>
          <button className="primary-button" type="submit" disabled={props.reportLoading}>
            {props.reportLoading ? <LoaderCircle className="spin" size={16} /> : <Layers3 size={16} />}
            生成结构化报告
          </button>
        </form>
      </section>

      <section className="panel panel-span-2">
        <SectionHeading
          title="报告结果"
          description="章节、摘要和来源引用统一在这里呈现。"
          hint="如果某个章节过短，通常意味着主体太宽泛，建议回到左侧收紧主题或切换报告类型。"
        />
        {props.reportResult ? (
          <div className="report-view">
            <article className="highlight-card">
              <strong>{props.reportResult.title}</strong>
              <p>{props.reportResult.overall_summary}</p>
              <div className="meta-row">
                <span>来源数 {props.reportResult.sources_count}</span>
                <span>{formatDate(props.reportResult.generated_at)}</span>
              </div>
            </article>
            {props.reportResult.sections.map((section) => (
              <article key={section.section} className="section-card">
                <div className="result-head">
                  <strong>{section.section}</strong>
                  <span>{section.sources.length > 0 ? `来源 ${section.sources.join(", ")}` : "未附来源"}</span>
                </div>
                <p>{section.content}</p>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState text="配置主体与类型后即可出报告。" />
        )}
      </section>
    </div>
  );
}
