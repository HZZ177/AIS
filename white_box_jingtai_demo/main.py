import uuid

from crewai import Crew, process, LLM
from white_box_jingtai_demo.Multi_agents.agents import Agents
from white_box_jingtai_demo.Core.utils import save_to_md
from white_box_jingtai_demo.CodeAnalyzer.source_collector import analyze_code
from white_box_jingtai_demo.Multi_agents.tasks import Tasks

# 初始化一个llm大语言模型
llm = LLM(
    # openrouter
    model="openrouter/deepseek/deepseek-chat-v3-0324:free",
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)


# ========================组装agents工作流========================
agents = Agents()
source_code_analyzer_agent = agents.source_code_analyzer_agent(llm)     # 分析源码并生成测试点agent
test_point_checker_agent = agents.test_point_checker_agent(llm)     # 测试点审核agent
testcase_generator_agent = agents.testcase_generator_agent(llm)     # 测试用例生成agent


tasks = Tasks()
source_code_analysis_task = tasks.source_code_analysis_task(source_code_analyzer_agent)     # 分析源码并生成测试点task
test_point_check_task = tasks.test_point_checker_task(test_point_checker_agent)     # 测试点审核task
testcase_generate_task = tasks.testcase_generate_task(testcase_generator_agent)       # 测试用例生成task

crew = Crew(
    agents=[source_code_analyzer_agent, test_point_checker_agent, testcase_generator_agent],
    tasks=[source_code_analysis_task, test_point_check_task, testcase_generate_task],
    Process=process.Process.sequential,     # 流式执行
    verbose=True    # 详细打印过程信息
)


if __name__ == "__main__":
    # 定义项目路径，要测试的函数入口
    project_path = r"C:\Users\86364\PycharmProjects\cd_findcar_automation_engine"
    entry_point = "apps.parking_camera.urls.upload_parking_picture"

    # 解析并收集调用链源码
    source_code = str(analyze_code(project_path, entry_point, 'python'))
    extra_info = "无"

    result = crew.kickoff(
        inputs={
            "source_data": source_code,
            "extra_info": extra_info
        }
    )

    # 保存用例到md文件
    uuid = str(uuid.uuid4()).replace("-", "")
    save_to_md(result, f"generate_testcase_{uuid}")
