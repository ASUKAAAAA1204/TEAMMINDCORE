import { Database, LoaderCircle } from "lucide-react";
import type { AnalysisResponse, DocumentSummary } from "../api";
import { EmptyState, SectionHeading, safeStringify } from "../shared";

function formatOutputLabel(value: string) {
  switch (value) {
    case "json":
      return "结构化 JSON";
    case "markdown":
      return "Markdown 文本";
    case "text":
      return "纯文本";
    default:
      return value;
  }
}

export function AnalysisPanel(props: {
  analysisTask: string;
  analysisFormat: string;
  analysisLoading: boolean;
  analysisResult: AnalysisResponse | null;
  parsedDocuments: DocumentSummary[];
  selectedDocumentIds: string[];
  onTaskChange: (value: string) => void;
  onFormatChange: (value: string) => void;
  onToggleDocument: (documentId: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>;
}) {
  return (
    <div className="content-grid">
      <section className="panel">
        <SectionHeading
          title="分析任务"
          description="围绕已解析文档执行任务分析。"
          hint="建议把任务描述写成一个明确问题，例如“这份材料重点在讲什么”或“抽取销售趋势与风险点”。"
        />
        <form className="stacked-form" onSubmit={props.onSubmit}>
          <label>
            任务描述
            <textarea value={props.analysisTask} onChange={(event) => props.onTaskChange(event.target.value)} rows={5} />
          </label>
          <label>
            输出格式
            <select value={props.analysisFormat} onChange={(event) => props.onFormatChange(event.target.value)}>
              <option value="json">{formatOutputLabel("json")}</option>
              <option value="markdown">{formatOutputLabel("markdown")}</option>
              <option value="text">{formatOutputLabel("text")}</option>
            </select>
          </label>
          <div className="picker-shell">
            <div className="picker-head">
              <strong>已选文档</strong>
              <span>
                {props.selectedDocumentIds.length} / {props.parsedDocuments.length}
              </span>
            </div>
            <div className="picker-list">
              {props.parsedDocuments.map((document) => (
                <label key={document.id} className="picker-item">
                  <input
                    type="checkbox"
                    checked={props.selectedDocumentIds.includes(document.id)}
                    onChange={() => props.onToggleDocument(document.id)}
                  />
                  <span>{document.filename}</span>
                </label>
              ))}
              {props.parsedDocuments.length === 0 && <EmptyState text="先在文档页完成解析。" compact />}
            </div>
          </div>
          <button className="primary-button" type="submit" disabled={props.analysisLoading}>
            {props.analysisLoading ? <LoaderCircle className="spin" size={16} /> : <Database size={16} />}
            执行分析
          </button>
        </form>
      </section>

      <section className="panel panel-span-2">
        <SectionHeading
          title="分析结果"
          description="摘要、统计和图表建议会被拆开显示。"
          hint="如果统计为空，优先检查文档是否解析完成，或把任务描述改得更具体。"
        />
        {props.analysisResult ? (
          <div className="analysis-grid">
            <article className="highlight-card">
              <strong>{props.analysisResult.task_id}</strong>
              <p>{String(props.analysisResult.results.summary ?? "暂无摘要。")}</p>
            </article>
            <article className="section-card">
              <div className="result-head">
                <strong>统计概览</strong>
                <span>{formatOutputLabel(String(props.analysisResult.results.output_format ?? props.analysisFormat))}</span>
              </div>
              <pre>{safeStringify(props.analysisResult.results.statistics ?? {})}</pre>
            </article>
            <article className="section-card">
              <div className="result-head">
                <strong>图表建议</strong>
                <span>图表描述</span>
              </div>
              <p>{String(props.analysisResult.results.chart_description ?? "暂无图表建议。")}</p>
            </article>
            <article className="section-card">
              <div className="result-head">
                <strong>完整结果</strong>
                <span>原始 JSON</span>
              </div>
              <pre>{safeStringify(props.analysisResult.results)}</pre>
            </article>
          </div>
        ) : (
          <EmptyState text="选择文档并提交任务后，这里会输出分析结果。" />
        )}
      </section>
    </div>
  );
}
