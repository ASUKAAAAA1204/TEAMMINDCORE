import type { HealthResponse, ToolsResponse } from "../api";
import { SectionHeading } from "../shared";

export function HealthPanel(props: {
  health: HealthResponse | null;
  tools: ToolsResponse["tools"];
}) {
  return (
    <div className="content-grid">
      <section className="panel panel-span-2">
        <SectionHeading
          title="运行时健康"
          description="全部读取自 `/health` 与 `/tools`。"
          hint="这里是排查问题的第一站，尤其适合确认向量库、解析器和代理后端是否正常。"
        />
        <div className="stats-grid">
          {[
            ["向量后端", props.health?.vector_store_backend ?? "--"],
            ["检索后端", props.health?.retrieval_backend ?? "--"],
            ["编排后端", props.health?.orchestrator_backend ?? "--"],
            ["任务规划", props.health?.task_planning_backend ?? "--"],
            ["报告生成", props.health?.report_generation_backend ?? "--"],
            ["分析生成", props.health?.analysis_generation_backend ?? "--"],
          ].map(([label, value]) => (
            <article key={label} className="metric-card">
              <span>{label}</span>
              <strong>{value}</strong>
              <small>运行状态</small>
            </article>
          ))}
        </div>
        <div className="health-grid">
          {[
            ["深度解析", props.health?.deep_parser_backends.join(", ") || "已停用"],
            ["RAGFlow", props.health?.ragflow_enabled ? "已启用" : "已停用"],
            ["MinerU", props.health?.mineru_enabled ? "已启用" : "已停用"],
            ["LlamaIndex", props.health?.llamaindex_enabled ? "已启用" : "已停用"],
            ["LangGraph", props.health?.langgraph_enabled ? "已启用" : "已停用"],
            ["主代理", props.health?.main_orchestrator ?? "--"],
          ].map(([label, value]) => (
            <article key={label} className="section-card compact-card">
              <strong>{label}</strong>
              <p>{value}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <SectionHeading
          title="工具模式"
          description="安装器接入结果也会在这里出现。"
          hint="如果刚安装了工具但这里还没出现，先点击右上角刷新，再检查安装路径和健康状态。"
        />
        <div className="tool-list">
          {props.tools.map((tool) => (
            <article key={tool.name} className="tool-card">
              <strong>{tool.name}</strong>
              <p>{tool.description}</p>
              <small>{Object.keys(tool.parameters.properties ?? {}).length} 个参数字段</small>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
