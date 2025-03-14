import os
from white_box_demo.PythonCodeAnalyzer import PythonCodeAnalyzer


if __name__ == "__main__":
    # todo 暂时屏蔽用例生成逻辑
    api_key = "123"
    if not api_key:
        print("请设置OPENAI_API_KEY环境变量")
        exit(1)

    # 初始化分析器
    analyzer = PythonCodeAnalyzer(
        project_path=r"C:\Users\86364\PycharmProjects\cd_findcar_automation_engine",
        openai_api_key=api_key
    )

    # 分析指定的接口/抽象类
    results = analyzer.analyze_interface("apps.lora_node.urls.alarm_recovery_report")