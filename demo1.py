import time
import PyPDF2
import requests
from dotenv import load_dotenv
import os
import re
import pandas as pd
from openai import OpenAI
from openpyxl.styles import Alignment

# 加载 OPENROUTER API 密钥（需提前设置环境变量或使用 .env 文件）
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = 'openai/gpt-4o-mini'


def extract_text_from_pdf(pdf_path):
    """提取 PDF 文本内容"""
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text


def call_llm_model(prompt, text, max_retries=4):
    """调用 OPENROUTER 模型（增强重试机制）"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    # 严格格式要求的系统提示
    system_prompt = """  
    你是一个资深测试架构师，需遵循以下原则生成测试用例：
    
    【三维覆盖策略】
    1. 功能路径：确保覆盖所有显式需求+隐含业务规则
    2. 异常空间：包含以下测试模式：
       - 无效输入（类型错误/越界值/非法字符）
       - 失效容错（超时/重试/降级策略）
       - 资源极限（内存泄漏/线程死锁/存储满载）
    3. 状态迁移：验证所有可能的状态转换路径
    
    【质量强化机制】
    4. 必须包含：
       - 边界爆破：±1临界值测试
       - 时序验证：乱序操作/重复提交
       - 数据耦合：跨功能数据依赖测试
       - 环境扰动：时钟回拨/时区切换
    
    【可测性要求】
    5. 每个用例应满足：
       √ 可独立执行
       √ 包含可观测断言
       √ 前置条件明确
       √ 结果可自动化验证
    
    【风险导向设计】
    6. 按以下优先级排序：
       1) 核心业务流程
       2) 资金相关操作
       3) 安全敏感功能
       4) 高频使用场景
    
    【验证深度】
    7. 每个测试点需生成：
       - 正向验证（标准路径）
       - 反向验证（异常处理）
       - 边界验证（极值场景）
       - 突变验证（随机故障注入）
    
    【智慧注入】
    8. 应用以下测试模式：
       ▶ 基于代码覆盖的用例优化（语句/分支/条件）
       ▶ 基于风险矩阵的优先级分配
       ▶ 基于正交缺陷分类的用例设计
       ▶ 基于模糊测试的随机探索
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(
                OPENROUTER_API_ENDPOINT,
                headers=headers,
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{prompt}\n相关文本：{text}"}
                    ],
                    "temperature": 0.3  # 降低随机性
                },
                timeout=50
            )
            response.raise_for_status()
            json_data = response.json()
            print(f"\n=== API调试信息 ===")
            print("API响应状态码：", response.status_code)
            print("API响应内容：", response.text.strip())
            print(f"请求耗时：{response.elapsed.total_seconds():.2f}s")
            print(f"响应Token数：{json_data.get('usage', {}).get('total_tokens','未知')}")
            return json_data
        except requests.exceptions.Timeout:
            print(f"请求超时，重试中 ({attempt + 1}/{max_retries})...")
            time.sleep(5)
        except Exception as e:
            print(f"API请求异常（{str(e)}），重试中 ({attempt + 1}/{max_retries})...")
            time.sleep(5)
    raise Exception("API请求失败超过最大重试次数")


def generate_test_cases(pdf_path, output_excel="./生成测试用例 / TestCase_Report_v4.xlsx"):
    """主流程：解析 PDF -> 生成测试用例 -> 返回结构化数据"""
    # 1. 提取 PDF 文本
    text = extract_text_from_pdf(pdf_path)
    print("读取的pdf文本是----------------------------------\n", text)
    # 2. 提取需求（添加重试机制）
    requirements = ""
    for _ in range(3):
        try:
            requirements = call_llm_model(
                """
                请从以下文档中提取所有明确的需求，返回需求请严格按照以下格式：
                需求点一：xxxx
                需求点二：xxxx
                需求点三：xxxx
                ......
                不要有任何额外信息
                """,
                text
            )['choices'][0]['message']['content']
            break
        except Exception as e:
            print(f"需求提取失败，重试中... ({str(e)})")
            time.sleep(5)
    print("提取的需求是----------------------------------\n", requirements.strip())
    # 3. 生成测试点（添加类型检查）
    test_points = ""
    for _ in range(3):
        try:
            response = call_llm_model(
                """
                为以下需求生成测试点，每个测试点需包含：用例名称、输入条件、预期输出
                返回需求请严格按照以下格式：
                ### 测试点 x: xxxxxx
                - **用例名称**: xxxxxx
                - **输入条件**: xxxxxx
                - **预期输出**: xxxxxx
                
                不要有任何额外信息
                """,
                requirements
            )
            if 'choices' in response and len(response['choices']) > 0:
                test_points = response['choices'][0]['message']['content']
                break
        except KeyError:
            print("响应格式异常，正在重试...")
            time.sleep(5)
    print("生成的测试点是---------------------------------\n", test_points.strip())
    # 4. 生成测试用例（最终必须返回数据）
    test_cases0 = ""
    try:
        response = call_llm_model(
            """
            将测试点转换为详细的测试用例，每个测试点都需要用多个用例尽可能全面的覆盖
            生成用例时，严格按以下格式生成测试用例：
            ### 测试用例[编号]：[用例名称]
            **优先级**：[高/中/低]
            **测试步骤**：
            1. [步骤描述]
            2. [步骤描述]
            **预期结果**：[预期结果描述]
            除此之外不要有任何额外信息！
            """,
            test_points
        )
        test_cases0 = response['choices'][0]['message']['content']
    except Exception as e:
        print(f"测试用例生成失败: {str(e)}")
        return []
    print("生成的测试用例是--------------------------------\n", test_cases0.strip())
    # 5. 解析并返回结构化数据
    return parse_test_cases(test_cases0)  # 直接返回结构化数据


