import { Bot, LoaderCircle } from "lucide-react";
import type { OrchestratorResponse } from "../api";
import { EmptyState, SectionHeading, formatDate, safeStringify } from "../shared";

export function OrchestratorPanel(props: {
  orchestratorTask: string;
  orchestratorAgent: string;
  orchestratorMaxSteps: number;
  orchestratorTimeout: number;
  orchestratorLoading: boolean;
  orchestratorResult: OrchestratorResponse | null;
  availableAgents: string[];
  onTaskChange: (value: string) => void;
  onAgentChange: (value: string) => void;
  onMaxStepsChange: (value: number) => void;
  onTimeoutChange: (value: number) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>;
}) {
  return (
    <div className="content-grid">
      <section className="panel">
        <SectionHeading
          title="代理任务"
          description="把多步骤任务交给主代理统一调度。"
          hint="适合需要先检索、再分析、再汇总的复杂任务；简单任务优先用单模块更直接。"
        />
        <form className="stacked-form" onSubmit={props.onSubmit}>
          <label>
            主代理
            <select value={props.orchestratorAgent} onChange={(event) => props.onAgentChange(event.target.value)}>
              {props.availableAgents.map((agent) => (
                <option key={agent} value={agent}>
                  {agent}
                </option>
              ))}
            </select>
          </label>
          <label>
            任务描述
            <textarea value={props.orchestratorTask} onChange={(event) => props.onTaskChange(event.target.value)} rows={6} />
          </label>
          <label>
            最大步数
            <input
              type="number"
              min={1}
              max={50}
              value={props.orchestratorMaxSteps}
              onChange={(event) => props.onMaxStepsChange(Number(event.target.value))}
            />
          </label>
          <label>
            超时时间（秒）
            <input
              type="number"
              min={30}
              max={1200}
              value={props.orchestratorTimeout}
              onChange={(event) => props.onTimeoutChange(Number(event.target.value))}
            />
          </label>
          <button className="primary-button" type="submit" disabled={props.orchestratorLoading}>
            {props.orchestratorLoading ? <LoaderCircle className="spin" size={16} /> : <Bot size={16} />}
            调度主代理
          </button>
        </form>
      </section>

      <section className="panel panel-span-2">
        <SectionHeading
          title="执行追踪"
          description="逐步展示代理调用链和最终结果。"
          hint="先看步骤轨迹，再看最终结果，可以更快判断代理在哪一步做出了错误决策。"
        />
        {props.orchestratorResult ? (
          <div className="report-view">
            <article className="highlight-card">
              <strong>{props.orchestratorResult.main_agent}</strong>
              <p>
                任务 {props.orchestratorResult.task_id} 已于 {formatDate(props.orchestratorResult.executed_at)} 完成。
              </p>
              <div className="meta-row">
                <span>{props.orchestratorResult.status}</span>
                <span>规划后端：{props.orchestratorResult.planning_backend}</span>
              </div>
            </article>
            <article className="section-card">
              <div className="result-head">
                <strong>轨迹</strong>
                <span>{props.orchestratorResult.trace.length} 步</span>
              </div>
              <div className="timeline">
                {props.orchestratorResult.trace.map((row, index) => (
                  <div key={`${row.timestamp}-${index}`} className="timeline-row">
                    <span>{String(row.step ?? index + 1)}</span>
                    <div>
                      <strong>{String(row.action ?? "step")}</strong>
                      <p>{String(row.timestamp ?? "")}</p>
                    </div>
                  </div>
                ))}
              </div>
            </article>
            <article className="section-card">
              <div className="result-head">
                <strong>最终结果</strong>
                <span>JSON</span>
              </div>
              <pre>{safeStringify(props.orchestratorResult.result)}</pre>
            </article>
          </div>
        ) : (
          <EmptyState text="这里会显示主代理的执行轨迹与结果。" />
        )}
      </section>
    </div>
  );
}
