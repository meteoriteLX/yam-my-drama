import { useEffect, useState } from "react";
import {
  createConversionJob,
  fetchConversionJob,
  fetchHealth,
  loadSampleNovel,
  parseChapters,
} from "./api.js";
import ChapterPreview from "./components/ChapterPreview.jsx";
import ConversionProgress from "./components/ConversionProgress.jsx";
import NovelInput from "./components/NovelInput.jsx";
import YamlEditor from "./components/YamlEditor.jsx";

export default function App() {
  const [backendOnline, setBackendOnline] = useState(null);
  const [novelText, setNovelText] = useState("");
  const [parseResult, setParseResult] = useState(null);
  const [conversionJob, setConversionJob] = useState(null);
  const [yamlText, setYamlText] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [converting, setConverting] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

  useEffect(() => {
    if (!conversionJob?.job_id || !["queued", "running"].includes(conversionJob.status)) {
      setConverting(false);
      return undefined;
    }

    setConverting(true);
    const timer = window.setInterval(async () => {
      try {
        const latest = await fetchConversionJob(conversionJob.job_id);
        setConversionJob(latest);
        if (latest.result?.yaml) {
          setYamlText((current) => current || latest.result.yaml);
        }
        if (!["queued", "running"].includes(latest.status)) {
          setConverting(false);
        }
      } catch (err) {
        setConverting(false);
        setError(err instanceof Error ? err.message : "获取转换进度失败");
      }
    }, 1200);

    return () => window.clearInterval(timer);
  }, [conversionJob?.job_id, conversionJob?.status]);

  async function handleParse() {
    setLoading(true);
    setError(null);

    try {
      const result = await parseChapters(novelText);
      setParseResult(result);
    } catch (err) {
      setParseResult(null);
      setError(err instanceof Error ? err.message : "解析失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadSample() {
    setError(null);
    try {
      const text = await loadSampleNovel();
      setNovelText(text);
      setParseResult(null);
      setConversionJob(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "样例加载失败");
    }
  }

  async function handleOneClickDemo() {
    setError(null);
    setLoading(true);

    try {
      const text = await loadSampleNovel();
      setNovelText(text);
      const parsed = await parseChapters(text);
      setParseResult(parsed);
      setConversionJob(null);
      const job = await createConversionJob(text);
      setConversionJob(job);
      setYamlText(job.result?.yaml ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "一键体验失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleStartConversion() {
    setError(null);
    setConversionJob(null);
    setConverting(true);

    try {
      const job = await createConversionJob(novelText);
      setConversionJob(job);
      setYamlText(job.result?.yaml ?? "");
    } catch (err) {
      setConverting(false);
      setError(err instanceof Error ? err.message : "转换任务创建失败");
    }
  }

  async function handleCopyYaml() {
    if (!yamlText.trim()) {
      return;
    }
    await navigator.clipboard.writeText(yamlText);
  }

  function handleDownloadYaml() {
    if (!yamlText.trim()) {
      return;
    }
    const blob = new Blob([yamlText], { type: "text/yaml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "script.yaml";
    link.click();
    URL.revokeObjectURL(url);
  }

  function handleClear() {
    setNovelText("");
    setParseResult(null);
    setConversionJob(null);
    setYamlText("");
    setConverting(false);
    setError(null);
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <h1>AI 小说转剧本工具</h1>
          <span
            className={`backend-status ${
              backendOnline === null
                ? "checking"
                : backendOnline
                  ? "online"
                  : "offline"
            }`}
          >
            {backendOnline === null && "检测后端..."}
            {backendOnline === true && "后端已连接"}
            {backendOnline === false && "后端未连接"}
          </span>
        </div>
        <p className="subtitle">粘贴 3 章以上小说文本，异步生成可编辑的 YAML 剧本初稿</p>
      </header>

      <main className="main-grid">
        <NovelInput
          value={novelText}
          onChange={setNovelText}
          onParse={handleParse}
          onLoadSample={handleLoadSample}
          onClear={handleClear}
          loading={loading || converting}
          disabled={backendOnline === false}
        />

        <div className="button-row action-row">
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleStartConversion}
            disabled={backendOnline === false || converting || !novelText.trim()}
          >
            {converting ? "转换中..." : "开始转换为 YAML 剧本"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleOneClickDemo}
            disabled={backendOnline === false || loading || converting}
          >
            一键体验样例
          </button>
        </div>

        {error && (
          <div className="alert alert-error" role="alert">
            {error}
          </div>
        )}

        {backendOnline === false && (
          <div className="alert alert-warning" role="alert">
            无法连接后端，请先启动 API 服务（默认 http://localhost:8000）
          </div>
        )}

        <ConversionProgress job={conversionJob} onCopyYaml={handleCopyYaml} />

        {yamlText && (
          <YamlEditor
            value={yamlText}
            onChange={setYamlText}
            onCopy={handleCopyYaml}
            onDownload={handleDownloadYaml}
            sourceLabel={conversionJob?.status === "succeeded" ? "最新生成稿" : "编辑中"}
          />
        )}

        <ChapterPreview result={parseResult} />
      </main>

      <footer className="footer">yam-my-drama · 异步小说转剧本 Pipeline</footer>
    </div>
  );
}
