SCRIPT_BLOCK_SYSTEM_PROMPT = """你是一位专业影视编剧，擅长将小说场景改写为可拍摄的剧本格式。

你的任务：根据场景信息与原文章节片段，生成包含动作描述（action_blocks）和角色对白（dialogues）的剧本块。

规则：
1. action_blocks 使用现在时，描述可拍摄的画面与动作，不要写心理独白
2. 小说中的心理描写应外化为动作或表情，必要时用简短 parenthetical
3. dialogues 必须使用提供的 character_id，不要编造未注册角色
4. 对白简洁自然，符合角色性格
5. 只输出 JSON，不要 Markdown 代码块，不要额外解释"""

SCRIPT_BLOCK_USER_TEMPLATE = """请为以下场景生成剧本块。

幕号：{act}
场景 ID：{scene_id}
章节号：{chapter_number}

场景信息：
- 场次：{scene_number}
- 地点：{location}
- 内/外景：{int_ext}
- 时间：{time}
- 概述：{summary}
- 参与角色：{character_names}

角色注册表（dialogues 必须使用 character_id）：
{character_registry}

原文参考：
{chapter_content}

请严格输出如下 JSON：
{{
  "scene_id": "{scene_id}",
  "scene_number": {scene_number},
  "heading": {{
    "int_ext": "{int_ext}",
    "location": "{location}",
    "time": "{time}"
  }},
  "source_mapping": {{
    "chapter": {chapter_number},
    "excerpt": "原文摘要（50字以内）"
  }},
  "action_blocks": [
    "可拍摄的动作描述，现在时"
  ],
  "dialogues": [
    {{
      "character_id": "char_xxx",
      "line": "台词",
      "parenthetical": "可选语气",
      "emotion": "可选情绪"
    }}
  ],
  "transition": "CUT TO:",
  "notes": "改编说明（可选）"
}}"""


def build_script_block_prompt(
    *,
    act: int,
    scene_id: str,
    chapter_number: int,
    chapter_content: str,
    scene_number: int,
    location: str,
    int_ext: str,
    time: str,
    summary: str,
    character_names: list[str],
    character_registry: str,
) -> tuple[str, str]:
    user_prompt = SCRIPT_BLOCK_USER_TEMPLATE.format(
        act=act,
        scene_id=scene_id,
        chapter_number=chapter_number,
        scene_number=scene_number,
        location=location.replace('"', '\\"'),
        int_ext=int_ext,
        time=time,
        summary=summary.replace('"', '\\"'),
        character_names="、".join(character_names) or "无",
        character_registry=character_registry,
        chapter_content=chapter_content.strip(),
    )
    return SCRIPT_BLOCK_SYSTEM_PROMPT, user_prompt


def format_character_registry(characters: list) -> str:
    lines = []
    for character in characters:
        lines.append(
            f"- id: {character.id}, name: {character.name}, role: {character.role}"
        )
    return "\n".join(lines)
