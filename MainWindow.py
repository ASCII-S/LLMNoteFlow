import sys
import json
import logging
from PyQt6.QtWidgets import QLabel, QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QPlainTextEdit
from config_editor import ConfigEditor
from apihandler import list_workspaces
from apicallgui import APICallGUI
from config import log_file
from pathlib import Path
from feature import md_folder_to_cards
from file_utils import init_folder

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("主窗口")
        self.setGeometry(100, 100, 800, 600)

        # 初始化文件夹
        init_folder()

        # **日志配置**
        self.log_file = Path(log_file)
        self.setup_logging()

        # 主窗口的中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 主布局
        self.layout = QVBoxLayout()

        # 配置按钮
        self.config_button = QPushButton("配置")
        self.config_button.clicked.connect(self.open_config_editor)
        self.layout.addWidget(self.config_button)

        # API 测试按钮
        self.api_test_button = QPushButton("测试 API")
        self.api_test_button.clicked.connect(self.open_api_window)
        self.layout.addWidget(self.api_test_button)

        # **刷新按钮**
        self.refresh_button = QPushButton("刷新工作区")
        self.refresh_button.clicked.connect(self.load_workspaces)
        self.layout.addWidget(self.refresh_button)

         # **功能1按钮**
        self.refresh_button = QPushButton("批量询问")
        self.refresh_button.clicked.connect(md_folder_to_cards)
        self.layout.addWidget(self.refresh_button)

        # **只读文本框(显示目录结构)**
        title = QLabel("**文件需要按照以下形式放置**")
        self.layout.addWidget(title)
        self.text_widget = QPlainTextEdit()
        self.text_widget.setReadOnly(True)  # 只读模式
        self.text_widget.setPlainText(self.get_directory_structure())
        self.layout.addWidget(self.text_widget)

        # **只读文本框（显示工作区信息）**
        self.text_widget = QPlainTextEdit()
        self.text_widget.setReadOnly(True)  # 只读模式
        self.layout.addWidget(self.text_widget)

        # **日志窗口**
        self.log_widget = QPlainTextEdit()
        self.log_widget.setReadOnly(True)  # 只读模式
        self.layout.addWidget(self.log_widget)

        # 加载历史日志
        self.load_log()

        # 初次加载工作区数据
        self.load_workspaces()

        self.central_widget.setLayout(self.layout)

    def setup_logging(self):
        """配置日志记录到文件"""
        # 判断日志文件是否存在，不存在则创建
        if not self.log_file.exists():
            print("日志文件不存在，开始新日志记录...")
            self.log_file.touch()
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def append_log(self, message):
        """追加日志到日志框并写入文件"""
        self.log_widget.appendPlainText(message)  # 更新 UI 日志窗口
        logging.info(message)  # 记录到文件
        with open(self.log_file, "a") as log_file:
            log_file.write(message + "\n")  # 追加到日志文件

    def load_log(self):
        """加载日志文件到日志窗口"""
        try:
            with open(self.log_file, "r") as log_file:
                self.log_widget.setPlainText(log_file.read())
        except FileNotFoundError:
            self.log_widget.setPlainText("日志文件不存在，开始新日志记录...")

    def open_config_editor(self):
        """打开配置编辑窗口"""
        self.config_window = ConfigEditor()
        self.config_window.show()

    def open_api_window(self):
        """打开 API 调用窗口"""
        self.api_window = APICallGUI()
        self.api_window.show()

    def load_workspaces(self):
        """调用 API 并解析数据到文本框"""
        try:
            data = list_workspaces()  # 获取 API 数据
            formatted_text = self.format_workspaces(data)
            self.text_widget.setPlainText(formatted_text)
            self.append_log("工作区已刷新")
        except Exception as e:
            error_msg = f"加载工作区失败: {e}"
            self.text_widget.setPlainText(error_msg)
            self.append_log(error_msg)

    def format_workspaces(self, data):
        """格式化工作区数据为可读文本"""
        if "workspaces" not in data:
            return "无可用工作区数据"

        result = []
        for workspace in data["workspaces"]:
            workspace_name = workspace["name"]
            workspace_slug = workspace["slug"]
            result.append(f"📂 {workspace_name} ({workspace_slug})")  # 一级目录

            if "threads" in workspace and workspace["threads"]:
                for thread in workspace["threads"]:
                    thread_name = thread["name"]
                    thread_slug = thread["slug"]
                    result.append(f"    └── 📝 {thread_name} ({thread_slug})")  # 二级目录

        return "\n".join(result) if result else "未找到任何线程"

    def get_directory_structure(self):
        """返回格式化的目录结构文本"""
        return """📂 Project-Notes2Cards
├─📂 data
│  ├─📄 Notes.md
├─📂 prompt
    ├─📄 principle.md"""
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
