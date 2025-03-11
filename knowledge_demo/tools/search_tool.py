from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import requests
import json


class YunWeiSearchToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    keyword: str = Field(..., description="需要查询的关键字")


class SearchTool(BaseTool):
    name: str = "search_tool"
    description: str = """
    需要查询任何与项目背景以及问答相关的信息时，使用该工具用来搜索运维中心知识库的信息，提供背景信息支持
    """
    args_schema: Type[BaseModel] = YunWeiSearchToolInput

    def _run(self, keyword: str) -> str:
        # Your tool's logic here
        url = "https://yunwei-help.keytop.cn/helpApi/HelpDoc/getDataByKeyword"
        payload = json.dumps({
            "keyword": keyword,
            "pageIndex": 1,
            "pageSize": 20,
            "projectId": "27"
        })
        headers = {
            'token': '5iw61f16wtjh2p46ue38h19tloo5pftw9fupsd7omeyd6b9uj1jyv4pr0ts86hvdozt8apcrbhbahb9giw74o0kt14c0mxzzxfp40wmfqdiaahsxdvaqzvofmmplm2aesjtgk1pt67zpx7bb',
            'userid': '6c2c601eaf9c4babbb0f8b1a6601260c',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return "车位状态变化慢可能是因为紧急模式开关打开造成的"


if __name__ == "__main__":
    tool = YunWeiSearchTool()
    print(tool.run("车位状态"))
