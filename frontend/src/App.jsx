import { useEffect, useState } from "react";
import { fetchHealth, loadSampleNovel, parseChapters } from "./api.js";
import ChapterPreview from "./components/ChapterPreview.jsx";
import NovelInput from "./components/NovelInput.jsx";

export default function App() {
  const [backendOnline, setBackendOnline] = useState(null);
  const [novelText, setNovelText] = useState("");
  const [parseResult, setParseResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : "样例加载失败");
    }
  }

  function handleClear() {
    setNovelText("");
    setParseResult(null);
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
        <p className="subtitle">粘贴小说文本，自动识别章节并校验是否满足 3 章以上要求</p>
      </header>

      <main className="main-grid">
        <NovelInput
          value={novelText}
          onChange={setNovelText}
          onParse={handleParse}
          onLoadSample={handleLoadSample}
          onClear={handleClear}
          loading={loading}
          disabled={backendOnline === false}
        />

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

        <ChapterPreview result={parseResult} />
      </main>

      <footer className="footer">yam-my-drama · 小说章节解析</footer>
    </div>
  );
}
