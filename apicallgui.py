import sys
import json
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QComboBox, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QFormLayout, QMainWindow
from config_editor import ConfigEditor  # 引入新建的配置编辑器
import importlib  # 重新加载 config
import config
from apihandler import *  # 引入你的 API 调用函数

class APICallGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("API 调用 GUI")
        self.setGeometry(100, 100, 600, 400)

        # 可用的 API 方法
        self.api_methods = {
            "test_api_connection": [],
            "create_workspace": ["Workspace_name"],
            "create_thread": ["WORKSPACE_SLUG", "thread_name", "thread_slug"],
            "update_workspace": ["workspace_slug", "key", "value"],
            "list_workspaces": [],
            "delete_workspace": ["workspace_slug"],
            "send_message_to_workspace": ["workspace_slug", "message", "mode"],
            "send_chat_to_thread": ["workspace_slug", "thread_slug", "message", "mode"],
            "send_stream_chat_to_thread": ["workspace_slug", "thread_slug", "message", "mode"],
            "create_document_folder": ["folder_name"],
            "move_file": ["file_from", "file_to"],
            "upload_file": ["file_path"],
            "get_documents": [],
            "upload_to_folder": ["local_file_path", "output_dir"],
            "update_workspace_embeddings": ["workspace_slug", "add_files", "delete_files"],
            "update_document_pin_status": ["workspace_slug", "doc_path", "pin_status"],
        }

        # 创建 UI 组件
        self.layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        # 选择 API 方法的下拉菜单
        self.api_selector = QComboBox()
        self.api_selector.addItems(self.api_methods.keys())
        self.api_selector.currentTextChanged.connect(self.update_params)
        self.form_layout.addRow(QLabel("选择 API 方法:"), self.api_selector)

        # 动态参数输入框
        self.param_inputs = []
        self.params_layout = QFormLayout()
        self.form_layout.addRow(self.params_layout)

        # JSON 输入框
        self.json_input = QTextEdit()
        # self.json_input.setPlaceholderText('在此输入 JSON 数据 (可选)...')
        # self.form_layout.addRow(QLabel("JSON 数据:"), self.json_input)

        # 执行按钮
        self.call_button = QPushButton("调用 API")
        self.call_button.clicked.connect(self.call_api)
        self.form_layout.addRow(self.call_button)

        # 结果显示框
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.form_layout.addRow(QLabel("返回结果:"), self.result_display)

        # 添加布局
        self.layout.addLayout(self.form_layout)
        self.setLayout(self.layout)

        # 初始化默认参数输入框
        self.update_params()

    def update_params(self):
        """根据选择的 API 方法动态生成输入框"""
        # 清除旧的参数输入框
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.param_inputs.clear()  # 确保列表清空

        # 获取当前选择的 API 方法
        selected_api = self.api_selector.currentText()
        params = self.api_methods.get(selected_api, [])

        # 创建新的输入框
        for param in params:
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"输入 {param}")
            self.params_layout.addRow(QLabel(f"{param}:"), input_field)
            self.param_inputs.append(input_field)

    def call_api(self):
        """获取用户输入并调用 API"""
        selected_api = self.api_selector.currentText()
        params = [input_field.text() for input_field in self.param_inputs]

        try:
            json_content = json.loads(self.json_input.toPlainText()) if self.json_input.toPlainText() else {}
        except json.JSONDecodeError:
            self.result_display.setText("错误：无效的 JSON 格式")
            return

        # 调用apihandler中的函数
        api_function = getattr(sys.modules["apihandler"], selected_api, None)

        if api_function:
            try:
                # 调用 API 并获取结果
                result = api_function(*params, **json_content)
                self.result_display.setText(json.dumps(result, indent=4, ensure_ascii=False))
            except Exception as e:
                self.result_display.setText(f"API 调用失败: {str(e)}")
        else:
            self.result_display.setText("错误: API 方法不存在")

if __name__ == "__main__":
    app = QApplication([])
    window = APICallGUI()
    window.show()
    app.exec()
