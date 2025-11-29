"""
GUI 通用组件
"""
from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QPushButton, 
                             QProgressBar, QTextEdit, QLabel, QHBoxLayout,
                             QVBoxLayout, QWidget, QHeaderView, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import pandas as pd


class DataPreviewTable(QTableWidget):
    """
    数据预览表格组件
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def load_dataframe(self, df: pd.DataFrame, max_rows: int = 20):
        """加载 DataFrame 到表格"""
        self.clear()
        
        if df.empty:
            self.setRowCount(0)
            self.setColumnCount(0)
            return
        
        # 限制行数
        df_display = df.head(max_rows)
        
        self.setRowCount(len(df_display))
        self.setColumnCount(len(df_display.columns))
        self.setHorizontalHeaderLabels([str(col) for col in df_display.columns])
        
        # 填充数据
        for i in range(len(df_display)):
            for j in range(len(df_display.columns)):
                value = df_display.iloc[i, j]
                item = QTableWidgetItem(str(value))
                self.setItem(i, j, item)
        
        # 自动调整列宽
        self.resizeColumnsToContents()


class ProgressPanel(QWidget):
    """
    进度显示面板
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def update_progress(self, value: int, message: str = ""):
        """更新进度"""
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
    
    def reset(self):
        """重置"""
        self.progress_bar.setValue(0)
        self.status_label.setText("准备就绪")


class LogViewer(QTextEdit):
    """
    日志查看器
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMinimumHeight(150)
        self.setMaximumHeight(250)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def append_log(self, message: str):
        """添加日志"""
        self.append(message)
        # 自动滚动到底部
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
    
    def clear_log(self):
        """清空日志"""
        self.clear()


class NavigationButtons(QWidget):
    """
    向导导航按钮组
    """
    previous_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    
    def __init__(self, show_previous: bool = True, parent=None):
        super().__init__(parent)
        self.init_ui(show_previous)
    
    def init_ui(self, show_previous: bool):
        layout = QHBoxLayout()
        layout.addStretch()
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        layout.addWidget(self.cancel_btn)
        
        # 上一步按钮
        if show_previous:
            self.previous_btn = QPushButton("< 上一步")
            self.previous_btn.clicked.connect(self.previous_clicked.emit)
            layout.addWidget(self.previous_btn)
        else:
            self.previous_btn = None
        
        # 下一步按钮
        self.next_btn = QPushButton("下一步 >")
        self.next_btn.clicked.connect(self.next_clicked.emit)
        layout.addWidget(self.next_btn)
        
        self.setLayout(layout)
    
    def set_next_text(self, text: str):
        """设置下一步按钮文字"""
        self.next_btn.setText(text)
    
    def enable_next(self, enabled: bool):
        """启用/禁用下一步按钮"""
        self.next_btn.setEnabled(enabled)
    
    def enable_previous(self, enabled: bool):
        """启用/禁用上一步按钮"""
        if self.previous_btn:
            self.previous_btn.setEnabled(enabled)


class CheckableTableWidget(QTableWidget):
    """
    带复选框的表格
    """
    selection_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def load_items(self, items: list, columns: list):
        """
        加载数据项
        items: [(col1, col2, ...), ...]
        columns: [header1, header2, ...]
        """
        self.clear()
        self.setRowCount(len(items))
        self.setColumnCount(len(columns) + 1)  # +1 for checkbox
        
        headers = ["选择"] + columns
        self.setHorizontalHeaderLabels(headers)
        
        for i, item in enumerate(items):
            # 复选框
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check_item.setCheckState(Qt.CheckState.Checked)
            self.setItem(i, 0, check_item)
            
            # 其他列
            for j, value in enumerate(item):
                self.setItem(i, j + 1, QTableWidgetItem(str(value)))
        
        self.resizeColumnsToContents()
        self.itemChanged.connect(lambda: self.selection_changed.emit())
    
    def get_checked_items(self, column_index: int = 1) -> list:
        """获取选中的项（返回指定列的值）"""
        checked = []
        for i in range(self.rowCount()):
            if self.item(i, 0).checkState() == Qt.CheckState.Checked:
                checked.append(self.item(i, column_index).text())
        return checked
    
    def check_all(self, checked: bool):
        """全选/全不选"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.rowCount()):
            self.item(i, 0).setCheckState(state)

