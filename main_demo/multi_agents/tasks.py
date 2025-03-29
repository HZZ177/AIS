from crewai import Task


class Tasks:
    @staticmethod
    def search_task(agent) -> Task:
        search_task = Task(
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
            agent=agent,
            verbose=True
        )
        return search_task

    @staticmethod
    def customer_task(agent):
        customer_task = Task(
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
            agent=agent,
            verbose=True,
        )
        return customer_task
