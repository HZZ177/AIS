from typing import Dict

from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os


class CodeLogicAnalyzer:
    """代码逻辑分析器"""

    def __init__(self, api_key: str = None):
        # 优先使用传入的API密钥，否则使用环境变量
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("请提供OpenAI API密钥")

        # 初始化OpenAI LLM
        self.llm = OpenAI(
            temperature=0.1,
            openai_api_key=self.api_key,
            max_tokens=1000
        )

        # 创建代码分析提示模板
        self.analysis_prompt = PromptTemplate(
            input_variables=["method_name", "method_code"],
            template="""
            请对以下Python方法进行详细分析:

            方法名: {method_name}

            源代码:
            ```python
            {method_code}
            ```

            请提供以下分析:
            1. 方法的主要功能和作用
            2. 关键的输入参数及其类型
            3. 主要的控制流分支（if-else, try-except等）
            4. 可能的边界情况和异常处理路径
            5. 返回值类型和意义
            6. 函数的副作用（如修改全局状态或外部资源）

            请以结构化的方式呈现分析结果。
            """
        )

        self.analysis_chain = LLMChain(llm=self.llm, prompt=self.analysis_prompt)

    def analyze_method(self, method_name: str, method_code: str) -> str:
        """分析方法的代码逻辑"""
        if not method_code:
            return f"无法分析{method_name}：代码为空"

        try:
            result = self.analysis_chain.run(method_name=method_name, method_code=method_code)
            return result
        except Exception as e:
            print(f"分析方法 {method_name} 时出错: {str(e)}")
            return f"分析出错: {str(e)}"

    def analyze_implementation_chain(self, call_hierarchy: Dict, implementations: Dict) -> Dict:
        """分析实现链上所有方法的逻辑"""
        analysis_results = {}

        def analyze_node_recursive(node_name, node_data):
            # 只分析实现类方法
            if node_data['type'] == 'implementation':
                class_name, method_name = node_name.split('.')

                # 从实现中找到方法代码
                method_code = None
                for impl_class, impl_data in implementations.items():
                    if impl_class == class_name:
                        for method in impl_data['methods']:
                            if method['name'] == method_name:
                                method_code = method['body']
                                break
                        break

                if method_code:
                    analysis = self.analyze_method(node_name, method_code)
                    analysis_results[node_name] = {
                        'analysis': analysis,
                        'file_path': node_data['file_path'],
                        'line_no': node_data['line_no']
                    }

            # 递归分析子节点
            for child_name, child_data in node_data.get('children', {}).items():
                if not isinstance(child_data, str) and not child_data.get('circular_ref', False):  # 避免处理循环引用
                    analyze_node_recursive(child_name, child_data)

        # 从每个接口方法开始分析
        for interface, hierarchy in call_hierarchy.items():
            analyze_node_recursive(interface, hierarchy)

        return analysis_results
