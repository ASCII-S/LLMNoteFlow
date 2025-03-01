from typing import Union, List, Dict, Optional
import sys
import csv
import os
import json
from file_utils import get_files_in_order, text_file_to_string, move_to_folder, split_md_by_title
from apihandler import send_stream_chat_to_thread, create_workspace, list_workspaces, update_workspace, create_thread, get_documents, create_document_folder, send_chat_to_thread, delete_workspace

import importlib
import config

global source_file_path, des_folder_path, global_prompt_file_path, workspace_name, chatmodel, thread_name, output_file_name, output_file_path, finished_folder, unfinished_folder, init_updates, source_file_name, output_folder_path

def reload_config():
    # 以全局变量的形式重新配置 config 模块
    global source_file_path, des_folder_path, global_prompt_file_path, workspace_name, chatmodel, thread_name, output_file_name, output_file_path, finished_folder, unfinished_folder, init_updates, source_file_name, output_folder_path
    importlib.reload(config)
    workspace_name = config.workspace_name
    chatmodel = config.chatmodel
    thread_name = config.thread_name
    project_folder_path = config.project_folder_path
    source_file_name = config.source_file_name
    global_prompt_file_name = config.global_prompt_file_name
    output_file_suffix = config.output_file_suffix
    #######don't modify this config#######
    # 默认模型
    default_model = "deepseek-r1:14b"
    # 使用本地文件夹名称构建路径
    #data
    data_folder_name = "data"
    data_folder = os.path.join(project_folder_path, data_folder_name)
    source_file_path = os.path.join(data_folder, source_file_name)
    #prompt
    global_prompt_folder_name = "prompt"
    global_prompt_folder_path = os.path.join(project_folder_path, global_prompt_folder_name)
    global_prompt_file_path = os.path.join(global_prompt_folder_path, global_prompt_file_name)
    #processed
    processed_folder_name = "processed"  # 存放所有处理后的数据
    processed_folder = os.path.join(project_folder_path, processed_folder_name)
    ##des_folder
    des_folder_path = os.path.join(processed_folder, os.path.basename(source_file_path).split(".")[0])
    ###finished_folder
    finished_folder_name = "finished"
    finished_folder = os.path.join(des_folder_path, finished_folder_name)
    ###unfinished_folder
    unfinished_folder_name = "unfinished"
    unfinished_folder = os.path.join(des_folder_path, unfinished_folder_name)
    #output
    output_folder_name = "output"
    output_folder_path = os.path.join(project_folder_path, output_folder_name)
    output_file_name  = os.path.basename(source_file_path).split(".")[0]
    output_file_path = os.path.join(output_folder_path, f"{output_file_name}_{output_file_suffix}")
    #log
    log_folder_name = "log"
    log_folder_path = os.path.join(project_folder_path, log_folder_name)
    WORKSPACE_CACHE_FILE = os.path.join(log_folder_path, "workspace_cache.json")  # 记录历史输入的 JSON 文件
    last_update_file = os.path.join(log_folder_path, "last_update.txt")  # 记录上次 API 请求时间

    #update workspace
    init_updates = {
        "name": workspace_name,
        "chatProvider": "ollama",
        "chatModel": chatmodel,
        "chatMode": "chat",
        "agentProvider": "ollama",
        "agentModel": chatmodel
    }
    #######end:don't modify this config#######


# **检查 JSON 字符串中是否存在指定的键值对**
def check_list_dict(json_str: str, key: str, value: Union[str, int, None] = None) -> Union[bool, List[Union[str, int]], Dict, None]:
    """
    检查 JSON 格式的字符串中是否存在指定的键值对，或者列出该键下的所有值，或返回匹配的整个字典。

    :param json_str: JSON 格式的字符串
    :param key: 需要查找的键 (如 "name"、"id" 等)
    :param value: 需要匹配的值（可选）
    :return:
        - 如果提供 `value`，返回匹配的整个字典（若找到）或 `None`（未找到）。
        - 如果未提供 `value`，返回该 `key` 下的所有值列表。
        - 如果 `workspaces` 为空或 `key` 不存在，返回 `False`（查询 `key=value`）或 `[]`（查询所有值）。
    """
    try:
        data = json.loads(json_str)  # 解析 JSON 字符串
    except json.JSONDecodeError:
        print("JSON 格式错误")
        return False

    workspaces = data

    if not workspaces:
        print("json 为空或不存在:\n", workspaces)
        return False if value is not None else []
    
    # 检查 key 是否存在于任意 workspace
    if not any(key in workspace for workspace in workspaces):
        print(f"没有该键: {key}")
        return False if value is not None else []

    if value is not None:
        # 查询 key-value 是否匹配并返回整个字典
        for workspace in workspaces:
            if workspace.get(key) == value:
                return workspace  # 返回整个字典
        print(f"未找到 {key}={value} 对应的工作空间")
        return None
    else:
        # 获取所有 key 对应的值
        return [workspace[key] for workspace in workspaces if key in workspace]


