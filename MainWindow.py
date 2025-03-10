import sys
import json
from PyQt6.QtGui import QFont, QColor, QBrush
from PyQt6.QtWidgets import QLabel, QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QMessageBox
from PyQt6.QtWidgets import (
    QDialog,                # 对话框
    QFormLayout,            # 表单布局
    QLineEdit,              # 文本输入框
    QComboBox,              # 下拉选择框
    QDoubleSpinBox,         # 双精度数值调节框
    QDialogButtonBox,       # 对话框按钮组
    QHBoxLayout,            # 水平布局容器（新增）
    QProgressBar            # 进度条（新增）
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtCore import Qt  # 导入 Qt 枚举
from PyQt6.QtWidgets import QMenu  # 导入菜单类
from PyQt6.QtWidgets import QInputDialog  # 导入输入对话框
from config_editor import ConfigEditor
from apihandler import list_workspaces
import apihandler
from apicallgui import APICallGUI
from config import WORKSPACE_CACHE_FILE
from pathlib import Path
from feature import md_folder_to_cards, md_folder_note_improver
from file_utils import init_folder

# 功能配置列表（名称-处理函数映射）
functions_config = [
    {
        "name": "批量生成卡片", 
        "handler": md_folder_to_cards,
        "description": "将 Markdown 笔记批量转换为 Anki 卡片"
    },
    {
        "name": "改进笔记内容", 
        "handler": md_folder_note_improver,
        "description": "优化 Markdown 笔记的结构与内容"
    }
]

# 节点类型常量
NODE_TYPE_WORKSPACE = "workspace"
NODE_TYPE_THREAD = "thread"
# 定义数据角色常量
NODE_TYPE_ROLE = Qt.ItemDataRole.UserRole
SLUG_ROLE = Qt.ItemDataRole.UserRole + 1  # 新增角色用于存储 slug

class WorkspaceLoader(QThread):
    finished = pyqtSignal(dict)

    def run(self):
        try:
            data = apihandler.list_workspaces()
            self.finished.emit(data)
        except Exception as e:
            self.finished.emit({"error": str(e)})

class WorkerThread(QThread):
    # 新增进度信号：current_index（当前处理序号）, total_files（总文件数）
    progress_updated = pyqtSignal(int, int)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, task_function):
        super().__init__()
        self.task_function = task_function

    def run(self):
        try:
            # 执行任务并传递进度回调
            self.task_function(progress_callback=self._update_progress)
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _update_progress(self, current_index, total_files):
        """内部方法，触发进度信号"""
        self.progress_updated.emit(current_index, total_files)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("主窗口")
        self.setGeometry(100, 100, 800, 600)


        # 初始化文件夹
        init_folder()

        # 主窗口的中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 主布局
        self.layout = QVBoxLayout()

        # API 测试按钮
        self.api_test_button = QPushButton("测试 API")
        self.api_test_button.clicked.connect(self.open_api_window)
        self.layout.addWidget(self.api_test_button)

        # **工作区树形结构**
        self.workspace_cache = None
        self.update_workspace_cache()
        self.workspace_tree = QTreeWidget()
        self.workspace_tree.setHeaderLabels(["📁工作区 / 📝线程"])
        self.layout.addWidget(self.workspace_tree)
        self.workspace_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.workspace_tree.customContextMenuRequested.connect(self.show_context_menu)
        # 仅当节点展开时加载子节点
        self.workspace_tree.itemExpanded.connect(self.lazy_load_children)
        # 添加加载状态标签
        self.loading_label = QLabel("🔄 正在加载工作区数据...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setVisible(False)
        # 将标签插入到树形控件之后的位置
        layout_index = self.layout.indexOf(self.workspace_tree) + 1
        self.layout.insertWidget(layout_index, self.loading_label)

        # 配置按钮# 连接配置更新信号
        self.config_button = QPushButton("配置批量处理")
        self.config_button.clicked.connect(self.open_config_editor)
        self.layout.addWidget(self.config_button)

        # ======================== 功能选择区域 ========================
        # 创建水平布局容器
        self.function_layout = QHBoxLayout()

        # 左侧功能下拉菜单
        self.function_selector = QComboBox()
        for func in functions_config:
            # 添加项并存储处理函数到 UserRole 数据
            self.function_selector.addItem(func["name"], userData=func["handler"])
            # 可选：设置 ToolTip 提示
            self.function_selector.setItemData(
                self.function_selector.count()-1, 
                func["description"], 
                Qt.ItemDataRole.ToolTipRole
            )
        self.function_layout.addWidget(self.function_selector)

        # 右侧运行按钮
        self.run_button = QPushButton("运行")
        self.run_button.setShortcut("Return")  # 回车键触发
        self.run_button.setFixedWidth(100)  # 设定合适宽度
        self.run_button.clicked.connect(self._execute_selected_function)  # 连接信号
        self.function_layout.addWidget(self.run_button)
        # 将功能布局添加到主布局
        self.layout.addLayout(self.function_layout)
        # 停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.setFixedWidth(100)  # 设定合适宽度
        self.stop_button.clicked.connect(self._stop_task)  # 连接信号
        self.function_layout.addWidget(self.stop_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)  # 百分比模式
        self.layout.addWidget(self.progress_bar)
        # =============================================================

        # 初次加载工作区数据
        self.load_workspaces()

        
        self.central_widget.setLayout(self.layout)

    def open_config_editor(self):
        """打开配置编辑窗口"""
        self.config_window = ConfigEditor()
        self.config_window.show()

    def open_api_window(self):
        """打开 API 调用窗口"""
        self.api_window = APICallGUI()
        self.api_window.show()

    def load_workspaces(self):
        self.workspace_tree.clear()
        self.loading_label.setVisible(True)
        self.loader = WorkspaceLoader()
        self.loader.finished.connect(self.on_workspace_loaded)
        self.loader.start()

    def on_workspace_loaded(self, data):
        """隐藏加载状态并填充数据"""
        self.loading_label.setVisible(False)
        if "error" in data:
            QMessageBox.critical(self, "错误", data["error"])
            return
        # 更新UI的代码移到这里
        self.populate_tree(data.get("workspaces", []))

    def populate_tree(self, workspaces):
        self.workspace_tree.setUniformRowHeights(True)  # 提升渲染性能
        self.workspace_tree.setSortingEnabled(True)     # 启用自动排序
        
        # 批量创建节点
        items = []
        for ws in workspaces:
            # 创建工作区节点
            item = QTreeWidgetItem([f"📁 {ws['name']} ({ws.get('chatModel', '')})"])
            item.setData(0, NODE_TYPE_ROLE, NODE_TYPE_WORKSPACE)  # 设置节点类型!!!
            item.setData(0, SLUG_ROLE, ws["slug"])
            item.setFont(0, QFont("Arial", 12, QFont.Weight.Bold))
            item.setForeground(0, QBrush(QColor("#0057b8")))
            
            # 预添加空的thread子节点占位
            placeholder = QTreeWidgetItem()
            placeholder.setText(0, "加载中...")
            item.addChild(placeholder)
            
            items.append(item)
        
        self.workspace_tree.addTopLevelItems(items)
        self.workspace_tree.collapseAll()

    def lazy_load_children(self, item):
        if item.childCount() == 1 and item.child(0).text(0) == "加载中...":
            # 移除占位节点
            item.removeChild(item.child(0))
            
            # 同步加载线程数据（实际开发建议用异步）
            workspace_slug = item.data(0, SLUG_ROLE)
            workspace_data = next(
                (ws for ws in self.workspace_cache.get("workspaces", []) 
                if ws["slug"] == workspace_slug), None
            )
            
            if workspace_data:
                for thread in workspace_data.get("threads", []):
                    thread_item = QTreeWidgetItem()
                    thread_item.setText(0, f"📝 {thread['name']}")
                    thread_item.setData(0, NODE_TYPE_ROLE, NODE_TYPE_THREAD)  # 关键!!!
                    thread_item.setData(0, SLUG_ROLE, thread["slug"])
                    thread_item.setFont(0, QFont("Arial", 10))
                    thread_item.setForeground(0, QBrush(QColor("#333333")))
                    item.addChild(thread_item)

    def update_workspace_cache(self):
        """
        **调用 API 获取最新的工作区数据**
        - **更新 `workspace_cache.json`**
        - **更新 UI**
        """
        if self.workspace_cache:  # 使用内存缓存
            return self.workspace_cache
        try:
            data = list_workspaces()
            if isinstance(data, dict) and "workspaces" in data:
                with open(WORKSPACE_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            else:
                raise ValueError("无效的 API 响应")
        except Exception as e:
            error_msg = f"加载工作区失败: {e}"

        self.workspace_cache = data  # 缓存结果
        return data
    
    def show_context_menu(self, pos):
        selected_item = self.workspace_tree.currentItem()
        if not selected_item:
            return

        menu = QMenu(self)
        item_type = selected_item.data(0, NODE_TYPE_ROLE) 

        # 根据类型生成菜单项
        if item_type == NODE_TYPE_WORKSPACE:
            self._add_workspace_menu_actions(menu, selected_item)
        elif item_type == NODE_TYPE_THREAD:
            self._add_thread_menu_actions(menu, selected_item)
        else:
            return  # 未知类型不显示菜单

        # 公共操作（如刷新）
        menu.addSeparator()
        refresh_action = menu.addAction("重新加载工作区")
        refresh_action.triggered.connect(self.load_workspaces)

        menu.exec(self.workspace_tree.viewport().mapToGlobal(pos))

    def _add_workspace_menu_actions(self, menu, item):
        """为工作区节点添加操作"""
        create_workspace_action = menu.addAction("创建工作区")
        create_workspace_action.triggered.connect(lambda: self.create_workspace(item))
        create_thread_action = menu.addAction("创建线程")
        create_thread_action.triggered.connect(lambda: self.create_thread(item))
        delete_action = menu.addAction("删除工作区")
        delete_action.triggered.connect(lambda: self.delete_workspace(item))

        edit_action = menu.addAction("编辑设置")
        edit_action.triggered.connect(lambda: self.edit_workspace(item))

    def _add_thread_menu_actions(self, menu, item):
        """为线程节点添加操作"""
        delete_action = menu.addAction("删除线程")
        delete_action.triggered.connect(lambda: self.delete_thread(item))
        
        chat_action = menu.addAction("发送消息")
        #chat_action.triggered.connect(lambda: self.send_to_thread(item))

    def create_workspace(self, item):
        """创建工作区"""
        # 弹出输入对话框
        workspace_name, ok = QInputDialog.getText(
            self, "创建工作区", "请输入工作区名称：", text="新工作区"
        )
        
        if ok and workspace_name:
            # 调用 API 创建工作区
            result = apihandler.create_workspace(workspace_name)
            
            if result and "error" not in result:
                result = result["workspace"]
                # 创建节点并添加到树形控件
                workspace_item = QTreeWidgetItem()
                workspace_item.setText(0, f"📁 {result['name']} ({result.get('chatModel', '')})")
                workspace_item.setData(0, NODE_TYPE_ROLE, NODE_TYPE_WORKSPACE)
                workspace_item.setData(0, SLUG_ROLE, result["slug"])
                workspace_item.setFont(0, QFont("Arial", 12, QFont.Weight.Bold))
                workspace_item.setForeground(0, QBrush(QColor("#0057b8")))
                self.workspace_tree.addTopLevelItem(workspace_item)

    def create_thread(self, item):
        """创建线程（直接通过节点数据获取 slug）"""
        if not item:  # **检查 item 是否有效**
            QMessageBox.critical(self, "错误", "请选择一个工作区以创建线程")
            return

        # **确保选中的节点是工作区**
        node_type = item.data(0, NODE_TYPE_ROLE)
        if node_type != NODE_TYPE_WORKSPACE:
            QMessageBox.critical(self, "错误", "线程必须创建在工作区下")
            return

        workspace_slug = item.data(0, SLUG_ROLE)  # **获取工作区 slug**

        # **弹出输入对话框**
        thread_name, ok = QInputDialog.getText(
            self, "创建线程", "请输入线程名称：", text="new_thread"
        )

        if ok and thread_name:
            # **调用 API 创建线程**
            result = apihandler.create_thread(workspace_slug, thread_name)

            if result and "error" not in result:
                result = result["thread"]

                # **创建线程节点并添加到对应的 workspace**
                thread_item = QTreeWidgetItem()
                thread_item.setText(0, f"📝 {thread_name}")
                thread_item.setData(0, NODE_TYPE_ROLE, NODE_TYPE_THREAD)
                thread_item.setData(0, SLUG_ROLE, result["slug"])
                thread_item.setFont(0, QFont("Arial", 10))  # **设置字体**
                thread_item.setForeground(0, QBrush(QColor("#333333")))  # **灰色字体**

                item.addChild(thread_item)  # **正确添加子节点**
                item.setExpanded(True)  # **展开工作区**


    def delete_workspace(self, item):
        """删除工作区（直接通过节点数据获取 slug）"""
        # 从节点中直接读取 slug
        workspace_slug = item.data(0, SLUG_ROLE)
        
        # 弹出确认对话框
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除工作区（slug: {workspace_slug}）吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 调用 API 删除
            result = apihandler.delete_workspace(workspace_slug)
            
            if result and "error" not in result:
                # 从界面移除节点
                self.workspace_tree.takeTopLevelItem(
                    self.workspace_tree.indexOfTopLevelItem(item)
                )
            elif result:
                QMessageBox.critical(self, "错误", result["error"])

    def delete_thread(self, item):
        """删除线程（直接通过节点数据获取 slug）"""
        # 从节点中直接读取线程 slug
        thread_slug = item.data(0, SLUG_ROLE)
        # 获取父工作区节点
        workspace_item = item.parent()
        workspace_slug = workspace_item.data(0, SLUG_ROLE)  # 父工作区的 slug

        # 确认对话框
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除线程（slug: {thread_slug}）吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 从树形控件中移除
            # 调用 API 删除
            result = apihandler.delete_thread(workspace_slug, thread_slug)
            
            if result and "error" not in result:
                # 从界面移除节点
                item.parent().removeChild(item)
            elif result:
                QMessageBox.critical(self, "错误", result["error"])

    def edit_workspace(self, item):
        """编辑工作区设置"""
        workspace_slug = item.data(0, SLUG_ROLE)

        # **获取当前工作区信息**
        workspaces = self.workspace_cache.get("workspaces", [])
        workspace = next((ws for ws in workspaces if ws["slug"] == workspace_slug), None)

        if not workspace:
            QMessageBox.critical(self, "错误", "未找到该工作区")
            return

        # **创建对话框**
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑工作区设置")
        layout = QFormLayout(dialog)

        # **当前工作区名称**
        name_edit = QLineEdit(workspace.get("name", ""), dialog)
        layout.addRow(QLabel("工作区名称:"), name_edit)

        # **聊天模型 (`chatModel`)**
        model_edit = QComboBox(dialog)
        model_edit.setEditable(True)  # **允许手动输入**
        model_edit.addItem("deepseek-r1:14b")  # **默认值**

        # **获取所有 `chatModel`（遍历所有 `workspace`）**
        chatmodels = {"deepseek-r1:14b"}  # **用 `set` 去重**
        for ws in workspaces:
            model = ws.get("chatModel")
            if model:
                chatmodels.add(model)

        # **填充 `chatModel` 选项**
        for model in sorted(chatmodels):
            if model_edit.findText(model) == -1:
                model_edit.addItem(model)

        model_edit.setCurrentText(workspace.get("chatModel", "deepseek-r1:14b"))
        layout.addRow(QLabel("聊天模型:"), model_edit)

        # **系统提示词 (`openAiPrompt`)**
        prompt_edit = QLineEdit(workspace.get("openAiPrompt", "你是一个智能助手，能够理解并响应我的问题，以清晰、简洁和专业的方式提供帮助。无\
                                              论是信息查询、任务辅助还是创意生成，请根据我的需求提供准确、高效的回答。如果需要，可以提供结构化的\
                                              内容或分步指导。请始终保持简明扼要，并在必要时提供额外的优化建议。"), dialog)
        layout.addRow(QLabel("系统提示词:"), prompt_edit)

        # **相似度阈值 (`similarityThreshold`)**
        threshold_edit = QDoubleSpinBox(dialog)
        threshold_edit.setRange(0.0, 1.0)
        threshold_edit.setSingleStep(0.05)
        threshold_edit.setValue(workspace.get("similarityThreshold", 0.25))
        layout.addRow(QLabel("相似度阈值:"), threshold_edit)

        # **温度 (`openAiTemp`)**
        temp_edit = QDoubleSpinBox(dialog)
        temp_edit.setRange(0.0, 1.0)
        temp_edit.setSingleStep(0.05)
        temp_edit.setValue(workspace.get("openAiTemp", 0.7))
        layout.addRow(QLabel("温度:"), temp_edit)

        # **拒绝回答 (`queryRefusalResponse`)**
        refusal_edit = QLineEdit(workspace.get("queryRefusalResponse", "未找到相关信息"), dialog)
        layout.addRow(QLabel("拒绝回答:"), refusal_edit)

        # **按钮组**
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updates = {
                "name": name_edit.text().strip(),
                "chatModel": model_edit.currentText(),
                "openAiPrompt": prompt_edit.text().strip(),
                "similarityThreshold": threshold_edit.value(),
                "openAiTemp": temp_edit.value(),
                "queryRefusalResponse": refusal_edit.text().strip()
            }

            try:
                result = apihandler.update_workspace(workspace_slug, updates)
                if result and "error" not in result:
                    # **更新 UI**
                    item.setText(0, f"📁 {updates['name']} ({updates['chatModel']})")

                    # **更新本地缓存**
                    self.update_workspace_cache()

                    QMessageBox.information(self, "成功", "工作区设置已更新")
                else:
                    QMessageBox.critical(self, "错误", result.get("error", "未知错误"))

            except Exception as e:
                QMessageBox.critical(self, "异常", f"更新失败: {str(e)}")

    def _execute_selected_function(self):
        """动态执行选中的功能"""
        # 获取当前选中项的处理函数
        handler = self.function_selector.currentData()  # 通过 UserRole 获取
        
        if not handler or not callable(handler):
            QMessageBox.warning(self, "错误", "无效的功能处理程序")
            return

        # 禁用按钮防止重复点击
        self.run_button.setEnabled(False)
        self.run_button.setText("运行中...")

        # 创建后台线程
        self.worker_thread = WorkerThread(handler)
        
        # 任务开始时重置进度条
        self.progress_bar.setValue(0)
        # 连接信号槽
        self.worker_thread.finished.connect(self._on_task_finished)
        self.worker_thread.error_occurred.connect(self._on_task_error)
        # 连接进度信号
        self.worker_thread.progress_updated.connect(self._update_progress_bar)
        
        # 启动线程
        self.worker_thread.start()

    def _stop_task(self):
        """停止当前任务"""
        if self.worker_thread.isRunning():
            self.worker_thread.terminate()  # 强制终止线程
            self.run_button.setEnabled(True)
            self.run_button.setText("运行")
            self.progress_bar.setValue(0)
            QMessageBox.information(self, "停止", "任务已停止！")
            
    def _update_progress_bar(self, current_index, total_files):
        """根据进度更新进度条"""
        progress_percent = int((current_index / total_files) * 100)
        self.progress_bar.setValue(progress_percent)
        
    def _on_task_finished(self):
        self.progress_bar.setValue(100)  # 完成后显示 100%
        """任务完成时的处理"""
        self.run_button.setEnabled(True)
        self.run_button.setText("运行")
        QMessageBox.information(self, "完成", "任务执行成功！")

    def _on_task_error(self, error_msg):
        self.progress_bar.setValue(0)  # 出错时重置
        """任务出错时的处理"""
        self.run_button.setEnabled(True)
        self.run_button.setText("运行")
        QMessageBox.critical(self, "错误", f"任务执行失败:\n{error_msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
