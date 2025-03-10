# LLMNoteFlow

## 项目概述

LLMNoteFlow是一个基于大语言模型(LLM)的笔记处理工具，旨在帮助用户高效地管理、转换和优化Markdown格式的笔记。该应用程序提供了友好的图形用户界面，支持批量处理笔记文件，并与API服务进行交互。

## 主要功能

- **批量生成Anki卡片**：将Markdown笔记自动转换为Anki学习卡片，便于记忆和复习
- **笔记内容优化**：自动改进Markdown笔记的结构与内容，提升笔记质量
- **工作区与线程管理**：创建和管理多个工作区和线程，组织不同的笔记处理任务
- **API集成**：与外部API服务交互，支持高级文本处理功能

## 系统要求

- Python 3.8+
- PyQt6
- Ollama安装并启动，具备本地模型
- AnythingLLm安装并启动

## 安装指南

1. 克隆或下载本仓库
2. 安装依赖包：
   ```
   pip install PyQt6 requests
   ```
3. 配置config.py文件中的API设置和项目路径

## 使用方法

### 启动应用

```
python MainWindow.py
```

### 基本操作流程

1. **测试API连接**：点击"测试API"按钮确认API服务可用
2. **配置工作环境**：
   - 创建或选择工作区
   - 创建处理线程
   - 设置输入/输出文件路径
3. **选择功能**：从下拉菜单中选择所需功能（生成卡片或改进笔记）
4. **运行处理**：点击"运行"按钮开始处理，进度条会显示当前进度

### 工作区管理

- 右键点击工作区树形结构可以：
  - 创建新工作区
  - 创建新线程
  - 删除现有工作区/线程
  - 刷新工作区列表

## 配置说明

主要配置文件为`config.py`，包含以下关键设置：

```python
# API 配置
API_URL = "http://localhost:3001/api"  # API服务地址
API_KEY = "YOUR_API_KEY"              # API密钥

# 工作区配置
workspace_name = "CardsGenerator"      # 默认工作区名称
chatmodel = "deepseek-r1:7b"          # 使用的语言模型

# 项目路径配置
project_folder_path = "YOUR_PROJECT_PATH"  # 项目主目录
source_file_name = "YOUR_SOURCE_FILE.md"   # 源文件名称
```

## 文件夹结构

应用程序会自动创建以下文件夹结构：

```
project_folder_path/
├── data/                  # 存放源数据文件
├── prompt/                # 自定义提示词文件
├── processed/             # 处理中的文件
│   └── [source_file]/
│       ├── finished/      # 处理完成的文件
│       └── unfinished/    # 待处理的文件
├── output/                # 最终输出文件
└── log/                   # 日志文件
```

## 内置提示词模板

应用程序包含内置的提示词模板，位于`inline_prompt`文件夹：

- **Anki卡片生成**：用于生成符合记忆优化原则的Anki卡片
- **Markdown笔记丰富**：用于优化笔记结构和内容

## 贡献指南

欢迎提交问题报告和功能建议。如需贡献代码，请遵循以下步骤：

1. Fork本仓库
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

[MIT License](LICENSE)