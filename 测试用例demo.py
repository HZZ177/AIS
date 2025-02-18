from datetime import datetime

import litellm
from crewai import Agent, Task, Crew, process, LLM

# os.environ["OPENAI_API_KEY"] = "sk-f90f833388614e509da4e80528285dc2"
# os.environ["OPENAI_API_KEY"] = "sk-bff4abb64efa423392aa04813aebd1a0"
with open("./knowledge/test.txt", "r", encoding="utf-8") as f:
    content = f.read()

# 初始化一个llm大语言模型
llm = LLM(
    # deepseek
    # model="deepseek/deepseek-chat",
    # base_url="https://api.deepseek.com",
    # api_key="sk-f90f833388614e509da4e80528285dc2"

    # openrouter
    model="openrouter/google/gemini-2.0-flash-001",
    base_url="https://openrouter.ai/api/v1",
    api_key="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"

    # 硅基流动
    # model="deepseek-ai/DeepSeek-V3",
    # base_url="https://api.siliconflow.cn/v1",
    # api_key="sk-vxyvdnryevgolxatlsqilklzpiyfadxpkkqpvsagrgvuzavi"

    # ollama
    # model="ollama/deepseek-r1:1.5b",
    # base_url="http://127.0.0.1:11434",

    # 千问
    # model="openai/qwen-max",
    # base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/",
    # api_key="sk-bff4abb64efa423392aa04813aebd1a0"
)

# 创建一个需求文档读取工具，通过调用外部工具完成文档内容向量化并读取
# tool_pdf = DOCXSearchTool(
#     docx=r"C:\Users\86364\PycharmProjects\AIS\knowledge\test.docx",
#     config=dict(
#         embedder=dict(
#             provider="ollama",
#             config=dict(
#                 model="nomic-embed-text",
#                 base_url="http://127.0.0.1:11434",
#             )
#         )
#     )
# )

# ============================agents============================
# 创建多个agents
requirements_analysis_agent = Agent(
    role="软件测试需求分析工程师",
    goal="读取需求文件中的全部内容，分析其中的测试需求，你只能使用中文来沟通和回答",
    # backstory="""
    # 你是一位根据用户提供的PDF文件分析测试需求的测试工程师，你给出的资料会传递给下一位测试员作为需求信息。
    # 请让你的回答尽可能的详细，如果没有找到相关资料，请直接说无任何需求资料可提供
    # """,
    backstory="""""",
    # tools=[tool_pdf],
    verbose=True,
    llm=llm
)

testcase_agent = Agent(
    role="软件用例生成工程师",
    goal="根据需求列表编写测试用例，你只能使用中文来沟通和回答",
    # backstory="""
    # 你是一位专业的软件测试用例编写工程师，请根据发送给你的需求，尽量全面的设计用例，尽可能详细
    # 如果没有接收到任何拆分后的需求信息，请直接说没有接收到任何需求信息，无法拆分用例
    # """,
    backstory="""""",
    verbose=True,
    llm=llm
)

# ============================tasks============================
# 创建需求分析工程师对应的任务
task_requirements = Task(
    description=f"""
    读取测试点中的全部内容，分析并总结，你只能使用中文来沟通和回答，如果没有查询到需求内容，直接返回没有查询到
    
    """,
    expected_output="""
    用分点的形式列出根据需求文档内容拆分出的详细的需求列表
    """,
    agent=requirements_analysis_agent,
    verbose=True,
    llm=llm
)

# 创建测试用例分析工程师对应的任务
task_testcase = Task(
    description=rf"""
    1、根据提供给你的测试点列表编写测试用例，每一条测试点至少对应一条用例，使用等价类，边界值，异常值等方法，尽量全面的设计用例
    2、所有关于输入框，选择框，支付金额等需要有限制，能够分类的场景，都必须使用等价类边界值分类进行用例设计
    2、返回的格式用markdown语法，且除了标题分级外不要用其他的语法例如加粗，斜体等，下面是一个用例的格式示例:
    # 总名称
    ## 模块分级1
    ### 模块分级2
    #### 用例标题
    ##### 【前置条件】xxxxx
    ##### 步骤1\n步骤1\n步骤2
    ###### 预期结果1\n预期结果2\n预期结果3
    3、不同参数类型的用例用分成不同的用例，而不是在对应这个测试点的步骤中分成多个步骤，
    比如验证某个配置的测试点，不填该配置，填入生效的值，填入不生效的值，应该分为三个用例，而不是一个用例的三个步骤对应三种预期结果
    4、标题分级的要求是，无论怎么分类，最好第三级是用例标题，最多到第四级是用例标题；不要使用代码块，代码块会导致导入xmind时内容进入备注里
    4、下面是本次需求经过拆分好的测试点内容\n{content}"
    """,
    # 如果没有接收到任何拆分后的需求信息，请直接说没有接收到任何需求信息，无法拆分用例
    expected_output="测试用例列表",
    agent=testcase_agent,
    verbose=True,
    llm=llm
)

# ========================执行agents工作流========================
crew = Crew(
    agents=[testcase_agent],
    tasks=[task_testcase],
    Process=process.Process.sequential,
    verbose=True
)

result = crew.kickoff()
with open(r"D:\obsidian\仓库\Everything\用例DEMO\testcase_result.md", "w", encoding="utf-8") as f:
    f.write(str(result))
# print(result)
