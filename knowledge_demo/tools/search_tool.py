from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import requests
import json


class YunWeiSearchToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    keyword: str = Field(..., description="需要查询的关键字")


class SearchTool(BaseTool):
    name: str = "search_tool"  # 修改工具名称，使用更规范的名称
    description: str = """
    当需要查询运维中心知识库信息时使用该工具。

    """
    args_schema: Type[BaseModel] = YunWeiSearchToolInput

    def _run(self, keyword: str) -> str:
        try:
            print(f"接受的输入：{keyword}")
            url = "https://yunwei-help.keytop.cn/helpApi/HelpDoc/getDataByKeyword"
            payload = {
                "keyword": keyword,
                "pageIndex": 1,
                "pageSize": 20,
                "projectId": 27
            }
            headers = {
                'token': '5iw61f16wtjh2p46ue38h19tloo5pftw9fupsd7omeyd6b9uj1jyv4pr0ts86hvdozt8apcrbhbahb9giw74o0kt14c0mxzzxfp40wmfqdiaahsxdvaqzvofmmplm2aesjtgk1pt67zpx7bb',
                'userid': '6c2c601eaf9c4babbb0f8b1a6601260c',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, json=payload)
            # print(response.text)
            data = response.json().get("data").get("list")
            md_list = []
            for i, _ in enumerate(data):
                title = _.get("text")
                md_info = _.get("md")
                if "接口" not in title:
                    md_list.append(f"{i+1}、{md_info}")
                else:
                    print(f"查询到{title}—接口相关内容，跳过引用")

            md_info = "\n\n\n".join(md_list)
            # print(md_info)

            if response.status_code == 200:
                # 处理响应数据
                return md_info
            else:
                return f"查询失败: HTTP {response.status_code}"

        except Exception as e:
            return f"查询出错: {str(e)}"


if __name__ == "__main__":
    tool = SearchTool()
    print(tool.run("车位状态"))
