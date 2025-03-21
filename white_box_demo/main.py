import os
import sys
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

    # 分析指定的API入口点
    endpoint = "apps.lora_node.urls.alarm_recovery_report"
    results = analyzer.analyze_api_endpoint(endpoint)
    
    if results:
        print(f"成功分析API入口点: {endpoint}")
        print(f"调用链包含 {len(results['call_graph'].nodes())} 个函数")
        
        # 输出调用链上的所有函数
        print("\n调用链上的函数:")
        for node in results['call_graph'].nodes():
            print(f"  - {node}")
            
        # 可以将源码集合发送给AI进行测试用例生成
        # ...
    else:
        print(f"分析API入口点失败: {endpoint}")