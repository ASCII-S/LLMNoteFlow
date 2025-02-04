import requests
import base64
import sys
import os
import json
from typing import Union, List, Dict, Optional
from SeperateMd import get_files_in_order 
from SeperateMd import text_file_to_string
import shutil
import csv
import ast

# API 配置
API_URL = "http://localhost:3001/api"
API_KEY = "VCA7TJR-XWE4F0N-P46WAEV-NHEA2SV"

# 请求头
headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# **步骤 1**: 测试 API 是否连通
def test_api_connection():
    auth_url = f"{API_URL}/v1/auth"
    response = requests.get(auth_url, headers=headers)
    if response.status_code == 200:
        print("✅ 连接成功，API 认证通过！")
    else:
        print(f"❌ 连接失败，HTTP 状态码: {response.status_code}")
        print("错误信息:", response.text)
        return False
    return True

# **步骤 2**: 创建新的 workspace
def create_workspace(Workspace_name="My New Workspace"):
    workspace_url = f"{API_URL}/v1/workspace/new"

    # 新 workspace 的 JSON 数据
    workspace_data = {
        "name": Workspace_name,
        "similarityThreshold": 0.7,
        "openAiTemp": 0.7,
        "openAiHistory": 20,
        "queryRefusalResponse": "Custom refusal message",
        "chatMode": "chat",
        "topN": 4
    }

    # 发送请求创建 workspace
    response = requests.post(workspace_url, json=workspace_data, headers=headers)
       
    if response.status_code == 200:
        try:
            # 返回响应的 JSON 数据
            print(f"✅ Workspace:{Workspace_name} 创建成功！")
            return response.json()
        except ValueError:
            print("error","响应不是有效的 JSON 格式")
            return None
    else:
        return {"error": f"Workspace 创建失败，HTTP 状态码: {response.status_code}", "message": response.text}
    
# **步骤 3**: 在 `test` workspace 中创建新 Thread
def create_thread(WORKSPACE_SLUG,thread_name="Example-thread",thread_slug="example-thread"):
    thread_url = f"{API_URL}/v1/workspace/{WORKSPACE_SLUG}/thread/new"
    
    slug = WORKSPACE_SLUG+"-"+thread_slug
    # 发送的 JSON 数据
    data = {
        "userId": 1,  # 可选参数
        "name": thread_name,
        "slug": slug
    }

    response = requests.post(thread_url, json=data, headers=headers)

    if response.status_code == 200:
        print("✅ Thread 创建成功！")
        #print("响应内容:", response.json())
        print("slug:",slug)
        return response.json()
    else:
        print(f"❌ Thread 创建失败，HTTP 状态码: {response.status_code}")
        print("错误信息:", response.text)


