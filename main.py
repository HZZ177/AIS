from crewai import Agent, Task, Crew
from crewai_tools import PDFSearchTool
from langchain_openai import ChatOpenAI
import os

os.environ["OPENAI_API_KEY"] = "sk-f90f833388614e509da4e80528285dc2"

# 初始化一个llm大语言模型
llm = ChatOpenAI(
    model="deepseek/deepseek-chat",
    base_url="https://api.deepseek.com"
)

# 创建一个需求文档读取的智能体，该智能体通过调用 外部工具 完成文档内容读取
tool_pdf = PDFSearchTool(
    pdf="api_doc.pdf",
    config=dict(
        embedder=dict(
            provider="ollama",
            config=dict(
                model="nomic-embed-text",
                base_url="http://127.0.0.1:11434",
            )
        )
    )
)

# ============================agents============================
# 创建多个agents
requirements_analysis_agent = Agent(
    role="软件测试需求分析工程师",
    goal="读取需求文件，分析其中的测试需求",
    backstory="你是一位根据用户提供的PDF文件获取测试需求的测试工程师，请让你的回答尽可能的详细",
    tools=[tool_pdf],
    verbose=True,
    llm=llm
)

testcase_agent = Agent(
    role="软件用例生成工程师",
    goal="根据需求列表编写测试用例",
    backstory="你是一位专业的软件测试用例编写工程师，请让你的回答尽可能详细。",
    verbose=True,
    llm=llm
)

# ============================tasks============================
# 创建需求分析工程师对应的任务
task_requirements = Task(
    description="读取需求文档，分解出详细的需求条目",
    expected_output="详细的需求列表",
    agent=requirements_analysis_agent,
    verbose=True,
    llm=llm
)

# 创建测试用例分析工程师对应的任务
task_testcase = Task(
    description="根据需求列表编写测试用例，尽可能覆盖到多种用例设计方法。",
    expected_output="测试用例列表",
    agent=testcase_agent,
    verbose=True,
    llm=llm
)

# ========================执行agents工作流========================
crew = Crew(
    agents=[requirements_analysis_agent, testcase_agent],
    tasks=[task_requirements, task_testcase],
    verbose=True
)

result = crew.kickoff()
print(result)















