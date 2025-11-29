"""
向导 Step 3: 选择检验项目
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QGroupBox, QMessageBox,
                             QCheckBox, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import pyqtSignal, Qt
import pandas as pd

from core import TestMapper, ColumnMapper
from .components import CheckableTableWidget, NavigationButtons


class WizardStep3Tests(QWidget):
    """
    Step 3: 选择检验项目
    """
    next_step = pyqtSignal(dict)
    previous_step = pyqtSignal()
    cancel = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.df_preview = None
        self.mapper = None
        self.test_stats = None
        self.selected_tests = set()
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("<h2>步骤 3: 选择检验项目</h2>")
        layout.addWidget(title)
        
        desc = QLabel("从数据中扫描到的所有检验项目，请勾选需要抽取的项目")
        layout.addWidget(desc)
        
        # 搜索和全选区
        control_layout = QHBoxLayout()
        
        # 搜索框
        search_label = QLabel("搜索:")
        search_label.setMinimumWidth(50)
        control_layout.addWidget(search_label)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入项目名称进行搜索...")
        self.search_edit.textChanged.connect(self.filter_tests)
        control_layout.addWidget(self.search_edit, stretch=1)
        
        # 全选/全不选
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setMinimumWidth(80)
        self.select_all_btn.clicked.connect(lambda: self.test_table.check_all(True))
        control_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("全不选")
        self.deselect_all_btn.setMinimumWidth(80)
        self.deselect_all_btn.clicked.connect(lambda: self.test_table.check_all(False))
        control_layout.addWidget(self.deselect_all_btn)
        
        layout.addLayout(control_layout)
        
        # 项目表格
        test_group = QGroupBox("检验项目列表")
        test_layout = QVBoxLayout()
        
        self.info_label = QLabel("未加载数据")
        test_layout.addWidget(self.info_label)
        
        self.test_table = CheckableTableWidget()
        self.test_table.setMinimumHeight(300)
        self.test_table.selection_changed.connect(self.update_selection_count)
        test_layout.addWidget(self.test_table)
        
        self.selection_label = QLabel("已选择: 0 个项目")
        test_layout.addWidget(self.selection_label)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # 导航按钮
        self.nav_buttons = NavigationButtons(show_previous=True)
        self.nav_buttons.next_clicked.connect(self.on_next)
        self.nav_buttons.previous_clicked.connect(self.previous_step.emit)
        self.nav_buttons.cancel_clicked.connect(self.cancel.emit)
        layout.addWidget(self.nav_buttons)
        
        self.setLayout(layout)
    
    def load_data(self, data: dict):
        """加载数据"""
        self.df_preview = data['df_preview']
        self.mapper = data['mapper']
        
        # 应用映射
        df_mapped = self.mapper.apply(self.df_preview)
        
        # 统计检验项目
        if 'test_name' not in df_mapped.columns:
            QMessageBox.warning(self, "错误", "未找到 test_name 字段")
            return
        
        temp_mapper = TestMapper()
        self.test_stats = temp_mapper.get_test_statistics(df_mapped, 'test_name')
        
        # 填充表格
        items = []
        for _, row in self.test_stats.iterrows():
            items.append((row['test_name'], row['count']))
        
        self.test_table.load_items(items, ['项目名称', '出现次数'])
        
        # 更新信息
        self.info_label.setText(f"✓ 扫描到 {len(self.test_stats)} 个不同的检验项目")
        self.update_selection_count()
    
    def filter_tests(self):
        """过滤/搜索检验项目"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.test_table.rowCount()):
            test_name = self.test_table.item(i, 1).text().lower()
            
            if search_text in test_name:
                self.test_table.setRowHidden(i, False)
            else:
                self.test_table.setRowHidden(i, True)
    
    def update_selection_count(self):
        """更新选择计数"""
        selected = self.test_table.get_checked_items(column_index=1)
        self.selection_label.setText(f"已选择: {len(selected)} 个项目")
        
        # 至少选择一个项目才能继续
        self.nav_buttons.enable_next(len(selected) > 0)
    
    def on_next(self):
        """下一步"""
        selected = self.test_table.get_checked_items(column_index=1)
        
        if not selected:
            QMessageBox.warning(self, "提示", "请至少选择一个检验项目")
            return
        
        # 创建 test_mapping（此时还没有别名和单位，Step 3 只是选择）
        test_mapping = {}
        for test_name in selected:
            test_mapping[test_name] = {
                'aliases': [test_name],
                'unit': None,
                'range': None
            }
        
        data = {
            'test_mapping': test_mapping,
            'selected_tests': selected
        }
        
        self.next_step.emit(data)

