import { FileSearch, LoaderCircle } from "lucide-react";
import type { SearchResponse } from "../api";
import { EmptyState, SectionHeading, safeStringify, truncate } from "../shared";

export function RetrievalPanel(props: {
  retrievalQuery: string;
  retrievalTopK: number;
  retrievalAlpha: number;
  retrievalTags: string;
  retrievalDate: string;
  retrievalLoading: boolean;
  retrievalResult: SearchResponse | null;
  onQueryChange: (value: string) => void;
  onTopKChange: (value: number) => void;
  onAlphaChange: (value: number) => void;
  onTagsChange: (value: string) => void;
  onDateChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>;
}) {
  return (
    <div className="content-grid">
      <section className="panel">
        <SectionHeading
          title="检索参数"
          description="通过自然语言问题、标签和日期范围定位证据。"
          hint="如果结果太宽泛，先缩小标签范围；如果结果太少，适当调高 Top K 或降低混合权重。"
        />
        <form className="stacked-form" onSubmit={props.onSubmit}>
          <label>
            检索问题
            <textarea value={props.retrievalQuery} onChange={(event) => props.onQueryChange(event.target.value)} rows={5} />
          </label>
          <label>
            返回条数 Top K
            <input
              type="number"
              min={1}
              max={20}
              value={props.retrievalTopK}
              onChange={(event) => props.onTopKChange(Number(event.target.value))}
            />
          </label>
          <label>
            混合权重 Alpha
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={props.retrievalAlpha}
              onChange={(event) => props.onAlphaChange(Number(event.target.value))}
            />
            <span className="field-hint">{props.retrievalAlpha.toFixed(2)}</span>
          </label>
          <label>
            标签过滤
            <input value={props.retrievalTags} onChange={(event) => props.onTagsChange(event.target.value)} />
          </label>
          <label>
            起始日期
            <input type="date" value={props.retrievalDate} onChange={(event) => props.onDateChange(event.target.value)} />
          </label>
          <button className="primary-button" type="submit" disabled={props.retrievalLoading}>
            {props.retrievalLoading ? <LoaderCircle className="spin" size={16} /> : <FileSearch size={16} />}
            执行混合检索
          </button>
        </form>
      </section>

      <section className="panel panel-span-2">
        <SectionHeading
          title="证据结果"
          description="直接展示召回内容、相关度和来源文档。"
          hint="这里展示的是证据片段，不是最终结论；需要汇总时请转到报告或分析模块。"
        />
        <div className="result-stack">
          {props.retrievalResult?.results.map((result, index) => (
            <article key={`${result.document_id}-${index}`} className="result-card">
              <div className="result-head">
                <strong>{result.document_id}</strong>
                <span>相关度 {result.score.toFixed(3)}</span>
              </div>
              <p>{truncate(result.text, 360)}</p>
              <pre>{safeStringify(result.metadata)}</pre>
            </article>
          ))}
          {props.retrievalResult && props.retrievalResult.results.length === 0 && <EmptyState text="没有召回到结果。" />}
          {!props.retrievalResult && <EmptyState text="提交查询后，结果将在这里展开。" />}
        </div>
      </section>
    </div>
  );
}
