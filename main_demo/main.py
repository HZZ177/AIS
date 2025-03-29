from crewai import Agent, Task, Crew, process, LLM
import os
from tools.search_tool_vector import SearchTool
from main_demo.core.logger import logger

os.environ["OPENAI_API_KEY"] = "sk-f90f833388614e509da4e80528285dc2"

# 初始化一个llm大语言模型
llm = LLM(
    # openrouter
    model="openrouter/google/gemini-2.0-flash-001",
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

# ============================agents============================

search_tool = SearchTool()

# 创建多个agents
search_agent = Agent(
    role="finder",
    goal="根据用户的问题来寻找对应可能解决问题的资料",
    backstory="你是一位根据用户提供的问题，运用工具查询所有可能相关的背景资料和QA资料的检索员，请让你的返回结果尽可能的全面，注意你只能使用中文",
    verbose=True,
    allow_delegation=False,
    # knowledge_sources=[knowledge_source],
    tools=[search_tool,],
    llm=llm
)

answer_agent = Agent(
    role="customer",
    goal="根据用户的问题和检索员提供的对应资料，回答用户的问题",
    backstory="你是一位资深客服，请让你的回答尽可能详细，所有回答的内容需要从参考资料中获取，并且需要根据用户的问题给出最合适的答案，注意你只能使用中文",
    verbose=True,
    allow_delegation=False,
    # knowledge_sources=[knowledge_source],
    llm=llm
)

# ============================tasks============================
task_requirements = Task(
    description="""
    1、你需要根据客户的问题【{question}】，使用工具【search_tool】进行相关背景资料的查询并提供给其他人
    2、你只能使用工具查询出的资料作为信息来源，除此之外不要用使用任何其他来源的信息
    注意：
        如果没有从工具中找到匹配的相关资料，请直接返回没有搜索到任何参考资料
        如果有找到任何可用的资料，请你以以下格式返回：
        【相关参考资料】
        xxxxx
    """,
    expected_output="""
    查询到的详细的资料
    """,
    agent=search_agent,
    verbose=True,
    llm=llm
)

task_testcase = Task(
    description="""
    根据查询员提供的参考资料，结合用户的问题{question}分析问题可能出现在哪里，对应的解决方案是什么
    如果上一步返回给你没有找到任何资料，请直接说明没有接收到任何参考资料，无法回答
    注意：如果有多条建议或方案，请分点列出
    例如：
    【用户】
        入车之后车位状态不变
    【回答】：
        1、可能是由于xxxx
        2、xxxxxxxxxxxxxxx
        3、xxxxxxxxxxxxxxx
    """,
    expected_output="""
    对客户问题的解答
    """,
    agent=answer_agent,
    verbose=True,
    llm=llm
)

# ========================执行agents工作流========================
# 在创建 crew 之前调试可用工具
logger.info("search_agent的可用工具", [tool.name for tool in search_agent.tools])

crew = Crew(
    agents=[search_agent, answer_agent],
    tasks=[task_requirements, task_testcase],
    Process=process.Process.sequential,
    # knowledge_sources=[knowledge_source],
    verbose=True
)


if __name__ == "__main__":
    # 确保 inputs 的 key 与 Task description 中的占位符一致
    result = crew.kickoff(inputs={"question": "车位状态"})
    print("------最终结果------")
    print(result)
