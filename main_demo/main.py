from crewai import Agent, Task, Crew, process, LLM
from main_demo.multi_agents.agents import Agents
from main_demo.multi_agents.tasks import Tasks
from tools.search_tool_vector import SearchTool
from main_demo.core.logger import logger

# 初始化模型
llm = LLM(
    # openrouter
    model="openrouter/google/gemini-2.0-flash-001",
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

# =============================agents============================= #
# 初始化向量搜索工具
search_tool = SearchTool()

# 初始化agents
agents = Agents()
search_agent = agents.search_agent(llm, tools=[search_tool])
customer_agent = agents.customer_agent(llm)

# 初始化tasks
tasks = Tasks()
search_task = tasks.search_task(search_agent)
customer_task = tasks.customer_task(customer_agent)

# 开始crew流程
crew = Crew(
    agents=[search_agent, customer_agent],
    tasks=[search_task, customer_task],
    Process=process.Process.sequential,     # 流式执行
    verbose=True    # 详细打印过程信息
)


if __name__ == "__main__":
    # 确保 inputs 的 key 与 Task description 中的占位符一致
    result = crew.kickoff(inputs={"question": "车位状态"})
    logger.info(f"------最终结果------\n{result}")
