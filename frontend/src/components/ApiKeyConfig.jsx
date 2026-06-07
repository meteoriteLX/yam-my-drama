import { useState } from "react";

/**
 * @param {{
 *   value: string;
 *   onChange: (value: string) => void;
 *   onTest: () => void;
 *   disabled: boolean;
 *   configured: boolean;
 *   testing: boolean;
 *   testResult: 'success' | 'error' | null;
 * }} props
 */
export default function ApiKeyConfig({
  value,
  onChange,
  onTest,
  disabled,
  configured,
  testing,
  testResult,
}) {
  const [showKey, setShowKey] = useState(false);

  function handleToggleShow() {
    setShowKey((prev) => !prev);
  }

  return (
    <section className="card api-key-panel">
      <div className="panel-header">
        <h2>API 密钥配置</h2>
        <span className={`status-badge ${configured ? "success" : "warning"}`}>
          {configured ? "已配置" : "未配置"}
        </span>
      </div>

      <div className="api-key-input-wrap">
        <label className="input-label">DeepSeek API Key</label>
        <div className="input-with-button">
          <input
            type={showKey ? "text" : "password"}
            className="api-key-input"
            value={value}
            onChange={(event) => onChange(event.target.value)}
            placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            disabled={disabled}
          />
          <button
            type="button"
            className="btn btn-ghost btn-icon"
            onClick={handleToggleShow}
            disabled={disabled || !value}
          >
            {showKey ? "隐藏" : "显示"}
          </button>
        </div>
        <p className="input-hint">
          在 <a href="https://platform.deepseek.com/" target="_blank" rel="noopener noreferrer">DeepSeek 平台</a> 获取 API 密钥
        </p>
      </div>

      <div className="button-row">
        <button
          type="button"
          className="btn btn-primary"
          onClick={onTest}
          disabled={disabled || !value.trim() || testing}
        >
          {testing ? "测试中..." : "测试连接"}
        </button>
        {value && (
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => onChange("")}
            disabled={disabled}
          >
            清除密钥
          </button>
        )}
      </div>

      {testResult && (
        <div className={`alert ${testResult === "success" ? "alert-success" : "alert-error"}`} role="alert">
          {testResult === "success" ? (
            <span>✓ API 密钥验证成功，可正常使用</span>
          ) : (
            <span>✗ API 密钥验证失败，请检查密钥是否正确</span>
          )}
        </div>
      )}
    </section>
  );
}