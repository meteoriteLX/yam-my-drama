from __future__ import annotations

import re
from dataclasses import dataclass, field

MIN_CHAPTERS_REQUIRED = 3

# 中文章标题：第一章 / 第1章 / 第十二章 等
_CN_CHAPTER_RE = re.compile(
    r"^第([0-9一二三四五六七八九十百千万零两]+)章\s*(.*)$"
)
# 英文章标题：Chapter 1 / CHAPTER 1 Title
_EN_CHAPTER_RE = re.compile(
    r"^Chapter\s+(\d+)\s*(.*?)\s*$",
    re.IGNORECASE,
)

_CN_DIGIT_MAP = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "百": 100,
    "千": 1000,
    "万": 10000,
    "两": 2,
}


class ChapterParseError(ValueError):
    """Raised when novel text cannot be parsed into chapters."""


@dataclass
class ParsedChapter:
    chapter_number: int
    title: str
    heading: str
    content: str
    char_count: int = 0
    paragraph_count: int = 0

    def __post_init__(self) -> None:
        self.char_count = len(self.content.strip())
        paragraphs = [p for p in re.split(r"\n\s*\n", self.content.strip()) if p.strip()]
        self.paragraph_count = len(paragraphs)


@dataclass
class ParsedNovel:
    chapters: list[ParsedChapter] = field(default_factory=list)
    preamble: str = ""
    min_chapters_required: int = MIN_CHAPTERS_REQUIRED

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    @property
    def is_valid(self) -> bool:
        return self.chapter_count >= self.min_chapters_required

    @property
    def message(self) -> str:
        if self.is_valid:
            return f"成功识别 {self.chapter_count} 个章节，满足至少 {self.min_chapters_required} 章的要求。"
        if self.chapter_count == 0:
            return (
                f"未能识别任何章节。请使用「第一章」「第1章」或「Chapter 1」等格式标记章节标题，"
                f"且至少需要 {self.min_chapters_required} 章。"
            )
        return (
            f"至少需要 {self.min_chapters_required} 个章节，当前识别到 {self.chapter_count} 个。"
        )


def _chinese_numeral_to_int(value: str) -> int | None:
    if not value:
        return None
    if value.isdigit():
        return int(value)

    total = 0
    current = 0
    for char in value:
        if char not in _CN_DIGIT_MAP:
            return None
        digit = _CN_DIGIT_MAP[char]
        if digit >= 10:
            current = max(1, current) * digit if current else digit
            if digit >= 100:
                total += current
                current = 0
        else:
            current += digit
    return total + current


def _match_chapter_heading(line: str) -> tuple[int, str, str] | None:
    stripped = line.strip()
    if not stripped:
        return None

    cn_match = _CN_CHAPTER_RE.match(stripped)
    if cn_match:
        raw_number, raw_title = cn_match.groups()
        chapter_number = _chinese_numeral_to_int(raw_number)
        if chapter_number is None:
            return None
        title = raw_title.strip()
        return chapter_number, title, stripped

    en_match = _EN_CHAPTER_RE.match(stripped)
    if en_match:
        chapter_number = int(en_match.group(1))
        title = en_match.group(2).strip()
        return chapter_number, title, stripped

    return None


def parse_novel(text: str, min_chapters: int = MIN_CHAPTERS_REQUIRED) -> ParsedNovel:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise ChapterParseError("小说文本不能为空。")

    lines = normalized.split("\n")
    headings: list[tuple[int, int, str, str]] = []
    fallback_index = 0

    for index, line in enumerate(lines):
        matched = _match_chapter_heading(line)
        if matched is None:
            continue

        chapter_number, title, heading = matched
        if chapter_number <= 0:
            fallback_index += 1
            chapter_number = fallback_index
        else:
            fallback_index = max(fallback_index, chapter_number)

        headings.append((index, chapter_number, title, heading))

    if not headings:
        raise ChapterParseError(
            "未能识别章节标题。请使用「第一章 标题」「第1章 标题」或「Chapter 1 Title」格式。"
        )

    preamble = "\n".join(lines[: headings[0][0]]).strip()
    chapters: list[ParsedChapter] = []

    for idx, (line_index, chapter_number, title, heading) in enumerate(headings):
        next_line_index = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines)
        body_lines = lines[line_index + 1 : next_line_index]
        content = "\n".join(body_lines).strip()

        chapters.append(
            ParsedChapter(
                chapter_number=chapter_number,
                title=title,
                heading=heading,
                content=content,
            )
        )

    return ParsedNovel(
        chapters=chapters,
        preamble=preamble,
        min_chapters_required=min_chapters,
    )
