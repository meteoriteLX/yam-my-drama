const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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

/**
 * @param {string} text
 * @returns {Promise<import('./types').ChapterParseResult>}
 */
export async function parseChapters(text) {
  const response = await fetch(`${API_BASE_URL}/api/chapters/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