def update_workspace(workspace_slug, key, value):
    url = f"{API_URL}/v1/workspace/{workspace_slug}/update"  # 替换成你的 API URL

    # 准备要更新的工作区设置数据
    workspace_data = {
        key: value
    }

    # 发送 PUT 请求更新工作区设置
    response = requests.post(url, json=workspace_data, headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        print(f"工作区设置更新成功:{key}={value}")
        return response.json()  # 返回 JSON 格式的响应内容
    else:
        print(f"工作区设置更新请求失败，状态码：{response.status_code}")
        return response.text  # 返回错误消息或响应内容
    
# **获取 Workspace 列表**
def list_workspaces():
    url = f"{API_URL}/v1/workspaces"  # API_URL 需要提前定义
    response = requests.get(url, headers=headers)  # headers 需要提前定义

    # 检查请求是否成功
    if response.status_code == 200:
        workspaces = response.json()
        return workspaces
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return response.text  # 返回错误信息或响应内容

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
        print("workspaces 为空或不存在")
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


# **删除指定 Workspace**
def delete_workspace(workspace_slug):
    delete_url = f"{API_URL}/v1/workspace/{workspace_slug}"

    # 发送 DELETE 请求删除 workspace
    response = requests.delete(delete_url, headers=headers)

    # 打印响应状态码
    print(f"HTTP 状态码: {response.status_code}")

    # 如果响应有内容，尝试解析 JSON
    if response.status_code == 200:
        try:
            response_json = response.json()
            print("响应内容:", response_json)
        except requests.exceptions.JSONDecodeError:
            print("响应没有返回 JSON 数据:", response.text)
    else:
        print(f"❌ 删除 Workspace 失败，HTTP 状态码: {response.status_code}")
        print("响应内容:", response.text)

# 读取并转换图片为 base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 发送聊天消息的函数
def send_message_to_workspace(workspace_slug, message, mode="chat"):
    url = f"{API_URL}/v1/workspace/{workspace_slug}/chat"
    
    # 请求体数据
    payload = {
        "message": message,
        "mode": mode,
    }

    # 发送 POST 请求
    response = requests.post(url, headers=headers, json=payload)


    # 检查响应
    if response.status_code == 200:
        print("✅ 消息发送成功！")
        return response.json()
    else:
        print(f"❌ 消息发送失败，HTTP 状态码: {response.status_code}")
        print("错误信息:", response.text)

def send_chat_to_thread(workspace_slug, thread_slug, message, mode="chat"):
    url = f"{API_URL}/v1/workspace/{workspace_slug}/thread/{thread_slug}/chat"
    
    # 准备请求的payload
    payload = {
        "message": message,
        "mode": mode
    }

    # 发送POST请求
    response = requests.post(url, json=payload, headers=headers)
    
    # 检查请求是否成功
    if response.status_code == 200:
        print("响应成功！")
        return response.json()  # 返回JSON格式的响应内容
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return response.text  # 返回错误消息或响应内容
    
def send_stream_chat_to_thread(workspace_slug, thread_slug, message="Hello World!", mode="chat"):
    url = f"{API_URL}/v1/workspace/{workspace_slug}/thread/{thread_slug}/stream-chat"

    payload = {
        "message": message,
        "mode": mode
    }
    
    # 使用 stream=True 来启用流式响应
    response = requests.post(url, headers=headers, json=payload, stream=True)
    
    if response.status_code == 200:
        #print(f"Thread stream chat 启动成功，您已提交内容为：{message}")
        result = ""
        # 逐行读取返回的流数据
        for line in response.iter_lines():
            if line:
                # 将字节解码为字符串
                decoded_line = line.decode('utf-8')
                # 检查是否以 "data: " 开头，如果是，则去掉这个前缀
                prefix = "data: "
                if decoded_line.startswith(prefix):
                    json_str = decoded_line[len(prefix):]
                else:
                    json_str = decoded_line

                try:
                    # 将 json 字符串解析为字典
                    data = json.loads(json_str)
                    # 获取 textResponse 对应的值
                    text_response = data.get("textResponse")
                    if text_response:
                        #print(text_response,end="")
                        result += text_response if text_response else ""
                except Exception as e:
                    print("JSON解析出错:", e)
        print("")
        #print("最终结果:", result)
        return result
    else:
        print(f"请求失败，状态码：{response.status_code}")
        print("错误信息:", response.text)

def create_document_folder(folder_name):
    url = f"{API_URL}/v1/document/create-folder"
    
    # 准备请求的payload
    payload = {
        "name": folder_name
    }

    # 发送POST请求
    response = requests.post(url, json=payload, headers=headers)
    
    # 检查请求是否成功
    if response.status_code == 200:
        print("文件夹创建成功！")
        return response.json()  # 返回JSON格式的响应内容
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return response.text  # 返回错误消息或响应内容
    
def move_file(file_from, file_to):
    url = f"{API_URL}/v1/document/move-files"
    
    payload = {
        "files": [
            {
                "from": file_from,
                "to": file_to
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print("文件移动成功！")
        return response.json()
    else:
        print(f"文件移动请求失败，状态码：{response.status_code}")
        return None
    
def upload_file(file_path):
    url = f"{API_URL}/v1/document/upload"
    

    # 打开要上传的文件
    with open(file_path, 'rb') as file:
        # 使用files参数上传文件
        files = {
            'file': (file.name, file, 'text/plain')
        }

        # 发送POST请求
        response = requests.post(url, headers=headers, files=files)
    
    # 检查请求是否成功
    if response.status_code == 200:
        print(f"文件:{file_path}上传成功！")
        return response.json()  # 返回JSON格式的响应内容
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return response.text  # 返回错误消息或响应内容

    
def get_documents():
    url = f"{API_URL}/v1/documents"  # API地址
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("文件列表获取成功！")
        return response.json()
    else:
        print(f"查询文件列表请求失败，状态码：{response.status_code}")
        return None

def extract_nested_value(response_json, first_key, second_key=None, third_key=None):
    """
    从 JSON 响应中提取第一层、第二层或第三层的嵌套键的值。

    :param response_json: API 返回的 JSON 数据
    :param first_key: 第一层键，例如 "documents"
    :param second_key: （可选）第二层键，例如 "name"
    :param third_key: （可选）第三层键，例如 "location"
    :return: 提取的值，若不存在则返回 None
    """
    if isinstance(response_json, dict) and response_json.get("success"):
        first_value = response_json.get(first_key)  # 获取第一层键值
        if second_key is None:
            return first_value  # 只查询第一层键

        if isinstance(first_value, list) and first_value:
            second_value = first_value[0].get(second_key)  # 查询第二层键
            if third_key is None:
                return second_value  # 只查询第二层键

            if isinstance(second_value, dict):
                return second_value.get(third_key)  # 查询第三层键

    return None  # 如果任何一层不存在，则返回 None


def upload_to_folder(local_file_path, output_dir):
    # 上传文件
    upload_file_response = upload_file(local_file_path)
    
    # 提取上传文件的 location
    #file_location = extract_nested_value(upload_file_response, "documents", "location")
    data = json.loads(json.dumps(upload_file_response))
    file_location = data["documents"][0]["location"]
    # 获取文件名
    file_name = file_location.split("/")[-1]
    
    # 源文件路径
    file_from = file_location
    
    # 目标文件路径
    file_to = output_dir + '/' + file_name
    
    # 移动文件
    if move_file(file_from, file_to):
        print(f"文件从: {file_from}\n移动到: {file_to}")
    
    return file_to

def update_workspace_embeddings(workspace_slug, add_files=None, delete_files=None):
    url = f"{API_URL}/v1/workspace/{workspace_slug}/update-embeddings"
    
    # 创建请求体
    payload = {
        "adds": add_files or [],
        "deletes": delete_files or []
    }
    
    # 发送请求
    response = requests.post(url, headers=headers, json=payload)
    
    # 检查请求是否成功
    if response.status_code == 200:
        print("工作空间更新成功！")
        return response.json()
    else:
        print(f"update_workspace_embeddings请求失败，状态码：{response.status_code}")
        return response.text  # 返回错误消息或响应内容

def test_update_workspace_embeddings():
    # 示例调用
    workspace_slug = "7btest"
    add_files = ["C9_docker2/C9_docker.md-b71ae8a6-b14d-432e-aee6-77d5ab48b8a0.json"]
    delete_files = []
    update_workspace_embeddings(workspace_slug, add_files, delete_files)

def update_document_pin_status(workspace_slug, doc_path, pin_status):
    url = f"{API_URL}/v1/workspace/{workspace_slug}/update-pin"
    
    # 创建请求体
    payload = {
        "docPath": doc_path,
        "pinStatus": pin_status
    }
    
    # 发送请求
    response = requests.post(url, headers=headers, json=payload)
    
    # 检查请求是否成功
    if response.status_code == 200:
        print("文档固定状态更新成功！")
        return response.json()
    else:
        print(f"update_document_pin_status请求失败，状态码：{response.status_code}")
        return response.text  # 返回错误消息或响应内容
    
def test_update_document_pin_status():
    # 示例调用
    workspace_slug = "7btest"
    doc_path = "C9_docker2/C9_docker.md-b71ae8a6-b14d-432e-aee6-77d5ab48b8a0.json"
    pin_status = True
    update_document_pin_status(workspace_slug, doc_path, pin_status)

def init_workspace(workspace_name = "DefaultWorkspace",chatmodel = "deepseek-r1:7b",global_prompt = "你是一个智能助手"):
    workspace_name_json = check_list_dict(json_str:=json.dumps(list_workspaces().get("workspaces")), "name", workspace_name)
    if not workspace_name_json:
        workspace_name_json = create_workspace(workspace_name).get("workspace")
        workspace_name_slug = workspace_name_json.get("slug")
        print(f"Workspace-slug:{workspace_name_slug}")
        update_workspace(workspace_name_slug, "chatProvider", "ollama")
        update_workspace(workspace_name_slug, "chatModel", chatmodel)
        update_workspace(workspace_name_slug, "agentProvider", "ollama")
        update_workspace(workspace_name_slug, "agentModel", chatmodel)
        update_workspace(workspace_name_slug, "openAiPrompt", global_prompt)
    else:
        print(f"Workspace:{workspace_name} already exists, continue...")
    return workspace_name_json
    
def init_workspace_thread(workspace_name_slug, thread_name = "DefaultThread", thread_slug = "DefaultThread"):
    workspace_name_json = check_list_dict(json_str:=json.dumps(list_workspaces().get("workspaces")), "slug", workspace_name_slug)
    thread_name_json = check_list_dict(json_str:=json.dumps(workspace_name_json.get("threads")), "name", thread_name)
    if not thread_name_json:
        thread_name_json = create_thread(workspace_name_slug, thread_name, thread_slug).get("thread")
    else:
        print(f"Thread:{thread_name} already exists, continue...")
    return thread_name_json

def init_workspace_folder(workspace_name = "DefaultWorkspace"):
    workspace_folder = workspace_name
    workspace_folder_json = check_list_dict(json_str:=json.dumps(get_documents().get("localFiles").get("items")), "name", workspace_folder)
    if not workspace_folder_json:
        workspace_folder_json = create_document_folder(workspace_folder)
    else:
        print(f"Folder:{workspace_folder} already exists, continue...")
    return

def main():
        
    #workspace_name = "AnkiCards-C++primer"
    workspace_name = "test"
    global_prompt_file_path = "./card_principle/principle.md"
    workspace_name_slug = init_workspace(workspace_name,"deepseek-r1:7b",text_file_to_string(global_prompt_file_path)).get("slug")
    chat_thread_slug = init_workspace_thread(workspace_name_slug).get("slug")

    local_folder_path = "mdsource"
    output_file_path = "output.csv"
    finished_folder = "finished"
    unfinished_folder = "unfinished"

    move_to_folder = lambda src, dst: (os.makedirs(dst) if not os.path.exists(dst) else None) or shutil.move(src, os.path.join(dst, os.path.basename(src)))

    for md_file in get_files_in_order(local_folder_path):
        try: 
            md_content = text_file_to_string(md_file)
            md_content = md_content
            print("thinking...\n")
            #chat_respond = send_message_to_workspace(workspace_name_slug, md_content).get("textResponse")
            chat_respond = send_stream_chat_to_thread(workspace_name_slug, chat_thread_slug, md_content)
            chat_think = chat_respond.split("<think>")[-1].split("</think>")[0]
            chat_answer = chat_respond.split("</think>")[-1]
            # print(chat_think)
            # print("respond:\n")
            # print(chat_respond)
            csv_content = chat_answer.split("```json")[-1].split("```")[0].strip()
            csv_content = ast.literal_eval(csv_content)
            csv_writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
            csv_writer.writerows(csv_content)
            # 按照 UTF-8 编码写入 CSV 文件
            with open(output_file_path, "a+", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
                writer.writerows(csv_content)
            move_to_folder(md_file, finished_folder)
        except Exception as e:
            print(f"Error processing file {md_file}: {e}")
            # 将出现异常的 md_file 移动到未完成的文件夹中
            move_to_folder(md_file, unfinished_folder)
            continue

if __name__ == "__main__":
    main()