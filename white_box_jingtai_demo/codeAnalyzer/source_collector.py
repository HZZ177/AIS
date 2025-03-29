import os
from LanguageAnalyzers.python_analyzer import PythonAnalyzer
from LanguageAnalyzers.java_analyzer import JavaAnalyzer
from white_box_jingtai_demo.core.logger import logger


def create_analyzer(project_path, language=None):
    """工厂函数，返回匹配的分析器"""
    if not language:
        # 自动检测语言
        if os.path.exists(os.path.join(project_path, 'pom.xml')) or \
                os.path.exists(os.path.join(project_path, 'build.gradle')):
            language = 'java'
        elif os.path.exists(os.path.join(project_path, 'requirements.txt')) or \
                os.path.exists(os.path.join(project_path, 'setup.py')):
            language = 'python'
        else:
            pass    # 预留的其他辨认逻辑

    # 返回对应的分析器
    if language == 'python':
        return PythonAnalyzer(project_path)
    elif language == 'java':
        return JavaAnalyzer(project_path)
    else:
        raise ValueError(f"不支持的语言: {language}")


def analyze_code(project_path, entry_point, language=None):
    """统一的分析入口"""

    # 初步分析源码调用链
    analyzer = create_analyzer(project_path, language)
    results = analyzer.analyze_entry_point(entry_point)

    # 处理结果，过滤第三方库或内置库等
    if results:
        call_graph = results['call_graph']
        source_code = results['source_code']
        
        # 过滤只保留项目源码
        project_source_code = {}
        for func_path, source_info in source_code.items():
            file_path = source_info.get('file', '')
            # 检查是否是项目文件
            if ('site-packages' not in file_path and 
                'venv' not in file_path and
                project_path in file_path):
                project_source_code[func_path] = source_info
        
        # 更新结果
        results['source_code'] = project_source_code
        
        # 打印统计信息
        logger.info(f"调用链分析完成: {entry_point}")
        logger.info(f"发现 {len(call_graph.nodes())} 个函数/方法")
        logger.info(f"收集了 {len(project_source_code)} 个项目源码片段")
        
        # 打印所有发现的函数名称
        logger.info("发现的函数/方法名称:")
        for node in call_graph.nodes():
            logger.info(f"  - {node}")
        
        logger.info(f"收集到的源码片段:")
        for func_name in project_source_code:
            logger.info(f"  - {func_name}")

        # 生成调用链可视化图形
        analyzer.visualize_call_graph()

        return results
    else:
        logger.error(f"分析失败: {entry_point}")
        return None


if __name__ == "__main__":
    project_path = r"C:\Users\86364\PycharmProjects\cd_findcar_automation_engine"
    entry_point = "apps.parking_camera.urls.upload_parking_picture"

    results = analyze_code(project_path, entry_point, 'python')
    logger.info(f"最终收集到的信息：\n{results}")
    logger.info(f"收集到的源码信息：{results.get('source_code', '无源码信息')}")
