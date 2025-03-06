from crewai import Agent, Task, Crew, process, LLM
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
import os

os.environ["OPENAI_API_KEY"] = "sk-f90f833388614e509da4e80528285dc2"

# 初始化一个llm大语言模型
llm = LLM(
    # openrouter
    model="openrouter/google/gemini-2.0-flash-001",
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

# 建立文件型知识库
knowledge_source = PDFKnowledgeSource(
    file_paths=["findcarQA.pdf"],
    api_key="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"  # 添加API密钥
)

# ============================agents============================
# 创建多个agents
search_agent = Agent(
    role="finder",
    goal="读取QA文档，根据用户的问题来寻找对应可能解决问题的资料",
    backstory="你是一位根据用户提供的问题，在PDF文件中找寻对应资料的检索员，请让你的返回结果尽可能的全面",
    verbose=True,
    allow_delegation=False,
    knowledge_sources=[knowledge_source],
    llm=llm
)

answer_agent = Agent(
    role="customer",
    goal="根据用户的问题和检索员提供的对应资料，回答用户的问题",
    backstory="你是一位资深客服，请让你的回答尽可能详细，所有回答的内容需要从参考资料中获取，并且需要根据用户的问题给出最合适的答案。",
    verbose=True,
    allow_delegation=False,
    knowledge_sources=[knowledge_source],
    llm=llm
)

# ============================tasks============================
task_requirements = Task(
    description="读取辅助文档，分析其中和客户问题：{question} 最相关的资料，找出相关性最高的5条提供给下一步，注意：如果没有从文档中找到精确匹配的相关资料原文，请直接返回没有找到",
    expected_output="5条与问题{question}最相关的详细的资料",
    agent=search_agent,
    verbose=True,
    llm=llm
)

task_testcase = Task(
    description="根基查询员提供的资料，结合用户的问题{question}分析问题可能出现在哪里，对应的解决方案是什么，如果上一步返回给你没有找到任何资料，请直接说明没有找到",
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
