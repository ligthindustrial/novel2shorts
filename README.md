【AI小说+剧本+短剧全流程Agent Web版 使用教程】

1. 环境安装
   1）安装Python 3.10+
   2）打开终端，进入当前文件夹，执行：
      pip install -r requirements.txt

2. 配置API密钥
   打开 ai_shortdrama_web.py
   找到 llm = ChatOpenAI 那一行
   把 api_key="" 填上你的 DeepSeek / 其他大模型API密钥

3. 启动运行
   终端执行：
   streamlit run ai_shortdrama_web.py

4. 使用方法
   1）网页输入小说文本
   2）点击一键生成
   3）自动产出：小说解析、短剧大纲、分镜剧本、字幕、AI镜头提示词、合规审核
   4）可单独复制提示词做AI视频，也可下载全套TXT

5. 接口支持
   可替换为：DeepSeek、通义千问、星火、GPT 兼容OpenAI格式接口