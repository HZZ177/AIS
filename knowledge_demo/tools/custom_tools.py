from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import requests
import json


class YunWeiSearchToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    keyword: str = Field(..., description="需要查询的关键字")


class YunWeiSearchTool(BaseTool):
    name: str = "运维中心搜索工具"
    description: str = """
    运维中心知识库包含了项目的背景信息，问答信息，技术支持等
    该工具用来根据提供的搜索接口，按照关键搜索运维中心知识库的信息，提供背景信息支持
    """
    args_schema: Type[BaseModel] = YunWeiSearchToolInput

    def _run(self, argument: str) -> str:
        # Your tool's logic here
        url = "https://yunwei-help.keytop.cn/helpApi/HelpDoc/getDataByKeyword"
        payload = json.dumps({
            "keyword": argument,
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

        return response.text


if __name__ == "__main__":
    tool = YunWeiSearchToolInput()
    print(tool.run("车位状态"))
