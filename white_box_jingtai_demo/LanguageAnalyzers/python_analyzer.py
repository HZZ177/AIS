import os
import ast
import networkx as nx
import re
from white_box_jingtai_demo.LanguageAnalyzers.base_analyzer import BaseAnalyzer
from white_box_jingtai_demo.core.logger import logger


class PythonAnalyzer(BaseAnalyzer):
    """Python代码分析器"""

    def __init__(self, project_path):
        super().__init__(project_path)
        self.decorated_functions = None
        self.related_modules = None
        self.entry_module = None

    def analyze_entry_point(self, entry_point_path):
        """分析Python入口点及其调用链"""
        try:
            # 记录入口点的模块信息
            self.entry_module = '.'.join(entry_point_path.split('.')[:2]) if '.' in entry_point_path else ''
            self.related_modules = self._get_related_modules(self.entry_module)

            # 找到入口点文件
            file_path, function_name = self.find_entry_point_file(entry_point_path)
            if not file_path:
                logger.info(f"未找到入口点: {entry_point_path}")
                return None

            # 解析文件
            module_ast = self.parse_file(file_path)
            if not module_ast:
                return None

            # 找到目标函数/方法
            target_node = self._find_function_node(module_ast, function_name)
            if not target_node:
                logger.info(f"在文件 {file_path} 中未找到函数 {function_name}")
                return None

            # 分析调用链
            self.call_graph = nx.DiGraph()
            self.call_graph.add_node(entry_point_path)
            self._analyze_calls_recursive(target_node, entry_point_path, set())

            # 收集源码
            all_source_code = self.collect_source_code()

            # 过滤只保留项目源码
            project_source_code = {}
            for func_path, source_info in all_source_code.items():
                file_path = source_info.get('file', '')
                # 检查是否是项目文件
                if ('site-packages' not in file_path and
                        'venv' not in file_path and
                        self.project_path in file_path):
                    project_source_code[func_path] = source_info

            return {
                'entry_point': entry_point_path,
                'call_graph': self.call_graph,
                'source_code': project_source_code  # 只返回项目源码
            }

        except Exception as e:
            logger.error(f"分析Python入口点时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def find_entry_point_file(self, entry_point_path):
        """根据入口点路径找到源文件"""
        parts = entry_point_path.split('.')
        function_name = parts[-1]

        # 记录原始部分，用于调试
        original_parts = parts.copy()

        # 构建可能的文件路径
        possible_paths = []

        # 处理不同情况的路径构造
        for i in range(len(parts) - 1):
            # 提取前i+1个部分作为模块路径
            module_parts = parts[:i + 1]
            remain_parts = parts[i + 1:-1]

            # 情况1: 作为Python模块文件
            file_path = os.path.join(self.project_path, *module_parts) + '.py'
            if remain_parts:
                class_name = '.'.join(remain_parts)
                possible_paths.append((file_path, function_name, class_name))
            else:
                possible_paths.append((file_path, function_name))

            # 情况2: 作为包的__init__.py
            init_path = os.path.join(self.project_path, *module_parts, '__init__.py')
            if remain_parts:
                class_name = '.'.join(remain_parts)
                possible_paths.append((init_path, function_name, class_name))
            else:
                possible_paths.append((init_path, function_name))

        # 最后尝试查找与名称直接匹配的文件（如完全匹配的类名）
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    possible_paths.append((os.path.join(root, file), function_name))

        # 尝试所有可能的路径
        for path_info in possible_paths:
            file_path = path_info[0]
            if os.path.exists(file_path):
                # 验证文件中是否包含目标函数/方法
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if f"def {function_name}" in content or f"class {function_name}" in content:
                        logger.info(f"找到匹配: {path_info} 对应 {original_parts}")
                        return path_info

        # 增加调试信息
        logger.info(f"未找到入口点文件: {entry_point_path}，尝试了 {len(possible_paths)} 个可能路径")
        return None, None

    def parse_file(self, file_path):
        """解析Python文件为AST"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 尝试查找带装饰器的函数
            function_pattern = r'@\w+(?:\.\w+)*(?:\([^)]*\))?\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\('
            matches = re.findall(function_pattern, content)
            # 存储文件中的装饰器函数名
            self.decorated_functions = set(matches) if matches else set()

            return ast.parse(content, filename=file_path)
        except UnicodeDecodeError:
            # 尝试不同编码
            for encoding in ['latin-1', 'gbk', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    return ast.parse(content, filename=file_path)
                except:
                    continue
            logger.error(f"无法解析文件 {file_path}，编码问题")
            return None
        except SyntaxError as e:
            logger.error(f"文件 {file_path} 存在语法错误: {e}")
            return None
        except Exception as e:
            logger.error(f"解析文件 {file_path} 时出错: {e}")
            return None

    @staticmethod
    def _find_function_node(module_ast, function_name, class_name=None):
        """在AST中查找函数或方法定义"""
        for node in ast.walk(module_ast):
            # 查找函数 - 同时支持普通函数和异步函数
            if isinstance(node, ast.FunctionDef) and node.name == function_name and not class_name:
                return node

            # 查找带装饰器的函数，包括异步函数
            if isinstance(node, ast.AsyncFunctionDef) and node.name == function_name and not class_name:
                return node

            # 查找类中的方法 - 同时支持普通方法和异步方法
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for child in node.body:
                    if (isinstance(child, ast.FunctionDef) or isinstance(child,
                                                                         ast.AsyncFunctionDef)) and child.name == function_name:
                        return child
        return None

    def _analyze_calls_recursive(self, node, caller_path, visited, depth=0, max_depth=10):
        """递归分析函数调用，增加深度限制"""
        if caller_path in visited or depth > max_depth:
            return

        visited.add(caller_path)
        logger.info(f"分析调用: {caller_path} [深度: {depth}]")

        # 从调用路径中提取模块前缀，用于统一处理实例方法调用
        module_prefix = '.'.join(caller_path.split('.')[:-1]) if '.' in caller_path else ''

        # 收集当前函数体中的所有调用
        found_calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                called_path = self.resolve_call_path(child, caller_path)
                if called_path:
                    # 标准化调用路径格式，处理self.方法调用
                    if called_path.startswith('self.'):
                        method_name = called_path.split('.')[-1]
                        # 尝试构建完整的模块路径
                        if module_prefix:
                            called_path = f"{module_prefix}.{method_name}"

                    # 只处理项目内部的调用
                    if self.is_project_function(called_path):
                        found_calls.append(called_path)
                        self.call_graph.add_node(called_path)
                        self.call_graph.add_edge(caller_path, called_path)

            # 处理异步函数的await表达式
            elif isinstance(child, ast.Await) and isinstance(child.value, ast.Call):
                called_path = self.resolve_call_path(child.value, caller_path)
                if called_path and self.is_project_function(called_path):
                    if called_path.startswith('self.'):
                        method_name = called_path.split('.')[-1]
                        if module_prefix:
                            called_path = f"{module_prefix}.{method_name}"

                    found_calls.append(called_path)
                    self.call_graph.add_node(called_path)
                    self.call_graph.add_edge(caller_path, called_path)

        # 递归处理找到的所有调用
        for called_path in found_calls:
            # 跳过明显的模块边界跨越
            if self._is_different_module(caller_path, called_path):
                logger.info(f"跳过跨模块调用: {caller_path} -> {called_path}")
                continue

            # 尝试找到被调用函数的定义
            file_info = self.find_entry_point_file(called_path)
            if file_info and isinstance(file_info, tuple) and len(file_info) >= 2:
                file_path, function_name = file_info[:2]
                if file_path and os.path.exists(file_path):
                    called_ast = self.parse_file(file_path)
                    if called_ast:
                        # 查找类定义或函数定义
                        called_node = None
                        if len(file_info) > 2 and file_info[2]:  # 有类名
                            class_name = file_info[2]
                            for node in ast.walk(called_ast):
                                if isinstance(node, ast.ClassDef) and node.name == class_name:
                                    for method in node.body:
                                        if (isinstance(method, ast.FunctionDef) or
                                            isinstance(method, ast.AsyncFunctionDef)) and method.name == function_name:
                                            called_node = method
                                            break
                        else:  # 直接查找顶级函数
                            for node in ast.walk(called_ast):
                                if ((isinstance(node, ast.FunctionDef) or
                                     isinstance(node, ast.AsyncFunctionDef)) and node.name == function_name):
                                    called_node = node
                                    break

                        if called_node:
                            self._analyze_calls_recursive(called_node, called_path, visited, depth + 1, max_depth)
                        else:
                            logger.info(f"在文件 {file_path} 中未找到函数 {function_name}")

    def extract_calls(self, ast_node, caller):
        """从AST节点提取调用"""
        calls = []
        for node in ast.walk(ast_node):
            if isinstance(node, ast.Call):
                call_path = self.resolve_call_path(node, caller)
                if call_path:
                    calls.append(call_path)
        return calls

    def resolve_call_path(self, call_expr, context_path):
        """解析调用表达式的完整路径"""
        if isinstance(call_expr.func, ast.Name):
            # 简单函数调用 func()
            name = call_expr.func.id
            return self._resolve_import(name, context_path)

        elif isinstance(call_expr.func, ast.Attribute):
            # 复杂属性调用的完整解析
            return self._resolve_complex_attribute_call(call_expr.func, context_path)

        return None

    @staticmethod
    def _resolve_import(name, context_path):
        """解析导入的函数名"""
        # 这里需要解析当前模块的导入语句，简化版
        module_path = '.'.join(context_path.split('.')[:-1])
        return f"{module_path}.{name}"

    @staticmethod
    def _resolve_complex_attribute_call(attr_node, context_path):
        """解析复杂的属性调用链，如 obj.method() 或 module.submodule.func()"""
        parts = []
        current = attr_node

        # 收集属性链，如 a.b.c.method
        while isinstance(current, ast.Attribute):
            parts.insert(0, current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.insert(0, current.id)

            # 处理情况1: 本地变量调用
            context_parts = context_path.split('.')
            module_path = '.'.join(context_parts[:-1])

            # 处理情况2: 导入的模块调用
            # 这里应该查找导入语句来解析模块全名，简化版本:
            if parts[0] in ["lora_node", "service", "DeviceManager", "logger"]:
                # 尝试构建可能的完整路径
                # 对于lora_node这样的局部变量，查找在context中的定义
                if parts[0] == "lora_node":
                    # 这是在函数中创建的局部变量，通过查找get_lora_node的返回值类型确定
                    return f"core.lora_node_service.LoraNodeService.{parts[1]}"
                elif parts[0] == "DeviceManager":
                    return f"core.device_manager.DeviceManager.{parts[1]}"
                elif parts[0] == "logger":
                    return f"core.logger.logger.{parts[1]}"
                else:
                    return '.'.join(parts)

        # 无法解析时，返回原始属性链
        return '.'.join(parts)

    def locate_definition(self, function_path):
        """定位函数定义的文件和位置"""
        file_path, function_name = self.find_entry_point_file(function_path)
        if not file_path or not os.path.exists(file_path):
            return None, None

        # 解析文件找到函数定义位置
        ast_tree = self.parse_file(file_path)
        if not ast_tree:
            return None, None

        # 查找函数定义 (包括异步函数)
        for node in ast.walk(ast_tree):
            if (isinstance(node, ast.FunctionDef) or isinstance(node,
                                                                ast.AsyncFunctionDef)) and node.name == function_name:
                return file_path, (node.lineno, node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 10)

        return None, None

    def extract_function_source(self, file_path, position):
        """提取函数的源代码"""
        start_line, end_line = position

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 确保行号在有效范围内
            start_line = max(1, start_line)
            end_line = min(len(lines), end_line if end_line else len(lines))

            # 向上查找装饰器
            current = start_line - 2  # 往上看一行检查装饰器
            while current >= 0 and lines[current].strip().startswith('@'):
                start_line = current + 1
                current -= 1

            source = ''.join(lines[start_line - 1:end_line])
            return {
                'source': source,
                'file': file_path,
                'start_line': start_line,
                'end_line': end_line
            }

        except Exception as e:
            logger.error(f"提取函数源码时出错: {e}")
            return None

    def is_project_function(self, node_path, file_path=None):
        """判断函数是否为项目自定义函数"""

        # 1. 过滤掉self.xxx形式的调用，它们会在_analyze_calls_recursive方法中被标准化
        if node_path.startswith('self.'):
            return True

        # 1. 如果路径包含典型的第三方库标识，直接排除
        third_party_indicators = [
            'site-packages', 'venv', 'Lib',
            'fastapi.', 'starlette.', 'typing_extensions.', 'asyncio.',
            'flask.', 'loguru.', 'gevent.', 'anyio.'
        ]

        for indicator in third_party_indicators:
            if indicator in node_path or (file_path and indicator in file_path):
                return False

        # 2. 检查是否为Python内置函数
        builtin_functions = [
            'str', 'int', 'len', 'print', 'dict', 'list', 'set',
            'tuple', 'map', 'filter', 'sorted', 'enumerate', 'zip',
            'round', 'min', 'max', 'sum', 'any', 'all', 'ord', 'chr'
        ]

        node_parts = node_path.split('.')
        if node_parts[-1] in builtin_functions:
            return False

        # 3. 检查是否为项目路径
        if file_path:
            project_prefixes = [
                os.path.join(self.project_path, "apps"),
                os.path.join(self.project_path, "core"),
                # 添加其他项目目录...
            ]

            for prefix in project_prefixes:
                if file_path.startswith(prefix):
                    return True

        # 4. 判断函数名称特征
        # 如果函数名明显是项目内特定业务术语相关，则认为是项目函数
        business_terms = [
            'lora', 'node', 'camera', 'device', 'sensor', 'report',
            'heartbeat', 'connect', 'disconnect', 'schedule'
        ]

        for term in business_terms:
            if term in node_parts[-1].lower():
                return True

        # 新增判断：确保分析范围限制在入口点的相关模块内
        if self.entry_module and '.' in node_path:
            node_module = '.'.join(node_path.split('.')[:2])
            if node_module != self.entry_module and not self._is_related_module(node_module):
                return False

        # 默认情况下保守处理，如果无法确定则收集
        return True

    def collect_source_code(self):
        """收集调用链上所有函数的源码，只包括自己项目实现的函数"""
        source_collection = {}

        logger.info("调试信息 - 尝试收集源码的节点:")
        for node in self.call_graph.nodes():
            logger.info(f"  处理节点: {node}")

            # 更智能地定位源文件
            file_info = self.find_entry_point_file(node)
            file_path = file_info[0] if file_info and isinstance(file_info, tuple) and len(file_info) >= 1 else None

            # 使用智能分类函数判断
            if not self.is_project_function(node, file_path):
                logger.info(f"    跳过非项目函数: {node}")
                continue

            if file_path and os.path.exists(file_path):
                # 解析文件查找函数定义位置
                ast_tree = self.parse_file(file_path)
                if ast_tree:
                    # 根据是否有类名判断查找方式
                    if len(file_info) > 2 and file_info[2]:  # 有类名
                        class_name = file_info[2]
                        for node_ast in ast.walk(ast_tree):
                            if isinstance(node_ast, ast.ClassDef) and node_ast.name == class_name:
                                for method in node_ast.body:
                                    if ((isinstance(method, ast.FunctionDef) or
                                         isinstance(method, ast.AsyncFunctionDef)) and
                                            method.name == file_info[-1]):
                                        position = (method.lineno, method.end_lineno if hasattr(method,
                                                                                                'end_lineno') else method.lineno + 20)
                                        logger.info(f"    找到定义: {file_path} 位置: {position}")
                                        source_collection[node] = self.extract_function_source(file_path, position)
                    else:  # 直接查找顶级函数
                        for node_ast in ast.walk(ast_tree):
                            if ((isinstance(node_ast, ast.FunctionDef) or
                                 isinstance(node_ast, ast.AsyncFunctionDef)) and
                                    node_ast.name == file_info[-1]):
                                position = (node_ast.lineno, node_ast.end_lineno if hasattr(node_ast,
                                                                                            'end_lineno') else node_ast.lineno + 20)
                                logger.info(f"    找到定义: {file_path} 位置: {position}")
                                source_collection[node] = self.extract_function_source(file_path, position)
            else:
                logger.error(f"    未找到文件: {file_path}")

        return source_collection

    @staticmethod
    def _is_different_module(caller_path, called_path):
        """判断两个调用路径是否属于不同的模块"""
        if '.' not in caller_path or '.' not in called_path:
            return False

        caller_module = '.'.join(caller_path.split('.')[:2])  # 取前两部分作为模块标识
        called_module = '.'.join(called_path.split('.')[:2])

        # 特殊处理core模块和apps模块之间的合法调用
        if caller_module == 'apps.lora_node' and called_module == 'core.lora_node_service':
            return False

        return caller_module != called_module

    @staticmethod
    def _get_related_modules(entry_module):
        """获取与入口模块相关的合法调用模块列表"""
        related = set()

        # 这里可以定义模块间的关联关系
        module_relations = {
            'apps.lora_node': ['core.lora_node_service', 'core.device_manager', 'core.util'],
            'core.lora_node_service': ['apps.four_bytes_node']
        }

        if entry_module in module_relations:
            related.update(module_relations[entry_module])

        return related

    def _is_related_module(self, module_name):
        """判断模块是否与入口模块相关"""
        return module_name in self.related_modules
