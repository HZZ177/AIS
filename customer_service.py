from crewai import Agent, Task, Crew, process, LLM
from crewai.knowledge.source.crew_docling_source import CrewDoclingSource
from crewai_tools import PDFSearchTool
from langchain_openai import ChatOpenAI
import os

# os.environ["OPENAI_API_KEY"] = "sk-f90f833388614e509da4e80528285dc2"

# 初始化一个llm大语言模型
llm = LLM(
    model="deepseek/deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key="sk-f90f833388614e509da4e80528285dc2"
)

# 建立文件型知识库
knowledge_source = CrewDoclingSource(
    file_paths=[
        "../files/findcarQA.pdf",
    ],
)

# ============================agents============================
# 创建多个agents
search_agent = Agent(
    role="检索员",
    goal="读取QA文档，根据用户的问题来寻找对应可能解决问题的资料",
    backstory="你是一位根据用户提供的问题，在PDF文件中找寻对应资料的检索员，请让你的返回结果尽可能的全面",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

answer_agent = Agent(
    role="资深客服",
    goal="根据用户的问题和检索员提供的对应资料，回答用户的问题",
    backstory="你是一位资深客服，请让你的回答尽可能详细，所有回答的内容需要从参考资料中获取，并且需要根据用户的问题给出最合适的答案。",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ============================tasks============================
task_requirements = Task(
    description="读取辅助文档，分析其中和客户问题：{question} 最相关的资料，找出相关性最高的5条提供给下一步",
    expected_output="5条与问题{question}最相关的详细的资料",
    agent=search_agent,
    verbose=True,
    llm=llm
)

task_testcase = Task(
    description="根基查询员提供的资料，结合用户的问题{question}分析问题可能出现在哪里，对应的解决方案是什么",
    expected_output="问题可能出现在什么地方或者什么环节，对应的解决方案是什么",
    agent=answer_agent,
    verbose=True,
    llm=llm
)

# ========================执行agents工作流========================
crew = Crew(
    agents=[search_agent, answer_agent],
    tasks=[task_requirements, task_testcase],
    Process=process.Process.sequential,
    knowledge_sources=[knowledge_source],
    verbose=True
)


if __name__ == "__main__":
    result = crew.kickoff(inputs={"question": "车位状态变化非常慢"})
    # # print(result)
    # result = tool_pdf.run(
    #     pdf='files/findcarQA.pdf',
    #     query="车位状态变化太慢"
    # )
    # print(result)
