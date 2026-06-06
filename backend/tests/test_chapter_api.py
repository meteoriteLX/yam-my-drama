from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_NOVEL_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "sample_novel.txt"
)


class TestChapterParseAPI:
    def test_parse_sample_novel_success(self) -> None:
        text = SAMPLE_NOVEL_PATH.read_text(encoding="utf-8")
        response = client.post("/api/chapters/parse", json={"text": text})

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["chapter_count"] == 3
        assert data["min_chapters_required"] == 3
        assert len(data["chapters"]) == 3
        assert data["chapters"][0]["heading"] == "第一章 雨夜"
        assert data["chapters"][0]["paragraph_count"] >= 1

    def test_parse_invalid_chapter_count(self) -> None:
        text = """
第一章 一
内容。

第二章 二
内容。
"""
        response = client.post("/api/chapters/parse", json={"text": text})

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["chapter_count"] == 2

    def test_parse_empty_text_returns_422(self) -> None:
        response = client.post("/api/chapters/parse", json={"text": "   "})

        assert response.status_code == 422

    def test_parse_no_headings_returns_400(self) -> None:
        response = client.post(
            "/api/chapters/parse",
            json={"text": "没有章节标题的正文"},
        )

        assert response.status_code == 400
        assert "未能识别章节标题" in response.json()["detail"]