# 新建并且初始化工作空间
def init_workspace(workspace_name = "DefaultWorkspace",chatmodel = "deepseek-r1:7b",global_prompt = "你是一个智能助手"):
    workspace_name_json = check_list_dict(json_str:=json.dumps(list_workspaces().get("workspaces")), "name", workspace_name)
    if workspace_name_json:
        workspace_name_slug = workspace_name_json.get("slug")
        print(f"Workspace:{workspace_name} already exists, recreat it...")
        delete_workspace(workspace_name_slug)
        workspace_name_json = None
    if not workspace_name_json:
        workspace_name_json = create_workspace(workspace_name).get("workspace")
        workspace_name_slug = workspace_name_json.get("slug")
        print(f"Workspace-slug:{workspace_name_slug}")
        update_workspace(workspace_name_slug, init_updates)
        return workspace_name_json
    return workspace_name_json

# 新建并且初始化工作空间的thread  
def init_workspace_thread(workspace_name_slug, thread_name = "DefaultThread"):
    workspace_name_json = check_list_dict(json_str:=json.dumps(list_workspaces().get("workspaces")), "slug", workspace_name_slug)
    thread_name_json = check_list_dict(json_str:=json.dumps(workspace_name_json.get("threads")), "name", thread_name)
    if not thread_name_json:
        thread_name_json = create_thread(workspace_name_slug, thread_name).get("thread")
    else:
        print(f"Thread:{thread_name} already exists, continue...")
    return thread_name_json

# 初始化工作空间对应的文件夹
def init_workspace_folder(workspace_name = "DefaultWorkspace"):
    workspace_folder = workspace_name
    workspace_folder_json = check_list_dict(json_str:=json.dumps(get_documents().get("localFiles").get("items")), "name", workspace_folder)
    if not workspace_folder_json:
        workspace_folder_json = create_document_folder(workspace_folder)
    else:
        print(f"Folder:{workspace_folder} already exists, continue...")
    return

def md_folder_to_cards(progress_callback=None):
    reload_config()
    # 切割笔记文件
    split_md_by_title(source_file_path, des_folder_path, ignore_title=True)
    global_prompt = text_file_to_string(global_prompt_file_path)
    workspace_name_slug = init_workspace(workspace_name,chatmodel,global_prompt).get("slug")
    chat_thread_slug = init_workspace_thread(workspace_name_slug,thread_name).get("slug")
    update_workspace(workspace_name_slug, init_updates)
    update_workspace(workspace_name_slug, {"openAiprompt": global_prompt})
    #move_to_folder = lambda src, dst: (os.makedirs(dst) if not os.path.exists(dst) else None) or shutil.move(src, os.path.join(dst, os.path.basename(src)))
    
    # 如果已经存在结果文件output_file_path则删除
    if os.path.exists(output_file_path):
        os.remove(output_file_path)
        print(f"Deleted the existing output file: {output_file_path}")
    # 获取文件列表并计算总数
    files = list(get_files_in_order(des_folder_path))
    total_files = len(files)
    for index, md_file in enumerate(files, start=1):
        try: 
            md_content = text_file_to_string(md_file)
            #md_content = global_prompt + "\n以下是需要你处理的笔记内容:\n" + md_content
            print("\nthinking...")

            #chat_respond = send_message_to_workspace(workspace_name_slug, md_content).get("textResponse")
            #chat_respond = send_chat_to_thread(workspace_name_slug, chat_thread_slug, md_content).get("textResponse")
            chat_respond = send_stream_chat_to_thread(workspace_name_slug, chat_thread_slug, md_content)
            chat_think = chat_respond.split("<think>")[-1].split("</think>")[0]
            chat_answer = chat_respond.split("</think>")[-1]

            # print(chat_think)
            # print("respond:\n")
            print("chat_respond:\n",chat_respond,"end chat_respond\n")
            # 从回答中提取 JSON 内容
            try:
                # 提取并解析 JSON 部分
                csv_content = chat_answer.split("```json")[-1].split("```")[0].strip()
                json_data = json.loads(csv_content)  # 使用 json.loads 代替 ast.literal_eval
            except Exception as e:
                print("Answer is not a valid json format")
                print(csv_content)
                continue

            # 打印解析后的 JSON 数据（调试用）
            print("Parsed JSON Data:", json_data)

            # 确保数据格式为字典，并从中获取 '回答' 列表
            if isinstance(json_data, dict) and '回答' in json_data:
                answer_data = json_data['回答']  # 获取 '回答' 列表
                if isinstance(answer_data, list):  # 确保是列表
                    # 写入 CSV 数据
                    csv_writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
                    for entry in answer_data:
                        # 假设每个 entry 是一个字典，包含 '问题' 和 '答案'
                        csv_writer.writerow([entry['问题'], entry['答案']])

                    # 按 UTF-8 编码写入 CSV 文件
                    with open(output_file_path, "a+", newline="", encoding="utf-8") as csvfile:
                        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
                        for entry in answer_data:
                            writer.writerow([entry['问题'], entry['答案']])
                else:
                    print("'回答' is not a list.")
            else:
                print("Parsed JSON data does not contain '回答' or is not a dictionary.")
            
            move_to_folder(md_file, finished_folder)
            
            # 触发进度更新（每处理一个文件更新一次）
            if progress_callback:
                progress_callback(index, total_files)
        except Exception as e:
            print(f"Error processing file {md_file}: {e}")
            sys.exit(1)
            # 将出现异常的 md_file 移动到未完成的文件夹中
            move_to_folder(md_file, unfinished_folder)
            continue

