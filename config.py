
#######modify this config#######
# API 配置
API_URL = r"http://localhost:3001/api"
API_KEY = r"VCA7TJR-XWE4F0N-P46WAEV-NHEA2SV"
# 工作区配置
workspace_name = r"CardsGenerator"
chatmodel = r"deepseek-r1:7b"
thread_name = r"input_new"
# 项目主目录
project_folder_path = r"D:\Document\ankiCards\并行程序设计"
# 待处理文件位置:project_folder_path/data
source_file_name = r"第 4 章 c++多线程编程 11c2c4690d19804c9627ceac0e15a881.md"
# 全局提示文件位置:project_folder_path/global_prompt_file_name
global_prompt_file_name = r"cardsGenerator.md"
# 输出文件后缀
output_file_suffix = r"cards-7b.csv"
#######end:modify this config#######


#######don't modify this config#######
import os
from datetime import datetime
# 请求头
headers = {
    "Authorization": "Bearer VCA7TJR-XWE4F0N-P46WAEV-NHEA2SV"
}
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
# 检查 global_prompt_file_name 是否为内置提示词
inline_prompt_folder_name = "inline_prompt"
inline_prompt_folder_path = os.path.join(os.path.dirname(__file__), inline_prompt_folder_name)
if os.path.exists(os.path.join(inline_prompt_folder_path, global_prompt_file_name)):
    # 如果是内置提示词，使用 inline_prompt 文件夹路径
    global_prompt_file_path = os.path.join(inline_prompt_folder_path, global_prompt_file_name)
else:
    # 否则使用默认的 prompt 文件夹路径
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
output_file_name  = os.path.basename(source_file_path)#.replace(" ","")
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
