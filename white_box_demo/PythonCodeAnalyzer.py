import os
from typing import Dict

from white_box_demo.CallGraphBuilder import CallGraphBuilder
from white_box_demo.CodeLogicAnalyzer import CodeLogicAnalyzer
from white_box_demo.PythonInterfaceAnalyzer import PythonInterfaceAnalyzer
from white_box_demo.TestCaseGenerator import TestCaseGenerator


class PythonCodeAnalyzer:
    """Python代码分析器主类"""

    def __init__(self, project_path: str, openai_api_key: str = None):
        self.project_path = project_path
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        # 初始化各个组件
        self.interface_analyzer = PythonInterfaceAnalyzer(project_path)
        self.logic_analyzer = CodeLogicAnalyzer(self.api_key)
        # self.test_generator = TestCaseGenerator(self.logic_analyzer)

    def analyze_interface(self, interface_full_name: str) -> Dict:
        """分析接口及其调用链，生成测试用例"""
        print(f"开始分析接口: {interface_full_name}")

        # 1. 解析接口和实现
        interface_data = self.interface_analyzer.parse_interface(interface_full_name)
        if not interface_data:
            print(f"未找到接口: {interface_full_name}")
            return None

        interface_name = interface_full_name.split('.')[-1]
        implementations = self.interface_analyzer.find_implementations(interface_name)
        if not implementations:
            print(f"未找到接口 {interface_name} 的实现类")
            return None

        # 2. 构建调用图
        graph_builder = CallGraphBuilder(self.interface_analyzer)
        graph = graph_builder.build_call_graph(interface_full_name)
        call_hierarchy = graph_builder.get_call_hierarchy()

        # 3. 可视化调用图
        graph_builder.visualize_call_graph("call_graph")

        # 4. 分析代码逻辑
        print("分析代码逻辑...")
        analysis_results = self.logic_analyzer.analyze_implementation_chain(
            call_hierarchy, implementations)

        print(analysis_results)

        # # 5. 生成测试用例
        # print("生成测试用例...")
        # test_cases = self.test_generator.generate_all_test_cases(call_hierarchy, implementations, analysis_results)
        #
        # # 6. 生成报告
        # report = self.test_generator.format_report(
        #     call_hierarchy, analysis_results, test_cases)
        #
        # # 7. 保存报告
        # report_file = "interface_analysis_report.md"
        # with open(report_file, "w") as f:
        #     f.write(report)

        print(f"分析完成，报告已保存至: {report_file}")

        return {
            'interface': interface_data,
            'implementations': implementations,
            'call_hierarchy': call_hierarchy,
            'analysis': analysis_results,
            'test_cases': test_cases,
            'report': report
        }
