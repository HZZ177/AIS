import datetime

import PyPDF2

from agents import Agents
from tasks import Tasks

from crewai import Crew, process, LLM
from crewai_tools.tools.pdf_search_tool.pdf_search_tool import PDFSearchTool


# 初始化一个llm大语言模型
openrouter_llm = LLM(
    model="openrouter/google/gemini-2.0-flash-001",
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

deepseek_llm = LLM(
    model="deepseek/deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key="sk-f90f833388614e509da4e80528285dc2"
)

# 定义使用的llm
llm = openrouter_llm


def extract_text_from_pdf(pdf_path):
    """提取 PDF 文本内容"""
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text


# ============================agents============================
# # 创建多个agents
# requirements_analysis_agent = Agent(
#     role="软件测试需求分析工程师",
#     goal="使用工具，读取需求文件中需要的部分，分析其中的测试点，你只能使用中文来沟通和回答",
#     backstory="""
#     你是一位根据用户提供的PDF文件分析测试需求的测试工程师，你给出的资料会传递给下一位测试员作为需求信息。
#     请让你的回答尽可能的详细，如果没有找到相关资料，请直接说无任何需求资料可提供
#     """,
#     # backstory="""""",
#     tools=[tool_pdf],
#     verbose=True,
#     llm=llm
# )
#
# testcase_generator_agent = Agent(
#     role="软件用例生成工程师",
#     goal="根据需求列表编写测试用例，你只能使用中文来沟通和回答",
#     backstory="""
#     你是一位专业的软件测试用例编写工程师，请根据发送给你的需求，尽量全面的设计用例，尽可能详细
#     如果没有接收到任何拆分后的需求信息，请直接说没有接收到任何需求信息，无法拆分用例
#     """,
#     # backstory="""""",
#     verbose=True,
#     llm=llm
# )
#
# # ============================tasks============================
# # 创建需求分析工程师对应的任务
# task_requirements = Task(
#     description=f"""
#     读取需求文件中的“功能需求说明”部分，分析并总结测试点
#     你只能使用中文来沟通和回答，如果没有查询到需求内容，直接返回没有查询到
#     """,
#     expected_output="""
#     用分点的形式列出根据需求文档内容拆分出的详细的测试点
#     """,
#     agent=requirements_analysis_agent,
#     verbose=True,
#     llm=llm
# )
#
# # 创建测试用例分析工程师对应的任务
# task_testcase = Task(
#     description=rf"""
#     1、根据提供给你的测试点列表编写测试用例，每一条测试点至少对应一条用例，使用等价类，边界值，异常值等方法，尽量全面的设计用例
#     2、所有关于输入框，选择框，支付金额等需要有限制，能够分类的场景，都必须使用等价类边界值分类进行用例设计
#     3、返回的格式用markdown语法，且除了标题分级外不要用其他的语法例如加粗，斜体等，下面是一个用例的格式示例:
#     # 总名称
#     ## 模块分级1
#     ### 模块分级2
#     #### 用例标题
#     ##### 【前置条件】
#     ##### 步骤
#         ###### 步骤1
#         ###### 步骤2
#     ##### 预期结果
#         ###### 预期结果2
#         ###### 预期结果3
#     4、不同参数类型的用例用分成不同的用例，而不是在对应这个测试点的步骤中分成多个步骤，
#     比如验证某个配置的测试点，不填该配置，填入生效的值，填入不生效的值，应该分为三个用例，而不是一个用例的三个步骤对应三种预期结果
#     5、标题分级的要求是，无论怎么分类，最好第三级是用例标题，最多到第四级是用例标题；不要使用代码块，代码块会导致导入xmind时内容进入备注里
#     """,
#     # 4、下面是本次需求经过拆分好的测试点内容\n{content}，请输出不少于120条用例，尽可能的拆分详细"
#     # 如果没有接收到任何拆分后的需求信息，请直接说没有接收到任何需求信息，无法拆分用例
#     expected_output="测试用例列表",
#     agent=testcase_generator_agent,
#     verbose=True,
#     llm=llm
# )

# ========================执行agents工作流========================
agents = Agents()
requirements_analysis_agent_static = agents.requirements_analysis_agent_static(llm)
test_point_checker_agent = agents.test_point_checker_agent(llm)
testcase_generator_agent = agents.testcase_generator_agent(llm)


tasks = Tasks()
requirements_task = tasks.requirements_analysis_task(requirements_analysis_agent_static)
test_point_check_task = tasks.test_point_checker_task(test_point_checker_agent)
testcase_task = tasks.testcase_task(testcase_generator_agent)

crew = Crew(
    agents=[requirements_analysis_agent_static, test_point_checker_agent, testcase_generator_agent],
    tasks=[requirements_task, test_point_check_task, testcase_task],
    Process=process.Process.sequential,
    verbose=True
)


if __name__ == "__main__":
    requirements = extract_text_from_pdf("knowledge/test.pdf")
    extra_info = extract_text_from_pdf("knowledge/相机告警信息上报.pdf")

    result = crew.kickoff(
        inputs={
            "requirements": requirements,
            "extra_info": extra_info
        }
    )

    now = datetime.datetime.now().strftime("%m-%d-%H-%M")
    save_path = rf"C:\obsidian\仓库\Everything\AI 相关\AI用例\testcase_result-{now}.md"
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(str(result))
