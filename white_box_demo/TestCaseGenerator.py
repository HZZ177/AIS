from typing import Dict

from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate

from white_box_demo.CodeLogicAnalyzer import CodeLogicAnalyzer


class TestCaseGenerator:
    """测试用例生成器"""

    def __init__(self, analyzer: CodeLogicAnalyzer):
        self.analyzer = analyzer

        # 创建测试用例生成提示模板
        self.test_case_prompt = PromptTemplate(
            input_variables=["method_name", "method_code", "logic_analysis"],
            template="""
            请为以下Python方法生成详细的pytest测试用例:

            方法名: {method_name}

            源代码:
            ```python
            {method_code}
            ```

            方法逻辑分析:
            {logic_analysis}

            请生成以下测试用例:
            1. 正常功能测试（覆盖主要功能路径）
            2. 边界条件测试（极限值、空值等）
            3. 异常情况测试（错误输入、异常触发等）
            4. 包含必要的mock对象和依赖设置

            使用pytest格式编写测试函数，包含测试函数、测置和断言。
            为每个测试用例添加清晰的docstring说明测试内容和预期结果。
            """
        )

        self.test_chain = LLMChain(llm=self.analyzer.llm, prompt=self.test_case_prompt)

    def generate_test_case(self, method_name: str, method_code: str, logic_analysis: str) -> str:
        """为指定方法生成测试用例"""
        if not method_code:
            return f"无法为{method_name}生成测试用例：代码为空"

        try:
            result = self.test_chain.run(
                method_name=method_name,
                method_code=method_code,
                logic_analysis=logic_analysis
            )
            return result
        except Exception as e:
            print(f"为方法 {method_name} 生成测试用例时出错: {str(e)}")
            return f"生成测试用例出错: {str(e)}"

    def generate_all_test_cases(self, call_hierarchy: Dict, implementations: Dict, analysis_results: Dict) -> Dict:
        """为调用链中的实现方法生成测试用例"""
        test_cases = {}

        def process_node_recursive(node_name, node_data):
            # 只为实现类方法生成测试
            if node_data['type'] == 'implementation':
                class_name, method_name = node_name.split('.')

                # 查找方法代码
                method_code = None
                for impl_class, impl_data in implementations.items():
                    if impl_class == class_name:
                        for method in impl_data['methods']:
                            if method['name'] == method_name:
                                method_code = method['body']
                                break
                        break

                # 获取逻辑分析结果
                logic_analysis = analysis_results.get(node_name, {}).get('analysis', '未找到逻辑分析')

                if method_code:
                    # 生成测试用例
                    test_case = self.generate_test_case(node_name, method_code, logic_analysis)
                    test_cases[node_name] = {
                        'test_code': test_case,
                        'file_path': node_data['file_path'],
                        'line_no': node_data['line_no']
                    }

            # 递归处理子节点
            for child_name, child_data in node_data.get('children', {}).items():
                if not isinstance(child_data, str) and not child_data.get('circular_ref', False):  # 避免处理循环引用
                    process_node_recursive(child_name, child_data)

        # 从每个接口方法开始处理
        for interface, hierarchy in call_hierarchy.items():
            process_node_recursive(interface, hierarchy)

        return test_cases

    def format_report(self, call_hierarchy: Dict, analysis_results: Dict, test_cases: Dict) -> str:
        """生成完整的分析和测试报告（Markdown格式）"""
        report = "# 接口分析与测试报告\n\n"

        # 1. 调用层次结构
        report += "## 1. 接口调用层次结构\n\n"
        for interface, hierarchy in call_hierarchy.items():
            report += f"### 接口方法：{interface}\n\n"
            report += self._format_hierarchy(hierarchy, 0)
            report += "\n\n"

        # 2. 代码逻辑分析
        report += "## 2. 代码逻辑分析\n\n"
        for method_name, analysis in analysis_results.items():
            report += f"### {method_name}\n\n"
            report += f"**文件路径:** {analysis['file_path']}:{analysis['line_no']}\n\n"
            report += f"{analysis['analysis']}\n\n"
            report += "---\n\n"

        # 3. 测试用例
        report += "## 3. 生成的测试用例\n\n"
        for method_name, test_case in test_cases.items():
            report += f"### {method_name} 的测试用例\n\n"
            report += f"**文件路径:** {test_case['file_path']}:{test_case['line_no']}\n\n"
            report += "```python\n"
            report += test_case['test_code']
            report += "\n```\n\n"
            report += "---\n\n"

        return report

    def _format_hierarchy(self, node: Dict, level: int) -> str:
        """格式化节点层次结构为Markdown"""
        if isinstance(node, str) or node.get('circular_ref'):
            return "  " * level + "- [循环引用]\n"

        indent = "  " * level
        result = ""

        # 当前节点信息
        node_type = node.get('type', '')
        file_info = f"{node.get('file_path', 'Unknown')}:{node.get('line_no', 'Unknown')}"
        result += f"{indent}- **{node_type}** [{file_info}]\n"

        # 子节点
        for child_name, child_data in node.get('children', {}).items():
            result += f"{indent}  - {child_name}\n"
            result += self._format_hierarchy(child_data, level + 2)

        return result
