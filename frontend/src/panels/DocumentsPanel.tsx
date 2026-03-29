import { LoaderCircle, Trash2, UploadCloud } from "lucide-react";
import type { DocumentSummary } from "../api";
import { EmptyState, InlineError, LoadingBlock, SectionHeading, formatDate } from "../shared";

function formatParseModeLabel(value: string) {
  switch (value) {
    case "deep":
      return "深度解析";
    case "auto":
      return "自动判断";
    case "fast":
      return "快速解析";
    default:
      return value;
  }
}

function formatParseStatusLabel(value: string) {
  switch (value) {
    case "uploaded":
      return "已上传";
    case "parsed":
      return "已解析";
    default:
      return value;
  }
}

export function DocumentsPanel(props: {
  uploadTeamId: string;
  uploadTags: string;
  uploadParseMode: string;
  pendingFiles: File[];
  uploading: boolean;
  docKeyword: string;
  docStatus: string;
  docTags: string;
  documents: DocumentSummary[];
  documentsLoading: boolean;
  documentsError: string | null;
  selectedDocumentIds: string[];
  fileInputRef: React.RefObject<HTMLInputElement>;
  onUploadTeamIdChange: (value: string) => void;
  onUploadTagsChange: (value: string) => void;
  onUploadParseModeChange: (value: string) => void;
  onFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onUpload: (event: React.FormEvent<HTMLFormElement>) => Promise<void>;
  onDocKeywordChange: (value: string) => void;
  onDocStatusChange: (value: string) => void;
  onDocTagsChange: (value: string) => void;
  onToggleDocument: (documentId: string) => void;
  onDeleteDocument: (documentId: string) => Promise<void>;
}) {
  return (
    <div className="content-grid">
      <section className="panel">
        <SectionHeading
          title="上传与解析"
          description="表单字段与 `/ingestion/upload` 接口保持一致。"
          hint="团队 ID 用于隔离文档空间，标签用于后续检索筛选；深度解析适合高质量抽取，快速解析适合先看结构。"
        />
        <form className="stacked-form" onSubmit={props.onUpload}>
          <label>
            团队 ID
            <input value={props.uploadTeamId} onChange={(event) => props.onUploadTeamIdChange(event.target.value)} />
          </label>
          <label>
            标签
            <input
              value={props.uploadTags}
              onChange={(event) => props.onUploadTagsChange(event.target.value)}
              placeholder="例如：PRD、风险、客户洞察"
            />
          </label>
          <label>
            解析模式
            <select value={props.uploadParseMode} onChange={(event) => props.onUploadParseModeChange(event.target.value)}>
              <option value="deep">{formatParseModeLabel("deep")}</option>
              <option value="auto">{formatParseModeLabel("auto")}</option>
              <option value="fast">{formatParseModeLabel("fast")}</option>
            </select>
          </label>
          <label className="upload-dropzone">
            <UploadCloud size={18} />
            <span>{props.pendingFiles.length > 0 ? `已选择 ${props.pendingFiles.length} 个文件` : "点击选择或拖入文件"}</span>
            <input ref={props.fileInputRef} type="file" multiple onChange={props.onFileChange} />
          </label>
          <button className="primary-button" type="submit" disabled={props.uploading}>
            {props.uploading ? <LoaderCircle className="spin" size={16} /> : <UploadCloud size={16} />}
            提交解析任务
          </button>
        </form>
      </section>

      <section className="panel panel-span-2">
        <SectionHeading
          title="文档池"
          description="可在这里筛选、选择、删除并查看文档元数据。"
          hint="只有解析完成的文档才能进入分析、报告和统合流程。"
        />
        <div className="toolbar">
          <input
            value={props.docKeyword}
            onChange={(event) => props.onDocKeywordChange(event.target.value)}
            placeholder="按文件名或文本关键词过滤"
          />
          <select value={props.docStatus} onChange={(event) => props.onDocStatusChange(event.target.value)}>
            <option value="all">全部状态</option>
            <option value="uploaded">{formatParseStatusLabel("uploaded")}</option>
            <option value="parsed">{formatParseStatusLabel("parsed")}</option>
          </select>
          <input value={props.docTags} onChange={(event) => props.onDocTagsChange(event.target.value)} placeholder="按标签过滤" />
        </div>
        {props.documentsLoading ? (
          <LoadingBlock text="正在同步文档池..." />
        ) : props.documentsError ? (
          <InlineError text={props.documentsError} />
        ) : (
          <div className="document-list">
            {props.documents.map((document) => (
              <article key={document.id} className="document-card">
                <label className="document-main">
                  <input
                    type="checkbox"
                    checked={props.selectedDocumentIds.includes(document.id)}
                    disabled={document.parse_status !== "parsed"}
                    onChange={() => props.onToggleDocument(document.id)}
                  />
                  <div>
                    <strong>{document.filename}</strong>
                    <p>{document.id}</p>
                    <div className="meta-row">
                      <span>{formatDate(document.upload_time)}</span>
                      <span>{String(document.metadata.parser_name ?? "解析器待定")}</span>
                      <span>{document.tags.join(" / ") || "无标签"}</span>
                    </div>
                  </div>
                </label>
                <div className="document-actions">
                  <span className={`status-badge status-${document.parse_status}`}>{formatParseStatusLabel(document.parse_status)}</span>
                  <button type="button" className="icon-button" onClick={() => void props.onDeleteDocument(document.id)}>
                    <Trash2 size={15} />
                  </button>
                </div>
              </article>
            ))}
            {props.documents.length === 0 && <EmptyState text="当前过滤条件下没有文档。" />}
          </div>
        )}
      </section>
    </div>
  );
}
