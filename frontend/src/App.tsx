import { useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  FileText,
  Loader2,
  RefreshCw,
  ShieldAlert,
  Table2,
  UploadCloud
} from "lucide-react";
import { analyzeReport } from "./api";
import type { FindingResponse, MetricResponse, ReportAnalysisResponse, RiskLevel } from "./types";

const levelLabels: Record<string, string> = {
  high: "高",
  medium: "中",
  low: "低"
};

const levelOrder = ["high", "medium", "low"];

export function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [includeAi, setIncludeAi] = useState(true);
  const [result, setResult] = useState<ReportAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const groupedFindings = useMemo(() => groupFindings(result?.findings ?? []), [result]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile || isLoading) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const analysis = await analyzeReport(selectedFile, { includeAi });
      setResult(analysis);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "分析失败，请稍后重试。");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="control-panel" aria-label="财报上传和分析设置">
          <div className="brand-row">
            <div className="brand-mark">C</div>
            <div>
              <h1>Cara 财报风险分析</h1>
              <p>确定性抽取优先，AI 只做证据解读。</p>
            </div>
          </div>

          <form className="upload-form" onSubmit={handleSubmit}>
            <label className="file-drop">
              <UploadCloud aria-hidden="true" />
              <span>{selectedFile ? selectedFile.name : "选择 .pdf、.txt、.md 财报文件"}</span>
              <input
                type="file"
                accept=".pdf,.txt,.md,.text"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
            </label>

            <label className="toggle-row">
              <input
                type="checkbox"
                checked={includeAi}
                onChange={(event) => setIncludeAi(event.target.checked)}
              />
              <span>生成 AI 解读</span>
            </label>

            <button className="primary-button" type="submit" disabled={!selectedFile || isLoading}>
              {isLoading ? <Loader2 className="spin" aria-hidden="true" /> : <ShieldAlert aria-hidden="true" />}
              <span>{isLoading ? "分析中" : "开始分析"}</span>
            </button>
          </form>

          {error && (
            <div className="error-box" role="alert">
              <AlertTriangle aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          <div className="status-strip">
            <CheckCircle2 aria-hidden="true" />
            <span>后端默认地址：127.0.0.1:8000</span>
          </div>
        </aside>

        <section className="results-panel" aria-label="财报分析结果">
          {!result ? (
            <EmptyState />
          ) : (
            <>
              <SummaryHeader result={result} />

              <section className="content-grid">
                <div className="analysis-column">
                  {result.ai_summary && (
                    <section className="panel-section ai-panel">
                      <div className="section-title">
                        <Bot aria-hidden="true" />
                        <h2>AI 解读</h2>
                      </div>
                      <MarkdownPreview markdown={result.ai_summary} />
                    </section>
                  )}

                  <section className="panel-section">
                    <div className="section-title">
                      <ShieldAlert aria-hidden="true" />
                      <h2>风险发现</h2>
                    </div>
                    <RiskGroups groups={groupedFindings} />
                  </section>
                </div>

                <div className="analysis-column">
                  <section className="panel-section">
                    <div className="section-title">
                      <Table2 aria-hidden="true" />
                      <h2>抽取指标</h2>
                    </div>
                    <MetricsTable metrics={result.metrics} />
                  </section>

                  <section className="panel-section">
                    <div className="section-title">
                      <FileText aria-hidden="true" />
                      <h2>Markdown 报告</h2>
                    </div>
                    <pre className="markdown-preview">{result.markdown}</pre>
                  </section>
                </div>
              </section>
            </>
          )}
        </section>
      </section>
    </main>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <RefreshCw aria-hidden="true" />
      <h2>上传财报后查看风险分析</h2>
      <p>结果会展示公司快照、风险分数、指标证据、风险分组和报告预览。</p>
    </div>
  );
}

function SummaryHeader({ result }: { result: ReportAnalysisResponse }) {
  const snapshot = result.snapshot;
  return (
    <header className="summary-header">
      <div>
        <p className="eyebrow">分析对象</p>
        <h2>{snapshot.company_name ?? "未知公司"}</h2>
        <p className="summary-meta">
          {[snapshot.report_period, snapshot.report_type, snapshot.source_path].filter(Boolean).join(" / ")}
        </p>
      </div>

      <div className="score-block">
        <span>风险分数</span>
        <strong>{result.score}</strong>
      </div>

      <div className="counts-row" aria-label="风险等级统计">
        {levelOrder.map((level) => (
          <div className={`count-pill ${level}`} key={level}>
            <span>{levelLabels[level]}</span>
            <strong>{result.summary_counts[level] ?? 0}</strong>
          </div>
        ))}
      </div>
    </header>
  );
}

