import os

'''项目目录'''
# 项目根目录，指向main_demo
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

'''一级目录'''
chromadb_db_path = os.path.abspath(os.path.join(project_path, 'chromadb_db'))     # app根目录
core_path = os.path.abspath(os.path.join(project_path, 'core'))     # core目录
log_path = os.path.abspath(os.path.join(project_path, 'logs'))
tools_path = os.path.abspath(os.path.join(project_path, 'tools'))

'''二级目录'''


if __name__ == '__main__':
    print(log_path)
    # pass
