from typing import Dict, Set

import networkx as nx
import matplotlib.pyplot as plt
from graphviz import Digraph
import re


class CallGraphBuilder:
    """调用关系图构建器"""

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.graph = nx.DiGraph()

    def build_call_graph(self, interface_name: str) -> nx.DiGraph:
        """构建从接口方法开始的调用图"""
        # 首先确保解析了接口和其实现
        if not self.analyzer.interfaces:
            self.analyzer.parse_interface(interface_name)

        if not self.analyzer.implementations:
            self.analyzer.find_implementations(interface_name.split('.')[-1])

        # 添加接口方法节点
        for interface, interface_data in self.analyzer.interfaces.items():
            for method in interface_data['methods']:
                method_id = f"{interface}.{method['name']}"
                self.graph.add_node(method_id,
                                    type='interface',
                                    file_path=interface_data['path'],
                                    line_no=method['line_no'])

                # 添加实现类方法节点并连接
                for impl_class, impl_data in self.analyzer.implementations.items():
                    if impl_data['interface'] == interface:
                        for method_impl in impl_data['methods']:
                            if method_impl['name'] == method['name']:
                                impl_method_id = f"{impl_class}.{method_impl['name']}"
                                self.graph.add_node(impl_method_id,
                                                    type='implementation',
                                                    file_path=impl_data['path'],
                                                    line_no=method_impl['line_no'])
                                self.graph.add_edge(method_id, impl_method_id)

                                # 分析方法体中的调用
                                self._analyze_method_calls(impl_method_id, impl_class, method_impl)

        return self.graph

    def _analyze_method_calls(self, caller_id: str, caller_class: str, method_info: Dict) -> None:
        """分析方法体中的方法调用"""
        method_body = method_info['body']
        if not method_body:
            return

        # 使用正则表达式查找方法调用（简化版，实际应用中可能需要更复杂的解析）
        # self.xxx() 模式
        self_calls = re.findall(r'self\.(\w+)\(', method_body)
        for method_name in self_calls:
            callee_id = f"{caller_class}.{method_name}"
            self.graph.add_node(callee_id, type='method_call')
            self.graph.add_edge(caller_id, callee_id)

        # xxx.yyy() 模式（可能是其他对象的方法调用）
        obj_calls = re.findall(r'(\w+)\.(\w+)\(', method_body)
        for obj_name, method_name in obj_calls:
            if obj_name != 'self':
                callee_id = f"{obj_name}.{method_name}"
                self.graph.add_node(callee_id, type='external_call')
                self.graph.add_edge(caller_id, callee_id)

        # 函数调用模式 zzz()
        func_calls = re.findall(r'(?<![.\w])(\w+)\(', method_body)
        for func_name in func_calls:
            if func_name not in ('if', 'for', 'while', 'print', 'str', 'int', 'list', 'dict', 'set', 'tuple'):
                callee_id = f"function.{func_name}"
                self.graph.add_node(callee_id, type='function_call')
                self.graph.add_edge(caller_id, callee_id)

    def visualize_call_graph(self, output_file: str = "call_graph") -> None:
        """使用Graphviz可视化调用关系图"""
        dot = Digraph(comment='接口调用关系图')

        # 添加节点
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('type', '')
            file_path = self.graph.nodes[node].get('file_path', 'Unknown')
            line_no = self.graph.nodes[node].get('line_no', 'Unknown')

            # 根据节点类型设置不同的样式
            if node_type == 'interface':
                dot.node(node, f"{node}\n[接口: {file_path}:{line_no}]", shape='ellipse', style='filled',
                         fillcolor='lightblue')
            elif node_type == 'implementation':
                dot.node(node, f"{node}\n[实现: {file_path}:{line_no}]", shape='box', style='filled',
                         fillcolor='lightgreen')
            elif node_type in ('method_call', 'external_call', 'function_call'):
                dot.node(node, node, shape='diamond', style='filled', fillcolor='lightgray')
            else:
                dot.node(node, node)

        # 添加边
        for edge in self.graph.edges():
            dot.edge(edge[0], edge[1])

        # 保存和渲染图形
        dot.render(output_file, format='png', cleanup=True)
        print(f"调用关系图已保存为: {output_file}.png")

    def get_call_hierarchy(self) -> Dict:
        """获取接口的完整调用层次结构"""
        hierarchy = {}

        # 找出所有接口方法（根节点）
        interface_nodes = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'interface']

        # 为每个接口方法构建调用层次结构
        for interface_node in interface_nodes:
            hierarchy[interface_node] = self._build_hierarchy_recursive(interface_node, set())

        return hierarchy

    def _build_hierarchy_recursive(self, node: str, visited: Set[str]) -> Dict:
        """递归构建节点的调用层次结构"""
        if node in visited:
            return {'circular_ref': True}  # 处理循环引用

        visited.add(node)
        result = {
            'type': self.graph.nodes[node].get('type', 'unknown'),
            'file_path': self.graph.nodes[node].get('file_path', 'Unknown'),
            'line_no': self.graph.nodes[node].get('line_no', 'Unknown'),
            'children': {}
        }

        # 获取该节点的所有后继节点
        for successor in self.graph.successors(node):
            result['children'][successor] = self._build_hierarchy_recursive(successor, visited.copy())

        return result

    def build_call_graph_from_function(self, function, full_name):
        """从特定函数开始构建调用图
        
        Args:
            function: 函数对象
            full_name: 函数的完整导入路径
        
        Returns:
            NetworkX有向图对象
        """
        self.call_graph = nx.DiGraph()
        self.analyzed_functions = set()
        
        # 直接从给定函数开始分析
        self._analyze_function(function, full_name)
        
        return self.call_graph
