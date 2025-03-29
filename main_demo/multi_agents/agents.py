from crewai import Agent


class Agents:
    @staticmethod
    def search_agent(llm, tools: list = None):
        search_agent = Agent(
            role="finder",
            goal="根据用户的问题来寻找对应可能解决问题的资料",
            backstory="你是一位根据用户提供的问题，运用工具查询所有可能相关的背景资料和QA资料的检索员，请让你的返回结果尽可能的全面，注意你只能使用中文",
            verbose=True,
            tools=tools,
            llm=llm
        )
        return search_agent

    @staticmethod
    def customer_agent(llm):
        customer_agent = Agent(
            role="customer",
            goal="根据用户的问题和检索员提供的对应资料，回答用户的问题",
            backstory="你是一位资深客服，请让你的回答尽可能详细，所有回答的内容需要从参考资料中获取，并且需要根据用户的问题给出最合适的答案，注意你只能使用中文",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )
        return customer_agent
