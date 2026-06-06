import { useEffect, useState } from "react";
import { fetchHealth, fetchHello } from "./api.js";

export default function App() {
  const [health, setHealth] = useState(null);
  const [hello, setHello] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [healthData, helloData] = await Promise.all([
          fetchHealth(),
          fetchHello(),
        ]);
        setHealth(healthData);
        setHello(helloData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return (
    <div className="app">
      <header className="header">
        <h1>AI 小说转剧本工具</h1>
        <p className="subtitle">Novel to Script — 项目初始化完成</p>
      </header>

      <main className="card">
        <h2>系统状态</h2>
        {loading && <p className="muted">正在连接后端...</p>}
        {error && (
          <p className="error">
            后端连接失败：{error}
            <br />
            <span className="hint">请确认 backend 已在 8000 端口启动</span>
          </p>
        )}
        {!loading && !error && (
          <ul className="status-list">
            <li>
              <span className="label">Health</span>
              <code>{JSON.stringify(health)}</code>
            </li>
            <li>
              <span className="label">Hello</span>
              <code>{JSON.stringify(hello)}</code>
            </li>
          </ul>
        )}
      </main>

      <footer className="footer">
        PR-01 · 前后端 Hello World 可运行
      </footer>
    </div>
  );
}
