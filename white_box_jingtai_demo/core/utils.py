from white_box_jingtai_demo.core.file_path import output_path


def save_to_md(content, file_name="generate_testcase"):
    """保存markdown格式测试用例到md文件"""
    save_path = rf"{output_path}\{file_name}.md"
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(str(content))
