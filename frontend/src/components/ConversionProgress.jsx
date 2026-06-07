const STATUS_LABELS = {
  queued: "排队中",
  running: "转换中",
  succeeded: "已完成",
  failed: "失败",
};

/**
 * @param {{ job: any; onCopyYaml?: () => void }} props
 */
export default function ConversionProgress({ job, onCopyYaml }) {
  if (!job) {
    return null;
  }

  const stats = job.result?.stats;

  return (
    <section className="card progress-panel">
      <div className="panel-header">
        <div>
          <h2>转换进度</h2>
          <p className="panel-desc">后台异步生成剧本，页面会自动轮询最新状态</p>
        </div>
        <span className={`status-badge ${job.status === "failed" ? "warning" : "success"}`}>
          {STATUS_LABELS[job.status] ?? job.status}
        </span>
      </div>

      <div className="progress-track" aria-label="转换进度">
        <div className="progress-fill" style={{ width: `${job.progress}%` }} />
      </div>
      <div className="progress-meta">
        <strong>{job.progress}%</strong>
        <span>{job.message}</span>
      </div>

      {job.error && (
        <div className="alert alert-error" role="alert">
          {job.error}
        </div>
      )}

      {stats && (
        <div className="stats-grid">
          <div><strong>{stats.chapter_count}</strong><span>章节</span></div>
          <div><strong>{stats.act_count}</strong><span>幕</span></div>
          <div><strong>{stats.scene_count}</strong><span>场景</span></div>
          <div><strong>{stats.character_count}</strong><span>角色</span></div>
        </div>
      )}

    </section>
  );
}
