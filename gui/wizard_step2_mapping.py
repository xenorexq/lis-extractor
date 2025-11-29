"""
向导 Step 2: 字段映射
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QComboBox,
                             QGroupBox, QMessageBox, QCheckBox, QPushButton,
                             QHeaderView)
from PyQt6.QtCore import pyqtSignal, Qt
import pandas as pd

from core import ColumnMapper
from .components import NavigationButtons


class WizardStep2Mapping(QWidget):
    """
    Step 2: 字段映射
    """
    next_step = pyqtSignal(dict)
    previous_step = pyqtSignal()
    cancel = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.df_preview = None
        self.column_examples = {}
        self.mapping_combos = {}
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("<h2>步骤 2: 字段映射</h2>")
        layout.addWidget(title)
        
        desc = QLabel("请将原始列名映射为标准字段。必填字段: patient_id, sample_datetime, test_name, test_value")
        layout.addWidget(desc)
        
        # 映射表格区
        mapping_group = QGroupBox("列映射")
        mapping_layout = QVBoxLayout()
        
        # 自动建议和全选按钮
        suggest_btn_layout = QHBoxLayout()
        self.auto_suggest_btn = QPushButton("🔍 自动建议映射")
        self.auto_suggest_btn.clicked.connect(self.auto_suggest_mapping)
        suggest_btn_layout.addWidget(self.auto_suggest_btn)
        
        suggest_btn_layout.addStretch()
        
        # 全选/全不选按钮
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setMinimumWidth(80)
        self.select_all_btn.clicked.connect(self.select_all_columns)
        suggest_btn_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("全不选")
        self.deselect_all_btn.setMinimumWidth(80)
        self.deselect_all_btn.clicked.connect(self.deselect_all_columns)
        suggest_btn_layout.addWidget(self.deselect_all_btn)
        
        mapping_layout.addLayout(suggest_btn_layout)
        
        # 映射表格
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(4)
        self.mapping_table.setHorizontalHeaderLabels(["包含", "原始列名", "示例值", "映射为"])
        
        # 设置列宽模式
        header = self.mapping_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.mapping_table.setColumnWidth(0, 60)
        self.mapping_table.setMinimumHeight(300)
        mapping_layout.addWidget(self.mapping_table)
        
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # 验证信息
        self.validation_label = QLabel("")
        layout.addWidget(self.validation_label)
        
        # 导航按钮
        self.nav_buttons = NavigationButtons(show_previous=True)
        self.nav_buttons.next_clicked.connect(self.on_next)
        self.nav_buttons.previous_clicked.connect(self.previous_step.emit)
        self.nav_buttons.cancel_clicked.connect(self.cancel.emit)
        layout.addWidget(self.nav_buttons)
        
        self.setLayout(layout)
    
    def load_data(self, data: dict):
        """加载上一步传来的数据"""
        self.df_preview = data['df_preview']
        self.column_examples = ColumnMapper({}).get_example_values(self.df_preview)
        
        self.populate_mapping_table()
    
    def populate_mapping_table(self):
        """填充映射表格"""
        columns = self.df_preview.columns.tolist()
        
        self.mapping_table.setRowCount(len(columns))
        self.mapping_combos.clear()
        
        # 标准字段选项
        standard_fields = ['(不映射)'] + ColumnMapper.STANDARD_FIELDS
        
        for i, col in enumerate(columns):
            # 复选框 - 是否包含此列
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check_item.setCheckState(Qt.CheckState.Checked)
            self.mapping_table.setItem(i, 0, check_item)
            
            # 原始列名
            col_item = QTableWidgetItem(str(col))
            col_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.mapping_table.setItem(i, 1, col_item)
            
            # 示例值
            examples = self.column_examples.get(col, [])
            example_text = " | ".join(examples[:3])
            example_item = QTableWidgetItem(example_text)
            example_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.mapping_table.setItem(i, 2, example_item)
            
            # 映射下拉框
            combo = QComboBox()
            combo.addItems(standard_fields)
            combo.currentTextChanged.connect(self.validate_mapping)
            self.mapping_table.setCellWidget(i, 3, combo)
            self.mapping_combos[col] = combo
        
        # 连接复选框变化事件
        self.mapping_table.itemChanged.connect(self.validate_mapping)
    
    def auto_suggest_mapping(self):
        """自动建议映射"""
        columns = self.df_preview.columns.tolist()
        suggestions = ColumnMapper.suggest_mapping(columns)
        
        for col, combo in self.mapping_combos.items():
            suggested_field = None
            for field, suggested_col in suggestions.items():
                if suggested_col == col:
                    suggested_field = field
                    break
            
            if suggested_field:
                index = combo.findText(suggested_field)
                if index >= 0:
                    combo.setCurrentIndex(index)
        
        self.validate_mapping()
    
    def select_all_columns(self):
        """全选所有列"""
        for i in range(self.mapping_table.rowCount()):
            self.mapping_table.item(i, 0).setCheckState(Qt.CheckState.Checked)
        self.validate_mapping()
    
    def deselect_all_columns(self):
        """全不选所有列"""
        for i in range(self.mapping_table.rowCount()):
            self.mapping_table.item(i, 0).setCheckState(Qt.CheckState.Unchecked)
        self.validate_mapping()
    
    def get_mapping(self) -> dict:
        """获取当前映射"""
        mapping = {}
        
        for i in range(self.mapping_table.rowCount()):
            # 检查是否勾选
            if self.mapping_table.item(i, 0).checkState() != Qt.CheckState.Checked:
                continue
            
            col_name = self.mapping_table.item(i, 1).text()
            combo = self.mapping_table.cellWidget(i, 3)
            standard_field = combo.currentText()
            
            if standard_field != '(不映射)':
                mapping[standard_field] = col_name
        
        return mapping
    
    def validate_mapping(self):
        """验证映射是否完整"""
        mapping = self.get_mapping()
        
        # 检查必填字段
        required = ColumnMapper.REQUIRED_FIELDS
        mapped_fields = set(mapping.keys())
        missing = set(required) - mapped_fields
        
        if missing:
            msg = f"⚠️ 缺少必填字段: {', '.join(missing)}"
            self.validation_label.setText(f'<font color="red">{msg}</font>')
            self.nav_buttons.enable_next(False)
        else:
            msg = f"✓ 映射完整！已映射 {len(mapping)} 个字段"
            self.validation_label.setText(f'<font color="green">{msg}</font>')
            self.nav_buttons.enable_next(True)
    
    def on_next(self):
        """下一步"""
        mapping = self.get_mapping()
        
        if not mapping:
            QMessageBox.warning(self, "提示", "请至少映射一个字段")
            return
        
        # 验证必填字段
        mapper = ColumnMapper(mapping)
        is_valid, missing = mapper.validate()
        
        if not is_valid:
            QMessageBox.warning(
                self, 
                "映射不完整", 
                f"请映射以下必填字段:\n{', '.join(missing)}"
            )
            return
        
        # 传递数据
        data = {
            'mapping': mapping,
            'mapper': mapper
        }
        
        self.next_step.emit(data)


# 需要导入 QPushButton
from PyQt6.QtWidgets import QPushButton