function RiskGroups({ groups }: { groups: Record<string, FindingResponse[]> }) {
  if (Object.values(groups).every((items) => items.length === 0)) {
    return <p className="muted">基于已抽取指标，暂未发现明显的规则化风险信号。</p>;
  }

  return (
    <div className="risk-list">
      {levelOrder.map((level) =>
        groups[level]?.map((finding) => (
          <article className={`risk-item ${level}`} key={`${level}-${finding.title}`}>
            <div className="risk-heading">
              <span>{levelLabels[finding.level] ?? finding.level}</span>
              <h3>{finding.title}</h3>
            </div>
            <p>{finding.description}</p>
            <div className="evidence-list">
              {finding.evidence.map((item) => (
                <blockquote key={item}>{item}</blockquote>
              ))}
            </div>
          </article>
        ))
      )}
    </div>
  );
}

function MetricsTable({ metrics }: { metrics: MetricResponse[] }) {
  if (metrics.length === 0) {
    return <p className="muted">未抽取到可展示的财务指标。</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>指标</th>
            <th>值</th>
            <th>证据行</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => (
            <tr key={metric.key}>
              <td>
                <strong>{metric.name}</strong>
                <span>{metric.key}</span>
              </td>
              <td>
                {formatNumber(metric.value)}
                {metric.unit ? ` ${metric.unit}` : ""}
              </td>
              <td>{metric.line_number ? `第 ${metric.line_number} 行` : "未标注"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MarkdownPreview({ markdown }: { markdown: string }) {
  return <div className="markdown-rendered">{renderMarkdownBlocks(markdown)}</div>;
}

function renderMarkdownBlocks(markdown: string) {
  const lines = markdown.replace(/\r\n/g, "\n").trim().split("\n");
  const blocks: ReactNode[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (!line.trim()) {
      index += 1;
      continue;
    }

    const fenceMatch = line.match(/^```(\S*)\s*$/);
    if (fenceMatch) {
      const codeLines: string[] = [];
      index += 1;

      while (index < lines.length && !/^```\s*$/.test(lines[index])) {
        codeLines.push(lines[index]);
        index += 1;
      }

      blocks.push(
        <pre className="md-code-block" key={`code-${index}`}>
          <code>{codeLines.join("\n")}</code>
        </pre>
      );
      index += 1;
      continue;
    }

    const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      blocks.push(renderMarkdownHeading(level, headingMatch[2], `heading-${index}`));
      index += 1;
      continue;
    }

    if (isTableStart(lines, index)) {
      const headers = splitTableRow(lines[index]);
      const rows: string[][] = [];
      index += 2;

      while (index < lines.length && lines[index].includes("|") && lines[index].trim()) {
        rows.push(splitTableRow(lines[index]));
        index += 1;
      }

      blocks.push(
        <div className="md-table-wrap" key={`table-${index}`}>
          <table>
            <thead>
              <tr>
                {headers.map((cell, cellIndex) => (
                  <th key={`head-${cellIndex}`}>{renderInlineMarkdown(cell, `head-${cellIndex}`)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={`row-${rowIndex}`}>
                  {headers.map((_, cellIndex) => (
                    <td key={`cell-${rowIndex}-${cellIndex}`}>
                      {renderInlineMarkdown(row[cellIndex] ?? "", `cell-${rowIndex}-${cellIndex}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    const unorderedMatch = line.match(/^\s*[-*+]\s+(.+)$/);
    const orderedMatch = line.match(/^\s*\d+[.)]\s+(.+)$/);
    if (unorderedMatch || orderedMatch) {
      const ordered = Boolean(orderedMatch);
      const items: string[] = [];

      while (index < lines.length) {
        const itemMatch = ordered
          ? lines[index].match(/^\s*\d+[.)]\s+(.+)$/)
          : lines[index].match(/^\s*[-*+]\s+(.+)$/);

        if (!itemMatch) {
          break;
        }

        items.push(itemMatch[1]);
        index += 1;
      }

      const ListTag = ordered ? "ol" : "ul";
      blocks.push(
        <ListTag key={`list-${index}`}>
          {items.map((item, itemIndex) => (
            <li key={`item-${itemIndex}`}>{renderInlineMarkdown(item, `item-${itemIndex}`)}</li>
          ))}
        </ListTag>
      );
      continue;
    }

    if (/^>\s?/.test(line)) {
      const quoteLines: string[] = [];

      while (index < lines.length && /^>\s?/.test(lines[index])) {
        quoteLines.push(lines[index].replace(/^>\s?/, ""));
        index += 1;
      }

      blocks.push(
        <blockquote className="md-blockquote" key={`quote-${index}`}>
          {renderInlineMarkdown(quoteLines.join("\n"), `quote-${index}`)}
        </blockquote>
      );
      continue;
    }

    const paragraphLines = [line.trim()];
    index += 1;

    while (index < lines.length && lines[index].trim() && !isMarkdownBlockStart(lines, index)) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }

    blocks.push(
      <p key={`paragraph-${index}`}>{renderInlineMarkdown(paragraphLines.join(" "), `paragraph-${index}`)}</p>
    );
  }

  return blocks;
}

function isMarkdownBlockStart(lines: string[], index: number) {
  const line = lines[index];
  return (
    /^```/.test(line) ||
    /^(#{1,4})\s+/.test(line) ||
    /^\s*[-*+]\s+/.test(line) ||
    /^\s*\d+[.)]\s+/.test(line) ||
    /^>\s?/.test(line) ||
    isTableStart(lines, index)
  );
}

function isTableStart(lines: string[], index: number) {
  return lines[index]?.includes("|") && Boolean(lines[index + 1]) && isTableSeparator(lines[index + 1]);
}

function isTableSeparator(line: string) {
  const cells = splitTableRow(line);
  return cells.length > 1 && cells.every((cell) => /^:?-{3,}:?$/.test(cell.trim()));
}

function splitTableRow(line: string) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function renderMarkdownHeading(level: number, text: string, key: string) {
  const content = renderInlineMarkdown(text, key);

  if (level === 1) {
    return (
      <h3 className="md-heading" key={key}>
        {content}
      </h3>
    );
  }

  if (level === 2) {
    return (
      <h4 className="md-heading" key={key}>
        {content}
      </h4>
    );
  }

  if (level === 3) {
    return (
      <h5 className="md-heading" key={key}>
        {content}
      </h5>
    );
  }

  return (
    <h6 className="md-heading" key={key}>
      {content}
    </h6>
  );
}

function renderInlineMarkdown(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const tokenPattern = /(`[^`]+`|\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = tokenPattern.exec(text))) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }

    const token = match[0];
    const key = `${keyPrefix}-${match.index}`;

    if (token.startsWith("`")) {
      nodes.push(<code key={key}>{token.slice(1, -1)}</code>);
    } else if (token.startsWith("[")) {
      const linkMatch = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      const href = linkMatch ? linkMatch[2] : "";
      nodes.push(
        <a href={getSafeHref(href)} key={key} rel="noreferrer" target="_blank">
          {linkMatch?.[1] ?? token}
        </a>
      );
    } else if (token.startsWith("**")) {
      nodes.push(<strong key={key}>{renderInlineMarkdown(token.slice(2, -2), key)}</strong>);
    } else {
      nodes.push(<em key={key}>{renderInlineMarkdown(token.slice(1, -1), key)}</em>);
    }

    lastIndex = tokenPattern.lastIndex;
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }

  return nodes;
}

function getSafeHref(href: string) {
  return /^(https?:|mailto:|#)/i.test(href) ? href : "#";
}

function groupFindings(findings: FindingResponse[]) {
  const groups: Record<string, FindingResponse[]> = {
    high: [],
    medium: [],
    low: []
  };

  for (const finding of findings) {
    const level = normalizeLevel(finding.level);
    groups[level] = groups[level] ?? [];
    groups[level].push(finding);
  }

  return groups;
}

function normalizeLevel(level: RiskLevel) {
  return levelOrder.includes(level) ? level : "low";
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("zh-CN", {
    maximumFractionDigits: 2
  }).format(value);
}
