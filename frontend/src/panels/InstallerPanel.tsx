import { CheckCircle2, ExternalLink, LoaderCircle, Wrench } from "lucide-react";
import type { InstallResponse, InstallerSearchResult } from "../api";
import { EmptyState, SectionHeading } from "../shared";

export function InstallerPanel(props: {
  installerQuery: string;
  installerLoading: boolean;
  installerResults: InstallerSearchResult[];
  installingRepo: string | null;
  installResult: InstallResponse | null;
  onQueryChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>;
  onInstall: (repoUrl: string) => Promise<void>;
}) {
  return (
    <div className="content-grid">
      <section className="panel">
        <SectionHeading
          title="仓库检索"
          description="让开源仓库进入 TeamMindHub 工具层。"
          hint="先用更宽一点的关键词找候选仓库，再结合许可证、描述和星标数做初筛。"
        />
        <form className="stacked-form" onSubmit={props.onSubmit}>
          <label>
            GitHub 关键词
            <input value={props.installerQuery} onChange={(event) => props.onQueryChange(event.target.value)} />
          </label>
          <button className="primary-button" type="submit" disabled={props.installerLoading}>
            {props.installerLoading ? <LoaderCircle className="spin" size={16} /> : <Wrench size={16} />}
            搜索开源仓库
          </button>
        </form>
        {props.installResult && (
          <article className="highlight-card compact-card">
            <strong>{props.installResult.tool_name}</strong>
            <p>{props.installResult.message}</p>
            <small>{props.installResult.installed_path}</small>
          </article>
        )}
      </section>

      <section className="panel panel-span-2">
        <SectionHeading
          title="候选仓库"
          description="可以直接确认安装并刷新工具模式。"
          hint="安装前先打开仓库链接查看 README；不要只根据星标数做决定。"
        />
        <div className="result-stack">
          {props.installerResults.map((item) => (
            <article key={item.url} className="result-card">
              <div className="result-head">
                <strong>{item.name}</strong>
                <span>{item.stars} 星标</span>
              </div>
              <p>{item.description || item.readme_summary}</p>
              <div className="meta-row">
                <span>{item.license || "未知许可证"}</span>
                <a href={item.url} target="_blank" rel="noreferrer">
                  仓库链接 <ExternalLink size={13} />
                </a>
              </div>
              <button
                type="button"
                className="secondary-button"
                onClick={() => void props.onInstall(item.url)}
                disabled={props.installingRepo === item.url}
              >
                {props.installingRepo === item.url ? <LoaderCircle className="spin" size={16} /> : <CheckCircle2 size={16} />}
                接入 TeamMindHub
              </button>
            </article>
          ))}
          {props.installerResults.length === 0 && <EmptyState text="输入检索词后，这里会显示候选开源仓库。" />}
        </div>
      </section>
    </div>
  );
}
