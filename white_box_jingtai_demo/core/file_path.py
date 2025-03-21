import os

'''项目目录'''
# 项目根目录，指向white_box_jingtai_demo
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

'''一级目录'''
CodeAnalyzer_path = os.path.abspath(os.path.join(project_path, 'CodeAnalyzer'))     # app根目录
log_path = os.path.abspath(os.path.join(project_path, 'logs'))
LanguageAnalyzers_path = os.path.abspath(os.path.join(project_path, 'LanguageAnalyzers'))
core_path = os.path.abspath(os.path.join(project_path, 'core'))     # core目录

'''二级目录'''


if __name__ == '__main__':
    print(project_path)
    # pass
