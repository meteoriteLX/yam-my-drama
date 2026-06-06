import { useRef } from "react";

/**
 * @param {{
 *   value: string;
 *   onChange: (value: string) => void;
 *   onParse: () => void;
 *   onLoadSample: () => void;
 *   onClear: () => void;
 *   loading: boolean;
 *   disabled: boolean;
 * }} props
 */
export default function NovelInput({
  value,
  onChange,
  onParse,
  onLoadSample,
  onClear,
  loading,
  disabled,
}) {
  const fileInputRef = useRef(null);

  function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      onChange(String(reader.result ?? ""));
    };
    reader.onerror = () => {
      onChange("");
    };
    reader.readAsText(file, "UTF-8");
    event.target.value = "";
  }

  return (
    <section className="card input-panel">
      <div className="panel-header">
        <h2>小说输入</h2>
        <p className="panel-desc">粘贴或上传 .txt 小说文本，需包含至少 3 个章节</p>
      </div>

      <textarea
        className="novel-textarea"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={"在此粘贴小说正文...\n\n支持格式：\n第一章 标题\n第1章 标题\nChapter 1 Title"}
        rows={14}
        disabled={loading}
      />

      <div className="input-meta">
        <span className="muted">{value.length} 字符</span>
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,text/plain"
          className="file-input-hidden"
          onChange={handleFileChange}
          disabled={loading}
        />
      </div>

      <div className="button-row">
        <button
          type="button"
          className="btn btn-primary"
          onClick={onParse}
          disabled={disabled || loading || !value.trim()}
        >
          {loading ? "解析中..." : "解析章节"}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
        >
          上传 .txt
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onLoadSample}
          disabled={loading}
        >
          加载样例
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={onClear}
          disabled={loading || !value}
        >
          清空
        </button>
      </div>
    </section>
  );
}
