
#######modify this config#######
# API 配置
API_URL = r"http://localhost:3001/api"
API_KEY = r"VCA7TJR-XWE4F0N-P46WAEV-NHEA2SV"
# 工作区配置
workspace_name = r"NoteImprover32b"
chatmodel = r"deepseek-r1:32b"
thread_name = r"newThread"
# 项目主目录
project_folder_path = r"D:\Document\ankiCards\c++primer"
# 待处理文件位置:project_folder_path/data
source_file_name = r"第 10 章 泛型算法.md"
# 全局提示文件位置:project_folder_path/global_prompt_file_name
global_prompt_file_name = r"noteimprover_easy.md"
# 输出文件后缀
output_file_suffix = r"improved-32b.md"
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
