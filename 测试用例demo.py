from crewai import Agent, Task, Crew, process, LLM
from crewai_tools import PDFSearchTool
from langchain_openai import ChatOpenAI
import os

# os.environ["OPENAI_API_KEY"] = "sk-f90f833388614e509da4e80528285dc2"
os.environ["OPENAI_API_KEY"] = "sk-bff4abb64efa423392aa04813aebd1a0"

# 初始化一个llm大语言模型
llm = ChatOpenAI(
    # deepseek
    # model="deepseek/deepseek-chat",
    # base_url="https://api.deepseek.com",
    # api_key="sk-f90f833388614e509da4e80528285dc2"
    # 硅基流动
    # model="deepseek-ai/DeepSeek-V3",
    # base_url="https://api.siliconflow.cn/v1",
    # api_key="sk-vxyvdnryevgolxatlsqilklzpiyfadxpkkqpvsagrgvuzavi"
    # ollama
    # model="ollama/deepseek-r1:1.5b",
    # base_url="http://127.0.0.1:11434",
    # 千问
    model="openai/qwen-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/",
    api_key="sk-bff4abb64efa423392aa04813aebd1a0"
)

# 创建一个需求文档读取工具，通过调用外部工具完成文档内容向量化并读取
tool_pdf = PDFSearchTool(
    pdf="/knowledge/test.pdf",
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
    goal="读取需求文件，分析其中的测试需求，你只能使用中文来沟通和回答",
    backstory="你是一位根据用户提供的PDF文件获取测试需求的测试工程师，请让你的回答尽可能的详细",
    tools=[tool_pdf],
    verbose=True,
    llm=llm
)

testcase_agent = Agent(
    role="软件用例生成工程师",
    goal="根据需求列表编写测试用例，你只能使用中文来沟通和回答",
    backstory="你是一位专业的软件测试用例编写工程师，请让你的回答尽可能详细。",
    verbose=True,
    llm=llm
)

# ============================tasks============================
# 创建需求分析工程师对应的任务
task_requirements = Task(
    description="读取需求文档，分解出详细的需求条目",
    expected_output="你得到的详细的需求列表，用分点的形式列出",
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
    Process=process.Process.sequential,
    verbose=True
)

result = crew.kickoff()
# print(result)















