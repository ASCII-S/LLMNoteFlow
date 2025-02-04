import os
import re

# 清理非法字符
def clean_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

# 清理无效字符，保留标题的回车符
def clean_content(content):
    cleaned_content = []
    for line in content:
        line = line.rstrip()  # 去掉行尾的空格
        # 如果这一行是空行或仅包含`---`，则跳过
        if line and line != '---':  
            cleaned_content.append(line + '\n')  # 保留回车符
    # 如果清理后的内容只有标题和空行，返回空列表
    if len(cleaned_content) <= 1:
        return None
    return cleaned_content

def split_md_by_title(md_file_path, output_dir):
    with open(md_file_path, 'r', encoding='utf-8') as md_file:
        content = md_file.readlines()

    file_content = []
    file_counter = 1  # 文件编号

    for line in content:
        # 跳过以 #include 开头的行
        if line.strip().startswith("#include"):
            continue
        if not line.strip():  # 跳过空行
            continue

        # 处理一级标题
        if line.startswith('#') and line.count('#') == 1:
            # 如果当前内容有实际内容且不为空，保存
            if file_content:
                cleaned_content = clean_content(file_content)
                if cleaned_content:  # 如果清理后的内容不为空
                    file_name = f"{file_counter:03d}.md"
                    file_path = os.path.join(output_dir, file_name)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
                    with open(file_path, 'w', encoding='utf-8') as section_file:
                        section_file.writelines(cleaned_content)
                    file_counter += 1
            # 清空当前内容，准备开始新的一段
            file_content = [f"# {line.strip('#').strip()}\n"]  # 保留标题及其换行符

        # 处理二级标题
        elif line.startswith('#') and line.count('#') == 2:
            # 保存之前的内容（如果有的话）
            if file_content:
                cleaned_content = clean_content(file_content)
                if cleaned_content:  # 如果清理后的内容不为空
                    file_name = f"{file_counter:03d}.md"
                    file_path = os.path.join(output_dir, file_name)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
                    with open(file_path, 'w', encoding='utf-8') as section_file:
                        section_file.writelines(cleaned_content)
                    file_counter += 1
            # 清空当前内容，准备开始新的一段
            file_content = [f"## {line.strip('#').strip()}\n"]  # 保留标题及其换行符
        
        # 处理三级标题
        elif line.startswith('#') and line.count('#') == 3:
            # 保存之前的内容（如果有的话）
            if file_content:
                cleaned_content = clean_content(file_content)
                if cleaned_content:  # 如果清理后的内容不为空
                    file_name = f"{file_counter:03d}.md"
                    file_path = os.path.join(output_dir, file_name)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
                    with open(file_path, 'w', encoding='utf-8') as section_file:
                        section_file.writelines(cleaned_content)
                    file_counter += 1
            # 清空当前内容，准备开始新的一段
            file_content = [f"### {line.strip('#').strip()}\n"]  # 保留标题及其换行符
        
        else:
            # 添加当前内容
            file_content.append(line)

    # 最后一部分的内容保存
    if file_content:
        cleaned_content = clean_content(file_content)
        if cleaned_content:  # 如果清理后的内容不为空
            file_name = f"{file_counter:03d}.md"
            file_path = os.path.join(output_dir, file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
            with open(file_path, 'w', encoding='utf-8') as section_file:
                section_file.writelines(cleaned_content)

def get_files_in_order(folder_path):
    # 获取文件夹内的所有文件，并按数字顺序排序
    files = [f for f in os.listdir(folder_path) if f.endswith('.md')]
    # 按文件名的数字顺序排序
    files.sort(key=lambda x: int(x.split('.')[0]))  # 通过文件名前的数字进行排序
    
    # 返回排序后的文件路径
    for file in files:
        yield os.path.join(folder_path, file)

def text_file_to_string(file_path):
    # 打开文件并读取内容
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

if __name__ == '__main__':
    input_md = './C9_docker.md'  # 输入Markdown文件路径
    output_dir = 'output'  # 输出文件夹路径
    split_md_by_title(input_md, output_dir)
