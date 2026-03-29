import { GitBranch, LoaderCircle } from "lucide-react";
import type { DocumentSummary, MergeResponse } from "../api";
import { EmptyState, SectionHeading } from "../shared";

function formatMergeStrategyLabel(value: string) {
  switch (value) {
    case "concatenate":
      return "顺序拼接";
    case "timeline":
      return "时间线整理";
    case "topic":
      return "按主题聚合";
    default:
      return value;
  }
}

function formatMergeFormatLabel(value: string) {
  switch (value) {
    case "markdown":
      return "Markdown 文本";
    case "text":
      return "纯文本";
    default:
      return value;
  }
}

export function IntegrationPanel(props: {
  mergeStrategy: string;
  mergeFormat: string;
  mergeLoading: boolean;
  mergeResult: MergeResponse | null;
  selectedDocuments: DocumentSummary[];
  onStrategyChange: (value: string) => void;
  onFormatChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>;
}) {
  return (
    <div className="content-grid">
      <section className="panel">
        <SectionHeading
          title="统合参数"
          description="把多份材料整理成一个可复用产物。"
          hint="时间线整理适合过程型材料，顺序拼接适合完整归并，按主题聚合适合做综述和归档。"
        />
        <form className="stacked-form" onSubmit={props.onSubmit}>
          <label>
            策略
            <select value={props.mergeStrategy} onChange={(event) => props.onStrategyChange(event.target.value)}>
              <option value="concatenate">{formatMergeStrategyLabel("concatenate")}</option>
              <option value="timeline">{formatMergeStrategyLabel("timeline")}</option>
              <option value="topic">{formatMergeStrategyLabel("topic")}</option>
            </select>
          </label>
          <label>
            输出格式
            <select value={props.mergeFormat} onChange={(event) => props.onFormatChange(event.target.value)}>
              <option value="markdown">{formatMergeFormatLabel("markdown")}</option>
              <option value="text">{formatMergeFormatLabel("text")}</option>
            </select>
          </label>
          <div className="selection-summary">
            {props.selectedDocuments.map((document) => (
              <span key={document.id} className="selected-chip">
                {document.filename}
              </span>
            ))}
            {props.selectedDocuments.length === 0 && <EmptyState text="当前没有选中的文档。" compact />}
          </div>
          <button className="primary-button" type="submit" disabled={props.mergeLoading}>
            {props.mergeLoading ? <LoaderCircle className="spin" size={16} /> : <GitBranch size={16} />}
            生成统合产物
          </button>
        </form>
      </section>

      <section className="panel panel-span-2">
        <SectionHeading
          title="统合结果"
          description="适合直接进入报告或审阅流程。"
          hint="如果正文太长，可以改用“按主题聚合”或“时间线整理”再生成一版更易读的结果。"
        />
        {props.mergeResult ? (
          <div className="report-view">
            <article className="highlight-card">
              <strong>合并完成</strong>
              <p>
                共纳入 {props.mergeResult.source_count} 份文档，输出长度 {props.mergeResult.total_length} 字符。
              </p>
            </article>
            <article className="section-card">
              <div className="result-head">
                <strong>合并正文</strong>
                <span>{formatMergeFormatLabel(props.mergeFormat)}</span>
              </div>
              <pre>{props.mergeResult.merged_content}</pre>
            </article>
          </div>
        ) : (
          <EmptyState text="选择文档后生成聚合内容。" />
        )}
      </section>
    </div>
  );
}