def md_folder_note_improver(progress_callback=None):
    reload_config()
    # 切割笔记文件
    split_md_by_title(source_file_path, des_folder_path, ignore_title=False)
    global_prompt = text_file_to_string(global_prompt_file_path)
    workspace_name_slug = init_workspace(workspace_name,chatmodel,global_prompt).get("slug")
    chat_thread_slug = init_workspace_thread(workspace_name_slug,thread_name).get("slug")
    update_workspace(workspace_name_slug, init_updates)
    update_workspace(workspace_name_slug, {"openAiPrompt": global_prompt})
    #move_to_folder = lambda src, dst: (os.makedirs(dst) if not os.path.exists(dst) else None) or shutil.move(src, os.path.join(dst, os.path.basename(src)))
    
    # 如果已经存在结果文件output_file_path则删除
    if os.path.exists(output_file_path):
        os.remove(output_file_path)
        print(f"Deleted the existing output file: {output_file_path}")
    # 获取文件列表并计算总数
    files = list(get_files_in_order(des_folder_path))
    total_files = len(files)
    for index, md_file in enumerate(files, start=1):
        try: 
            md_content = text_file_to_string(md_file)
            #md_content = global_prompt + "\n以下是需要你处理的笔记内容:\n" + md_content
        
            print("md_content:\n",md_content,"end md_content\n")
            print("\nthinking...")
            
            # 如果md_content中除去空行只有一行,并且他是以#或##开头的,则直接将他添加到new_md_file中
            if len(md_content.split("\n")) <= 2 and (md_content.startswith("#") or md_content.startswith("##")) and not md_content.startswith("###"):
                save_to_new_md_file(md_file, md_content)
                move_to_folder(md_file, finished_folder)
                continue

            #chat_respond = send_message_to_workspace(workspace_name_slug, md_content).get("textResponse")
            chat_respond = send_stream_chat_to_thread(workspace_name_slug, chat_thread_slug, md_content)
            chat_think = chat_respond.split("<think>")[-1].split("</think>")[0]
            chat_answer = chat_respond.split("</think>")[-1]

            # print(chat_think)
            # print("respond:\n")
            #print("chat_respond:\n",chat_respond,"end chat_respond\n")
            # 从回答中提取 JSON 内容
            
            # 将chat_answer添加到新的md文件中
            save_to_new_md_file(md_file, chat_answer)

            move_to_folder(md_file, finished_folder)

            # 触发进度更新（每处理一个文件更新一次）
            if progress_callback:
                progress_callback(index, total_files)
        except Exception as e:
            print(f"Error processing file {md_file}: {e}")
            sys.exit(1)
            # 将出现异常的 md_file 移动到未完成的文件夹中
            move_to_folder(md_file, unfinished_folder)
            continue

def save_to_new_md_file(md_file, chat_answer):
    """
    将chat_answer保存为新的md文件。
    
    参数:
        md_file (str): 原始md文件路径。
        chat_answer (str): 改进后的md内容。
    """
    try:        
        # 构造新的文件路径，可以将其保存到指定的文件夹
        new_md_file_path = output_file_path
        
        # 写入改进后的内容
        with open(new_md_file_path, 'a+', encoding='utf-8') as f:
            f.write(chat_answer)
        print(f"processed file: {os.path.basename(md_file)}")
        #print(f"Successfully saved the improved md file: {new_md_file_path}")
    except Exception as e:
        print(f"Error saving the new md file for {md_file}: {e}")


if __name__ == "__main__":
    #md_folder_to_cards()
    md_folder_note_improver()