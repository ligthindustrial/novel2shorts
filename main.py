import json
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import streamlit as st

# ---------------------- 大模型配置 ----------------------
# 请在这里填入你的 API Key
llm = ChatOpenAI(
    base_url="https://api.deepseek.com",
    api_key="",
    model="deepseek-chat",
    temperature=0.7
)

# ---------------------- 全局状态定义 ----------------------
class CreationState(TypedDict):
    novel_text: str
    novel_analysis: str
    short_play_outline: str
    script_content: str
    shot_prompts: List[str]
    subtitles: str
    compliance_check: str
    final_output: str

# ---------------------- 各Agent节点 ----------------------
def novel_analyze_agent(state: CreationState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业短剧编剧，拆解小说人设、世界观、核心冲突、爽点、关键剧情，适配60-90秒短剧改编结构。"),
        ("user", "小说文本：{text}\n输出结构化解析")
    ])
    chain = prompt | llm
    res = chain.invoke({"text": state["novel_text"]})
    return {"novel_analysis": res.content}

def outline_agent(state: CreationState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "按小说解析生成3幕式短剧大纲：开场抓眼→冲突爆发→爽点反转，符合短视频平台调性。"),
        ("user", "小说解析：{analysis}")
    ])
    chain = prompt | llm
    res = chain.invoke({"analysis": state["novel_analysis"]})
    return {"short_play_outline": res.content}

def script_agent(state: CreationState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "生成专业短剧分镜剧本：场景、景别、画面描述、人物台词、音效标注，短句适合口播。"),
        ("user", "短剧大纲：{outline}")
    ])
    chain = prompt | llm
    res = chain.invoke({"outline": state["short_play_outline"]})
    return {"script_content": res.content}

def shot_prompt_agent(state: CreationState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "将剧本拆为逐镜头AI绘画提示词+完整字幕，严格返回JSON，格式：{\"shots\":[],\"subtitles\":\"\"}"),
        ("user", "剧本：{script}")
    ])
    chain = prompt | llm
    content = chain.invoke({"script": state["script_content"]}).content
    try:
        data = json.loads(content)
        shots = data.get("shots", [])
        sub = data.get("subtitles", "")
    except:
        shots = [content[:200]]
        sub = "自动生成字幕"
    return {"shot_prompts": shots, "subtitles": sub}

def compliance_agent(state: CreationState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "审核短剧剧本和字幕，检查违规、价值观、敏感内容，给出审核结论。"),
        ("user", "剧本：{script}\n字幕：{sub}")
    ])
    chain = prompt | llm
    res = chain.invoke({"script": state["script_content"], "sub": state["subtitles"]}).content
    return {"compliance_check": res}

def final_output_agent(state: CreationState):
    # 修复：把换行拼接移到外面，避免 f-string 里的转义问题
    shots_text = "\n".join(state['shot_prompts'])
    final = """
【AI短剧全流程成品汇总】
📖小说解析：
{}

📋短剧大纲：
{}

🎬分镜剧本：
{}

🎥镜头提示词：
{}

📝完整字幕：
{}

⚖️合规审核：
{}
    """.format(
        state['novel_analysis'],
        state['short_play_outline'],
        state['script_content'],
        shots_text,
        state['subtitles'],
        state['compliance_check']
    )
    return {"final_output": final}

# ---------------------- 构建工作流 ----------------------
def build_workflow():
    workflow = StateGraph(CreationState)
    workflow.add_node("novel_analyze", novel_analyze_agent)
    workflow.add_node("outline", outline_agent)
    workflow.add_node("script", script_agent)
    workflow.add_node("shot_prompt", shot_prompt_agent)
    workflow.add_node("compliance", compliance_agent)
    workflow.add_node("final", final_output_agent)

    workflow.set_entry_point("novel_analyze")
    workflow.add_edge("novel_analyze", "outline")
    workflow.add_edge("outline", "script")
    workflow.add_edge("script", "shot_prompt")
    workflow.add_edge("shot_prompt", "compliance")
    workflow.add_edge("compliance", "final")
    workflow.add_edge("final", END)
    return workflow.compile()

# ---------------------- Streamlit网页界面 ----------------------
def main():
    st.set_page_config(page_title="AI小说-剧本-短剧全流程Agent", layout="wide")
    st.title("🎬 AI小说 → AI剧本 → AI短剧 全流程生成系统")
    st.divider()

    novel_input = st.text_area("请输入小说片段/章节：", height=250, placeholder="粘贴你的网文小说内容...")
    run_btn = st.button("🚀 一键生成全套短剧内容", type="primary")

    if run_btn and novel_input.strip():
        with st.spinner("正在多Agent协同生成中，请稍候..."):
            app = build_workflow()
            result = app.invoke({
                "novel_text": novel_input,
                "shot_prompts": []
            })

        st.success("✅ 生成完成！")
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📖 小说解析")
            st.write(result["novel_analysis"])

            st.subheader("📋 短剧大纲")
            st.write(result["short_play_outline"])

            st.subheader("⚖️ 合规审核")
            st.write(result["compliance_check"])

        with col2:
            st.subheader("🎬 分镜剧本")
            st.text_area("剧本内容", result["script_content"], height=300)

            st.subheader("📝 完整字幕")
            st.text_area("字幕文本", result["subtitles"], height=150)

        st.subheader("🎥 逐镜头AI视频提示词")
        for idx, p in enumerate(result["shot_prompts"], 1):
            st.code(f"镜头{idx}：{p}")

        st.divider()
        st.subheader("📦 完整汇总文案")
        st.download_button("下载完整结果TXT", result["final_output"], file_name="ai短剧全流程结果.txt")

if __name__ == "__main__":
    main()