import { AlertTriangle, CheckCircle2, LoaderCircle, Network, type LucideIcon } from "lucide-react";

export type FlashTone = "success" | "error" | "neutral";

export interface FlashMessage {
  tone: FlashTone;
  text: string;
}

export function SectionHeading(props: { title: string; description: string; hint?: string }) {
  return (
    <div className="section-heading">
      <strong>{props.title}</strong>
      <p>{props.description}</p>
      {props.hint ? <small className="section-hint">{props.hint}</small> : null}
    </div>
  );
}

export function EmptyState(props: { text: string; compact?: boolean }) {
  return <div className={`empty-state ${props.compact ? "is-compact" : ""}`}>{props.text}</div>;
}

export function LoadingBlock(props: { text: string }) {
  return (
    <div className="loading-block">
      <LoaderCircle className="spin" size={18} />
      <span>{props.text}</span>
    </div>
  );
}

export function InlineError(props: { text: string }) {
  return (
    <div className="inline-error">
      <AlertTriangle size={16} />
      <span>{props.text}</span>
    </div>
  );
}

export function StatusPill(props: { icon: LucideIcon; text: string }) {
  const Icon = props.icon;
  return (
    <span className="status-pill">
      <Icon size={14} />
      {props.text}
    </span>
  );
}

export function FlashIcon(props: { tone: FlashTone }) {
  if (props.tone === "success") {
    return <CheckCircle2 size={16} />;
  }
  if (props.tone === "error") {
    return <AlertTriangle size={16} />;
  }
  return <Network size={16} />;
}

export function formatDate(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function safeStringify(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function truncate(text: string, max = 180) {
  if (text.length <= max) {
    return text;
  }
  return `${text.slice(0, max)}...`;
}

export function splitTags(raw: string) {
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
