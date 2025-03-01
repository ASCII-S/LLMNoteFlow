import sys, os
import importlib
from config import *
import config
from file_utils import load_workspace_cache, get_unique_chatmodels
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QFileDialog
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import pyqtSignal, Qt
from pathlib import Path

import ast  # 用于解析变量值

class ConfigEditor(QWidget):
    config_updated = pyqtSignal()  # 发送信号，通知主界面更新配置

    def __init__(self):
        super().__init__()

        self.setWindowTitle("编辑配置")
        self.setGeometry(150, 150, 400, 500)

        # 主布局
        self.layout = QVBoxLayout()
        self.config_fields = {}

        # 存储不可修改部分和可修改部分
        self.immutable_config_lines = []
        self.modifiable_config_lines = []

        # **加载工作区数据**
        self.workspace_data = load_workspace_cache()

        self.load_config()  # 动态加载配置

        # 保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_config)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def load_config(self):
        """重新加载 config.py,并解析注释作为分割标题"""
        importlib.reload(config)  # 重新加载配置
        self.clear_layout()  # 清空 UI

        # 解析 `config.py` 的内容
        config_content = self.extract_config_content()

        # 动态生成 UI
        for item in config_content:
            if isinstance(item, str):  
                self.layout.addWidget(QLabel(f"📌 {item}"))  # 分割标题
            elif isinstance(item, tuple):
                key, value, original_line = item

                # **API_KEY 采用隐藏显示**
                if key == "API_KEY":
                    self.layout.addWidget(QLabel(key))
                    self.api_key_input = QLineEdit(str(value))
                    self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)  # **设置密码模式**
                    self.layout.addWidget(self.api_key_input)

                    # **添加 "显示/隐藏" 按钮**
                    self.toggle_api_key_button = QPushButton("显示 API_KEY")
                    self.toggle_api_key_button.setCheckable(True)  # 允许切换
                    self.toggle_api_key_button.toggled.connect(self.toggle_api_key_visibility)
                    self.layout.addWidget(self.toggle_api_key_button)

                    self.config_fields[key] = self.api_key_input  # 绑定 QLineEdit
                    continue
                
                # **工作区相关的下拉框**
                if key in ["workspace_name", "chatmodel", "thread_name"]:
                    self.layout.addWidget(QLabel(key))
                    combo_box = QComboBox()
                    combo_box.setEditable(True)  # **可手动输入**
                    self.update_workspace_options(combo_box, key, value)
                    self.layout.addWidget(combo_box)
                    self.config_fields[key] = combo_box  # **绑定 QComboBox**
                    
                    # **如果是 `workspace_name`，需要联动 `chatmodel` 和 `thread_name`**
                    if key == "workspace_name":
                        combo_box.currentTextChanged.connect(self.update_chatmodel_and_threads)

                    continue

                if key == "project_folder_path":
                    self.layout.addWidget(QLabel(key))
                    self.project_folder_path_input = QLineEdit(str(value).lstrip('r').strip('"'))  # 去除引号
                    self.project_folder_path_input.setReadOnly(True)  # 只读，避免手动输入错误
                    self.layout.addWidget(self.project_folder_path_input)
                    self.project_folder_button = QPushButton("选择项目目录")
                    self.project_folder_button.clicked.connect(self.choose_directory)
                    self.layout.addWidget(self.project_folder_button)
                    self.config_fields[key] = self.project_folder_path_input  # 绑定输入框                    
                    # **打开目录按钮**
                    self.open_directory_button = QPushButton("在资源管理器中打开该目录")
                    self.open_directory_button.clicked.connect(lambda: self.open_directory(project_folder_path))
                    self.layout.addWidget(self.open_directory_button)

                    continue  # 跳过普通输入框
                
                if value == "comment":  # 如果是注释
                    label = QLabel(f"🔹 {key}")  # 显示注释文本
                    label.setStyleSheet("color: gray; font-style: italic;")  # 让注释文本变灰
                    self.layout.addWidget(label)
                    continue  # 跳过注释

                # 处理 `source_file_name`，使用 QComboBox 选择
                if key == "source_file_name":
                    self.layout.addWidget(QLabel(key))
                    self.source_file_selector = QComboBox()
                    self.update_file_options(self.source_file_selector, os.path.join(project_folder_path, data_folder_name))
                    self.source_file_selector.setCurrentText(str(value))  # 设定当前选项
                    self.layout.addWidget(self.source_file_selector)
                    self.config_fields[key] = self.source_file_selector  # 绑定下拉框
                    continue  # 跳过普通输入框

                # 处理 `global_prompt_file_name`，使用 QComboBox 选择
                if key == "global_prompt_file_name":
                    self.layout.addWidget(QLabel(key))
                    self.prompt_file_selector = QComboBox()
                    self.update_file_options(self.prompt_file_selector, os.path.join(project_folder_path, global_prompt_folder_name))
                    self.prompt_file_selector.setCurrentText(str(value))  # 设定当前选项
                    self.layout.addWidget(self.prompt_file_selector)
                    self.config_fields[key] = self.prompt_file_selector  # 绑定下拉框
                    continue  # 跳过普通输入框
                
                # 其他普通输入框
                self.layout.addWidget(QLabel(key))
                input_field = QLineEdit(str(value))
                self.config_fields[key] = input_field
                self.layout.addWidget(input_field)
                # 保存原始行
                self.modifiable_config_lines.append(original_line)

    def toggle_api_key_visibility(self, checked):
        """切换 API_KEY 显示/隐藏"""
        if checked:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)  # 显示明文
            self.toggle_api_key_button.setText("隐藏 API_KEY")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)  # 隐藏内容
            self.toggle_api_key_button.setText("显示 API_KEY")

    def update_workspace_options(self, combo_box, key, current_value):
        """
        **更新 QComboBox 选项**
        - `workspace_name`：所有 `workspaces`
        - `chatmodel`：当前 `workspace_name` 关联的 `chatmodel`
        - `thread_name`：当前 `workspace_name` 关联的所有 `thread_name`
        """
        combo_box.clear()
        combo_box.addItem("input_new")  # **首项为 `新建`**

        workspaces = self.workspace_data.get("workspaces", [])

        if key == "workspace_name":
            default_workspace = "DefaultWorkspace"
            combo_box.addItem(default_workspace)  # **默认项**
            # **获取所有 `workspace_name`**
            for ws in workspaces:
                combo_box.addItem(ws["name"])

        elif key == "chatmodel":
            # **获取所有 `chatmodel` 并去重**
            chatmodels = get_unique_chatmodels()

            # **确保默认 `chatmodel` 存在**
            if default_model not in chatmodels:
                chatmodels.insert(0, default_model)

            # **填充 QComboBox**
            for model in chatmodels:
                if combo_box.findText(model) == -1:  # **避免重复**
                    combo_box.addItem(model)

        elif key == "thread_name":
            default_thread = "DefaultThread"
            combo_box.addItem(default_thread)  # **默认项**
            # **查找当前 `workspace_name` 的所有 `thread_name`**
            for ws in workspaces:
                if ws["name"] == self.config_fields["workspace_name"].currentText():
                    for thread in ws.get("threads", []):
                        combo_box.addItem(thread["name"])
                    break

        combo_box.setCurrentText(current_value)  # **设定默认值**

    def update_chatmodel_and_threads(self):
        """当 `workspace_name` 变更时，仅更新 `thread_name`，`chatmodel` 保持所有可能选项"""
        selected_workspace = self.config_fields["workspace_name"].currentText()

        # **更新 `thread_name`**
        self.config_fields["thread_name"].clear()
        #self.config_fields["thread_name"].addItem("新建线程")  # **始终包含 `新建`**

        for ws in self.workspace_data.get("workspaces", []):
            if ws["name"] == selected_workspace:
                # **填充 `thread_name`**
                for thread in ws.get("threads", []):
                    self.config_fields["thread_name"].addItem(thread["name"])
                self.config_fields["thread_name"].addItem("input_new")  # **始终包含 `新建`**


                return  # **匹配到 workspace，退出**
        
        # **如果是 workspace是`新建`，重置 `thread_name`**
        self.config_fields["thread_name"].clear()
        self.config_fields["thread_name"].addItem("input_new")


    def choose_directory(self):
        """让用户选择 `project_folder_path`"""
        folder = QFileDialog.getExistingDirectory(self, "选择项目主目录", project_folder_path)
        if folder:
            self.project_folder_path_input.setText(folder)  # 更新 UI
            self.config_fields["project_folder_path"] = self.project_folder_path_input  # 更新绑定
            # **更新 "打开目录" 按钮的事件，使其打开新选择的路径**
            self.open_directory_button.clicked.disconnect()  # 先断开旧的连接
            self.open_directory_button.clicked.connect(lambda: self.open_directory(folder))

            # **更新 `source_file_name` 和 `global_prompt_file_name` 的下拉菜单**
            self.update_file_options(self.source_file_selector, os.path.join(folder, data_folder_name))
            self.update_file_options(self.prompt_file_selector, os.path.join(folder, global_prompt_folder_name))

    # 处理打开项目目录的函数
    def open_directory(self, path):
        """打开指定的目录"""
        # 自动识别并处理路径
        path = os.path.normpath(path)  # 标准化路径
        
        # 检查目录是否存在
        if os.path.isdir(path):
            os.startfile(path)  # Windows打开目录
        else:
            print(f"目录不存在: {path}")


    def update_file_options(self, combo_box, folder_path, file_extension=".md"):
        """
        通用文件选择方法，自动列出指定文件夹下的文件，并更新 QComboBox 选项

        :param combo_box: 需要更新的 QComboBox 组件
        :param folder_path: 要搜索的文件夹路径
        :param file_extension: 需要筛选的文件后缀，如 `.md`
        """
        combo_box.clear()  # 清空旧选项
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            files = [f for f in os.listdir(folder_path) if f.endswith(file_extension)]
            if files:
                combo_box.addItems(files)  # 添加文件列表
            else:
                combo_box.addItem("（没有可用文件）")
        else:
            combo_box.addItem("（未找到文件夹）")

    def extract_config_content(self):
        """解析 `config.py` 文件，动态区分可修改和不可修改部分"""
        config_content = []  # 存储解析后的内容
        self.immutable_config_lines = []  # 存储不可修改部分的原始行
        with open("config.py", "r", encoding="utf-8") as f:
            lines = f.readlines()

        modify_start = False
        for line in lines:
            line = line.rstrip()

            # 提取可修改部分
            if "#######modify this config#######" in line:
                modify_start = True
                continue  # 跳过分割行
            if "#######end:modify this config#######" in line:
                modify_start = False
                continue  # 跳过分割行

            # 先读取可修改部分
            if modify_start:
                if line.startswith("# "):  # 解析注释
                    comment = line[2:].strip()  # 移除 `# ` 并保存注释
                    config_content.append((comment, "comment", line))  # 保存注释
                    self.modifiable_config_lines.append((comment, "comment", line))  # 保存注释信息
                elif "=" in line:
                    try:
                        key_value = line.split("=", 1)
                        if len(key_value) == 2:
                            key = key_value[0].strip()
                            value = key_value[1].strip()
                            value = ast.literal_eval(value)  # 解析值
                            if key == "project_folder_path":  # 如果是路径相关的配置
                                value = Path(line.split("=")[1].strip())  # 转换成 Path 对象
                            #print(f"key: {key}, value: {value}")
                            config_content.append((key, value, line))  # 存储键值对和原始行
                            self.modifiable_config_lines.append((key, value, line))  # 保存键值对
                    except Exception as e:
                        print(f"解析错误: {e}")

            # 然后读取不可修改部分
            else:
                self.immutable_config_lines.append(line)  # 保存不可修改部分

        return config_content

    def save_config(self):
        """保存用户修改的配置到 `config.py`"""
        for i, item in enumerate(self.modifiable_config_lines):
            if isinstance(item, tuple):
                key, value, original_line = item

                # 处理 `project_folder_path`
                if key == "project_folder_path":
                    new_value = self.project_folder_path_input.text()
                # 处理 `source_file_name` 和 `global_prompt_file_name`（QComboBox）
                elif key == "source_file_name":
                    new_value = self.source_file_selector.currentText()  # QComboBox 使用 currentText()
                elif key == "global_prompt_file_name":
                    new_value = self.prompt_file_selector.currentText()  # QComboBox 使用 currentText()
                # 其他普通输入框（QLineEdit）
                elif key in self.config_fields:
                    widget = self.config_fields[key]
                    if isinstance(widget, QLineEdit):  
                        new_value = widget.text()
                    elif isinstance(widget, QComboBox):  
                        new_value = widget.currentText()
                    else:
                        new_value = str(widget)  # 兜底情况，防止未识别的组件报错
                else:
                    continue  # 避免未识别的 key 影响执行

                self.modifiable_config_lines[i] = (key, new_value, original_line)

        # 写入文件
        with open("config.py", "w", encoding="utf-8") as f:
            # 先写入可修改部分
            f.write("\n#######modify this config#######\n")
            for item in self.modifiable_config_lines:
                if isinstance(item, tuple):
                    key, value, original_line = item
                    if value == "comment":  # 判断是否是注释
                        f.write(f"# {key}\n")  # 输出注释
                        continue
                    f.write(f'{key} = r"{value}"\n')

            f.write("#######end:modify this config#######")

            # 然后写入不可修改部分
            for line in self.immutable_config_lines:
                f.write(line + "\n")

        self.config_updated.emit()  # 发送信号，通知主界面更新配置
        self.close()  # 关闭窗口

    def clear_layout(self):
        """清空 UI 布局"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigEditor()
    window.show()
    sys.exit(app.exec())
