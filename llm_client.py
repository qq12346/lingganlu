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


def chat_stream(client, model, system_prompt, user_prompt, temperature=0.8, max_tokens=12000):
    """流式对话生成，逐块产出文本（自动剔除 <think>...</think> 段）。

    供 st.write_stream 使用；返回值为生成器产出的完整文本由 Streamlit 处理。
    """
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    buffer = ""
    in_think = False
    for chunk in resp:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue
        buffer += delta
        while True:
            if in_think:
                end = buffer.find("</think>")
                if end == -1:
                    # 防 "</think>" 被 chunk 切开：保留末尾 7 个字符等补齐
                    if len(buffer) > 7:
                        buffer = buffer[-7:]
                    break
                buffer = buffer[end + len("</think>"):]
                in_think = False
                continue
            start = buffer.find("<think>")
            if start == -1:
                # 防 "<think>" 被 chunk 切开：末尾最多保留 6 个字符等补齐
                if len(buffer) > 6:
                    emit, buffer = buffer[:-6], buffer[-6:]
                    yield emit
                break
            if start > 0:
                emit, buffer = buffer[:start], buffer[start:]
                yield emit
            in_think = True
            buffer = buffer[len("<think>"):]
    # 收尾：冲刷剩余 buffer（跳过可能是半截标签的 "<" 开头残留）
    if not in_think and buffer and not buffer.startswith("<"):
        yield buffer
