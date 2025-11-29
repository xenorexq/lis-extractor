"""
向导 Step 4: 数值解析规则
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QRadioButton, QButtonGroup, QLineEdit,
                             QTableWidget, QTableWidgetItem, QComboBox,
                             QMessageBox, QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt
import pandas as pd

from core import ValueParser, ColumnMapper
from .components import NavigationButtons
from core.utils import detect_special_value_patterns, detect_value_formats


class WizardStep4Values(QWidget):
    """
    Step 4: 数值解析规则
    """
    next_step = pyqtSignal(dict)
    previous_step = pyqtSignal()
    cancel = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.df_preview = None
        self.mapper = None
        self.special_patterns = {}
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("<h2>步骤 4: 数值解析规则</h2>")
        layout.addWidget(title)
        
        desc = QLabel("程序自动检测到以下特殊值格式，请设置解析规则")
        layout.addWidget(desc)
        
        # 格式统计预览
        format_preview_group = QGroupBox("📊 数值格式检测预览")
        format_preview_layout = QVBoxLayout()
        
        self.format_stats_label = QLabel("正在分析数据格式...")
        self.format_stats_label.setWordWrap(True)
        format_preview_layout.addWidget(self.format_stats_label)
        
        format_preview_group.setLayout(format_preview_layout)
        layout.addWidget(format_preview_group)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # 1. 小于号规则
        less_group = QGroupBox("小于号规则 (<x)")
        less_layout = QVBoxLayout()
        
        self.less_examples_label = QLabel("示例: 暂无")
        less_layout.addWidget(self.less_examples_label)
        
        self.less_btn_group = QButtonGroup()
        self.less_half_radio = QRadioButton("使用一半值 (x/2)")
        self.less_bound_radio = QRadioButton("使用下界值 (x)")
        self.less_na_radio = QRadioButton("设为 NA")
        
        self.less_half_radio.setChecked(True)
        self.less_btn_group.addButton(self.less_half_radio)
        self.less_btn_group.addButton(self.less_bound_radio)
        self.less_btn_group.addButton(self.less_na_radio)
        
        less_layout.addWidget(self.less_half_radio)
        less_layout.addWidget(self.less_bound_radio)
        less_layout.addWidget(self.less_na_radio)
        less_group.setLayout(less_layout)
        scroll_layout.addWidget(less_group)
        
        # 2. 大于号规则
        greater_group = QGroupBox("大于号规则 (>x)")
        greater_layout = QVBoxLayout()
        
        self.greater_examples_label = QLabel("示例: 暂无")
        greater_layout.addWidget(self.greater_examples_label)
        
        self.greater_btn_group = QButtonGroup()
        self.greater_keep_radio = QRadioButton("保持原值 (x)")
        self.greater_cap_radio = QRadioButton("使用自定义上限")
        self.greater_na_radio = QRadioButton("设为 NA")
        
        self.greater_keep_radio.setChecked(True)
        self.greater_btn_group.addButton(self.greater_keep_radio)
        self.greater_btn_group.addButton(self.greater_cap_radio)
        self.greater_btn_group.addButton(self.greater_na_radio)
        
        greater_layout.addWidget(self.greater_keep_radio)
        
        cap_layout = QHBoxLayout()
        cap_layout.addWidget(self.greater_cap_radio)
        self.cap_value_edit = QLineEdit()
        self.cap_value_edit.setPlaceholderText("输入上限值...")
        self.cap_value_edit.setMaximumWidth(150)
        cap_layout.addWidget(self.cap_value_edit)
        cap_layout.addStretch()
        greater_layout.addLayout(cap_layout)
        
        greater_layout.addWidget(self.greater_na_radio)
        greater_group.setLayout(greater_layout)
        scroll_layout.addWidget(greater_group)
        
        # 3. 阳性/阴性文本
        text_group = QGroupBox("阳性/阴性文本")
        text_layout = QVBoxLayout()
        
        self.positive_examples_label = QLabel("阳性示例: 暂无")
        text_layout.addWidget(self.positive_examples_label)
        
        self.negative_examples_label = QLabel("阴性示例: 暂无")
        text_layout.addWidget(self.negative_examples_label)
        
        self.text_btn_group = QButtonGroup()
        self.text_convert_radio = QRadioButton("转换为数值 (阳性=1, 弱阳性=0.5, 阴性=0)")
        self.text_na_radio = QRadioButton("全部设为 NA")
        
        self.text_convert_radio.setChecked(True)
        self.text_btn_group.addButton(self.text_convert_radio)
        self.text_btn_group.addButton(self.text_na_radio)
        
        text_layout.addWidget(self.text_convert_radio)
        text_layout.addWidget(self.text_na_radio)
        text_group.setLayout(text_layout)
        scroll_layout.addWidget(text_group)
        
        # 4. 无效/干扰值
        invalid_group = QGroupBox("无效/干扰值")
        invalid_layout = QVBoxLayout()
        
        self.invalid_examples_label = QLabel("示例: 暂无")
        invalid_layout.addWidget(self.invalid_examples_label)
        
        invalid_desc = QLabel("这些值将被设为 NA，并在 value_flag 中标记为 'invalid'")
        invalid_layout.addWidget(invalid_desc)
        
        invalid_group.setLayout(invalid_layout)
        scroll_layout.addWidget(invalid_group)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # 导航按钮
        self.nav_buttons = NavigationButtons(show_previous=True)
        self.nav_buttons.next_clicked.connect(self.on_next)
        self.nav_buttons.previous_clicked.connect(self.previous_step.emit)
        self.nav_buttons.cancel_clicked.connect(self.cancel.emit)
        layout.addWidget(self.nav_buttons)
        
        self.setLayout(layout)
    
    def load_data(self, data: dict):
        """加载数据并分析特殊值"""
        self.df_preview = data['df_preview']
        self.mapper = data['mapper']
        
        # 应用映射
        df_mapped = self.mapper.apply(self.df_preview)
        
        if 'test_value' not in df_mapped.columns:
            return
        
        # 检测特殊值模式
        self.special_patterns = detect_special_value_patterns(df_mapped['test_value'])
        
        # 检测数值格式分布
        format_info = detect_value_formats(df_mapped['test_value'])
        self._update_format_preview(format_info)
        
        # 更新示例显示
        if self.special_patterns['less_than']:
            examples = ', '.join(self.special_patterns['less_than'][:5])
            self.less_examples_label.setText(f"示例: {examples}")
        
        if self.special_patterns['greater_than']:
            examples = ', '.join(self.special_patterns['greater_than'][:5])
            self.greater_examples_label.setText(f"示例: {examples}")
        
        if self.special_patterns['positive']:
            examples = ', '.join(self.special_patterns['positive'][:5])
            self.positive_examples_label.setText(f"阳性示例: {examples}")
        
        if self.special_patterns['negative']:
            examples = ', '.join(self.special_patterns['negative'][:5])
            self.negative_examples_label.setText(f"阴性示例: {examples}")
        
        if self.special_patterns['invalid']:
            examples = ', '.join(self.special_patterns['invalid'][:10])
            self.invalid_examples_label.setText(f"示例: {examples}")
    
    def _update_format_preview(self, format_info: dict):
        """更新格式预览显示"""
        counts = format_info['format_counts']
        samples = format_info['samples']
        total = format_info['total']
        
        if total == 0:
            self.format_stats_label.setText("⚠️ 未检测到数据")
            return
        
        # 格式名称映射
        format_names = {
            'normal': '普通数字',
            'scientific': '科学计数法',
            'power': '幂表示',
            'titer': '滴度格式',
            'range': '区间格式',
            'less_than': '小于号',
            'greater_than': '大于号',
            'text_positive': '阳性文本',
            'text_negative': '阴性文本',
            'invalid': '无法识别'
        }
        
        # 构建统计文本
        stats_lines = []
        stats_lines.append(f"<b>检测到 {total} 个唯一值样本：</b><br>")
        
        # 按数量排序显示
        sorted_formats = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        for format_type, count in sorted_formats:
            if count > 0:
                percentage = (count / total) * 100
                format_name = format_names.get(format_type, format_type)
                
                # 获取样本
                sample_list = samples.get(format_type, [])
                sample_text = ', '.join(sample_list[:3]) if sample_list else '无'
                
                # 根据数量选择图标
                if percentage >= 50:
                    icon = "✓"
                elif percentage >= 10:
                    icon = "⚠"
                else:
                    icon = "•"
                
                stats_lines.append(
                    f"{icon} <b>{format_name}</b>: {count} ({percentage:.1f}%) "
                    f"<span style='color:gray;'>(示例: {sample_text})</span>"
                )
        
        # 添加说明
        stats_lines.append("<br><i>提示：滴度格式将提取冒号后的数值，区间格式将取中值</i>")
        
        self.format_stats_label.setText("<br>".join(stats_lines))
    
    def get_parsing_rules(self) -> dict:
        """获取解析规则"""
        rules = {
            'less_than': {},
            'greater_than': {},
            'positive_text': {'mapping': {}},
            'negative_text': {'mapping': {}},
            'invalid_values': {'mapping': {}}
        }
        
        # 小于号规则
        if self.less_half_radio.isChecked():
            rules['less_than']['rule'] = 'half'
        elif self.less_bound_radio.isChecked():
            rules['less_than']['rule'] = 'lower_bound'
        else:
            rules['less_than']['rule'] = 'na'
        
        # 大于号规则
        if self.greater_keep_radio.isChecked():
            rules['greater_than']['rule'] = 'keep'
        elif self.greater_cap_radio.isChecked():
            rules['greater_than']['rule'] = 'cap'
            try:
                cap_value = float(self.cap_value_edit.text())
                rules['greater_than']['cap_value'] = cap_value
            except:
                rules['greater_than']['rule'] = 'keep'
        else:
            rules['greater_than']['rule'] = 'na'
        
        # 阳性/阴性文本
        if self.text_convert_radio.isChecked():
            # 默认映射
            for val in self.special_patterns.get('positive', []):
                if '弱' in val or '±' in val:
                    rules['positive_text']['mapping'][val] = 0.5
                else:
                    rules['positive_text']['mapping'][val] = 1
            
            for val in self.special_patterns.get('negative', []):
                rules['negative_text']['mapping'][val] = 0
        else:
            # 全部 NA
            for val in self.special_patterns.get('positive', []):
                rules['positive_text']['mapping'][val] = None
            for val in self.special_patterns.get('negative', []):
                rules['negative_text']['mapping'][val] = None
        
        # 无效值
        for val in self.special_patterns.get('invalid', []):
            rules['invalid_values']['mapping'][val] = None
        
        return rules
    
    def on_next(self):
        """下一步"""
        rules = self.get_parsing_rules()
        
        data = {
            'value_parsing': rules
        }
        
        self.next_step.emit(data)

