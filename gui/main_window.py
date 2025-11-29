"""
主窗口
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QGroupBox, QComboBox,
                             QLineEdit, QFileDialog, QMessageBox, QTabWidget,
                             QTextEdit, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSlot
import os

from core import ProfileManager, ExtractorEngine, ExtractorThread
from .wizard_dialog import WizardDialog
from .components import ProgressPanel, LogViewer


class MainWindow(QMainWindow):
    """
    主窗口
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LIS Extractor - 医院检验数据抽取工具")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)  # 设置初始大小，但允许调整
        
        self.profile_manager = ProfileManager()
        self.extractor_engine = None
        self.extractor_thread = None
        
        self.init_ui()
        self.refresh_profiles()
    
    def init_ui(self):
        """初始化 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # 标题
        title = QLabel("<h1>LIS Extractor</h1>")
        title.setWordWrap(True)
        main_layout.addWidget(title)
        
        subtitle = QLabel("医院检验数据标准化抽取工具")
        subtitle.setWordWrap(True)
        main_layout.addWidget(subtitle)
        
        # 创建标签页
        tabs = QTabWidget()
        
        # Tab 1: 数据抽取
        extract_tab = self.create_extract_tab()
        tabs.addTab(extract_tab, "数据抽取")
        
        # Tab 2: Profile 管理
        profile_tab = self.create_profile_tab()
        tabs.addTab(profile_tab, "Profile 管理")
        
        # Tab 3: 关于
        about_tab = self.create_about_tab()
        tabs.addTab(about_tab, "关于")
        
        main_layout.addWidget(tabs)
        
        central_widget.setLayout(main_layout)
    
    def create_extract_tab(self) -> QWidget:
        """创建数据抽取标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 模式选择
        mode_group = QGroupBox("选择模式")
        mode_layout = QVBoxLayout()
        
        # 模式 1: 新建配置并抽取
        mode1_layout = QHBoxLayout()
        mode1_btn = QPushButton("🔧 新建格式配置并抽取数据")
        mode1_btn.setMinimumHeight(50)
        mode1_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        mode1_btn.clicked.connect(self.start_wizard)
        mode1_layout.addWidget(mode1_btn, stretch=3)
        mode1_desc = QLabel("首次使用或处理新格式的 LIS 文件")
        mode1_desc.setWordWrap(True)
        mode1_layout.addWidget(mode1_desc, stretch=2)
        mode_layout.addLayout(mode1_layout)
        
        mode_layout.addWidget(QLabel("或"))
        
        # 模式 2: 使用已有配置抽取
        mode2_label = QLabel("使用已有配置抽取数据:")
        mode_layout.addWidget(mode2_label)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # 使用已有 Profile 区域
        existing_group = QGroupBox("使用已有配置")
        existing_layout = QVBoxLayout()
        
        # Profile 选择
        profile_row = QHBoxLayout()
        profile_label = QLabel("配置:")
        profile_label.setMinimumWidth(50)
        profile_row.addWidget(profile_label)
        self.profile_combo = QComboBox()
        self.profile_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.profile_combo.currentTextChanged.connect(self.on_profile_selected)
        profile_row.addWidget(self.profile_combo, stretch=1)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedWidth(40)
        self.refresh_btn.clicked.connect(self.refresh_profiles)
        profile_row.addWidget(self.refresh_btn)
        existing_layout.addLayout(profile_row)
        
        # Profile 描述
        self.profile_desc_label = QLabel("请选择一个配置...")
        self.profile_desc_label.setWordWrap(True)
        existing_layout.addWidget(self.profile_desc_label)
        
        # 输入文件/文件夹
        input_row = QHBoxLayout()
        input_label = QLabel("输入:")
        input_label.setMinimumWidth(50)
        input_row.addWidget(input_label)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("选择 Excel 文件或文件夹...")
        self.input_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        input_row.addWidget(self.input_edit, stretch=1)
        
        self.input_file_btn = QPushButton("选择文件")
        self.input_file_btn.setMinimumWidth(80)
        self.input_file_btn.clicked.connect(self.select_input_file)
        input_row.addWidget(self.input_file_btn)
        
        self.input_folder_btn = QPushButton("选择文件夹")
        self.input_folder_btn.setMinimumWidth(90)
        self.input_folder_btn.clicked.connect(self.select_input_folder)
        input_row.addWidget(self.input_folder_btn)
        
        existing_layout.addLayout(input_row)
        
        # 输出目录
        output_row = QHBoxLayout()
        output_label = QLabel("输出:")
        output_label.setMinimumWidth(50)
        output_row.addWidget(output_label)
        self.output_edit = QLineEdit()
        self.output_edit.setText(os.path.join(os.getcwd(), "outputs"))
        self.output_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        output_row.addWidget(self.output_edit, stretch=1)
        
        self.output_btn = QPushButton("浏览...")
        self.output_btn.setMinimumWidth(80)
        self.output_btn.clicked.connect(self.select_output_dir)
        output_row.addWidget(self.output_btn)
        
        existing_layout.addLayout(output_row)
        
        # 运行按钮
        run_row = QHBoxLayout()
        run_row.addStretch()
        
        self.run_btn = QPushButton("▶️  开始抽取")
        self.run_btn.setMinimumHeight(40)
        self.run_btn.setMinimumWidth(150)
        self.run_btn.clicked.connect(self.start_extraction)
        self.run_btn.setEnabled(False)
        run_row.addWidget(self.run_btn)
        
        self.cancel_btn = QPushButton("⏹ 中止")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.cancel_extraction)
        self.cancel_btn.setEnabled(False)
        run_row.addWidget(self.cancel_btn)
        
        existing_layout.addLayout(run_row)
        
        existing_group.setLayout(existing_layout)
        layout.addWidget(existing_group)
        
        # 进度和日志区
        progress_group = QGroupBox("运行状态")
        progress_layout = QVBoxLayout()
        
        self.progress_panel = ProgressPanel()
        progress_layout.addWidget(self.progress_panel)
        
        progress_layout.addWidget(QLabel("运行日志:"))
        self.log_viewer = LogViewer()
        progress_layout.addWidget(self.log_viewer)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_profile_tab(self) -> QWidget:
        """创建 Profile 管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("<h3>Profile 管理</h3>"))
        
        # Profile 列表
        self.profile_list = QTextEdit()
        self.profile_list.setReadOnly(True)
        layout.addWidget(self.profile_list)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.clicked.connect(self.refresh_profile_list)
        layout.addWidget(refresh_btn)
        
        widget.setLayout(layout)
        return widget
    
    def create_about_tab(self) -> QWidget:
        """创建关于标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        about_text = """
        <h2>LIS Extractor</h2>
        <p><b>版本:</b> 1.0.0</p>
        <p><b>描述:</b> 医院检验数据标准化抽取工具</p>
        <br>
        <h3>功能特性</h3>
        <ul>
            <li>支持从医院 LIS 导出的 Excel 文件中抽取检验数据</li>
            <li>通过向导创建可重复使用的配置文件</li>
            <li>自动识别列、映射字段、选择项目</li>
            <li>智能解析特殊格式（<0.5, >1000, 阳性/阴性等）</li>
            <li>输出标准化的长表格式</li>
            <li>生成质量控制报告</li>
            <li>支持批量处理多个文件</li>
        </ul>
        <br>
        <h3>版权信息</h3>
        <p><b>许可协议:</b> MIT License</p>
        <p><b>版权所有:</b> © 2024 LIS Extractor Contributors</p>
        <p>本软件为开源软件，遵循 MIT 许可协议。您可以自由使用、修改和分发本软件。</p>
        <br>
        <p><b>GitHub:</b> <a href="https://github.com/xenorexq/lis-extractor">https://github.com/xenorexq/lis-extractor</a></p>
        <p><b>技术栈:</b> Python 3.10+, PyQt6, pandas</p>
        <p><b>开发:</b> Github: xenorexq (https://github.com/xenorexq)</p>
        """
        
        about_label = QLabel(about_text)
        about_label.setWordWrap(True)
        about_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(about_label)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def start_wizard(self):
        """启动向导"""
        wizard = WizardDialog(self)
        wizard.wizard_finished.connect(self.on_wizard_finished)
        wizard.exec()
    
    @pyqtSlot(dict)
    def on_wizard_finished(self, result: dict):
        """向导完成"""
        self.refresh_profiles()
        
        # 如果勾选了立即运行
        if result.get('run_immediately', False):
            # 选择刚创建的 profile
            profile_id = result['profile']['id']
            index = self.profile_combo.findData(profile_id)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
            
            # 设置输入输出路径
            self.input_edit.setText(result.get('input_path', ''))
            self.output_edit.setText(result.get('output_dir', ''))
            
            # 自动开始抽取
            QMessageBox.information(self, "提示", "Profile 已创建，即将开始抽取数据...")
            self.start_extraction()
    
    def refresh_profiles(self):
        """刷新 Profile 列表"""
        self.profile_combo.clear()
        
        profiles = self.profile_manager.list_profiles()
        
        if not profiles:
            self.profile_combo.addItem("(无可用配置)", None)
            return
        
        for profile in profiles:
            display_text = f"{profile['id']} - {profile['description'][:50]}"
            self.profile_combo.addItem(display_text, profile['id'])
    
    def refresh_profile_list(self):
        """刷新 Profile 详细列表"""
        profiles = self.profile_manager.list_profiles()
        
        if not profiles:
            self.profile_list.setPlainText("暂无 Profile 配置")
            return
        
        lines = []
        for i, profile in enumerate(profiles, 1):
            lines.append(f"{i}. {profile['id']}")
            lines.append(f"   描述: {profile['description']}")
            lines.append(f"   创建时间: {profile['created_time']}")
            lines.append(f"   文件: {profile['file_path']}")
            lines.append("")
        
        self.profile_list.setPlainText("\n".join(lines))
    
    def on_profile_selected(self, text: str):
        """Profile 选中时"""
        profile_id = self.profile_combo.currentData()
        
        if not profile_id:
            self.profile_desc_label.setText("请选择一个配置...")
            self.run_btn.setEnabled(False)
            return
        
        # 加载 profile
        profile = self.profile_manager.load_profile(profile_id)
        
        if profile:
            desc = profile.get('description', '无描述')
            self.profile_desc_label.setText(f"✓ {desc}")
            
            # 检查是否可以运行
            has_input = bool(self.input_edit.text())
            self.run_btn.setEnabled(has_input)
    
    def select_input_file(self):
        """选择输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Excel 文件",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.input_edit.setText(file_path)
            self.check_can_run()
    
    def select_input_folder(self):
        """选择输入文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择包含 Excel 文件的文件夹"
        )
        if folder_path:
            self.input_edit.setText(folder_path)
            self.check_can_run()
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.output_edit.text()
        )
        if dir_path:
            self.output_edit.setText(dir_path)
    
    def check_can_run(self):
        """检查是否可以运行"""
        has_profile = self.profile_combo.currentData() is not None
        has_input = bool(self.input_edit.text())
        
        self.run_btn.setEnabled(has_profile and has_input)
    
    def start_extraction(self):
        """开始抽取"""
        profile_id = self.profile_combo.currentData()
        input_path = self.input_edit.text()
        output_dir = self.output_edit.text()
        
        if not profile_id or not input_path:
            QMessageBox.warning(self, "提示", "请选择配置和输入文件")
            return
        
        # 获取 profile 路径
        profile_path = os.path.join(
            self.profile_manager.profiles_dir,
            f"{profile_id}.yaml"
        )
        
        # 创建抽取引擎
        self.extractor_engine = ExtractorEngine(profile_path)
        
        # 连接信号
        self.extractor_engine.progress.connect(self.on_progress)
        self.extractor_engine.log.connect(self.on_log)
        self.extractor_engine.finished.connect(self.on_extraction_finished)
        self.extractor_engine.error.connect(self.on_extraction_error)
        
        # 创建线程
        self.extractor_thread = ExtractorThread(
            self.extractor_engine,
            input_path,
            output_dir
        )
        
        # 启动线程
        self.extractor_thread.start()
        
        # 更新 UI
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.log_viewer.clear_log()
        self.log_viewer.append_log("=" * 50)
        self.log_viewer.append_log("开始抽取...")
        self.log_viewer.append_log("=" * 50)
    
    def cancel_extraction(self):
        """取消抽取"""
        if self.extractor_engine:
            self.extractor_engine.cancel()
        
        if self.extractor_thread:
            self.extractor_thread.quit()
            self.extractor_thread.wait()
        
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_panel.reset()
    
    @pyqtSlot(int, str)
    def on_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_panel.update_progress(value, message)
    
    @pyqtSlot(str)
    def on_log(self, message: str):
        """添加日志"""
        self.log_viewer.append_log(message)
    
    @pyqtSlot(dict)
    def on_extraction_finished(self, result: dict):
        """抽取完成"""
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        QMessageBox.information(
            self,
            "完成",
            f"数据抽取完成!\n\n"
            f"输出目录: {result['output_dir']}\n"
            f"数据行数: {result['total_rows']}\n"
            f"检验项目: {result['total_tests']}"
        )
    
    @pyqtSlot(str)
    def on_extraction_error(self, error_msg: str):
        """抽取出错"""
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        QMessageBox.critical(self, "错误", f"抽取失败:\n{error_msg}")

