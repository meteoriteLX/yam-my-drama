const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

let _llmApiKey = null;

export function setLlmApiKey(key) {
  _llmApiKey = key;
}

export function getLlmApiKey() {
  return _llmApiKey;
}

function buildHeaders(includeApiKey = false) {
  const headers = { "Content-Type": "application/json" };
  if (includeApiKey && _llmApiKey) {
    headers["X-LLM-API-Key"] = _llmApiKey;
  }
  return headers;
}

async function parseErrorMessage(response) {
  const data = await response.json().catch(() => ({}));
  if (typeof data.detail === "string") {
    return data.detail;
  }
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join("；");
  }
  return `请求失败 (${response.status})`;
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchLlmStatus() {
  const response = await fetch(`${API_BASE_URL}/api/llm/status`, {
    headers: buildHeaders(true),
  });
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }
  return response.json();
}

export async function testLlmConnection() {
  const response = await fetch(`${API_BASE_URL}/api/llm/test`, {
    method: "POST",
    headers: buildHeaders(true),
    body: JSON.stringify({ prompt: "请只回复：OK" }),
  });
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }
  return response.json();
}

/**
 * @param {string} text
 * @returns {Promise<import('./types').ChapterParseResult>}
 */
export async function parseChapters(text) {
  const response = await fetch(`${API_BASE_URL}/api/chapters/parse`, {
    method: "POST",
    headers: buildHeaders(false),
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

export async function loadSampleNovel() {
  const response = await fetch("/sample_novel.txt");
  if (!response.ok) {
    throw new Error("样例小说加载失败");
  }
  return response.text();
}

export async function createConversionJob(text) {
  const response = await fetch(`${API_BASE_URL}/api/convert/jobs`, {
    method: "POST",
    headers: buildHeaders(true),
    body: JSON.stringify({
      text,
      script_title: "AI 改编剧本初稿",
      author: "yam-my-drama",
      source_novel_title: "用户上传小说",
      source_novel_author: "未知",
    }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

export async function fetchConversionJob(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/convert/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }
  return response.json();
}
