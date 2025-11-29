"""
向导 Step 5: 输出设置
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QFileDialog, QGroupBox,
                             QCheckBox, QRadioButton, QButtonGroup)
from PyQt6.QtCore import pyqtSignal
import os


class WizardStep5Output(QWidget):
    """
    Step 5: 输出设置
    """
    next_step = pyqtSignal(dict)
    previous_step = pyqtSignal()
    cancel = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("<h2>步骤 5: 输出设置</h2>")
        layout.addWidget(title)
        
        desc = QLabel("设置输出目录和输出选项")
        layout.addWidget(desc)
        
        # 输出目录
        dir_group = QGroupBox("输出目录")
        dir_layout = QVBoxLayout()
        
        dir_row = QHBoxLayout()
        dir_label = QLabel("输出目录:")
        dir_label.setMinimumWidth(70)
        dir_row.addWidget(dir_label)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(os.path.join(os.getcwd(), "outputs"))
        dir_row.addWidget(self.output_dir_edit, stretch=1)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setMinimumWidth(80)
        self.browse_btn.clicked.connect(self.browse_output_dir)
        dir_row.addWidget(self.browse_btn)
        
        dir_layout.addLayout(dir_row)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        # 输出内容
        content_group = QGroupBox("输出内容")
        content_layout = QVBoxLayout()
        
        self.labs_long_check = QCheckBox("labs_long (标准化长表)")
        self.labs_long_check.setChecked(True)
        self.labs_long_check.setEnabled(False)  # 必选
        content_layout.addWidget(self.labs_long_check)
        
        self.qc_report_check = QCheckBox("qc_report (质量控制报告)")
        self.qc_report_check.setChecked(True)
        content_layout.addWidget(self.qc_report_check)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # 数据过滤选项
        filter_group = QGroupBox("数据过滤")
        filter_layout = QVBoxLayout()
        
        self.drop_unknown_check = QCheckBox("排除未选中的检验项目")
        self.drop_unknown_check.setChecked(True)
        filter_layout.addWidget(self.drop_unknown_check)
        
        self.drop_failed_check = QCheckBox("排除解析失败的行")
        self.drop_failed_check.setChecked(False)
        filter_layout.addWidget(self.drop_failed_check)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 元数据选项
        meta_group = QGroupBox("元数据")
        meta_layout = QVBoxLayout()
        
        self.add_profile_id_check = QCheckBox("添加 profile_id 列")
        self.add_profile_id_check.setChecked(True)
        meta_layout.addWidget(self.add_profile_id_check)
        
        self.add_run_id_check = QCheckBox("添加 run_id 列 (时间戳)")
        self.add_run_id_check.setChecked(True)
        meta_layout.addWidget(self.add_run_id_check)
        
        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)
        
        layout.addStretch()
        
        # 导航按钮
        self.nav_buttons = NavigationButtons(show_previous=True)
        self.nav_buttons.next_clicked.connect(self.on_next)
        self.nav_buttons.previous_clicked.connect(self.previous_step.emit)
        self.nav_buttons.cancel_clicked.connect(self.cancel.emit)
        layout.addWidget(self.nav_buttons)
        
        self.setLayout(layout)
    
    def load_data(self, data: dict):
        """加载数据（可选）"""
        pass
    
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.output_dir_edit.text()
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def get_output_options(self) -> dict:
        """获取输出选项"""
        return {
            'output_dir': self.output_dir_edit.text(),
            'include_qc_report': self.qc_report_check.isChecked(),
            'drop_unknown_tests': self.drop_unknown_check.isChecked(),
            'drop_failed_rows': self.drop_failed_check.isChecked(),
            'add_profile_id': self.add_profile_id_check.isChecked(),
            'add_run_id': self.add_run_id_check.isChecked()
        }
    
    def on_next(self):
        """下一步"""
        options = self.get_output_options()
        
        data = {
            'output_options': options
        }
        
        self.next_step.emit(data)


from .components import NavigationButtons

