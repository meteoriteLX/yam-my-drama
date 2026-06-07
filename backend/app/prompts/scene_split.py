SCENE_SPLIT_SYSTEM_PROMPT = """你是一位专业的影视编剧助手，擅长将小说章节拆解为可拍摄的剧本场景。

你的任务：阅读单章小说正文，识别其中的独立场景（scene），输出结构化 JSON。

规则：
1. 每个场景应有明确的地点、时间（内景/外景）和参与角色
2. 场景切换依据：地点变化、时间跳跃、叙事段落转折
3. 保留 source_excerpt 引用原文章节片段，便于溯源
4. 只输出 JSON，不要 Markdown 代码块，不要额外解释
5. 至少识别 1 个场景，通常一章 2-5 个场景"""

SCENE_SPLIT_USER_TEMPLATE = """请将以下小说章节拆解为场景列表。

章节号：{chapter_number}
章节标题：{chapter_title}

章节正文：
{content}

请严格输出如下 JSON 结构：
{{
  "chapter_number": {chapter_number},
  "chapter_title": "{chapter_title}",
  "scenes": [
    {{
      "scene_number": 1,
      "location": "地点名称",
      "int_ext": "INT",
      "time": "DAY",
      "summary": "本场景一句话概述",
      "characters": ["角色名"],
      "source_excerpt": "对应原文片段（50字以内）"
    }}
  ],
  "characters_mentioned": [
    {{
      "name": "角色名",
      "role_hint": "protagonist"
    }}
  ]
}}

字段说明：
- int_ext: INT（内景）| EXT（外景）| INT/EXT
- time: DAY | NIGHT | DAWN | DUSK | CONTINUOUS
- role_hint: protagonist | antagonist | supporting | extra"""


def build_scene_split_prompt(
    chapter_number: int,
    chapter_title: str,
    content: str,
) -> tuple[str, str]:
    user_prompt = SCENE_SPLIT_USER_TEMPLATE.format(
        chapter_number=chapter_number,
        chapter_title=chapter_title.replace('"', '\\"'),
        content=content.strip(),
    )
    return SCENE_SPLIT_SYSTEM_PROMPT, user_prompt
