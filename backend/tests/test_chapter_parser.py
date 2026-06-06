from pathlib import Path

import pytest

from app.services.chapter_parser import (
    MIN_CHAPTERS_REQUIRED,
    ChapterParseError,
    parse_novel,
)

SAMPLE_NOVEL_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "sample_novel.txt"
)


class TestParseNovel:
    def test_parse_sample_novel(self) -> None:
        text = SAMPLE_NOVEL_PATH.read_text(encoding="utf-8")
        result = parse_novel(text)

        assert result.chapter_count == 3
        assert result.is_valid is True
        assert result.chapters[0].chapter_number == 1
        assert result.chapters[0].title == "雨夜"
        assert result.chapters[1].title == "旧书"
        assert result.chapters[2].title == "未完成的句子"
        assert "林晚" in result.chapters[0].content
        assert result.preamble.startswith("《城市边缘》")

    def test_chinese_and_arabic_chapter_numbers(self) -> None:
        text = """
第一章 开端
内容一。

第2章 发展
内容二。

第三章 结局
内容三。
"""
        result = parse_novel(text)

        assert result.chapter_count == 3
        assert [chapter.chapter_number for chapter in result.chapters] == [1, 2, 3]
        assert result.is_valid is True

    def test_english_chapter_headings(self) -> None:
        text = """
Chapter 1 Opening
First scene.

Chapter 2 Middle
Second scene.

Chapter 3 Ending
Final scene.
"""
        result = parse_novel(text)

        assert result.chapter_count == 3
        assert result.chapters[0].title == "Opening"
        assert result.is_valid is True

    def test_invalid_when_less_than_three_chapters(self) -> None:
        text = """
第一章 一
内容。

第二章 二
内容。
"""
        result = parse_novel(text)

        assert result.chapter_count == 2
        assert result.is_valid is False
        assert str(MIN_CHAPTERS_REQUIRED) in result.message

    def test_empty_text_raises(self) -> None:
        with pytest.raises(ChapterParseError, match="不能为空"):
            parse_novel("   ")

    def test_no_chapter_heading_raises(self) -> None:
        with pytest.raises(ChapterParseError, match="未能识别章节标题"):
            parse_novel("这是一段没有章节标题的小说正文。")

    def test_paragraph_and_char_count(self) -> None:
        text = """
第一章 测试

第一段。

第二段。

第二章 测试二
内容。

第三章 测试三
内容。
"""
        result = parse_novel(text)
        first_chapter = result.chapters[0]

        assert first_chapter.paragraph_count == 2
        assert first_chapter.char_count > 0