def parse_test_cases(text):
    """
    解析测试用例文本并返回结构化数据（修复case_num作用域问题）
    """
    # text = generate_test_cases("99.pdf", "TestCase_Report_v3.xlsx")
    # 使用更精确的正则表达式分割用例块
    case_blocks = re.findall(r'### 测试用例(\d+)：([\s\S]*?)(?=###|$)', text)
    test_cases = []
    for case_num_str, block in case_blocks:
        try:
            # 基础信息解析
            case_num = int(case_num_str)
            header_part = block.split("**测试步骤**")[0]
            # 提取优先级
            priority_match = re.search(r'\*\*优先级\*\*：\s*(\S+)', header_part)
            priority = priority_match.group(1) if priority_match else "未指定"
            # 提取用例名称（移除编号部分）
            case_title = re.sub(r'测试用例\d+：', '', header_part.split("\n")[0]).strip()
            # 提取所有步骤组
            steps_sections = re.findall(r'\*\*测试步骤\*\*：\s*([\s\S]*?)\*\*预期结果\*\*：\s*([\s\S]*?)(?=\s*\*\*|\Z)', block)
            # 处理每个步骤组
            for group_idx, (steps, expected) in enumerate(steps_sections, 1):
                # 清洗步骤数据
                cleaned_steps = '\n'.join(
                    [f"{i + 1}. {step.strip()}"
                     for i, step in enumerate(re.findall(r'\d+\.\s*(.+?)\n',
                                                         steps))]
                )
                # 生成用例编号
                case_id = f"TC{case_num}" if len(steps_sections) == 1 else f"TC{case_num}.{group_idx}"
                test_cases.append({
                    "用例编号": case_id,
                    "用例名称": case_title,
                    "步骤": cleaned_steps,
                    "预期结果": expected.strip(),
                    "优先级": priority
                })
        except Exception as e:
            print(f"解析用例{case_num_str}时出错：{str(e)}")
            continue
    return test_cases


def export_to_excel(data, filename):
    """
    增强版Excel导出函数
    """
    df = pd.DataFrame(data)
    # 创建写入器并设置格式
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name='测试用例',
            columns=["用例编号", "用例名称", "步骤", "预期结果", "优先级"]
        )
        # 获取工作表对象
        worksheet = writer.sheets['测试用例']
        # 设置列宽（特殊处理步骤列）
        column_widths = {
            "A": 12,  # 用例编号
            "B": 25,  # 用例名称
            "C": 45,  # 步骤
            "D": 35,  # 预期结果
            "E": 10  # 优先级
        }
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width
        # 设置自动换行（从第二行开始）
        for row in worksheet.iter_rows(min_row=2, max_col=5,
                                       max_row=worksheet.max_row):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')


if __name__ == "__main__":
    # 生成结构化数据
    test_case_data = generate_test_cases("./knowledge/test.pdf")
    # 检查有效数据
    if test_case_data and len(test_case_data) > 0:
        # 添加文件存在性检查
        output_file = "./output/TestCase_ai.xlsx"
        if os.path.exists(output_file):
            os.remove(output_file)
        export_to_excel(test_case_data, output_file)
        print(f"成功生成 {len(test_case_data)} 条用例")
    else:
        print("错误：未生成有效测试用例数据")
