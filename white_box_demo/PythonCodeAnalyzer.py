import os
from typing import Dict
import importlib
import inspect
import traceback

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

    def analyze_api_endpoint(self, endpoint_path):
        """分析API入口点及其调用链
        
        Args:
            endpoint_path: API入口点的导入路径，例如'apps.lora_node.urls.alarm_recovery_report'
        
        Returns:
            包含API调用链所有函数源码的字典
        """
        print(f"开始分析API入口点: {endpoint_path}")
        
        try:
            # 动态导入模块
            module_parts = endpoint_path.split('.')
            module_name = '.'.join(module_parts[:-1])
            function_name = module_parts[-1]
            
            module = importlib.import_module(module_name)
            endpoint_function = getattr(module, function_name, None)
            
            if not endpoint_function:
                print(f"未找到API入口点函数: {endpoint_path}")
                return None
            
            # 构建调用图
            call_graph_builder = CallGraphBuilder(self.project_path)
            call_graph = call_graph_builder.build_call_graph_from_function(endpoint_function, endpoint_path)
            
            # 收集调用链上所有函数的源码
            source_code_collection = self._collect_source_code(call_graph)
            
            return {
                'endpoint': endpoint_path,
                'call_graph': call_graph,
                'source_code': source_code_collection
            }
            
        except Exception as e:
            print(f"分析API入口点时出错: {str(e)}")
            traceback.print_exc()
            return None
        
    def _collect_source_code(self, call_graph):
        """收集调用图中所有函数的源码"""
        source_code_collection = {}
        
        for node in call_graph.nodes():
            try:
                func_parts = node.split('.')
                module_name = '.'.join(func_parts[:-1])
                func_name = func_parts[-1]
                
                module = importlib.import_module(module_name)
                func = getattr(module, func_name)
                
                # 获取源码
                try:
                    source = inspect.getsource(func)
                    source_code_collection[node] = {
                        'source': source,
                        'file': inspect.getfile(func),
                        'line': inspect.getsourcelines(func)[1]
                    }
                except Exception as e:
                    print(f"无法获取函数 {node} 的源码: {str(e)}")
                
            except Exception as e:
                print(f"处理节点 {node} 时出错: {str(e)}")
            
        return source_code_collection
