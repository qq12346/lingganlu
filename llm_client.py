# -*- coding: utf-8 -*-
"""大模型调用封装（MiniMax / DeepSeek 均走 OpenAI 兼容接口）。"""

import os
import re

from openai import OpenAI

DEFAULT_BASE_URL = "https://api.minimaxi.com/v1"


def build_client(api_key=None, base_url=None):
    """构造 MiniMax 客户端。Key 优先取页面输入，其次读环境变量。"""
    return OpenAI(
        api_key=api_key or os.getenv("MINIMAX_API_KEY", "EMPTY"),
        base_url=base_url or os.getenv("MINIMAX_BASE_URL", DEFAULT_BASE_URL),
    )


def clean_think(text):
    """M2.x / M3 会把思考过程放在 <think>...</think> 里，展示时去掉。"""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def chat(client, model, system_prompt, user_prompt, temperature=0.8, max_tokens=12000):
    """单轮对话生成，返回清洗后的文本。"""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = resp.choices[0].message.content or ""
    return clean_think(content)
