# 灵感落 · AI 文创策划助手（MVP）

智极松 AI Skillathon · AI+文创及服务 赛道参赛项目（概念验证版）。

一句话定位：**为文创创作者提供 AI 结构化策划工具——输入一个创意想法，输出可落地的项目策划案与执行路径。**

## 功能

四个思维框架模块，一键串联生成完整策划案：

1. **思 · 第一性原理**：创意本质拆解（四因、隐含假设、机会与风险）
2. **值 · 价值追问**：这值得做吗（目的回溯、受益者与代价、底线检查）
3. **决 · 复杂决策**：场景与最小验证（目标用户、痛点、不确定性、验证实验）
4. **行 · 还原论工程**：执行路径（MVP 边界、成本拆解、死亡清单、反脆弱设计）

## 快速开始

```bash
cd 灵感落
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # 填入 MiniMax API Key（或直接在页面侧边栏填）
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`，在左侧选择模型服务商并填入 API Key 即可使用。

## 模型服务商（侧边栏可切换）

| 服务商 | 接入点 | 推荐模型 | 说明 |
|--------|--------|---------|------|
| MiniMax | `https://api.minimaxi.com/v1` | MiniMax-M3 | 新账号有免费试用额度；支持多模态（后续可扩展） |
| DeepSeek | `https://api.deepseek.com` | deepseek-v4-flash | 价格极低；思考模式可展示推理过程（贴合本项目"结构化思考"定位） |

> 注意：DeepSeek 旧模型名 `deepseek-chat` / `deepseek-reasoner` 已于 2026-07-24 弃用，请使用 `deepseek-v4-flash` 或 `deepseek-v4-pro`。

## 获取 MiniMax API Key（免费额度）

1. 打开对应服务商控制台：MiniMax <https://platform.minimaxi.com> / DeepSeek <https://platform.deepseek.com>
2. 在控制台创建 API Key（MiniMax 新账号通常自带免费试用额度；DeepSeek 新账号有少量赠送额度，超出后按量计费且价格极低）
3. 填入 `.env` 或页面侧边栏

## 演示脚本（录 Demo 视频用，任选 2-3 个）

1. "给家乡的一种地方小吃设计 IP 形象和短视频传播方案"
2. "想做一档'AI 时代的普通人生存指南'播客，怎么起步"
3. "为一个老字号茶馆策划一场面向年轻人的主题活动"

演示流程：输入想法 → 一键生成完整策划案 → 展示四段式结果 → 下载 Markdown。
录制工具：macOS 用 QuickTime Player（录屏），或 OBS。

## 参赛自查清单（提交前）

- [ ] 申报表无空项（暂不适用填"无"）
- [ ] Demo 视频 3-5 分钟、可播放
- [ ] 所有表述有事实支撑，无虚构
- [ ] 文件按官方规则命名：`AI文创及服务_项目名_团队名_申报表_版本日期.docx`
- [ ] 8 月 7 日 23:59 前完成官网提交
