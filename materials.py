# -*- coding: utf-8 -*-
"""项目资料解析：把用户上传的文件（md/txt/pdf/docx/zip）解析为纯文本上下文。"""

import io
import zipfile

MAX_FILE_CHARS = 8000    # 单文件最多注入的字符数
MAX_TOTAL_CHARS = 30000  # 全部资料合计上限（约 15k token，留出输出空间）

SUPPORTED = (".md", ".markdown", ".txt", ".pdf", ".docx")


def _extract_text(file_name, data):
    """按扩展名提取纯文本；不支持的类型返回空串。"""
    name = file_name.lower()
    try:
        if name.endswith((".md", ".markdown", ".txt")):
            return data.decode("utf-8", errors="replace")
        if name.endswith(".pdf"):
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if name.endswith(".docx"):
            from docx import Document

            doc = Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception:  # noqa: BLE001
        return ""
    return ""


def collect_materials(uploaded_files):
    """解析上传文件列表，返回 (资料文本, 文件摘要列表)。

    文件摘要: (文件名, 字符数, 是否因超限被丢弃)
    """
    items = []  # (文件名, 文本)
    for uf in uploaded_files:
        data = uf.read()
        if uf.name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    for info in zf.infolist():
                        if info.is_dir():
                            continue
                        if "__MACOSX" in info.filename or info.filename.endswith(".DS_Store"):
                            continue
                        if not info.filename.lower().endswith(SUPPORTED):
                            continue
                        text = _extract_text(info.filename, zf.read(info))
                        if text.strip():
                            items.append((info.filename, text))
            except zipfile.BadZipFile:
                continue
        else:
            text = _extract_text(uf.name, data)
            if text.strip():
                items.append((uf.name, text))

    parts, summaries, total = [], [], 0
    for fname, text in items:
        text = text.strip()
        if len(text) > MAX_FILE_CHARS:
            text = text[:MAX_FILE_CHARS] + "\n……（该文件内容过长，已截断）"
        block = f"【资料：{fname}】\n{text}"
        if total + len(block) > MAX_TOTAL_CHARS:
            summaries.append((fname, len(text), True))
            continue
        parts.append(block)
        total += len(block)
        summaries.append((fname, len(text), False))
    return "\n\n".join(parts), summaries
