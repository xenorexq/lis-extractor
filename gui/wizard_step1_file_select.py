"""
向导 Step 1: 选择文件/文件夹
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QFileDialog, QMessageBox,
                             QGroupBox)
from PyQt6.QtCore import pyqtSignal
import pandas as pd

from core import DataLoader
from .components import DataPreviewTable, NavigationButtons


class WizardStep1FileSelect(QWidget):
    """
    Step 1: 选择真实文件/文件夹并预览
    """
    next_step = pyqtSignal(dict)  # 发送数据到下一步
    cancel = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loader = DataLoader()
        self.df_preview = None
        self.header_row = 0
        self.file_path = ""
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("<h2>步骤 1: 选择数据文件</h2>")
        layout.addWidget(title)
        
        desc = QLabel("请选择 LIS 导出的 Excel 文件或包含多个 Excel 的文件夹")
        layout.addWidget(desc)
        
        # 文件选择区
        file_group = QGroupBox("数据源")
        file_layout = QVBoxLayout()
        
        # 单个文件
        file_row = QHBoxLayout()
        file_label = QLabel("选择文件:")
        file_label.setMinimumWidth(80)
        file_row.addWidget(file_label)
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("点击按钮选择 Excel 文件...")
        file_row.addWidget(self.file_edit, stretch=1)
        self.file_btn = QPushButton("浏览文件...")
        self.file_btn.setMinimumWidth(100)
        self.file_btn.clicked.connect(self.select_file)
        file_row.addWidget(self.file_btn)
        file_layout.addLayout(file_row)
        
        # 文件夹
        folder_row = QHBoxLayout()
        folder_label = QLabel("或选择文件夹:")
        folder_label.setMinimumWidth(80)
        folder_row.addWidget(folder_label)
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("点击按钮选择包含 Excel 的文件夹...")
        folder_row.addWidget(self.folder_edit, stretch=1)
        self.folder_btn = QPushButton("浏览文件夹...")
        self.folder_btn.setMinimumWidth(100)
        self.folder_btn.clicked.connect(self.select_folder)
        folder_row.addWidget(self.folder_btn)
        file_layout.addLayout(folder_row)
        
        # 加载预览按钮
        self.preview_btn = QPushButton("加载预览")
        self.preview_btn.clicked.connect(self.load_preview)
        self.preview_btn.setEnabled(False)
        file_layout.addWidget(self.preview_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 数据预览区
        preview_group = QGroupBox("数据预览 (前 20 行)")
        preview_layout = QVBoxLayout()
        
        self.info_label = QLabel("未加载数据")
        preview_layout.addWidget(self.info_label)
        
        self.preview_table = DataPreviewTable()
        preview_layout.addWidget(self.preview_table)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # 导航按钮
        self.nav_buttons = NavigationButtons(show_previous=False)
        self.nav_buttons.next_clicked.connect(self.on_next)
        self.nav_buttons.cancel_clicked.connect(self.cancel.emit)
        self.nav_buttons.enable_next(False)
        layout.addWidget(self.nav_buttons)
        
        self.setLayout(layout)
        
        # 连接信号
        self.file_edit.textChanged.connect(self.on_path_changed)
        self.folder_edit.textChanged.connect(self.on_path_changed)
    
    def select_file(self):
        """选择单个文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Excel 文件",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.file_edit.setText(file_path)
            self.folder_edit.clear()
    
    def select_folder(self):
        """选择文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择包含 Excel 文件的文件夹"
        )
        if folder_path:
            self.folder_edit.setText(folder_path)
            self.file_edit.clear()
    
    def on_path_changed(self):
        """路径变化时启用预览按钮"""
        has_path = bool(self.file_edit.text() or self.folder_edit.text())
        self.preview_btn.setEnabled(has_path)
        self.nav_buttons.enable_next(False)
    
    def load_preview(self):
        """加载预览数据"""
        try:
            # 确定输入路径
            if self.file_edit.text():
                input_path = self.file_edit.text()
            elif self.folder_edit.text():
                input_path = self.folder_edit.text()
                # 如果是文件夹，找第一个文件用于预览
                files = self.loader.find_excel_files(input_path)
                if not files:
                    QMessageBox.warning(self, "错误", "所选文件夹中未找到 Excel 文件")
                    return
                input_path = files[0]
            else:
                return
            
            self.file_path = input_path
            
            # 加载预览
            self.df_preview, self.header_row, _ = self.loader.load_preview(input_path, max_rows=100)
            
            # 显示预览
            self.preview_table.load_dataframe(self.df_preview, max_rows=20)
            
            # 更新信息
            info = f"✓ 已加载: {len(self.df_preview)} 行, {len(self.df_preview.columns)} 列 (Header 行: {self.header_row})"
            self.info_label.setText(info)
            
            # 启用下一步
            self.nav_buttons.enable_next(True)
            
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载文件:\n{str(e)}")
    
    def on_next(self):
        """下一步"""
        if self.df_preview is None:
            QMessageBox.warning(self, "提示", "请先加载预览数据")
            return
        
        # 准备数据传递给下一步
        data = {
            'input_path': self.file_edit.text() or self.folder_edit.text(),
            'df_preview': self.df_preview,
            'header_row': self.header_row,
            'columns': self.df_preview.columns.tolist()
        }
        
        self.next_step.emit(data)

