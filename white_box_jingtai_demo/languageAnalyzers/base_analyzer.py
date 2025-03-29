import os
import networkx as nx
from abc import ABC, abstractmethod


class BaseAnalyzer(ABC):
    """代码分析器的基类，定义了通用接口"""

    def __init__(self, project_path):
        self.project_path = project_path
        self.call_graph = nx.DiGraph()

    @abstractmethod
    def analyze_entry_point(self, entry_point_path):
        """分析指定入口点及其调用链"""
        pass

    @abstractmethod
    def find_entry_point_file(self, entry_point_path):
        """根据入口点路径找到对应的源文件"""
        pass

    @abstractmethod
    def parse_file(self, file_path):
        """解析源文件"""
        pass

    @abstractmethod
    def extract_calls(self, ast_node, caller):
        """从AST节点提取调用"""
        pass

    @abstractmethod
    def resolve_call_path(self, call_expr, context_path):
        """解析调用表达式的完整路径"""
        pass

    def collect_source_code(self):
        """收集调用链上所有函数的源码"""
        source_collection = {}

        for node in self.call_graph.nodes():
            file_path, position = self.locate_definition(node)
            if file_path and os.path.exists(file_path):
                source_collection[node] = self.extract_function_source(file_path, position)

        return source_collection

    @abstractmethod
    def locate_definition(self, function_path):
        """定位函数定义的文件和位置"""
        pass

    @abstractmethod
    def extract_function_source(self, file_path, position):
        """提取函数的源代码"""
        pass