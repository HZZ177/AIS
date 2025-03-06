#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/3/6 15:27
# @Author  : Heshouyi
# @File    : tasks.py
# @Software: PyCharm
# @description:
from crewai import Task


class Tasks:
    @staticmethod
    def requirements_analysis_task(agent) -> Task:
        requirements_task = Task(
            description="""
【需求文档内容】
{requirements}
【额外辅助信息】
{extra_info}

读取需求文件中的“功能需求说明”部分，分析并总结测试点
你只能使用中文来沟通和回答，如果没有查询到需求内容，直接返回没有查询到
请让你的回答尽可能的详细，如果没有找到相关资料，请直接说无任何需求资料可提供
请从以下文档中提取所有明确的需求，返回测试点请严格按照以下格式：
    测试点一：xxxx
    测试点二：xxxx
    测试点三：xxxx
    ......
    不要有任何额外信息，也不要有测试用例，只需要输出测试点
            """,
            expected_output="""
用分点的形式列出根据需求文档内容拆分出的详细的测试点
            """,
            agent=agent,
            verbose=True,
        )
        return requirements_task

    @staticmethod
    def test_point_checker_task(agent):
        test_point_checker_task = Task(
            description="""
【需求文档内容】
{requirements}
【额外辅助信息】
{extra_info}

根据提供给你的需求，审核前一个测试员拆分的测试点
1、如果你认为测试点已经完全覆盖需求，直接将测试点一模一样返回，格式如下：
    评审结果：【评审通过】不需要修改，以下是测试点列表：
    测试点一：xxxx
    测试点二：xxxx
    测试点三：xxxx
    ......

2、如果你认为有不足，在已有测试点的基础上进行优化补充，然后严格按照以下格式返回测试点：
    评审结果：【评审不通过】以下是修改优化后的测试点：
    测试点一：xxxx
    测试点二：xxxx
    测试点三：xxxx
    ......

除此之外不要有任何额外信息
            """,
            expected_output="""基于需求以及前一位测试人员拆分的测试点的基础上，评审优化后的测试点""",
            agent=agent,
            verbose=True,
            human_input=True
        )
        return test_point_checker_task

    @staticmethod
    def testcase_task(agent):
        testcase_task = Task(
            description=r"""
1、根据提供给你的测试点列表编写测试用例，每一个测试点应该对应多条用例，使用等价类，边界值，异常值等方法，尽量全面的设计用例
2、返回的格式用markdown语法，且除了标题分级外不要用其他的语法例如加粗，斜体等，下面是一个用例的格式示例:
# 总名称
## 模块分级1
### 模块分级2
#### 用例标题（例如：用例一：xxxx）
##### 【前置条件】
##### 步骤
    ###### 步骤1
    ###### 步骤2
##### 预期结果
    ###### 预期结果2
    ###### 预期结果3
4、不同参数类型的用例用分成不同的用例，而不是在对应这个测试点的步骤中分成多个步骤，
比如验证某个配置的测试点，不填该配置，填入生效的值，填入不生效的值，应该分为三个用例，而不是一个用例的三个步骤对应三种预期结果
5、标题分级的要求是，无论怎么分类，最好第三级是用例标题，最多到第四级是用例标题；不要使用代码块，代码块会导致导入xmind时内容进入备注里
            """,
            expected_output="测试用例列表",
            agent=agent,
            verbose=True
        )
        return testcase_task
