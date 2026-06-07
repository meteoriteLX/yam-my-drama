/**
 * @param {{ value: string; onChange: (value: string) => void; onCopy: () => void; onDownload: () => void; sourceLabel?: string }} props
 */
export default function YamlEditor({ value, onChange, onCopy, onDownload, sourceLabel }) {
  return (
    <section className="card editor-panel">
      <div className="panel-header">
        <div>
          <h2>YAML 在线编辑</h2>
          <p className="panel-desc">可直接修改剧本初稿，编辑内容会保持在当前页面中</p>
        </div>
        <span className="editor-source">{sourceLabel || "自动生成稿"}</span>
      </div>

      <textarea
        className="yaml-editor"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="生成后的 YAML 会显示在这里，支持直接编辑"
        rows={18}
      />

      <div className="editor-actions">
        <button type="button" className="btn btn-secondary" onClick={onCopy} disabled={!value.trim()}>
          复制内容
        </button>
        <button type="button" className="btn btn-secondary" onClick={onDownload} disabled={!value.trim()}>
          下载 YAML
        </button>
      </div>
    </section>
  );
}
