import os
import ast
import astroid
import importlib.util
import inspect
from typing import Dict, List, Tuple, Optional, Any, Set


class PythonInterfaceAnalyzer:
    """Python接口分析器"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.interfaces = {}  # 存储接口/抽象类及其方法
        self.implementations = {}  # 存储实现类及其方法
        self.modules = {}  # 存储导入的模块
        self.call_graph = {}  # 存储调用关系

    def find_all_python_files(self) -> List[str]:
        """查找项目中所有Python文件"""
        python_files = []
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files

    def load_module(self, file_path: str) -> Optional[astroid.Module]:
        """加载Python文件为astroid模块"""
        try:
            return astroid.parse(open(file_path).read(), file_path)
        except Exception as e:
            print(f"解析文件 {file_path} 出错: {str(e)}")
            return None

    def is_interface_or_abc(self, node: astroid.ClassDef) -> bool:
        """判断一个类是否为接口/抽象基类"""
        # 检查是否有抽象方法
        has_abstract_methods = any(
            isinstance(child, astroid.FunctionDef) and
            any(decorator.name == 'abstractmethod' for decorator in child.decorators.nodes)
            for child in node.body if
            isinstance(child, astroid.FunctionDef) and hasattr(child, 'decorators') and child.decorators
        )

        # 检查是否继承自ABC
        inherits_from_abc = any(
            base.name in ('ABC', 'ABCMeta', 'Protocol') or
            (hasattr(base, 'attrname') and base.attrname in ('ABC', 'ABCMeta', 'Protocol'))
            for base in node.bases
        )

        # 如果类中所有方法都是pass或raise NotImplementedError，则视为接口
        all_methods_abstract = all(
            isinstance(child, astroid.FunctionDef) and self._is_method_abstract(child)
            for child in node.body if isinstance(child, astroid.FunctionDef) and not child.name.startswith('__')
        )

        return has_abstract_methods or inherits_from_abc or all_methods_abstract

    def _is_method_abstract(self, method: astroid.FunctionDef) -> bool:
        """检查一个方法是否是抽象的（只有pass或者抛出NotImplementedError）"""
        if not method.body:
            return True

        # 检查方法体是否只包含pass语句
        if len(method.body) == 1 and isinstance(method.body[0], astroid.Pass):
            return True

        # 检查方法体是否只包含raise NotImplementedError
        if len(method.body) == 1 and isinstance(method.body[0], astroid.Raise):
            if isinstance(method.body[0].exc, astroid.Call):
                if hasattr(method.body[0].exc.func, 'name'):
                    return method.body[0].exc.func.name == 'NotImplementedError'
                elif hasattr(method.body[0].exc.func, 'attrname'):
                    return method.body[0].exc.func.attrname == 'NotImplementedError'

        return False

    def parse_interface(self, interface_full_name: str) -> Dict:
        """解析指定的接口或抽象类"""
        module_name, class_name = interface_full_name.rsplit('.', 1)
        found = False

        python_files = self.find_all_python_files()

        # 尝试通过模块路径查找接口类
        for file_path in python_files:
            module = self.load_module(file_path)
            if module:
                self.modules[file_path] = module

                # 查找符合名称的类
                for node in module.body:
                    if isinstance(node, astroid.ClassDef) and node.name == class_name:
                        # 检查是否为接口/抽象类
                        if self.is_interface_or_abc(node):
                            found = True
                            self.interfaces[class_name] = {
                                'path': file_path,
                                'module': module_name,
                                'methods': [],
                                'line_no': node.lineno
                            }

                            # 解析接口方法
                            for child in node.body:
                                if isinstance(child, astroid.FunctionDef) and not child.name.startswith('__'):
                                    method_info = {
                                        'name': child.name,
                                        'parameters': [param.name for param in child.args.args if param.name != 'self'],
                                        'line_no': child.lineno,
                                        'col_no': child.col_offset,
                                        'end_line_no': child.end_lineno,
                                        'end_col_no': child.end_col_offset,
                                        'docstring': ast.get_docstring(child) if hasattr(child, 'doc') else None
                                    }
                                    self.interfaces[class_name]['methods'].append(method_info)

        if not found:
            print(f"未找到接口或抽象类: {interface_full_name}")

        return self.interfaces

    def find_implementations(self, interface_name: str) -> Dict:
        """查找指定接口的所有实现类"""
        if not self.interfaces:
            print("请先解析接口")
            return {}

        python_files = self.find_all_python_files()

        for file_path in python_files:
            if file_path not in self.modules:
                module = self.load_module(file_path)
                if module:
                    self.modules[file_path] = module
            else:
                module = self.modules[file_path]

            if not module:
                continue

            for node in module.body:
                if isinstance(node, astroid.ClassDef):
                    # 检查是否实现了接口
                    for base in node.bases:
                        base_name = None
                        if hasattr(base, 'name'):
                            base_name = base.name
                        elif hasattr(base, 'attrname'):
                            base_name = base.attrname

                        if base_name and base_name in self.interfaces:
                            impl_name = node.name
                            self.implementations[impl_name] = {
                                'path': file_path,
                                'interface': base_name,
                                'methods': [],
                                'line_no': node.lineno
                            }

                            # 解析实现类方法
                            for child in node.body:
                                if isinstance(child, astroid.FunctionDef):
                                    # 检查是否是接口方法的实现
                                    interface_methods = [m['name'] for m in self.interfaces[base_name]['methods']]
                                    if child.name in interface_methods:
                                        method_info = {
                                            'name': child.name,
                                            'line_no': child.lineno,
                                            'col_no': child.col_offset,
                                            'end_line_no': child.end_lineno,
                                            'end_col_no': child.end_col_offset,
                                            'body': self._extract_method_code(file_path, child),
                                            'docstring': ast.get_docstring(child) if hasattr(child, 'doc') else None
                                        }
                                        self.implementations[impl_name]['methods'].append(method_info)

        return self.implementations

    def _extract_method_code(self, file_path: str, method: astroid.FunctionDef) -> str:
        """提取方法的完整代码文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start_line = method.lineno - 1  # 减1是因为行号从1开始，但列表索引从0开始
            end_line = method.end_lineno

            # 提取方法的完整代码文本
            method_lines = lines[start_line:end_line]
            return ''.join(method_lines)
        except Exception as e:
            print(f"提取方法代码出错: {str(e)}")
            return ""
