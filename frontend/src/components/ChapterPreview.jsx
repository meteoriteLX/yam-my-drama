import { useState } from "react";

/**
 * @param {{ chapter: import('../types').ChapterItem }} props
 */
function ChapterCard({ chapter }) {
  const [expanded, setExpanded] = useState(false);
  const preview =
    chapter.content.length > 180
      ? `${chapter.content.slice(0, 180)}...`
      : chapter.content;

  return (
    <article className="chapter-card">
      <button
        type="button"
        className="chapter-card-header"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
      >
        <div className="chapter-title-wrap">
          <span className="chapter-badge">第 {chapter.chapter_number} 章</span>
          <h3>{chapter.title || "（无标题）"}</h3>
          <p className="chapter-heading">{chapter.heading}</p>
        </div>
        <div className="chapter-stats">
          <span>{chapter.char_count} 字</span>
          <span>{chapter.paragraph_count} 段</span>
          <span className="expand-icon">{expanded ? "收起" : "展开"}</span>
        </div>
      </button>

      <div className={`chapter-content ${expanded ? "expanded" : ""}`}>
        <pre>{expanded ? chapter.content : preview}</pre>
      </div>
    </article>
  );
}

/**
 * @param {{ result: import('../types').ChapterParseResult | null }} props
 */
export default function ChapterPreview({ result }) {
  if (!result) {
    return (
      <section className="card preview-panel preview-empty">
        <h2>章节预览</h2>
        <p className="muted">解析后将在此展示章节列表与正文摘要</p>
      </section>
    );
  }

  return (
    <section className="card preview-panel">
      <div className="panel-header">
        <h2>章节预览</h2>
        <div className={`status-badge ${result.valid ? "success" : "warning"}`}>
          {result.valid ? "校验通过" : "章节不足"}
        </div>
      </div>

      <div className={`result-banner ${result.valid ? "success" : "warning"}`}>
        <p className="result-message">{result.message}</p>
        <p className="result-meta">
          已识别 <strong>{result.chapter_count}</strong> 章 · 至少需要{" "}
          <strong>{result.min_chapters_required}</strong> 章
        </p>
      </div>

      {result.preamble && (
        <div className="preamble-box">
          <span className="label">序言 / 前言</span>
          <pre>{result.preamble}</pre>
        </div>
      )}

      <div className="chapter-list">
        {result.chapters.map((chapter) => (
          <ChapterCard key={`${chapter.chapter_number}-${chapter.heading}`} chapter={chapter} />
        ))}
      </div>
    </section>
  );
}
