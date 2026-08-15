# -*- coding: utf-8 -*-
"""灵感落 · AI 文创策划助手（MVP）

运行：streamlit run app.py
"""

import os

import streamlit as st

from dotenv import load_dotenv

import llm_client as llm
from materials import collect_materials
from prompts import MODULES

load_dotenv()

st.set_page_config(page_title="灵感落 · AI 文创策划助手", page_icon="✨", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def inject_theme():
    """注入「东方雅致」主题样式（与设计稿一一对应，见 style.css）。"""
    css_path = os.path.join(BASE_DIR, "style.css")
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


inject_theme()

# ---------------- 服务商配置 ----------------
PROVIDERS = {
    "MiniMax": {
        "base_url": "https://api.minimaxi.com/v1",
        "models": ["MiniMax-M3", "MiniMax-M2.5", "MiniMax-M2.5-highspeed", "MiniMax-M2.1"],
        "hint": "platform.minimaxi.com",
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-v4-flash", "deepseek-v4-pro"],
        "hint": "platform.deepseek.com",
    },
}

# ---------------- 侧边栏 ----------------
with st.sidebar:
    st.markdown(
        """
<div class="side-brand">
  <span class="seal-sm">灵感落</span>
  <div>
    <div class="side-brand-name">灵感落</div>
    <div class="side-brand-tag">AI 文创策划助手</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("#### 设置")
    provider = st.selectbox("模型服务商", list(PROVIDERS.keys()))
    cfg = PROVIDERS[provider]
    api_key = st.text_input(
        f"{provider} API Key",
        type="password",
        help=f"在 {cfg['hint']} 创建 API Key 后填入。",
    )
    model = st.selectbox("模型", cfg["models"], index=0)
    temperature = st.slider("创造性（temperature）", 0.0, 1.5, 0.6, 0.1)
    st.markdown(
        f"还没有 Key？去 [{cfg['hint']}](https://{cfg['hint']}) 注册开发者账号。"
    )

# ---------------- 主界面 ----------------
st.markdown(
    """
<div class="hero">
  <div class="hero-eyebrow"><span class="line"></span><span class="eyebrow-text">思 · 值 · 决 · 行</span><span class="line"></span></div>
  <h1 class="hero-title">把灵感，落成事</h1>
  <p class="hero-sub">输入一个创意想法，四套思维框架帮你拆本质、问价值、验场景、定路径，从想到，到做到。</p>
</div>
<div class="framework-row">
  <div class="framework-card"><span class="seal">思</span><div><div class="fc-title">思 · 第一性原理</div><div class="fc-desc">拆本质：四因拆解，追问隐含假设</div></div></div>
  <span class="fc-arrow">→</span>
  <div class="framework-card"><span class="seal">值</span><div><div class="fc-title">值 · 价值追问</div><div class="fc-desc">问价值：值不值得做，底线在哪里</div></div></div>
  <span class="fc-arrow">→</span>
  <div class="framework-card"><span class="seal">决</span><div><div class="fc-title">决 · 复杂决策</div><div class="fc-desc">验场景：用概率与最小实验说话</div></div></div>
  <span class="fc-arrow">→</span>
  <div class="framework-card"><span class="seal">行</span><div><div class="fc-title">行 · 还原论工程</div><div class="fc-desc">定路径：MVP 边界与死亡清单</div></div></div>
</div>
""",
    unsafe_allow_html=True,
)

EXAMPLES = {
    "— 自定义输入 —": None,
    "老字号茶馆 · 面向年轻人的主题活动": {
        "input": "为一个老字号茶馆策划一场面向年轻人的主题活动",
        "output_file": os.path.join(BASE_DIR, "examples", "laozihao_v4.md"),
        "materials_file": os.path.join(BASE_DIR, "examples", "老字号茶馆资料库.md"),
    },
}

example_label = st.selectbox(
    "示例案例（选择后自动填入输入框，并载入该案例的分析结果）",
    list(EXAMPLES.keys()),
)


@st.cache_data
def load_example_output(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def apply_example_outputs(path):
    """把示例文件的四段内容填充到各模块标签页（即分析原本出现的位置）。"""
    content = load_example_output(path)
    markers = [(f"## {i}. {m['title']}", m["key"]) for i, m in enumerate(MODULES, start=1)]
    for idx, (marker, key) in enumerate(markers):
        start = content.find(marker)
        if start == -1:
            continue
        start += len(marker)
        end = content.find(markers[idx + 1][0], start) if idx + 1 < len(markers) else len(content)
        st.session_state[f"out_{key}"] = content[start:end].strip()


def load_example_materials(example):
    """载入示例自带的项目资料；未指定或文件缺失时清空示例资料。"""
    path = example.get("materials_file") if example else None
    if not path or not os.path.exists(path):
        st.session_state.pop("_materials_fp", None)
        st.session_state.pop("materials_text", None)
        st.session_state.pop("materials_summary", None)
        return
    with open(path, encoding="utf-8") as f:
        text = f.read().strip()
    st.session_state["_materials_fp"] = f"__example__:{os.path.basename(path)}"
    st.session_state["materials_text"] = text
    st.session_state["materials_summary"] = [(os.path.basename(path), len(text), False)]


selected_example = EXAMPLES[example_label]
# 仅在切换示例时载入（避免生成后的 rerun 把新结果覆盖回示例内容）
example_changed = st.session_state.get("_loaded_example") != example_label
if selected_example is not None and example_changed:
    st.session_state["_loaded_example"] = example_label
    st.session_state["idea_input"] = selected_example["input"]
    load_example_materials(selected_example)

idea = st.text_area(
    "你的创意想法（越具体越好）",
    key="idea_input",
    height=100,
    placeholder="例如：给家乡的一种地方小吃设计 IP 形象和短视频传播方案……",
)

if selected_example is not None:
    if example_changed:
        apply_example_outputs(selected_example["output_file"])
    mats_note = ""
    if selected_example.get("materials_file") and os.path.exists(
        selected_example["materials_file"]
    ):
        mats_note = "；已同时载入示例项目资料《老字号茶馆资料库》，一键生成时会引用其中的真实案例与数据"
    st.caption(
        f"已载入示例分析结果（{example_label}，产品实测迭代四轮后定稿）{mats_note}；也可以点“一键生成”实时重新生成。"
    )

# ---------------- 项目资料上传 ----------------
st.markdown("**📁 项目资料（可选）**")
uploaded_files = st.file_uploader(
    "上传与想法相关的资料——支持多选（md / txt / pdf / docx），或上传整理好的 ZIP 压缩包",
    type=["md", "markdown", "txt", "pdf", "docx", "zip"],
    accept_multiple_files=True,
    help="点击后弹出系统文件对话框；进入文件夹后 Cmd+A 可全选。资料会作为策划依据注入分析，避免 AI 凭空编造细节。",
)
if uploaded_files:
    fingerprint = "|".join(f"{f.name}:{f.size}" for f in uploaded_files)
    if st.session_state.get("_materials_fp") != fingerprint:
        with st.spinner("正在解析资料…"):
            materials_text, materials_summary = collect_materials(uploaded_files)
        st.session_state["_materials_fp"] = fingerprint
        st.session_state["materials_text"] = materials_text
        st.session_state["materials_summary"] = materials_summary
else:
    # 未上传文件时：若当前示例自带项目资料，恢复示例资料；否则清空
    example_mats = selected_example.get("materials_file") if selected_example else None
    want_fp = (
        f"__example__:{os.path.basename(example_mats)}"
        if example_mats and os.path.exists(example_mats)
        else None
    )
    if want_fp:
        if st.session_state.get("_materials_fp") != want_fp:
            load_example_materials(selected_example)
    else:
        st.session_state.pop("_materials_fp", None)
        st.session_state.pop("materials_text", None)
        st.session_state.pop("materials_summary", None)

included = [s for s in st.session_state.get("materials_summary", []) if not s[2]]
dropped = [s for s in st.session_state.get("materials_summary", []) if s[2]]
if included:
    names = "、".join(s[0] for s in included[:8]) + ("……" if len(included) > 8 else "")
    is_example = str(st.session_state.get("_materials_fp", "")).startswith("__example__:")
    suffix = "（示例自带，上传自己的资料可替换）" if is_example else ""
    st.caption(f"✅ 已加载 {len(included)} 份资料：{names}{suffix}")
if dropped:
    st.caption(f"⚠️ {len(dropped)} 份因总长度超限未纳入：" + "、".join(s[0] for s in dropped[:5]))
materials_text = st.session_state.get("materials_text", "")

tabs = st.tabs([m["tab"] for m in MODULES] + ["完整策划案"])
tab_list = list(tabs)


def run_module(module, current_idea, slot=None):
    """运行单个模块，若前置模块未生成则自动补齐。slot 非空时流式输出到该占位符。"""
    ctx_parts = []
    for prev in MODULES:
        if prev["key"] == module["key"]:
            break
        prev_out = st.session_state.get(f"out_{prev['key']}", "")
        if not prev_out:
            with st.spinner(f"正在补齐前置模块：{prev['tab']} …"):
                prev_out = run_module(prev, current_idea)
        ctx_parts.append(prev_out)
    ctx = "\n\n".join(ctx_parts)

    client = llm.build_client(api_key, base_url=cfg["base_url"])
    user_prompt = module["user"](current_idea, ctx, materials_text)
    if slot is not None:
        stream = llm.chat_stream(client, model, module["system"], user_prompt, temperature)
        result = slot.write_stream(stream) or ""
    else:
        with st.spinner(f"正在生成：{module['title']} …（约 30-90 秒）"):
            result = llm.chat(client, model, module["system"], user_prompt, temperature)
    st.session_state[f"out_{module['key']}"] = result
    return result


def require_idea():
    if not idea.strip():
        st.error("请先在上方输入你的创意想法。")
        return False
    if not api_key:
        st.error(f"请先在左侧侧边栏填写 {provider} API Key。")
        return False
    return True


for idx, module in enumerate(MODULES):
    with tab_list[idx]:
        st.subheader(module["title"])
        trigger_key = f"trigger_{module['key']}"
        error_key = f"error_{module['key']}"
        if st.button(
            "生成此模块", key=f"btn_{module['key']}", use_container_width=True, type="primary"
        ):
            st.session_state[trigger_key] = True

        if st.session_state.get(trigger_key):
            st.session_state[trigger_key] = False
            if require_idea():
                # 清空旧结果，避免流式输出时下方残留上一版内容
                st.session_state[f"out_{module['key']}"] = ""
                st.session_state.pop(error_key, None)
                try:
                    run_module(module, idea.strip(), slot=st.empty())
                except Exception as exc:  # noqa: BLE001
                    st.session_state[error_key] = str(exc)
                st.rerun()

        if st.session_state.get(error_key):
            st.error(
                f"生成失败：{st.session_state[error_key]}\n\n"
                "请检查 API Key、模型名与网络后重试。"
            )
            if st.button("🔄 重试此模块", key=f"retry_{module['key']}", use_container_width=True):
                st.session_state[trigger_key] = True
                st.rerun()

        out = st.session_state.get(f"out_{module['key']}", "")
        if out:
            st.markdown(out)

# ---------------- 完整策划案 ----------------
with tab_list[4]:
    st.subheader("完整策划案（一键生成四步）")
    if st.button("一键生成完整策划案", key="btn_all", use_container_width=True, type="primary"):
        st.session_state["trigger_all"] = True

    if st.session_state.get("trigger_all"):
        st.session_state["trigger_all"] = False
        if require_idea():
            progress = st.progress(0.0, text="准备开始…")
            # 清空旧结果，避免下方残留上一版
            for m in MODULES:
                st.session_state[f"out_{m['key']}"] = ""
            st.session_state.pop("all_done", None)
            try:
                for i, module in enumerate(MODULES):
                    progress.progress(
                        i / len(MODULES),
                        text=f"正在生成 {i + 1}/{len(MODULES)}：{module['tab']}（实时流式输出）",
                    )
                    st.markdown(f"### {module['title']}")
                    run_module(module, idea.strip(), slot=st.empty())
                progress.progress(1.0, text="四步全部生成完成")
                st.session_state["all_done"] = True
                st.session_state.pop("error_all", None)
            except Exception as exc:  # noqa: BLE001
                st.session_state["error_all"] = str(exc)
            st.rerun()

    if st.session_state.get("error_all"):
        st.error(
            f"生成失败：{st.session_state['error_all']}\n\n"
            "请检查 API Key、模型名与网络后重试。"
        )
        if st.button("🔄 重试完整生成", key="retry_all", use_container_width=True):
            st.session_state["trigger_all"] = True
            st.rerun()

    if st.session_state.get("all_done"):
        st.success("完整策划案已生成，见下方。")

    outputs = {m["key"]: st.session_state.get(f"out_{m['key']}", "") for m in MODULES}
    if all(outputs.values()):
        doc = "".join(
            f"## {i}. {m['title']}\n{outputs[m['key']]}\n\n"
            for i, m in enumerate(MODULES, start=1)
        )
        doc = f"# 策划案\n\n> 输入想法：{idea.strip()}\n\n{doc}" + (
            "---\n\n*由灵感落 AI 文创策划助手生成，"
            "AI 输出包含假设成分，提交/使用前请自行核实。*"
        )
        st.markdown("---")
        st.download_button(
            "下载策划案（Markdown）",
            data=doc.encode("utf-8"),
            file_name="策划案.md",
            mime="text/markdown",
            type="primary",
        )
        st.markdown(doc)

st.markdown(
    """
<div>
  <div class="method-title">为什么是「思 · 值 · 决 · 行」</div>
  <div class="method-grid">
    <div class="method-item"><div class="mi-title">思 · 拆本质</div><div class="mi-desc">想法不清：先拆四因与隐含假设，避免想当然立项</div></div>
    <div class="method-item"><div class="mi-title">值 · 问价值</div><div class="mi-desc">盲目立项：先回答值不值得做、什么不该被牺牲</div></div>
    <div class="method-item"><div class="mi-title">决 · 验场景</div><div class="mi-desc">自嗨验证：用概率和最小实验替代拍脑袋下注</div></div>
    <div class="method-item"><div class="mi-title">行 · 定路径</div><div class="mi-desc">纸上谈兵：MVP 边界、死亡清单、反脆弱与 7 天计划</div></div>
  </div>
</div>
<div class="app-footer">灵感落 · AI 文创策划助手 — 判断与路径由 AI 生成，提交或使用前请自行核实。</div>
""",
    unsafe_allow_html=True,
)
