"""
向导 Step 6: 生成 Profile + 开始抽取
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QGroupBox, QTextEdit,
                             QCheckBox, QMessageBox)
from PyQt6.QtCore import pyqtSignal
import os

from core import ProfileManager
from .components import NavigationButtons


class WizardStep6Summary(QWidget):
    """
    Step 6: 生成 Profile 并开始抽取
    """
    finish = pyqtSignal(dict)  # 完成向导，传递完整配置
    previous_step = pyqtSignal()
    cancel = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_wizard_data = {}
        self.profile_manager = ProfileManager()
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("<h2>步骤 6: 完成配置</h2>")
        layout.addWidget(title)
        
        desc = QLabel("检查配置摘要，设置 Profile 名称和描述")
        layout.addWidget(desc)
        
        # Profile 信息
        profile_group = QGroupBox("Profile 信息")
        profile_layout = QVBoxLayout()
        
        # Profile ID
        id_layout = QHBoxLayout()
        id_label = QLabel("Profile ID:")
        id_label.setMinimumWidth(80)
        id_layout.addWidget(id_label)
        self.profile_id_edit = QLineEdit()
        self.profile_id_edit.setPlaceholderText("例如: hospital_lis_2024")
        id_layout.addWidget(self.profile_id_edit, stretch=1)
        profile_layout.addLayout(id_layout)
        
        # Profile 描述
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("描述:"))
        self.profile_desc_edit = QTextEdit()
        self.profile_desc_edit.setPlaceholderText("例如: XX医院 LIS 系统住院检验格式")
        self.profile_desc_edit.setMaximumHeight(80)
        desc_layout.addWidget(self.profile_desc_edit)
        profile_layout.addLayout(desc_layout)
        
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)
        
        # 配置摘要
        summary_group = QGroupBox("配置摘要")
        summary_layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMinimumHeight(180)
        self.summary_text.setMaximumHeight(250)
        summary_layout.addWidget(self.summary_text)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # 完成后操作
        action_group = QGroupBox("完成后操作")
        action_layout = QVBoxLayout()
        
        self.run_immediately_check = QCheckBox("保存 Profile 后立即处理当前文件")
        self.run_immediately_check.setChecked(True)
        action_layout.addWidget(self.run_immediately_check)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # 导航按钮
        self.nav_buttons = NavigationButtons(show_previous=True)
        self.nav_buttons.set_next_text("完成并保存")
        self.nav_buttons.next_clicked.connect(self.on_finish)
        self.nav_buttons.previous_clicked.connect(self.previous_step.emit)
        self.nav_buttons.cancel_clicked.connect(self.cancel.emit)
        layout.addWidget(self.nav_buttons)
        
        self.setLayout(layout)
    
    def load_data(self, data: dict):
        """加载所有向导数据"""
        self.all_wizard_data = data
        self.generate_summary()
    
    def generate_summary(self):
        """生成配置摘要"""
        lines = []
        
        # 数据源
        lines.append("【数据源】")
        lines.append(f"  文件/文件夹: {self.all_wizard_data.get('input_path', 'N/A')}")
        lines.append("")
        
        # 字段映射
        lines.append("【字段映射】")
        mapping = self.all_wizard_data.get('mapping', {})
        for std_field, orig_col in mapping.items():
            lines.append(f"  {std_field} ← {orig_col}")
        lines.append("")
        
        # 检验项目
        lines.append("【检验项目】")
        selected_tests = self.all_wizard_data.get('selected_tests', [])
        lines.append(f"  已选择 {len(selected_tests)} 个项目")
        if len(selected_tests) <= 10:
            for test in selected_tests:
                lines.append(f"    - {test}")
        else:
            for test in selected_tests[:10]:
                lines.append(f"    - {test}")
            lines.append(f"    ... 还有 {len(selected_tests) - 10} 个")
        lines.append("")
        
        # 数值解析规则
        lines.append("【数值解析规则】")
        value_parsing = self.all_wizard_data.get('value_parsing', {})
        less_rule = value_parsing.get('less_than', {}).get('rule', 'half')
        greater_rule = value_parsing.get('greater_than', {}).get('rule', 'keep')
        lines.append(f"  小于号: {less_rule}")
        lines.append(f"  大于号: {greater_rule}")
        lines.append("")
        
        # 输出设置
        lines.append("【输出设置】")
        output_options = self.all_wizard_data.get('output_options', {})
        lines.append(f"  输出目录: {output_options.get('output_dir', 'N/A')}")
        lines.append(f"  包含质量报告: {'是' if output_options.get('include_qc_report', True) else '否'}")
        
        self.summary_text.setPlainText("\n".join(lines))
    
    def on_finish(self):
        """完成向导"""
        # 验证 Profile ID
        profile_id = self.profile_id_edit.text().strip()
        if not profile_id:
            QMessageBox.warning(self, "提示", "请输入 Profile ID")
            return
        
        # 检查是否已存在
        if self.profile_manager.profile_exists(profile_id):
            reply = QMessageBox.question(
                self,
                "确认覆盖",
                f"Profile '{profile_id}' 已存在，是否覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # 创建 Profile
        profile = self.profile_manager.create_profile_from_wizard(
            profile_id=profile_id,
            description=self.profile_desc_edit.toPlainText().strip(),
            column_mapping=self.all_wizard_data.get('mapping', {}),
            test_mapping=self.all_wizard_data.get('test_mapping', {}),
            value_parsing=self.all_wizard_data.get('value_parsing', {}),
            required_columns=list(self.all_wizard_data.get('mapping', {}).values()),
            skip_top_rows=self.all_wizard_data.get('header_row', 0),
            output_options={
                'drop_unknown_tests': self.all_wizard_data.get('output_options', {}).get('drop_unknown_tests', True),
                'drop_failed_rows': self.all_wizard_data.get('output_options', {}).get('drop_failed_rows', False)
            }
        )
        
        # 保存 Profile
        try:
            profile_path = self.profile_manager.save_profile(profile)
            QMessageBox.information(
                self,
                "成功",
                f"Profile 已保存!\n路径: {profile_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"无法保存 Profile:\n{str(e)}")
            return
        
        # 完成
        result = {
            'profile': profile,
            'profile_path': profile_path,
            'run_immediately': self.run_immediately_check.isChecked(),
            'input_path': self.all_wizard_data.get('input_path', ''),
            'output_dir': self.all_wizard_data.get('output_options', {}).get('output_dir', '')
        }
        
        self.finish.emit(result)

